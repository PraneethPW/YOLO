import json
import shutil
import cv2
import numpy as np
import pytest
from app.replay import fit_size,draw_tracks,ReplayWriter,replay_path,info_path
from app.config import settings


def test_replay_dimensions_are_even_and_bounded():
    assert fit_size(1920,1080)==(960,540)
    assert fit_size(641,361)==(640,360)
    assert max(fit_size(720,1280))<=960


def test_boxes_follow_the_measured_frame_coordinate_system():
    frame=np.zeros((100,200,3),dtype=np.uint8)
    tracks=[{'id':7,'class':'car','confidence':.85,'box':[100,80,300,160]}]
    annotated=draw_tracks(frame,tracks,400,200)
    assert annotated[60,50].any() # measured x=100 maps to rendered x=50
    assert not frame.any() # evidence input is never modified
    assert not annotated[90,190].any()


def test_encoded_replay_keeps_timing_and_observation_metadata(tmp_path,monkeypatch):
    if not shutil.which(settings.ffmpeg_binary):
        pytest.skip('FFmpeg is required for replay encoding integration')
    monkeypatch.setattr(settings,'data_dir',str(tmp_path))
    writer=ReplayWriter('encoding-test',160,90,8)
    try:
        tracks=[{'id':1,'class':'car','confidence':.9,'box':[20,20,70,60]}]
        for index in range(12):
            if index%2==0:
                writer.observe(index/8,tracks)
            writer.write(np.zeros((90,160,3),dtype=np.uint8),tracks,160,90)
        writer.finish()
        metadata=json.loads(info_path('encoding-test').read_text())
        assert metadata['duration']==1.5 and metadata['recorded'] is True
        assert [m['seconds'] for m in metadata['measurements']]==[0,.25,.5,.75,1,1.25]
        cap=cv2.VideoCapture(str(replay_path('encoding-test')))
        assert cap.isOpened() and int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==12
        assert cap.get(cv2.CAP_PROP_FPS)==8
        cap.release()
        assert not writer.temp.exists()
    finally:
        writer.abort()


def test_interrupted_encoding_never_publishes_a_partial_replay(tmp_path,monkeypatch):
    if not shutil.which(settings.ffmpeg_binary):
        pytest.skip('FFmpeg is required for replay encoding integration')
    monkeypatch.setattr(settings,'data_dir',str(tmp_path))
    writer=ReplayWriter('interrupted-test',160,90,8)
    writer.write(np.zeros((90,160,3),dtype=np.uint8),[],160,90)
    writer.abort()
    assert writer.process.poll() is not None
    assert not replay_path('interrupted-test').exists()
    assert not info_path('interrupted-test').exists()
    assert not writer.temp.exists()
