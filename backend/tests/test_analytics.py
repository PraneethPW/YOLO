from datetime import datetime,timezone
from uuid import uuid4
from app.analytics import sample_values


def test_recordings_use_playback_time_not_upload_time():
    source,job=uuid4(),uuid4()
    sample=sample_values(source,job,11.25,[],42,11.25,datetime(2026,10,8,tzinfo=timezone.utc))
    assert sample[1:4]==(str(job),job,2)
    assert sample[6:9]==(11.25,11.25,1)


def test_live_history_uses_wall_clock_and_separate_session():
    at=datetime(2026,10,8,12,30,7,tzinfo=timezone.utc)
    sample=sample_values(uuid4(),None,None,[],42,987.1,at)
    assert sample[1:4]==('live',None,int(at.timestamp()//5))
    assert sample[6:8]==(None,None)


def test_vehicle_mix_counts_observations_per_analyzed_frame():
    tracks=[{'class':'car','id':1},{'class':'car','id':2},{'class':'motorcycle','id':3},{'class':'truck','id':4}]
    sample=sample_values(uuid4(),uuid4(),0,tracks,85.4,0)
    assert sample[8:16]==(1,4,4,2,1,0,1,85.4)
    # The same tracked vehicle appearing in another frame remains another observation.
    later=sample_values(sample[0],sample[2],.25,tracks[:1],12,.25)
    assert later[9]==1 and later[11]==1


def test_bucket_boundary_and_duplicate_stamp_are_preserved():
    source,job=uuid4(),uuid4()
    a=sample_values(source,job,4.99,[],1,4.99)
    b=sample_values(source,job,5,[],1,5)
    assert a[3]==0 and b[3]==1
    assert b[-1]==5
