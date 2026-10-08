import {useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {MessageSquare} from 'lucide-react';
import {api} from './api';
import {ErrorMessage,Spinner,Status,date} from './ui';
import './analytics.css';
type Feedback={id:string;display_name:string;rating:number;quote:string;publish_consent:boolean;status:string;created_at:string;source_name:string;source_kind:string};
export default function FeedbackModeration(){
 const query=useQueryClient();const result=useQuery({queryKey:['feedback'],queryFn:()=>api<Feedback[]>('/feedback')});const [busy,setBusy]=useState('');const [error,setError]=useState<unknown>();
 async function review(id:string,status:'approved'|'hidden'){setBusy(id);setError(undefined);try{await api('/feedback/'+id,{method:'PATCH',body:JSON.stringify({status})});await query.invalidateQueries({queryKey:['feedback']});query.invalidateQueries({queryKey:['testimonials']});query.invalidateQueries({queryKey:['audit']});}catch(e){setError(e);}finally{setBusy('');}}
 return <section className="settings-card wide-card"><h2><MessageSquare size={21}/>Feedback & public testimonials</h2><p className="muted">Feedback comes from users who have analyzed footage. Publish only reviews whose authors have opted in. Source names and footage never appear in public testimonials.</p><ErrorMessage error={error||result.error}/>{result.isPending?<Spinner/>:result.data?.length?<div className="feedback-review">{result.data.map(f=><article key={f.id}><div><strong>{f.display_name}</strong><span>{f.rating} / 5</span><Status value={f.status}/></div><blockquote>{f.quote}</blockquote><small>{f.source_name} · {f.source_kind} · {date(f.created_at)}<br/>{f.publish_consent?'Author allows public display':'Private feedback — no public display consent'}</small><div>{f.publish_consent&&f.status!=='approved'&&<button className="button lime small" disabled={!!busy} onClick={()=>review(f.id,'approved')}>{busy===f.id?<Spinner/>:null}Publish testimonial</button>}{f.status!=='hidden'&&<button className="button outline small" disabled={!!busy} onClick={()=>review(f.id,'hidden')}>Hide feedback</button>}</div></article>)}</div>:<div className="quiet-panel">No feedback submitted yet. Users can share an experience from their source’s analysis page.</div>}</section>;
}
