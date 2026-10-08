import {Link} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {ArrowUpRight,FileVideo,ScanLine} from 'lucide-react';
import {api} from './api';
import {useAuth} from './auth';
import {Brand} from './Landing';
import {ErrorMessage,Spinner,Status} from './ui';
import RecordedReplay from './RecordedReplay';
import type {Source} from './types';
import './library.css';

export default function VideoLibrary({page=false}:{page?:boolean}){
 const {user}=useAuth();const sources=useQuery({queryKey:['library-sources'],queryFn:()=>api<Source[]>('/library/sources'),refetchInterval:10000});
 const content=<section className="video-library" id="shared-videos"><div className="library-heading"><div><span className="eyebrow">SHARED VIDEO COLLECTION</span><h2>Watch the road.<br/><span>See the detections.</span></h2><p>Recorded traffic footage with actual vehicle detections. Each video repeats automatically when it ends.</p></div><div className="library-access">{user&&user.role!=='visitor'?<Link className="button lime" to="/app">Your workspace <ArrowUpRight size={17}/></Link>:<><Link className="button outline" to="/login">Sign in</Link><Link className="button lime" to="/register">Register as new <ArrowUpRight size={17}/></Link></>}</div></div>
 <ErrorMessage error={sources.error}/>{sources.isPending?<div className="quiet-panel"><Spinner/>Loading shared videos</div>:sources.data?.length?<div className="library-grid">{sources.data.map(source=><article className="source-card library-card" key={source.id}><div className="source-view"><RecordedReplay source={source} publicLibrary/><div className="source-overlay"><span>DATASET VIDEO</span><Status value={source.recording?.replay_status==='ready'?'recorded_replay':source.recording?.status||'idle'}/></div></div><div className="source-content"><h3>{source.name}</h3><span className="shared-dataset-label"><FileVideo size={13}/>Shared recording</span><div className="source-actions"><Link className="button outline" to={user?'/app/live/'+source.id:'/login'} state={{from:'/app/live/'+source.id}}><ScanLine size={16}/>View analysis & graphs <ArrowUpRight size={15}/></Link></div></div></article>)}</div>:!sources.isError?<div className="quiet-panel"><FileVideo size={22}/>Shared recordings will appear here when they are published.</div>:null}
 {!page&&<Link className="text-button library-all" to="/videos">Open video collection <ArrowUpRight size={16}/></Link>}
 </section>;
 return page?<div className="library-page"><header className="library-nav"><Link to="/"><Brand/></Link><Link className="text-button" to="/">Back to home</Link></header>{content}</div>:content;
}
