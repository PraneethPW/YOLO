import hashlib
import ipaddress
import secrets
import socket
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from time import monotonic
from urllib.parse import urlsplit
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from . import db
from .config import settings

hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)
limits = defaultdict(deque)


def throttle(key, count=10, period=60):
    now = monotonic()
    q = limits[key]
    while q and q[0] < now - period:
        q.popleft()
    if len(q) >= count:
        raise HTTPException(429, 'Too many requests. Please try again shortly.')
    q.append(now)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_ok(value, encoded):
    try:
        return hasher.verify(encoded, value)
    except VerificationError:
        return False


def session(user, response: Response):
    refresh = secrets.token_urlsafe(48)
    expiry = user.get('visitor_expires_at') or datetime.now(timezone.utc) + timedelta(days=7)
    if expiry <= datetime.now(timezone.utc):
        raise HTTPException(401, 'Your private session has ended. Start a new session from the home page.')
    db.query('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(%s,%s,%s)',
             (digest(refresh), user['id'], expiry))
    response.set_cookie('aa_refresh', refresh, httponly=True, secure=settings.cookie_secure,
                        samesite='lax', max_age=max(1,int((expiry-datetime.now(timezone.utc)).total_seconds())), path='/api/auth')
    return access(user)


def access(user):
    payload = {'sub': str(user['id']), 'exp': datetime.now(timezone.utc) + timedelta(minutes=15)}
    return {'access_token': jwt.encode(payload, settings.jwt_secret, algorithm='HS256'),
            'user': {k: user[k] for k in ('id','name','email','role')}}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, 'Please sign in')
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=['HS256'])
        user = db.query('SELECT * FROM users WHERE id=%s', (payload['sub'],), one=True)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, 'Session expired')
    if not user or (user.get('visitor_expires_at') and user['visitor_expires_at'] <= datetime.now(timezone.utc)):
        raise HTTPException(401, 'Session expired')
    if user['role']=='visitor':
        raise HTTPException(401, 'Sign in or register to access the video dashboard')
    return user


def source_scope(user, alias='s'):
    # Shared recordings are visible to registered accounts. Personal uploads stay private.
    return (f"({alias}.is_shared OR {alias}.created_by=%s OR "
            f"(%s IN ('admin','operator') AND EXISTS (SELECT 1 FROM users owner "
            f"WHERE owner.id={alias}.created_by AND owner.role IN ('admin','operator'))))",
            (user['id'],user['role']))


def can_manage_source(source,user):
    if source['created_by']==user['id'] or user['role']=='admin':
        return True
    if user['role']=='operator':
        owner=db.query('SELECT role FROM users WHERE id=%s',(source['created_by'],),one=True)
        return bool(owner and owner['role'] in ('admin','operator'))
    return False


def admin(user=Depends(current_user)):
    if user['role'] != 'admin':
        raise HTTPException(403, 'Administrator access required')
    return user


def safe_url(url, allowed_hosts, protocols=('https',)):
    parsed = urlsplit(url)
    if parsed.scheme not in protocols or not parsed.hostname or parsed.fragment:
        raise HTTPException(422, 'Invalid source URL or protocol')
    if parsed.username or parsed.password:
        raise HTTPException(422, 'Credentials embedded in URLs are not supported')
    host = parsed.hostname.lower()
    allow = {h.strip().lower() for h in allowed_hosts.split(',') if h.strip()}
    # All remote camera/alert hosts must be explicitly approved by the deployer.
    # Prevent arbitrary destinations and DNS rebinding from public API input.
    if host not in allow:
        raise HTTPException(422, 'This host must be added to the server allowlist first')
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 554))
    except socket.gaierror:
        raise HTTPException(422, 'Host could not be resolved')
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            raise HTTPException(422, 'Localhost and metadata addresses are not allowed')
    return url


def audit(user, action, resource=None, detail=None):
    import json
    db.query('INSERT INTO audit_log(actor_id,action,resource_id,detail) VALUES(%s,%s,%s,%s::jsonb)',
             (user['id'], action, resource, json.dumps(detail or {})))
