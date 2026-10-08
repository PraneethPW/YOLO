import {Suspense,lazy,useRef} from 'react';
import {Link} from 'react-router-dom';
import {motion,useScroll,useTransform,useReducedMotion} from 'framer-motion';
import {Activity,ScanLine,Route,ShieldCheck,Radio,ChevronDown} from 'lucide-react';
import StartFlow from './StartFlow';
import LandingDetails from './LandingDetails';
import VideoLibrary from './VideoLibrary';
const Scene=lazy(()=>import('./Scene'));
export function Brand(){return <span className="brand"><span className="brand-mark"><Activity size={21}/></span>accident<span className="brand-light">alert</span><span className="brand-dot">®</span></span>;}
export default function Landing(){
 const section=useRef<HTMLDivElement>(null);const reduced=useReducedMotion();const {scrollYProgress}=useScroll({target:section,offset:['start start','end end']});const y=useTransform(scrollYProgress,[0,1],['0%','26%']);const scale=useTransform(scrollYProgress,[0,1],[1,1.22]);
 return <div className="landing" ref={section}>
  <div className="landing-scene" aria-hidden="true"><motion.img src="/road-hero.webp" alt="" style={reduced?{}:{y,scale}}/><div className="scene-shade"/>{!reduced&&<Suspense fallback={null}><Scene progress={scrollYProgress}/></Suspense>}</div>
  <header className="landing-nav"><Link to="/" aria-label="Accident Alert home"><Brand/></Link><nav><a href="#how-it-works">The system</a><Link to="/videos">Videos</Link><a href="#analysis">Analytics</a><Link className="nav-console" to="/login">Sign in <span className="keycap">↗</span></Link><Link className="nav-register" to="/register">Register as new</Link></nav></header>
  <section className="hero">
   <motion.div initial={{opacity:0,y:24}} animate={{opacity:1,y:0}} transition={{duration:.8}}>
    <div className="eyebrow"><span className="tiny-cross">+</span> ROAD INTELLIGENCE, IN MOTION</div>
    <h1>Every second.<br/><span>Every road.</span></h1>
    <p className="hero-copy">A clearer view of the road. Detect vehicle movement, review potential accidents, and get the right information to your response team.</p>
    <div className="hero-actions"><StartFlow compact/></div>
   </motion.div>
   <motion.div className="hero-side" initial={{opacity:0}} animate={{opacity:1}} transition={{delay:.5,duration:1}}><div className="side-rule"/><span>SEE THE SIGNAL.<br/>ACT WITH CONTEXT.</span><p>Vehicle tracking<br/>Multi-frame verification<br/>Operator review</p><div className="signal-bars">{Array.from({length:24},(_,i)=><i key={i} style={{height:10+(i%7)*4}}/>)}</div><small>ROAD MONITORING SYSTEM / 01</small></motion.div>
   <div className="hero-bottom"><span><ChevronDown size={16}/> SCROLL TO SEE THE SYSTEM</span><span>BUILT FOR THE MOMENTS THAT MATTER</span></div>
  </section>
  <section id="how-it-works" className="story-section"><div className="section-head"><span className="eyebrow">01 / FROM FOOTAGE TO EVIDENCE</span><h2>See more.<br/>Understand sooner.</h2><p>Bring your road footage into one place. Follow the evidence from vehicle movement to a reviewed incident.</p></div><div className="story-grid">{[
   {n:'01',icon:ScanLine,title:'Detect the movement.',text:'YOLO identifies cars, motorcycles, buses, and trucks in your video. Each camera keeps its own vehicle tracks.'},
   {n:'02',icon:Route,title:'Follow the evidence.',text:'Changes in motion and overlapping vehicles are checked across consecutive frames. Potential incidents arrive with measured signals and a captured image.'},
   {n:'03',icon:ShieldCheck,title:'Make the right call.',text:'Review the footage, confirm or dismiss a candidate, and send a signed alert to your configured response destination.'}
  ].map((item,i)=><motion.article key={item.n} initial={{opacity:0,y:45}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.3}} transition={{delay:i*.12,duration:.6}}><div className="story-top"><item.icon size={25}/><span>{item.n}</span></div><h3>{item.title}</h3><p>{item.text}</p></motion.article>)}</div></section>
  <section id="workspace" className="workspace-section"><motion.div initial={{opacity:0,y:35}} whileInView={{opacity:1,y:0}} viewport={{once:true}}><span className="eyebrow">02 / YOUR OPERATIONS WORKSPACE</span><h2>The road moves.<br/><span>Stay connected.</span></h2><p>Monitor a camera, analyze a video, and review your incident history. Live updates keep operators connected to the same evidence.</p><StartFlow/></motion.div><div className="workspace-list">{[['01','Connect your footage','Uploaded video, browser camera, or a configured CCTV stream.'],['02','Review what happened','Captured frames, vehicle tracks, and the original video.'],['03','Track the response','Confirmation, signed webhook delivery, and a shared audit trail.']].map(([n,title,text])=><div key={n}><span>{n}</span><div><h3>{title}</h3><p>{text}</p></div></div>)}</div></section>
  <VideoLibrary/>
  <LandingDetails/>
  <footer className="landing-footer"><Brand/><span>Accident Alert · Road monitoring & incident review</span><Link to="/login">Sign in</Link></footer>
 </div>;
}
