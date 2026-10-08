from datetime import datetime,timedelta,timezone
from uuid import uuid4
import jwt
import pytest
from fastapi.testclient import TestClient
from app import security
from app.main import app

identity=str(uuid4())
paths=['/api/sources','/api/jobs','/api/stats','/api/events','/api/library/sources',
       f'/api/library/jobs/{identity}/replay',f'/api/library/jobs/{identity}/replay/info',
       f'/api/library/sources/{identity}/snapshot',f'/api/jobs/{identity}/replay',
       f'/api/jobs/{identity}/video',f'/api/sources/{identity}/analytics']


def test_anonymous_users_cannot_access_video_or_dashboard_routes():
    client=TestClient(app)
    for path in paths:
        assert client.get(path).status_code==401,path
    assert client.post('/api/auth/visitor').status_code==401


def test_existing_guest_token_cannot_bypass_account_registration(monkeypatch):
    key='isolated-unit-test-signing-key-only'
    monkeypatch.setattr(security.settings,'jwt_secret',key)
    user={'id':identity,'role':'visitor','visitor_expires_at':datetime.now(timezone.utc)+timedelta(hours=1)}
    monkeypatch.setattr(security.db,'query',lambda *args,**kwargs:user)
    token=jwt.encode({'sub':identity,'exp':datetime.now(timezone.utc)+timedelta(minutes=5)},key,algorithm='HS256')
    client=TestClient(app,headers={'Authorization':'Bearer '+token})
    for path in paths:
        assert client.get(path).status_code==401,path


@pytest.mark.parametrize('role',['admin','operator','member'])
def test_registered_accounts_can_access_shared_collection(role,monkeypatch):
    key='isolated-unit-test-signing-key-only'
    monkeypatch.setattr(security.settings,'jwt_secret',key)
    user={'id':identity,'role':role,'visitor_expires_at':None}
    monkeypatch.setattr(security.db,'query',lambda sql,*args,**kwargs:user if sql.startswith('SELECT * FROM users') else [])
    token=jwt.encode({'sub':identity,'exp':datetime.now(timezone.utc)+timedelta(minutes=5)},key,algorithm='HS256')
    client=TestClient(app,headers={'Authorization':'Bearer '+token})
    assert client.get('/api/library/sources').status_code==200
