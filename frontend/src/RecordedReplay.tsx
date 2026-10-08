import {useEffect,useRef,useState} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {useReducedMotion} from 'framer-motion';
import {Pause,Play,RotateCcw,Repeat2} from 'lucide-react';
import {api,raw} from './api';
import {EvidenceImage,Spinner} from './ui';
import type {Source,Track} from './types';
import './replay.css';
type ReplayInfo={duration:number;recorded:true;measurements:{seconds:number;tracks:Track[]}[]};
const time=(s:number)=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
function observation(info:ReplayInfo,seconds:number){let low=0,high=info.measurements.length-1;while(low<=high){const mid=(low+high)>>1;if(info.measurements[mid].seconds<=seconds)low=mid+1;else high=mid-1;}return Math.max(0,high);}

export default function RecordedReplay({source,onTracks,publicLibrary=false}:{source:Source;publicLibrary?:boolean;onTracks?:(tracks:Track[]|null)=>void}){
 const query=useQueryClient();const reduced=useReducedMotion();const root=useRef<HTMLDivElement>(null);const video=useRef<HTMLVideoElement>(null);const callback=useRef(onTracks);callback.current=onTracks;
 const previousTime=useRef(0);const previousObservation=useRef(-1);const [inView,setInView]=useState(false);const [foreground,setForeground]=useState(!document.hidden);const [paused,setPaused]=useState(!!reduced);const [url,setUrl]=useState('');const [info,setInfo]=useState<ReplayInfo|null>(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [reload,setReload]=useState(0);const [seconds,setSeconds]=useState(0);const [loops,setLoops]=useState(1);const [count,setCount]=useState(0);
 const prefix=publicLibrary?'/library':'';const job=source.recording;const ready=job?.status==='completed'&&job.replay_status==='ready';
 useEffect(()=>{const observer=new IntersectionObserver(([entry])=>setInView(entry.isIntersecting),{rootMargin:'100px'});if(root.current)observer.observe(root.current);const visibility=()=>setForeground(!document.hidden);document.addEventListener('visibilitychange',visibility);return()=>{observer.disconnect();document.removeEventListener('visibilitychange',visibility);};},[]);
 useEffect(()=>{setUrl('');setInfo(null);previousObservation.current=-1;previousTime.current=0;setSeconds(0);setLoops(1);setError('');if(!ready||!inView||!foreground)return;
  let current=true,objectUrl='';const controller=new AbortController();
  Promise.all([raw(`${prefix}/jobs/${job!.id}/replay`,{signal:controller.signal}).then(r=>r.blob()),api<ReplayInfo>(`${prefix}/jobs/${job!.id}/replay/info`,{signal:controller.signal})]).then(([blob,data])=>{if(!current)return;objectUrl=URL.createObjectURL(blob);setInfo(data);setUrl(objectUrl);}).catch(e=>{if(current)setError(e.message||'Recorded playback is unavailable.');});
  return()=>{current=false;controller.abort();video.current?.pause();if(objectUrl)URL.revokeObjectURL(objectUrl);callback.current?.(null);};
 },[ready,job?.id,inView,foreground,reload,prefix]);
 useEffect(()=>{if(!url||!video.current)return;if(paused)video.current.pause();else video.current.play().catch(e=>{if(e.name==='NotAllowedError')setPaused(true);});},[url,paused]);
 function progress(){if(!video.current||!info)return;const at=video.current.currentTime;if(at+0.5<previousTime.current)setLoops(n=>n+1);previousTime.current=at;setSeconds(at);const index=observation(info,at);const tracks=info.measurements[index]?.tracks||[];setCount(tracks.length);if(previousObservation.current!==index){previousObservation.current=index;callback.current?.(tracks);}}
 function toggle(){if(!video.current)return;if(paused){video.current.play().then(()=>setPaused(false)).catch(()=>setError('Press play again to start recorded playback.'));}else{video.current.pause();setPaused(true);}}
 function restart(){if(!video.current)return;previousTime.current=0;previousObservation.current=-1;video.current.currentTime=0;setLoops(1);progress();}
 async function retry(){if(!job)return;setBusy(true);try{await api(`/jobs/${job.id}/replay/retry`,{method:'POST'});setReload(n=>n+1);query.invalidateQueries({queryKey:['sources']});query.invalidateQueries({queryKey:['jobs']});}catch(e){setError(e instanceof Error?e.message:'Could not prepare recorded playback');}finally{setBusy(false);}}
 const failed=job?.replay_status==='failed'||!!error;
 return <div className="recorded-replay" ref={root}>
 {url?<video ref={video} className="recorded-replay-video" src={url} loop muted playsInline preload="auto" autoPlay={!paused} aria-label={'Looping recorded video with measured vehicle tracks from '+source.name} onTimeUpdate={progress} onLoadedData={progress} onError={()=>{setError('Recorded playback could not load. Retry playback.');setUrl('');}} onPlay={()=>setPaused(false)}/>:source.last_frame_at?<EvidenceImage path={prefix+'/sources/'+source.id+'/snapshot'} version={source.last_frame_at} alt={'Latest analyzed frame from '+source.name}/>:<div className="replay-wait"><Repeat2 size={27}/><span>Analyze this recording to start replay</span></div>}
 <div className="replay-toolbar"><div><Repeat2 size={13}/><span>{url?`Recorded replay · ${time(seconds)} / ${time(info?.duration||0)} · Loop ${loops}`:failed?'Recorded replay unavailable':ready?'Loading recorded replay…':job?.status==='completed'?'Preparing recorded replay…':'Recorded video · analysis in progress'}</span></div>{url?<div className="replay-actions"><span>{count} vehicles</span><button type="button" onClick={toggle} aria-label={`${paused?'Play':'Pause'} recorded replay for ${source.name}`} title={paused?'Play replay':'Pause replay'}>{paused?<Play size={15}/>:<Pause size={15}/>}</button><button type="button" onClick={restart} aria-label={'Restart recorded replay for '+source.name} title="Restart replay"><RotateCcw size={14}/></button></div>:failed&&job?.status==='completed'&&source.can_manage&&!publicLibrary?<button type="button" className="replay-retry" disabled={busy} onClick={retry}>{busy?<Spinner/>:<RotateCcw size={13}/>}Retry replay</button>:job?.status==='completed'&&inView?<Spinner/>:null}</div>
 {error&&<span className="replay-error" role="alert">{error}</span>}
 </div>;
}
