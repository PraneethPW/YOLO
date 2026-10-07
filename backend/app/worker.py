import hashlib
import hmac
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4
import cv2
import httpx
from psycopg import OperationalError, InterfaceError
from . import db
from .config import settings
from .detector import detector
from .security import safe_url

log = logging.getLogger('accident-alert')
shutdown = threading.Event()
streams = {}
stream_lock = threading.Lock()


def save_jpeg(filename, frame):
    ok, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        raise ValueError('Unable to encode evidence frame')
    dest = settings.media / filename
    tmp = dest.with_suffix('.tmp')
    tmp.write_bytes(buffer.tobytes())
    os.replace(tmp, dest)
    return filename


def enqueue_alerts(incident_id):
    db.query('''INSERT INTO alert_deliveries(id,incident_id,target_id)
                SELECT gen_random_uuid(),%s,t.id FROM alert_targets t WHERE t.enabled
                AND EXISTS (SELECT 1 FROM incidents i JOIN sources s ON s.id=i.source_id
                            JOIN users u ON u.id=s.created_by WHERE i.id=%s AND u.role<>'visitor')
                ON CONFLICT(incident_id,target_id) DO NOTHING''', (incident_id,incident_id))
    db.event('alert', {'incident_id': str(incident_id)})


def process_frame(source_id, frame, timestamp, job_id=None, video_seconds=None):
    started = time.monotonic()
    if frame is None or frame.size == 0:
        raise ValueError('The image is empty')
    height, width = frame.shape[:2]
    if max(height,width) > 1280:
        frame = cv2.resize(frame, (int(width*1280/max(height,width)), int(height*1280/max(height,width))))
    tracks,candidates,annotated = detector.analyze(str(source_id), frame, timestamp)
    save_jpeg(f'{source_id}-latest.jpg', annotated)
    fps = round(1/max(0.001,time.monotonic()-started),2)
    updated = db.query("""WITH updated AS (
        UPDATE sources SET tracks=%s::jsonb,fps=%s,last_frame_at=now(),last_error=NULL,
        lease_expires_at=CASE WHEN kind='webcam' THEN now()+interval '60 seconds' ELSE NULL END
        WHERE id=%s RETURNING id,tracks,fps,last_frame_at,created_by
    ), published AS (
        INSERT INTO events(kind,payload,owner_id)
        SELECT 'frame',jsonb_build_object('id',id,'tracks',tracks,'fps',fps,'last_frame_at',last_frame_at),created_by
        FROM updated RETURNING id
    ) SELECT last_frame_at FROM updated,published""",(json.dumps(tracks),fps,source_id),one=True)
    for candidate in candidates:
        if job_id and db.query('SELECT id FROM incidents WHERE job_id=%s AND video_seconds=%s',(job_id,video_seconds),one=True):
            continue
        incident_id = uuid4()
        snapshot = save_jpeg(f'{incident_id}.jpg', annotated)
        db.query('''INSERT INTO incidents(id,source_id,job_id,score,signals,snapshot_path,video_seconds)
                    VALUES(%s,%s,%s,%s,%s::jsonb,%s,%s)''',
                    (incident_id,source_id,job_id,candidate['score'],json.dumps(candidate['signals']),snapshot,video_seconds))
        db.event('incident', {'id': str(incident_id), 'source_id': str(source_id)})
        if settings.auto_alert_candidates:
            # Explicit operator configuration: message remains marked UNCONFIRMED.
            enqueue_alerts(incident_id)
    return {'tracks': tracks, 'processing_fps': fps, 'candidates': len(candidates),
            'processed_at':updated['last_frame_at'],'processing_ms':round((time.monotonic()-started)*1000),
            'frame_width': annotated.shape[1], 'frame_height': annotated.shape[0]}


