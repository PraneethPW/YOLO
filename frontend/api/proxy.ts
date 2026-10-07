import type {IncomingMessage,ServerResponse} from 'node:http';
import {Readable} from 'node:stream';
export const config = {api:{bodyParser:false},maxDuration:300};

export default async function handler(req:IncomingMessage,res:ServerResponse) {
  const backend = process.env.BACKEND_URL;
  if (!backend) {res.writeHead(503,{'Content-Type':'application/json'});res.end(JSON.stringify({detail:'Backend connection has not been configured'}));return;}
  const incoming = new URL(req.url || '/', 'https://frontend.invalid');
  const path = incoming.searchParams.get('path') || '';
  if (!/^[a-zA-Z0-9_\-/]+$/.test(path) || path.includes('..')) {res.writeHead(400);res.end();return;}
  const target = new URL('/api/'+path,backend);
  for (const [key,value] of incoming.searchParams) if (key!=='path') target.searchParams.append(key,value);
  const headers = new Headers();
  for (const name of ['authorization','content-type','cookie','origin','last-event-id','range']) {
    const value=req.headers[name]; if (typeof value==='string') headers.set(name,value);
  }
  const controller = new AbortController();
  res.on('close',()=>controller.abort());
  try {
    const method=req.method || 'GET';
    const options:RequestInit & {duplex?:string} = {method,headers,redirect:'manual',signal:controller.signal};
    if (!['GET','HEAD'].includes(method)) {options.body=Readable.toWeb(req) as ReadableStream;options.duplex='half';}
    const upstream=await fetch(target,options);
    res.statusCode=upstream.status;
    for (const name of ['content-type','cache-control','content-disposition','content-range','accept-ranges']) {const value=upstream.headers.get(name);if(value)res.setHeader(name,value);}
    const cookies=upstream.headers.getSetCookie();if(cookies.length)res.setHeader('Set-Cookie',cookies);
    res.setHeader('X-Accel-Buffering','no');
    if (upstream.body) Readable.fromWeb(upstream.body as import('node:stream/web').ReadableStream).pipe(res);
    else res.end();
  } catch {if(!res.headersSent){res.writeHead(502,{'Content-Type':'application/json'});res.end(JSON.stringify({detail:'Monitoring server is unavailable'}));}else res.end();}
}
