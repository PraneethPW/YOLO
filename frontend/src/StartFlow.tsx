import {useRef,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {Camera,Upload,ArrowUpRight} from 'lucide-react';
import {api,uploadVideo} from './api';
import {useAuth} from './auth';
import {ErrorMessage,Spinner} from './ui';
import type {Source,User} from './types';

export default function StartFlow({compact=false}:{compact?:boolean}){
 const {user,accept,loading}=useAuth();const navigate=useNavigate();const picker=useRef<HTMLInputElement>(null);const [phase,setPhase]=useState('');const [percent,setPercent]=useState(0);const [error,setError]=useState<unknown>();
 async function connect(kind:'webcam'|'upload',video?:File){
  if(phase)return;setError(undefined);
  const limit=user&&user.role!=='visitor'?100:25;
  if(video&&(!video.size||! /\.(mp4|mov|avi|webm|mkv)$/i.test(video.name))){setError(new Error('Choose a nonempty MP4, MOV, AVI, WebM, or MKV video.'));return;}
  if(video&&video.size>limit*1024*1024){setError(new Error(`Choose a video under ${limit} MB.`));return;}
  setPhase(user?'Opening source':'Opening private session');
  let createdSource:string|undefined;
  try{
   if(!user){accept(await api<{user:User;access_token:string}>('/auth/visitor',{method:'POST'}));}
   const source=await api<Source>('/sources',{method:'POST',body:JSON.stringify({kind,name:video?video.name.slice(0,100):'My camera',location:'Location not provided'})});
   createdSource=source.id;
   if(video){setPhase('Uploading video');await uploadVideo(source.id,video,setPercent);}
   navigate('/app/live/'+source.id);
  }catch(e){setError(e);if(video&&createdSource)await api('/sources/'+createdSource+'/archive',{method:'POST'}).catch(()=>{});}finally{setPhase('');setPercent(0);if(picker.current)picker.current.value='';}
 }
 return <div className={'start-flow '+(compact?'start-compact':'')}>
  <div className="start-actions"><button className="button lime" disabled={!!phase||loading} onClick={()=>connect('webcam')}>{loading?<Spinner/>:<Camera size={20}/>}Use my camera <ArrowUpRight size={17}/></button><button className="button outline" disabled={!!phase||loading} onClick={()=>picker.current?.click()}><Upload size={19}/>Analyze a video</button></div>
  {phase&&<div className="transfer-state" role="status"><Spinner/>{phase}{phase==='Uploading video'&&<><strong>{percent}%</strong><progress value={percent} max={100}/></>}</div>}
  <ErrorMessage error={error}/><input ref={picker} type="file" hidden accept="video/mp4,video/webm,video/quicktime,.avi,.mkv" onChange={e=>{if(e.target.files?.[0])connect('upload',e.target.files[0]);}}/>
 </div>;
}