def run_job(job):
    source_id = job['source_id']
    capture = None
    try:
        detector.reset(str(source_id))
        capture = cv2.VideoCapture(job['path'])
        if not capture.isOpened():
            raise ValueError('Video cannot be decoded. Upload an MP4, MOV, AVI, or WebM video.')
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 240:
            fps = 25
        stride = max(1,int(fps/4))
        db.query("UPDATE sources SET status='processing',last_error=NULL WHERE id=%s", (source_id,))
        db.query('UPDATE jobs SET total_frames=%s WHERE id=%s', (total,job['id']))
        index = 0
        while not shutdown.is_set():
            current = db.query('SELECT status FROM jobs WHERE id=%s', (job['id'],),one=True)
            if current['status'] == 'cancelled':
                break
            # Decode every frame, infer 4 samples per second of source footage.
            ok, frame = capture.read()
            if not ok:
                if total > 0 and index < total * 0.95:
                    raise ValueError('Video ended before its declared frame count. File may be damaged.')
                break
            index += 1
            if (index-1) % stride:
                continue
            process_frame(source_id,frame,index/fps,job['id'],index/fps)
            progress = min(0.999,index/max(1,total))
            db.query('UPDATE jobs SET progress=%s,processed_frames=%s WHERE id=%s', (progress,index,job['id']))
            db.event('job', {'id': str(job['id']), 'progress': progress})
        if shutdown.is_set():
            db.query("UPDATE jobs SET status='queued' WHERE id=%s AND status='processing'", (job['id'],))
        else:
            db.query("UPDATE jobs SET status='completed',progress=1,processed_frames=%s,finished_at=now() WHERE id=%s AND status='processing'", (index,job['id']))
        db.query("UPDATE sources SET status='idle' WHERE id=%s", (source_id,))
    except Exception as exc:
        if isinstance(exc, (OperationalError, InterfaceError)):
            message = 'Analysis was interrupted by a connection problem. Retry using your saved video.'
        elif isinstance(exc, ValueError):
            message = str(exc)[:400]
        else:
            message = 'Video analysis stopped unexpectedly. Retry using your saved video.'
        log.error('Video processing failed: %s', type(exc).__name__)
        db.query("UPDATE jobs SET status='failed',error=%s,finished_at=now() WHERE id=%s", (message,job['id']))
        db.query("UPDATE sources SET status='error',last_error=%s WHERE id=%s", (message,source_id))
    finally:
        if capture:
            capture.release()
        detector.reset(str(source_id))
        db.event('job', {'id': str(job['id'])})


def video_worker():
    while not shutdown.wait(1):
        try:
            with db.connection() as conn:
                job = conn.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1").fetchone()
                if job:
                    conn.execute("UPDATE jobs SET status='processing' WHERE id=%s", (job['id'],))
            if job:
                run_job(job)
        except Exception as exc:
            log.error('Worker unavailable: %s',type(exc).__name__)
            shutdown.wait(5)


def run_stream(source, stop):
    cap = None
    try:
        safe_url(source['stream_url'],settings.camera_allowed_hosts,('https','http','rtsp','rtsps'))
        cap = cv2.VideoCapture(source['stream_url'],cv2.CAP_FFMPEG,
                [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,15000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,10000])
        if not cap.isOpened():
            raise ValueError('Camera connection failed. Verify stream URL and network access.')
        db.query("UPDATE sources SET status='live',last_error=NULL WHERE id=%s", (source['id'],))
        last = 0
        while not stop.is_set() and not shutdown.is_set():
            ok,frame = cap.read()
            if not ok:
                raise ValueError('Camera stream disconnected. Restart monitoring to reconnect.')
            now = time.monotonic()
            if now-last < 0.3:
                continue
            process_frame(source['id'],frame,now)
            last = now
        db.query("UPDATE sources SET status='idle' WHERE id=%s", (source['id'],))
    except Exception as exc:
        # Never expose a stream URL in an exception or audit record.
        db.query("UPDATE sources SET status='error',last_error=%s WHERE id=%s", ('Camera processing failed. Check server logs and stream access.',source['id']))
        log.error('Camera worker failed: %s',type(exc).__name__)
    finally:
        if cap:
            cap.release()
        detector.reset(str(source['id']))
        with stream_lock:
            streams.pop(str(source['id']),None)
        db.event('source', {'id': str(source['id'])})


