"""Browser-compatible recorded playback with measured YOLO tracks, never live events."""
import json
import os
import subprocess
import tempfile
import cv2
from .config import settings


def replay_path(job_id):
    return settings.media/f'{job_id}-replay.mp4'


def info_path(job_id):
    return settings.media/f'{job_id}-replay.json'


def fit_size(width,height):
    scale=min(1,960/max(width,height))
    return max(2,int(width*scale)//2*2),max(2,int(height*scale)//2*2)


def draw_tracks(frame,tracks,vision_width,vision_height):
    image=frame.copy()
    height,width=image.shape[:2]
    for track in tracks:
        x1,y1,x2,y2=track['box']
        x1,x2=[max(0,min(width-1,round(x*width/vision_width))) for x in (x1,x2)]
        y1,y2=[max(0,min(height-1,round(y*height/vision_height))) for y in (y1,y2)]
        color=(240,210,108)
        cv2.rectangle(image,(x1,y1),(x2,y2),color,2)
        label=f"#{track['id']} {track['class']} {track['confidence']:.0%}"
        font=cv2.FONT_HERSHEY_SIMPLEX
        (tw,th),_=cv2.getTextSize(label,font,.42,1)
        left=min(x1,max(0,width-tw-7));top=max(th+7,y1)
        cv2.rectangle(image,(left,top-th-7),(min(width-1,left+tw+6),top),color,-1)
        cv2.putText(image,label,(left+3,top-4),font,.42,(24,21,15),1,cv2.LINE_AA)
    return image


class ReplayWriter:
    def __init__(self,job_id,width,height,fps):
        self.job_id=job_id
        self.width,self.height=fit_size(width,height)
        self.fps=fps
        self.count=0
        self.measurements=[]
        self.temp=settings.media/f'{job_id}-replay.partial.mp4'
        self.temp.unlink(missing_ok=True)
        self.error_log=tempfile.TemporaryFile()
        self.process=subprocess.Popen([settings.ffmpeg_binary,'-hide_banner','-loglevel','error','-y',
            '-f','rawvideo','-pixel_format','bgr24','-video_size',f'{self.width}x{self.height}',
            '-framerate',str(fps),'-i','pipe:0','-an','-vf','fps=30' if fps>30 else 'null',
            '-c:v','libx264','-preset','veryfast','-crf','23','-threads','1','-pix_fmt','yuv420p',
            '-movflags','+faststart',str(self.temp)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
            stderr=self.error_log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))

    def observe(self,seconds,tracks):
        self.measurements.append({'seconds':seconds,'tracks':tracks})

    def write(self,frame,tracks,vision_width,vision_height):
        image=cv2.resize(frame,(self.width,self.height))
        image=draw_tracks(image,tracks,vision_width,vision_height)
        self.process.stdin.write(image.tobytes())
        self.count+=1

    def finish(self):
        self.process.stdin.close()
        if self.process.wait(timeout=90)!=0 or not self.count or not self.temp.is_file():
            raise ValueError('Recorded replay encoding failed')
        metadata={'duration':self.count/self.fps,'width':self.width,'height':self.height,
                  'measurements':self.measurements,'recorded':True}
        metadata_temp=info_path(self.job_id).with_suffix('.tmp')
        metadata_temp.write_text(json.dumps(metadata),encoding='utf-8')
        os.replace(self.temp,replay_path(self.job_id))
        os.replace(metadata_temp,info_path(self.job_id))
        self.error_log.close()

    def abort(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        if self.process.stdin and not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        self.error_log.close()
        self.temp.unlink(missing_ok=True)
