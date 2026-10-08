from uuid import uuid4
from app import security


def test_members_can_manage_their_own_source():
    identity=uuid4()
    assert security.can_manage_source({'created_by':identity},{'id':identity,'role':'member'})


def test_shared_visibility_does_not_grant_management():
    source={'created_by':uuid4(),'is_shared':True}
    for role in ('member','visitor'):
        assert not security.can_manage_source(source,{'id':uuid4(),'role':role})


def test_operator_cannot_manage_a_members_personal_upload(monkeypatch):
    monkeypatch.setattr(security.db,'query',lambda *args,**kwargs:{'role':'member'})
    assert not security.can_manage_source({'created_by':uuid4()},{'id':uuid4(),'role':'operator'})


def test_operator_retains_management_of_staff_sources(monkeypatch):
    monkeypatch.setattr(security.db,'query',lambda *args,**kwargs:{'role':'admin'})
    assert security.can_manage_source({'created_by':uuid4()},{'id':uuid4(),'role':'operator'})