def start_stream(source):
    with stream_lock:
        if str(source['id']) in streams:
            return
        if len(streams) >= 3:
            raise ValueError('This deployment supports up to three concurrent CCTV sources')
        stop = threading.Event()
        thread = threading.Thread(target=run_stream,args=(source,stop),daemon=True)
        streams[str(source['id'])] = (stop,thread)
        thread.start()


def stop_stream(source_id):
    with stream_lock:
        entry = streams.get(str(source_id))
        if entry:
            entry[0].set()


def alert_worker():
    while not shutdown.wait(2):
        try:
            deliveries = db.query('''SELECT d.*,t.url,t.secret,t.enabled FROM alert_deliveries d
                                     JOIN alert_targets t ON t.id=d.target_id
                                     WHERE d.status='pending' AND d.next_attempt_at<=now() LIMIT 10''')
            for delivery in deliveries:
                if not delivery['enabled']:
                    db.query("UPDATE alert_deliveries SET status='cancelled' WHERE id=%s", (delivery['id'],))
                    continue
                incident = db.query('''SELECT i.id,i.status,i.score,i.signals,i.detected_at,s.name AS source,
                                       s.location,s.latitude,s.longitude FROM incidents i
                                       JOIN sources s ON s.id=i.source_id WHERE i.id=%s''',(delivery['incident_id'],),one=True)
                if incident['status'] == 'dismissed':
                    db.query("UPDATE alert_deliveries SET status='cancelled' WHERE id=%s", (delivery['id'],))
                    continue
                payload = json.dumps({'delivery_id':str(delivery['id']), 'event':'accident_alert',
                                      'incident':incident}, default=str,sort_keys=True).encode()
                code = None
                error = None
                try:
                    safe_url(delivery['url'],settings.webhook_allowed_hosts)
                    signature = hmac.new(delivery['secret'].encode(),payload,hashlib.sha256).hexdigest()
                    with httpx.Client(timeout=15,follow_redirects=False) as client:
                        response = client.post(delivery['url'],content=payload,headers={
                            'Content-Type':'application/json','X-AccidentAlert-Signature':f'sha256={signature}',
                            'Idempotency-Key':str(delivery['id'])})
                    code = response.status_code
                    if not 200 <= code < 300:
                        error = f'Receiver returned HTTP {code}'
                except Exception as exc:
                    error = f'Delivery failed: {type(exc).__name__}'
                attempts = delivery['attempts']+1
                status = 'delivered' if error is None else ('failed' if attempts>=5 else 'pending')
                db.query('''UPDATE alert_deliveries SET status=%s,attempts=%s,response_code=%s,last_error=%s,
                             next_attempt_at=now()+(%s * interval '1 second'),
                             delivered_at=CASE WHEN %s='delivered' THEN now() ELSE NULL END WHERE id=%s''',
                             (status,attempts,code,error,min(300,2**attempts*5),status,delivery['id']))
                db.event('alert', {'id':str(delivery['id']),'status':status})
        except Exception as exc:
            log.error('Alert worker unavailable: %s',type(exc).__name__)
            shutdown.wait(5)


def start():
    shutdown.clear()
    db.query("UPDATE jobs SET status='queued' WHERE status='processing'")
    db.query("UPDATE sources SET status='idle' WHERE status IN ('live','processing')")
    threading.Thread(target=video_worker,daemon=True).start()
    threading.Thread(target=alert_worker,daemon=True).start()
    threading.Thread(target=lease_worker,daemon=True).start()


def lease_worker():
    while not shutdown.wait(10):
        try:
            stale=db.query("UPDATE sources SET status='idle',lease_expires_at=NULL WHERE kind='webcam' AND status='live' AND lease_expires_at<now() RETURNING id")
            for source in stale:
                detector.reset(str(source['id']))
                db.event('source',{'id':str(source['id'])})
            db.query("UPDATE jobs SET status='cancelled',finished_at=now() WHERE status IN ('queued','processing') AND source_id IN (SELECT s.id FROM sources s JOIN users u ON u.id=s.created_by WHERE u.role='visitor' AND u.visitor_expires_at<now())")
        except Exception as exc:
            log.error('Camera lease recovery failed: %s',type(exc).__name__)


def stop():
    shutdown.set()
    for entry in list(streams.values()):
        entry[0].set()
