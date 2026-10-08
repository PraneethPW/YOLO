import {useEffect,useState,type FormEvent} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {ArrowUpRight,Camera,Check,MapPin,RefreshCw,Search,ShieldCheck,Video,X} from 'lucide-react';
import {api} from './api';
import {EvidenceImage,ErrorMessage,Spinner,Status} from './ui';
import {IncidentDetail} from './Incidents';
import StartFlow from './StartFlow';
import type {Incident,Source} from './types';
import './coverage.css';

type Placement={id:string;location:string;latitude:string;longitude:string};
function health(source:Source,now:number){
 if(source.status==='error'||source.status==='processing')return source.status;
 if(source.status==='live')return source.last_frame_at&&now-Date.parse(source.last_frame_at)<10000?'live':'delayed';
 return 'idle';
}
function frameAge(value:string|null,now:number){
 if(!value)return 'No frames received';
 const seconds=Math.max(0,Math.floor((now-Date.parse(value))/1000));
 return seconds<2?'Frame just received':seconds<60?`Last frame ${seconds}s ago`:seconds<3600?`Last frame ${Math.floor(seconds/60)}m ago`:`Last frame ${Math.floor(seconds/3600)}h ago`;
}
const colors:Record<string,string>={live:'#ff4057',delayed:'#e6a7b6',error:'#ff6d7a',processing:'#f35578',idle:'#907c82'};
const kindLabel={upload:'Recorded video',webcam:'Browser camera',stream:'CCTV stream'};

