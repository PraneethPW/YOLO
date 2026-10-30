from datetime import datetime,timedelta,timezone
from uuid import uuid4
import cv2
import numpy as np
import pytest
from fastapi import HTTPException
from app import incident_service as service
from app.config import settings


def test_published_references_are_read_only_even_for_admin():
    owner=uuid4()
    row={'origin':'reference','reported_by':None,'_source_owner':owner}
    assert not service.can_review(row,{'id':owner,'role':'admin'})
    row['reported_by']=uuid4()
    assert service.can_review(row,{'id':row['reported_by'],'role':'member'})


def test_shared_source_does_not_grant_incident_review():
    row={'origin':'automated','reported_by':None,'_source_owner':uuid4(),'_owner_role':'admin'}
    assert not service.can_review(row,{'id':uuid4(),'role':'member'})
    assert service.can_review(row,{'id':uuid4(),'role':'operator'})


def test_scope_requires_private_report_owner_for_every_role():
    for role in ('member','operator','admin'):
        user={'id':uuid4(),'role':role}
        sql,params=service.incident_scope(user)
        assert 'i.reported_by IS NULL OR i.reported_by=%s' in sql
        assert params[-1]==user['id']


@pytest.mark.parametrize('seconds',[-1,10,11])
def test_rejects_out_of_range_video_evidence(seconds):
    with pytest.raises(HTTPException) as caught:
        service.validate_video_time(seconds,10)
    assert caught.value.status_code==422


def test_camera_reports_require_a_fresh_frame(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'data_dir',str(tmp_path))
    identity=uuid4()
    source={'id':identity,'kind':'stream','last_frame_at':datetime.now(timezone.utc)-timedelta(seconds=31)}
    (tmp_path/f'{identity}-latest.jpg').write_bytes(b'old')
    with pytest.raises(HTTPException) as caught:
        service.capture_report(source,None,0,uuid4())
    assert caught.value.status_code==409
    source['last_frame_at']=datetime.now(timezone.utc)
    result=service.capture_report(source,None,0,uuid4())
    assert result.read_bytes()==b'old'


def test_recording_report_saves_selected_frame(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'data_dir',str(tmp_path))
    path=tmp_path/'source.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10,(32,32))
    for index in range(20): writer.write(np.full((32,32,3),index*10,dtype=np.uint8))
    writer.release()
    result=service.capture_report({'kind':'upload'},{'path':str(path)},1,uuid4())
    frame=cv2.imread(str(result))
    assert frame is not None and 90<=float(frame.mean())<=115
    with pytest.raises(HTTPException): service.capture_report({'kind':'upload'},{'path':str(path)},2,uuid4())


def test_event_is_private_even_when_payload_has_shared_source(monkeypatch):
    calls=[]
    identity=uuid4();owner=uuid4();source=uuid4()
    def query(sql,params=(),one=False):
        calls.append((sql,params))
        if sql.startswith('SELECT'): return {'source_id':source,'created_by':owner,'is_private':True}
    monkeypatch.setattr(service.db,'query',query)
    service.db.event('incident',{'id':str(identity),'source_id':str(source)})
    assert 'coalesce(i.reported_by' in calls[0][0]
    assert calls[-1][1][-3:]==(owner,source,True)
