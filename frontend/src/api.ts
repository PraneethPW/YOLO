import type {User,LiveEvent} from './types';
let token='';
let backendUrl:Promise<string>|null=null;
async function largeTransferBase(){
 if(import.meta.env.DEV)return '';
 if(!backendUrl)backendUrl=fetch('/api/runtime').then(async r=>{const data=await r.json();if(!data.backend_url)throw new Error('Backend connection is not configured');return data.backend_url;}).catch(e=>{backendUrl=null;throw e;});
 return backendUrl;
}
let pendingRefresh:Promise<{access_token:string;user:User}>|null=null;
export function setToken(value:string){token=value;}
export async function refresh(){
  if(!pendingRefresh) pendingRefresh=fetch('/api/auth/refresh',{method:'POST',credentials:'include'}).then(async r=>{if(!r.ok)throw new Error('Please sign in');const data=await r.json();token=data.access_token;return data;}).finally(()=>pendingRefresh=null);
  return pendingRefresh;
}
export async function raw(path:string,init:RequestInit={},retry=true):Promise<Response>{
  const headers=new Headers(init.headers);if(token)headers.set('Authorization','Bearer '+token);
  if(init.body && !(init.body instanceof FormData) && !headers.has('Content-Type'))headers.set('Content-Type','application/json');
  let response:Response;
  const base=/\/upload$|\/video$|\/frame$|\/replay(?:\/info)?$/.test(path)?await largeTransferBase():'';
  try{response=await fetch(base+'/api'+path,{...init,headers,credentials:base?'omit':'include'});}catch{throw new Error('Unable to reach the monitoring server. Check your connection.');}
  if(response.status===401 && retry && !path.startsWith('/auth/')){try{await refresh();return raw(path,init,false);}catch{window.dispatchEvent(new Event('session-expired'));}}
  if(!response.ok){const data=await response.json().catch(()=>null);let detail=data?.detail;if(Array.isArray(detail))detail=detail.map((d:{msg:string})=>d.msg).join('. ');throw new Error(typeof detail==='string'?detail:`Request failed (${response.status})`);}
  return response;
}
export async function api<T>(path:string,init:RequestInit={}):Promise<T>{return (await raw(path,init)).json();}
export async function download(path:string,name:string){const blob=await (await raw(path)).blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export async function uploadVideo(sourceId:string,file:File,onProgress:(percent:number)=>void){
 const base=await largeTransferBase();
 const send=()=>new Promise<void>((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open('POST',base+'/api/sources/'+sourceId+'/upload');if(token)xhr.setRequestHeader('Authorization','Bearer '+token);xhr.withCredentials=!base;xhr.upload.onprogress=e=>{if(e.lengthComputable)onProgress(Math.round(e.loaded/e.total*100));};xhr.onerror=()=>reject(new Error('Upload connection lost. Please try again.'));xhr.onload=()=>{if(xhr.status>=200&&xhr.status<300){resolve();return;}let detail='Video upload failed';try{detail=JSON.parse(xhr.responseText).detail||detail;}catch{}reject(Object.assign(new Error(String(detail)),{status:xhr.status}));};const body=new FormData();body.append('file',file);xhr.send(body);});
 try{await send();}catch(e){if((e as {status?:number}).status===401){await refresh();await send();}else throw e;}
}
export async function eventStream(signal:AbortSignal,onEvent:(event:LiveEvent)=>void,onStatus:(value:boolean)=>void){
  let cursor=0;
  while(!signal.aborted){
    try{
      const response=await raw('/events?after='+cursor,{signal});const reader=response.body!.getReader();onStatus(true);const decoder=new TextDecoder();let pending='';
      while(!signal.aborted){const {done,value}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let index;
        while((index=pending.indexOf('\n\n'))>=0){const block=pending.slice(0,index);pending=pending.slice(index+2);const id=/^id: (\d+)/m.exec(block);if(id){cursor=Number(id[1]);const kind=/^event: (.+)/m.exec(block)?.[1]||'update';const data=/^data: (.+)/m.exec(block)?.[1];try{onEvent({kind,data:data?JSON.parse(data):{}});}catch{}}}
      }
    }catch{if(signal.aborted)return;}
    onStatus(false);await new Promise<void>(resolve=>{const timer=setTimeout(resolve,2500);signal.addEventListener('abort',()=>{clearTimeout(timer);resolve();},{once:true});});
  }
}
