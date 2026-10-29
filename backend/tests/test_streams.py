import threading
import pytest
from app import worker
from app.main import recording_availability


@pytest.mark.parametrize('fps,expected',[(30,1/30),(0,1/25),(float('nan'),1/25)])
def test_hls_segments_are_paced_at_a_valid_video_rate(fps,expected):
    class Capture:
        def get(self, key): return fps
    assert worker.stream_frame_period('https://camera.example/live.m3u8',Capture())==expected
    assert worker.stream_frame_period('rtsp://camera.example/live',Capture())==0


def test_camera_reconnects_and_releases_each_capture(monkeypatch):
    calls=[]
    captures=[]
    class Signal(threading.Event):
        def wait(self, timeout=None):
            calls.append(('wait',timeout))
            return self.is_set()
    stop=Signal()
    class Capture:
        def __init__(self,*args):
            self.open=len(captures)>0
            self.released=False
            captures.append(self)
        def isOpened(self): return self.open
        def read(self): return True,object()
        def release(self): self.released=True
    monkeypatch.setattr(worker.cv2,'VideoCapture',Capture)
    monkeypatch.setattr(worker,'safe_url',lambda *a:None)
    monkeypatch.setattr(worker.db,'query',lambda sql,*a,**k:calls.append((sql,a)))
    monkeypatch.setattr(worker.db,'event',lambda *a:None)
    monkeypatch.setattr(worker.detector,'reset',lambda *a:None)
    monkeypatch.setattr(worker,'shutdown',threading.Event())
    monkeypatch.setattr(worker,'streams',{})
    monkeypatch.setattr(worker,'process_frame',lambda *a:stop.set())
    worker.run_stream({'id':'camera','stream_url':'https://camera.example/live'},stop)
    assert len(captures)==2
    assert all(c.released for c in captures)
    assert ('wait',2) in calls
    assert any("status='live'" in call[0] for call in calls)
    assert any("status='error'" in call[0] for call in calls)
    assert not worker.streams


def test_stop_persists_desired_state_and_signals_worker(monkeypatch):
    stop=threading.Event()
    writes=[]
    monkeypatch.setattr(worker,'streams',{'camera':(stop,None)})
    monkeypatch.setattr(worker.db,'query',lambda sql,args:writes.append((sql,args)))
    worker.stop_stream('camera')
    assert stop.is_set()
    assert 'monitor_enabled=false' in writes[0][0]
    assert writes[0][1]==('camera',)


def test_only_enabled_unarchived_streams_are_resumed(monkeypatch):
    queries=[]
    resumed=[]
    def read(sql):
        queries.append(sql)
        return [{'id':'camera'}]
    monkeypatch.setattr(worker.db,'query',read)
    monkeypatch.setattr(worker,'start_stream',lambda source:resumed.append(source['id']))
    worker.resume_streams()
    assert resumed==['camera']
    assert "kind='stream' AND monitor_enabled AND NOT archived" in queries[0]


def test_recording_availability_does_not_expose_storage_paths(tmp_path):
    original=tmp_path/'recording.mp4'
    original.write_bytes(b'fixture')
    rows=[{'recording':{'_path':str(original)}},{'recording':{'_path':str(tmp_path/'missing.mp4')}},{'recording':None}]
    assert recording_availability(rows)==[{'recording':{'media_available':True}},
        {'recording':{'media_available':False}},{'recording':None}]
