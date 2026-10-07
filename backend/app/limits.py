from fastapi import HTTPException
from starlette.responses import JSONResponse
from .config import settings


class BodyLimitMiddleware:
    def __init__(self,app):
        self.app=app

    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope.get('method') in ('GET','HEAD','OPTIONS'):
            return await self.app(scope,receive,send)
        path=scope.get('path','')
        limit=(settings.max_upload_mb*1024*1024+1024*1024 if path.endswith('/upload')
               else 2_100_000 if path.endswith('/frame') else 65_536)
        headers=dict(scope['headers'])
        try:
            declared=int(headers.get(b'content-length',b'0'))
        except ValueError:
            return await JSONResponse({'detail':'Invalid content length'},400)(scope,receive,send)
        if declared>limit:
            return await JSONResponse({'detail':'Request exceeds the upload size limit'},413)(scope,receive,send)
        size=0
        async def bounded_receive():
            nonlocal size
            message=await receive()
            if message['type']=='http.request':
                size+=len(message.get('body',b''))
                if size>limit:
                    raise HTTPException(413,'Request exceeds the upload size limit')
            return message
        await self.app(scope,bounded_receive,send)