export default function Coverage(){
 const [params]=useSearchParams();
 const [selectedId,setSelectedId]=useState(params.get('source')||'');
 const [placement,setPlacement]=useState<Placement|null>(null);
 const [review,setReview]=useState<Incident|null>(null);
 const [search,setSearch]=useState('');
 const [filter,setFilter]=useState('all');
 const [now,setNow]=useState(Date.now());
 const [busy,setBusy]=useState(false);
 const [locating,setLocating]=useState(false);
 const [error,setError]=useState<unknown>();
 const query=useQueryClient();
 const sources=useQuery({queryKey:['sources'],queryFn:()=>api<Source[]>('/sources'),refetchInterval:5000});
 const incidents=useQuery({queryKey:['incidents','network'],queryFn:()=>api<Incident[]>('/incidents?active_only=true&limit=500'),refetchInterval:5000});
 const all=sources.data||[];
 const active=(incidents.data||[]).filter(i=>['review','confirmed'].includes(i.status));
 const incidentsBySource=new Map<string,Incident[]>();
 for(const incident of active){const group=incidentsBySource.get(incident.source_id)||[];group.push(incident);incidentsBySource.set(incident.source_id,group);}
 const sourceIncidents=(id:string)=>incidentsBySource.get(id)||[];
 const visible=all.filter(source=>(source.name+' '+source.location).toLowerCase().includes(search.toLowerCase())&&(filter==='all'||filter==='live'&&health(source,now)==='live'||filter==='review'&&sourceIncidents(source.id).length>0));
 const selected=visible.find(source=>source.id===selectedId)||visible[0];
 const selectedIncidents=selected?sourceIncidents(selected.id):[];
 const fresh=all.filter(source=>health(source,now)==='live').length;
 const attention=all.filter(source=>health(source,now)==='error'||health(source,now)==='delayed').length;
 const ordered=[...visible].sort((a,b)=>sourceIncidents(b.id).length-sourceIncidents(a.id).length||Number(['error','delayed'].includes(health(b,now)))-Number(['error','delayed'].includes(health(a,now)))||a.name.localeCompare(b.name));
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[]);
 useEffect(()=>{const id=params.get('source');if(id)setSelectedId(id);},[params]);

 function place(source:Source){
  setError(undefined);setSelectedId(source.id);
  setPlacement({id:source.id,location:source.location==='Location not provided'?'':source.location,latitude:source.latitude===null?'':String(source.latitude),longitude:source.longitude===null?'':String(source.longitude)});
 }
 async function saveLocation(event:FormEvent){
  event.preventDefault();if(!placement)return;
  if((placement.latitude==='')!==(placement.longitude==='')){setError(new Error('Enter both coordinates, or leave both blank.'));return;}
  setBusy(true);setError(undefined);
  try{
   const source=await api<Source>('/sources/'+placement.id+'/location',{method:'PATCH',body:JSON.stringify({location:placement.location,latitude:placement.latitude===''?null:Number(placement.latitude),longitude:placement.longitude===''?null:Number(placement.longitude)})});
   query.setQueryData<Source[]>(['sources'],old=>old?.map(item=>item.id===source.id?source:item));
   query.invalidateQueries({queryKey:['incidents']});setPlacement(null);
  }catch(e){setError(e);}finally{setBusy(false);}
 }
 function useDeviceLocation(){
  setError(undefined);
  if(!navigator.geolocation){setError(new Error('Device location is unavailable. Enter the coordinates manually.'));return;}
  setLocating(true);
  navigator.geolocation.getCurrentPosition(position=>{setPlacement(old=>old?{...old,latitude:position.coords.latitude.toFixed(6),longitude:position.coords.longitude.toFixed(6)}:null);setLocating(false);},()=>{setError(new Error('Device location is unavailable. Enter the coordinates manually.'));setLocating(false);},{timeout:15000,maximumAge:60000});
 }
 function refresh(){void sources.refetch();void incidents.refetch();}

 return <>
  <div className="page-title"><div><span className="eyebrow">NETWORK / LIVE OPERATIONS</span><h1>Road network<span className="title-dot">.</span></h1><p className="coverage-intro">Your footage, source health, and incidents in one view.</p></div><Link className="button outline" to="/app">Manage footage <ArrowUpRight size={17}/></Link></div>
  <ErrorMessage error={error||sources.error||incidents.error}/>
  <div className="network-summary"><span><Camera size={16}/><strong>{sources.data?all.length:'—'}</strong> connected sources</span><span><i className={fresh?'lime-dot':'network-idle-dot'}/><strong>{sources.data?fresh:'—'}</strong> live camera feeds</span><span><ShieldCheck size={16}/><strong>{incidents.data?active.length:'—'}{active.length===500?'+':''}</strong> active incidents</span><span className="network-sync">{sources.data?`Sources synced ${Math.max(0,Math.floor((now-sources.dataUpdatedAt)/1000))}s ago`:'Connecting…'}</span></div>
  <div className="network-layout coverage-layout">
   <section className="coverage-board" aria-label="Connected footage and source health">
    <div className="coverage-heading"><div><span className="eyebrow">SOURCE COVERAGE</span><h2>{all.length?'Latest captured footage':'Bring a road into view'}</h2></div><button className="icon-button" aria-label="Refresh coverage" onClick={refresh} disabled={sources.isFetching||incidents.isFetching}><RefreshCw size={18}/></button></div>
    {sources.isPending?<div className="coverage-state" role="status"><Spinner/>Loading connected sources…</div>:sources.isError&&!sources.data?<div className="coverage-state"><Camera size={32}/><h3>Coverage could not be loaded</h3><p>Reconnect to the monitoring server to see your sources.</p><button className="button outline" onClick={refresh}>Try again</button></div>:!all.length?<div className="coverage-state coverage-onboarding"><div className="coverage-empty-icon"><Camera size={34}/></div><h3>Start with footage you can act on.</h3><p>Connect your camera or upload a road video. Its captured frames, connection health, and incident evidence will appear here.</p><StartFlow/><div className="coverage-outcomes"><span><Video size={18}/>See captured frames</span><span><ShieldCheck size={18}/>Review incident evidence</span><span><MapPin size={18}/>Assign a road or location</span></div></div>:<>
     <div className="coverage-health"><span>{attention?`${attention} source${attention===1?'':'s'} need attention`:'No delayed or failed connections'}</span><span>Incident sources appear first</span></div>
     {!visible.length?<div className="coverage-state"><Search size={28}/><h3>No sources match this view</h3><button className="button outline" onClick={()=>{setSearch('');setFilter('all');}}>Show all sources</button></div>:<div className="coverage-grid">{ordered.map(source=>{
      const pending=sourceIncidents(source.id);const state=health(source,now);const hasLocation=source.location!=='Location not provided';
      return <article className={'coverage-card '+(selected?.id===source.id?'selected':'')} key={source.id}>
       <button className="coverage-preview" aria-label={'Inspect '+source.name} aria-pressed={selected?.id===source.id} onClick={()=>{setSelectedId(source.id);setPlacement(null);}}>
        {source.last_frame_at?<EvidenceImage path={'/sources/'+source.id+'/snapshot'} version={source.last_frame_at} alt={'Latest captured frame from '+source.name}/>:<div className="coverage-no-frame"><Camera size={28}/><span>{source.kind==='upload'?'Awaiting video analysis':'Waiting for camera frames'}</span></div>}
        <span className="coverage-kind">{kindLabel[source.kind]}</span>
       </button>
       <div className="coverage-card-body"><div className="coverage-card-title"><h3>{source.name}</h3><Status value={state}/></div><p className="coverage-location"><MapPin size={14}/>{hasLocation?source.location:'Road not assigned'}</p><div className="coverage-meta"><span>{frameAge(source.last_frame_at,now)}</span><span>{source.tracks.length} vehicles in captured frame</span></div>
        <div className="coverage-card-actions"><Link className="text-button" to={'/app/live/'+source.id}>Open {source.kind==='upload'?'video':'live view'} <ArrowUpRight size={15}/></Link>{pending.length?<button className="coverage-review" onClick={()=>setReview(pending[0])}><ShieldCheck size={14}/>{pending.length} active incident{pending.length===1?'':'s'}</button>:<button className="text-button" onClick={()=>place(source)}><MapPin size={14}/>{hasLocation?'Edit location':'Assign road'}</button>}</div>
       </div>
      </article>;
     })}</div>}
    </>}
   </section>
   <aside className="network-panel coverage-panel">{placement?<form className="network-placement" onSubmit={saveLocation}>
    <div className="network-panel-heading"><h2>Location for {all.find(source=>source.id===placement.id)?.name}</h2><button type="button" className="icon-button" aria-label="Cancel location editing" disabled={busy} onClick={()=>setPlacement(null)}><X size={18}/></button></div>
    <p className="coverage-location-help">Use the location where this footage was captured.</p><label>Road or area<input required minLength={2} maxLength={200} value={placement.location} onChange={e=>setPlacement({...placement,location:e.target.value})} placeholder="Road name, junction, or area"/></label>
    <div className="form-row"><label>Latitude (optional)<input type="number" step="any" min={-90} max={90} value={placement.latitude} onChange={e=>setPlacement({...placement,latitude:e.target.value})}/></label><label>Longitude (optional)<input type="number" step="any" min={-180} max={180} value={placement.longitude} onChange={e=>setPlacement({...placement,longitude:e.target.value})}/></label></div>
    <button type="button" className="button outline full" disabled={locating||busy} onClick={useDeviceLocation}>{locating?<Spinner/>:<MapPin size={16}/>}Use this device's location</button><button className="button lime full" disabled={busy||locating}>{busy?<Spinner/>:<Check size={17}/>}Save location</button>
   </form>:<>
    <label className="search network-search"><Search size={16}/><input aria-label="Find a source or road" placeholder="Find a source or road" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="network-filters">{[['all','All sources'],['live','Receiving'],['review','Incidents']].map(([value,label])=><button key={value} className={filter===value?'active':''} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{label}</button>)}</div>
    <div className="network-source-list">{visible.map(source=><button className={'network-source '+(selected?.id===source.id?'selected':'')} key={source.id} onClick={()=>setSelectedId(source.id)}><i style={{background:colors[health(source,now)]}}/><span><strong>{source.name}</strong><small>{source.location==='Location not provided'?'Road not assigned':source.location}</small></span><small>{health(source,now)}</small></button>)}</div>
    {selected?<section className="network-detail"><div className="network-panel-heading"><h2>{selected.name}</h2><Status value={health(selected,now)}/></div><p className="coverage-detail-kind">{kindLabel[selected.kind]}</p><div className="network-frame-info"><span>{frameAge(selected.last_frame_at,now)}</span><span>{selected.tracks.length} vehicles in captured frame</span></div><div className="network-detail-actions"><Link className="button lime small" to={'/app/live/'+selected.id}>Open {selected.kind==='upload'?'video':'live view'} <ArrowUpRight size={16}/></Link><button className="button outline small" onClick={()=>place(selected)}><MapPin size={16}/>{selected.location==='Location not provided'?'Assign road':'Edit location'}</button></div>{selected.last_error&&<ErrorMessage error={selected.last_error}/>}<div className="network-panel-heading"><h2>Active incidents</h2><span>{selectedIncidents.length}</span></div>{incidents.isError?<p className="network-empty">Incident status is unavailable. Retry the connection.</p>:selectedIncidents.length?selectedIncidents.map(incident=><button className="network-incident" key={incident.id} onClick={()=>setReview(incident)}><EvidenceImage path={'/incidents/'+incident.id+'/snapshot'} alt="Captured incident evidence"/><span><Status value={incident.status}/><small>{new Date(incident.detected_at).toLocaleString()}</small></span><ArrowUpRight size={16}/></button>):<p className="network-empty">{incidents.isPending?'Loading incident evidence…':'No active incidents for this source.'}</p>}</section>:<div className="coverage-side-empty"><ShieldCheck size={24}/><h3>{all.length?'Select a source':'Your source details appear here'}</h3><p>{all.length?'Change your search or filter to inspect a source.':'Inspect frame freshness, open footage, and review incidents from a connected source.'}</p></div>}
   </>}</aside>
  </div>
  {review&&<IncidentDetail incident={incidents.data?.find(incident=>incident.id===review.id)||review} onClose={()=>setReview(null)}/>}</>;
}
