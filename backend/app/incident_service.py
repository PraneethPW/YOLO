"""Scoped accident reports, reference cases and persistent in-app alert state."""
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4,uuid5,NAMESPACE_URL
import cv2
from fastapi import HTTPException
from . import db
from .config import settings
from .security import source_scope

INCIDENT_SELECT='''SELECT i.*,s.name AS source_name,s.location,s.latitude,s.longitude,s.kind AS source_kind,
 s.created_by AS _source_owner,u.role AS _owner_role,j.path AS _video_path
 FROM incidents i JOIN sources s ON s.id=i.source_id JOIN users u ON u.id=s.created_by
 LEFT JOIN jobs j ON j.id=i.job_id'''


def incident_scope(user):
    scope,params=source_scope(user)
    return f"({scope}) AND (i.reported_by IS NULL OR i.reported_by=%s)",(*params,user['id'])


def can_review(row,user):
    if row.get('origin')=='reference' and not row.get('reported_by'):
        return False
    return (row.get('reported_by')==user['id'] or row.get('_source_owner')==user['id']
        or user['role']=='admin' or (user['role']=='operator' and row.get('_owner_role') in ('admin','operator')))


def decorate(rows,user):
    for row in rows:
        row['can_review']=can_review(row,user)
        row['evidence_available']=(settings.media/row['snapshot_path']).is_file()
        path=row.pop('_video_path',None)
        row['video_available']=bool(path and Path(path).is_file())
        row.pop('_source_owner',None)
        row.pop('_owner_role',None)
    return rows


def validate_video_time(seconds,duration):
    if seconds<0 or seconds>=duration:
        raise HTTPException(422,'Select a timestamp inside the recording')
    return seconds


def capture_report(source,job,seconds,identity):
    target=settings.media/f'{identity}.jpg'
    if source['kind']=='upload':
        if not job or not Path(job['path']).is_file():
            raise HTTPException(404,'The original video is unavailable')
        capture=cv2.VideoCapture(job['path'])
        try:
            fps=capture.get(cv2.CAP_PROP_FPS)
            frames=capture.get(cv2.CAP_PROP_FRAME_COUNT)
            if not capture.isOpened() or fps<=0 or frames<=0:
                raise HTTPException(422,'This recording cannot be decoded')
            validate_video_time(seconds,frames/fps)
            capture.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
            ok,frame=capture.read()
            if not ok:
                raise HTTPException(422,'The selected frame cannot be decoded')
            h,w=frame.shape[:2]
            if max(h,w)>1280:
                frame=cv2.resize(frame,(int(w*1280/max(h,w)),int(h*1280/max(h,w))))
            if not cv2.imwrite(str(target),frame):
                raise HTTPException(500,'The evidence frame could not be saved')
        finally:
            capture.release()
    else:
        stamp=source.get('last_frame_at')
        latest=settings.media/f"{source['id']}-latest.jpg"
        if not stamp or (datetime.now(timezone.utc)-stamp).total_seconds()>30 or not latest.is_file():
            raise HTTPException(409,'Start this camera and wait for a fresh analyzed frame before reporting')
        shutil.copyfile(latest,target)
    return target


def create_report(source,job,seconds,notes,user):
    identity=uuid4()
    snapshot=capture_report(source,job,seconds,identity)
    signals={'method':'Operator-selected evidence','score_type':'operator report','track_ids':[],
             'supporting_frames':0,'required_frames':0,'window_seconds':0,'overlap':0,'motion':[]}
    try:
        db.query('''INSERT INTO incidents(id,source_id,job_id,score,signals,snapshot_path,video_seconds,
                    origin,reported_by,is_training,notes)
                    VALUES(%s,%s,%s,0,%s::jsonb,%s,%s,'operator',%s,%s,%s)''',
            (identity,source['id'],job['id'] if job else None,json.dumps(signals),snapshot.name,
             seconds if job else None,user['id'],bool(source.get('is_case_study')),notes))
    except Exception:
        snapshot.unlink(missing_ok=True)
        raise
    db.event('incident',{'id':str(identity),'source_id':str(source['id']),
                        'origin':'operator','is_training':bool(source.get('is_case_study'))})
    return identity


def create_practice(reference,user):
    if not reference.get('is_training') or reference.get('reported_by'):
        raise HTTPException(422,'Choose a published recorded case to start a practice review')
    if not reference.get('evidence_available') or not reference.get('video_available'):
        raise HTTPException(409,'This case is still preparing its evidence and video')
    identity=uuid5(NAMESPACE_URL,f"accident-alert:practice:{user['id']}:{reference['id']}")
    inserted=db.query('''INSERT INTO incidents(id,source_id,job_id,score,signals,snapshot_path,video_seconds,
              origin,is_training,reported_by,practice_of,notes)
              VALUES(%s,%s,%s,%s,%s::jsonb,%s,%s,'reference',true,%s,%s,%s)
              ON CONFLICT(reported_by,practice_of) DO NOTHING RETURNING id''',
        (identity,reference['source_id'],reference['job_id'],reference['score'],json.dumps(reference['signals']),
         reference['snapshot_path'],reference['video_seconds'],user['id'],reference['id'],
         'Private practice review of recorded accident footage.'),one=True)
    if inserted:
        db.event('incident',{'id':str(identity),'source_id':str(reference['source_id']),
                            'origin':'reference','is_training':True})
    return identity
