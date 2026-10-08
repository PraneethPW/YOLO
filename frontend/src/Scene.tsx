import {Component,useMemo,useRef,type ReactNode} from 'react';
import {Canvas,useFrame} from '@react-three/fiber';
import type {MotionValue} from 'framer-motion';
import * as THREE from 'three';
class Boundary extends Component<{children:ReactNode},{failed:boolean}>{state={failed:false};static getDerivedStateFromError(){return {failed:true};}render(){return this.state.failed?null:this.props.children;}}
function Trajectories({progress}:{progress:MotionValue<number>}){
 const group=useRef<THREE.Group>(null);const lines=useMemo(()=>Array.from({length:6},(_,i)=>{
  const curve=new THREE.CatmullRomCurve3([new THREE.Vector3(-9,-3+i*.25,-2),new THREE.Vector3(-2,-2+i*.25,0),new THREE.Vector3(4,2+i*.25,-1),new THREE.Vector3(12,4+i*.25,-5)]);
  return new THREE.TubeGeometry(curve,80,.006,6,false);
 }),[]);
 useFrame(({clock,pointer})=>{if(group.current){group.current.rotation.z=progress.get()*.22+Math.sin(clock.elapsedTime*.1)*.02;group.current.rotation.y=pointer.x*.08;group.current.position.y=-progress.get()*2;}});
 return <group ref={group}>{lines.map((geometry,i)=><mesh geometry={geometry} key={i}><meshBasicMaterial color={i%2?'#9685ff':'#56def5'} transparent opacity={.18}/></mesh>)}</group>;
}
export default function Scene({progress}:{progress:MotionValue<number>}){return <Boundary><Canvas dpr={[1,1.5]} camera={{position:[0,0,10],fov:55}} gl={{alpha:true,antialias:false}}><Trajectories progress={progress}/></Canvas></Boundary>;}
