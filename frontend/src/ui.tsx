import {useEffect,useRef,useState,type ReactNode} from 'react';
import {motion} from 'framer-motion';
import {AlertCircle,LoaderCircle,X} from 'lucide-react';
import {raw} from './api';
export function Spinner(){return <LoaderCircle size={19} className="spin"/>;}
export function ErrorMessage({error}:{error:unknown}){return error?<div className="error" role="alert"><AlertCircle size={18}/>{error instanceof Error?error.message:String(error)}</div>:null;}
export function Empty({icon,title,text,action}:{icon:ReactNode;title:string;text:string;action?:ReactNode}){return <div className="empty"><div className="empty-icon">{icon}</div><h3>{title}</h3><p>{text}</p>{action}</div>;}
export function Status({value}:{value:string}){return <span className={'status status-'+value}>{value==='review'?'Needs review':value.replaceAll('_',' ')}</span>;}
export function date(value:string){return new Date(value).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});}
export function Modal({title,children,onClose,wide=false}:{title:string;children:ReactNode;onClose:()=>void;wide?:boolean}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement;const overflow=document.body.style.overflow;document.body.style.overflow='hidden';ref.current?.querySelector<HTMLElement>('button,input,select,textarea')?.focus();const key=(event:KeyboardEvent)=>{if(event.key==='Escape')onClose();if(event.key==='Tab'){const focusable=ref.current?.querySelectorAll<HTMLElement>('button:not([disabled]),input,select,textarea,a[href],[tabindex="0"]');if(!focusable?.length)return;const first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}};document.addEventListener('keydown',key);return()=>{document.body.style.overflow=overflow;document.removeEventListener('keydown',key);previous?.focus();};},[onClose]);
 return <div className="modal-backdrop" onClick={e=>{if(e.target===e.currentTarget)onClose();}}><motion.div ref={ref} role="dialog" aria-modal="true" aria-label={title} className={'modal '+(wide?'modal-wide':'')} initial={{opacity:0,y:16}} animate={{opacity:1,y:0}}><div className="modal-head"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close dialog"><X size={21}/></button></div>{children}</motion.div></div>;
}
export function EvidenceImage({path,version='',alt,className=''}:{path:string;version?:string;alt:string;className?:string}){
 const [url,setUrl]=useState('');const [error,setError]=useState('');
 useEffect(()=>{let current=true;let objectUrl='';setError('');raw(path).then(r=>r.blob()).then(blob=>{objectUrl=URL.createObjectURL(blob);if(current)setUrl(objectUrl);else URL.revokeObjectURL(objectUrl);}).catch(e=>{if(current)setError(e.message);});return()=>{current=false;if(objectUrl)URL.revokeObjectURL(objectUrl);};},[path,version]);
 return url?<img src={url} alt={alt} className={className}/>:<div className={'image-wait '+className}>{error?<span>{error}</span>:<Spinner/>}</div>;
}
