from app.motion import MotionVerifier, iou


def vehicle(identity, x, y=0):
    return {'id':identity,'box':[x,y,x+80,y+50]}


def test_overlap_without_motion_never_triggers():
    detector=MotionVerifier()
    for i in range(50):
        assert detector.update([vehicle(1,0),vehicle(2,10)],i*.25)==[]


def test_sustained_deceleration_and_overlap_create_one_candidate():
    detector=MotionVerifier()
    candidates=[]
    for i in range(8):
        candidates+=detector.update([vehicle(1,i*20),vehicle(2,i*20+5)],i*.25)
    for i in range(8,14):
        candidates+=detector.update([vehicle(1,140),vehicle(2,145)],i*.25)
    assert len(candidates)==1
    evidence=candidates[0]
    assert evidence['signals']['supporting_frames']>=3
    assert evidence['signals']['window_seconds']>=.35
    assert evidence['signals']['score_type']=='heuristic evidence score'
    assert 0<evidence['score']<1


def test_parallel_traffic_does_not_trigger():
    detector=MotionVerifier()
    for i in range(30):
        assert detector.update([vehicle(1,i*20),vehicle(2,i*20+200)],i*.25)==[]


def test_tracks_expire_after_missing_frames():
    detector=MotionVerifier()
    detector.update([vehicle(1,0)],0)
    detector.update([],6)
    assert not detector.history


def test_iou_handles_nonintersecting_boxes():
    assert iou([0,0,10,10],[20,20,30,30])==0
    assert iou([0,0,10,10],[0,0,10,10])==1
