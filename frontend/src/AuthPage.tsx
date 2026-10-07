import {useState,type FormEvent} from 'react';
import {Link,Navigate,useLocation,useNavigate} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {ScanLine,ShieldCheck} from 'lucide-react';
import {api} from './api';
import {useAuth} from './auth';
import {Brand} from './Landing';
import {ErrorMessage,Spinner} from './ui';
import type {User} from './types';
export default function AuthPage(){
 const {user,accept}=useAuth();const navigate=useNavigate();const location=useLocation();const [mode,setMode]=useState<'login'|'register'>('login');const [error,setError]=useState<unknown>();const [busy,setBusy]=useState(false);
 const status=useQuery({queryKey:['auth-status'],queryFn:()=>api<{needs_setup:boolean}>('/auth/status')});
 const setup=status.data?.needs_setup;const register=setup||mode==='register';
 if(user)return <Navigate to="/app" replace/>;
 async function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();setError(undefined);setBusy(true);const data=Object.fromEntries(new FormData(event.currentTarget));try{const result=await api<{access_token:string;user:User}>('/auth/'+(register?'register':'login'),{method:'POST',body:JSON.stringify(data)});accept(result);navigate((location.state as {from?:string})?.from||'/app');}catch(e){setError(e);}finally{setBusy(false);}}
 return <main className="auth-page"><Link to="/" className="auth-brand"><Brand/></Link><div className="auth-art"><img src="/road-hero.webp" alt=""/><div/><span className="eyebrow">ACCIDENT ALERT / OPERATOR ACCESS</span><h1>Eyes on<br/>the road.</h1><p>Your footage. Your evidence.<br/>One connected response workspace.</p><span className="auth-foot"><ShieldCheck size={18}/> Secure operator access</span></div><section className="auth-panel"><div className="auth-box"><span className="auth-icon"><ScanLine size={26}/></span><span className="eyebrow">WELCOME TO YOUR WORKSPACE</span><h2>{setup?'Create your administrator account':register?'Join your team':'Welcome back.'}</h2><p>{setup?'Use the setup token from your backend environment file to create the first account.':register?'Enter the invitation token your administrator shared with you.':'Sign in to monitor your sources and review incident evidence.'}</p>
 <ErrorMessage error={error||status.error}/>{status.isPending?<Spinner/>:<form onSubmit={submit}>
 {register&&<label>Full name<input name="name" required minLength={2} maxLength={100} autoComplete="name"/></label>}
 <label>Email address<input name="email" type="email" required autoComplete="username"/></label><label>Password<input name="password" type="password" required minLength={register?12:1} maxLength={128} autoComplete={register?'new-password':'current-password'}/>{register&&<small>At least 12 characters</small>}</label>
 {register&&<label>{setup?'Setup token':'Invitation token'}<input name="token" type="password" required autoComplete="off"/></label>}
 <button className="button lime full" disabled={busy}>{busy?<Spinner/>:null}{register?'Create account':'Sign in'}</button></form>}
 {!setup&&<button className="text-button" onClick={()=>{setMode(register?'login':'register');setError(undefined);}}>{register?'Already have an account? Sign in':'Have an invitation? Join your team'}</button>}
 </div></section></main>;
}
