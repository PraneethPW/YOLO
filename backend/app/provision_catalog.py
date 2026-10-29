"""Explicitly provision the requested real shared media: python -m app.provision_catalog."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL,uuid5
import cv2
import httpx
from . import db,replay
from .config import settings
from .security import safe_url


def provision():
    catalog=json.loads(Path(__file__).with_name('catalog.json').read_text())
    owner=db.query("SELECT id FROM users WHERE role='admin' ORDER BY created_at LIMIT 1",one=True)
    if not owner:
        raise RuntimeError('An administrator account must exist before provisioning shared media')
    for item in catalog['recordings']:
        job=db.query('''SELECT j.* FROM jobs j JOIN sources s ON s.id=j.source_id
            WHERE j.original_name=%s AND s.is_shared ORDER BY j.created_at LIMIT 1''',(item['filename'],),one=True)
        source_id=job['source_id'] if job else uuid5(NAMESPACE_URL,'accident-alert:source:'+item['url'])
        job_id=job['id'] if job else uuid5(NAMESPACE_URL,'accident-alert:job:'+item['url'])
        path=Path(job['path']) if job else settings.media/f'{job_id}.mp4'
        if not path.is_file():
            temp=path.with_suffix('.download')
            try:
                with httpx.stream('GET',item['url'],follow_redirects=True,timeout=60) as response:
                    response.raise_for_status()
                    size=0
                    with temp.open('wb') as out:
                        for chunk in response.iter_bytes():
                            size+=len(chunk)
                            if size>settings.max_upload_mb*1024*1024:
                                raise ValueError('Published recording exceeds the configured upload limit')
                            out.write(chunk)
                capture=cv2.VideoCapture(str(temp))
                try:
                    frames=int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
                    if not capture.isOpened() or frames<1:
                        raise ValueError('Published recording could not be decoded')
                    if job and job['total_frames'] and frames!=job['total_frames']:
                        raise ValueError('Published recording does not match the original recording frame count')
                finally:
                    capture.release()
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
        with db.connection() as conn:
            conn.execute('''INSERT INTO sources(id,name,kind,location,created_by,is_shared,credit,reference_url)
                VALUES(%s,%s,'upload',%s,%s,true,%s,%s) ON CONFLICT(id) DO UPDATE
                SET name=EXCLUDED.name,is_shared=true,archived=false,credit=EXCLUDED.credit,reference_url=EXCLUDED.reference_url''',
                (source_id,item['name'],'Recorded dataset · capture location not supplied',owner['id'],item['credit'],item['reference_url']))
            conn.execute('''INSERT INTO jobs(id,source_id,path,original_name) VALUES(%s,%s,%s,%s)
                ON CONFLICT(id) DO NOTHING''',(job_id,source_id,str(path),item['filename']))
            if not job or job['replay_status']!='ready' or not replay.replay_path(job_id).is_file():
                conn.execute("UPDATE jobs SET status='queued',progress=0,error=NULL,replay_status='pending',replay_error=NULL,finished_at=NULL WHERE id=%s",(job_id,))
                conn.execute("UPDATE sources SET status='processing',last_error=NULL WHERE id=%s",(source_id,))
        print('Recording available:',item['name'],flush=True)
    for camera in catalog['cameras']:
        safe_url(camera['stream_url'],settings.camera_allowed_hosts,('https',))
        identity=uuid5(NAMESPACE_URL,'accident-alert:camera:'+camera['stream_url'])
        db.query('''INSERT INTO sources(id,name,kind,stream_url,location,latitude,longitude,created_by,is_shared,monitor_enabled,credit,reference_url)
            VALUES(%s,%s,'stream',%s,%s,%s,%s,%s,true,true,'Caltrans · public traffic camera','https://quickmap.dot.ca.gov/')
            ON CONFLICT(id) DO UPDATE SET archived=false,monitor_enabled=true,is_shared=true''',
            (identity,camera['name'],camera['stream_url'],camera['location'],camera['latitude'],camera['longitude'],owner['id']))
        print('Live camera configured:',camera['name'],flush=True)
    print('Restart the application to resume the configured cameras.',flush=True)


if __name__=='__main__':
    db.start()
    try:
        provision()
    finally:
        db.close()
