import {useEffect,useState,type FormEvent} from 'react';
import {Link,Navigate,useLocation,useNavigate} from 'react-router-dom';
import {ScanLine,ShieldCheck} from 'lucide-react';
import {api} from './api';
import {useAuth} from './auth';
import {Brand} from './Landing';
import {ErrorMessage,Spinner} from './ui';
import type {User} from './types';
import './library.css';
export default function AuthPage(){
 const {user,accept}=useAuth();const navigate=useNavigate();const location=useLocation();const register=location.pathname==='/register';const [error,setError]=useState<unknown>();const [busy,setBusy]=useState(false);
 useEffect(()=>setError(undefined),[register]);
 if(user&&user.role!=='visitor')return <Navigate to="/app" replace/>;
 async function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();setError(undefined);setBusy(true);const data=Object.fromEntries(new FormData(event.currentTarget));try{const result=await api<{access_token:string;user:User}>('/auth/'+(register?'register':'login'),{method:'POST',body:JSON.stringify(data)});accept(result);navigate((location.state as {from?:string})?.from||'/app');}catch(e){setError(e);}finally{setBusy(false);}}
 return <main className="auth-page"><Link to="/" className="auth-brand"><Brand/></Link><div className="auth-art"><img src="/road-hero.webp" alt=""/><div/><span className="eyebrow">ACCIDENT ALERT / YOUR ACCOUNT</span><h1>Eyes on<br/>the road.</h1><p>Watch the shared recordings.<br/>Keep your own analyses in one place.</p><span className="auth-foot"><ShieldCheck size={18}/> Your account. Your saved footage.</span></div><section className="auth-panel"><div className="auth-box"><span className="auth-icon"><ScanLine size={26}/></span><nav className="auth-tabs" aria-label="Account access"><Link to="/login" className={!register?'selected':''} state={location.state}>Sign in</Link><Link to="/register" className={register?'selected':''} state={location.state}>Register as new</Link></nav><h2>{register?'Create your account.':'Welcome back.'}</h2><p>{register?'Your name, email and password are all you need.':'Already registered? Sign in with your email and password.'}</p>
 <ErrorMessage error={error}/><form onSubmit={submit} key={register?'register':'login'}>
 {register&&<label>Full name<input name="name" required minLength={2} maxLength={100} autoComplete="name"/></label>}
 <label>Email address<input name="email" type="email" required autoComplete="username"/></label><label>Password<input name="password" type="password" required minLength={register?8:1} maxLength={128} autoComplete={register?'new-password':'current-password'}/>{register&&<small>At least 8 characters</small>}</label>
 <button className="button lime full" disabled={busy}>{busy?<Spinner/>:null}{register?'Create account':'Sign in'}</button></form>
 <Link className="text-button" to={register?'/login':'/register'} state={location.state}>{register?'Already have an account? Sign in':'New here? Register as new'}</Link>
 </div></section></main>;
}
