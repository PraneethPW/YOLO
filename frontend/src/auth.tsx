import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {api,refresh,setToken} from './api';
import type {User} from './types';
const Context=createContext<{user:User|null;loading:boolean;accept:(data:{user:User;access_token:string})=>void;logout:()=>Promise<void>}>({user:null,loading:true,accept:()=>{},logout:async()=>{}});
export function AuthProvider({children}:{children:ReactNode}){
 const [user,setUser]=useState<User|null>(null);const [loading,setLoading]=useState(true);const query=useQueryClient();
 useEffect(()=>{refresh().then(data=>setUser(data.user)).catch(()=>{}).finally(()=>setLoading(false));const expired=()=>{setUser(null);setToken('');query.clear();};window.addEventListener('session-expired',expired);return()=>window.removeEventListener('session-expired',expired);},[query]);
 function accept(data:{user:User;access_token:string}){setToken(data.access_token);setUser(data.user);query.clear();}
 async function logout(){await api('/auth/logout',{method:'POST'});setToken('');setUser(null);query.clear();}
 return <Context.Provider value={{user,loading,accept,logout}}>{children}</Context.Provider>;
}
export function useAuth(){return useContext(Context);}
