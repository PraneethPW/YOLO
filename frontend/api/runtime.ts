import type {IncomingMessage,ServerResponse} from 'node:http';
export default function handler(_req:IncomingMessage,res:ServerResponse){
 const backend=process.env.BACKEND_URL;
 res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store');
 res.end(JSON.stringify({backend_url:backend?new URL(backend).origin:null}));
}
