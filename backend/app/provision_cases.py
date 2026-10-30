"""Provision attributed historical collision footage and human reference evidence explicitly."""
import json
import subprocess
from pathlib import Path
from uuid import NAMESPACE_URL,uuid5
import httpx
from . import db
from .config import settings
from .incident_service import capture_report

CASES=[
 {'slug':'highway-rear-end','name':'Highway · rear-end collision','filename':'highway-rear-end-case.mp4',
  'url':'https://upload.wikimedia.org/wikipedia/commons/b/b1/Multiple_cars_rear-end_collision_on_highway.webm?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original',
  'reference':'https://commons.wikimedia.org/wiki/File:Multiple_cars_rear-end_collision_on_highway.webm',
  'start':14,'duration':14,'at':8,'notes':'Inspect the left lanes as vehicles reach a queue; the reference frame shows the collision sequence. Review the surrounding video before deciding.'},
 {'slug':'lane-change-rear-end','name':'Urban road · lane-change collision','filename':'lane-change-case.mp4',
  'url':'https://upload.wikimedia.org/wikipedia/commons/7/79/The_van_in_front_suddenly_changed_lanes_and_caused_the_vehicle_to_rear-end_collision.webm?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original',
  'reference':'https://commons.wikimedia.org/wiki/File:The_van_in_front_suddenly_changed_lanes_and_caused_the_vehicle_to_rear-end_collision.webm',
  'start':0,'duration':12,'at':4.5,'notes':'Inspect the vehicles changing lanes ahead of the dashcam and the abrupt closing distance. The original footage contains a purple highlight overlay.'}
]

def provision():
    owner=db.query("SELECT id FROM users WHERE role='admin' ORDER BY created_at LIMIT 1",one=True)
    if not owner: raise RuntimeError('An administrator must exist')
    for case in CASES:
        sid=uuid5(NAMESPACE_URL,'accident-alert:case-source:'+case['slug'])
        jid=uuid5(NAMESPACE_URL,'accident-alert:case-job:'+case['slug'])
        iid=uuid5(NAMESPACE_URL,'accident-alert:case-reference:'+case['slug'])
        path=settings.media/f'{jid}.mp4'
        if not path.is_file():
            temp=settings.media/f'{jid}.download.webm'
            output=settings.media/f'{jid}.converting.mp4'
            try:
                with httpx.stream('GET',case['url'],follow_redirects=True,timeout=90,
                    headers={'User-Agent':'AccidentAlertProject/1.0 (https://github.com/PraneethPW/YOLO)'}) as response:
                    response.raise_for_status()
                    size=0
                    with temp.open('wb') as out:
                        for chunk in response.iter_bytes():
                            size+=len(chunk)
                            if size>100*1024*1024: raise ValueError('Case download exceeds limit')
                            out.write(chunk)
                subprocess.run([settings.ffmpeg_binary,'-hide_banner','-loglevel','error','-y','-ss',str(case['start']),
                    '-i',str(temp),'-t',str(case['duration']),'-an','-vf','scale=960:-2','-c:v','libx264',
                    '-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True,timeout=180)
                output.replace(path)
            finally:
                temp.unlink(missing_ok=True);output.unlink(missing_ok=True)
        with db.connection() as conn:
            conn.execute('''INSERT INTO sources(id,name,kind,location,created_by,is_shared,is_case_study,credit,reference_url)
                VALUES(%s,%s,'upload','Recorded dashcam case · historical footage',%s,true,true,%s,%s)
                ON CONFLICT(id) DO UPDATE SET archived=false,is_shared=true,is_case_study=true,credit=EXCLUDED.credit''',
                (sid,case['name'],owner['id'],'Wikimedia Commons · public-domain automated footage · silent excerpt, resized; reference selected by a human',case['reference']))
            conn.execute('''INSERT INTO jobs(id,source_id,path,original_name) VALUES(%s,%s,%s,%s)
                ON CONFLICT(id) DO NOTHING''',(jid,sid,str(path),case['filename']))
        snapshot=capture_report({'kind':'upload'},{'path':str(path)},case['at'],iid)
        signals={'method':'Human-selected historical reference','track_ids':[],'supporting_frames':0,
                 'required_frames':0,'window_seconds':0,'overlap':0,'motion':[]}
        db.query('''INSERT INTO incidents(id,source_id,job_id,score,signals,snapshot_path,video_seconds,origin,is_training,notes)
            VALUES(%s,%s,%s,0,%s::jsonb,%s,%s,'reference',true,%s) ON CONFLICT(id) DO NOTHING''',
            (iid,sid,jid,json.dumps(signals),snapshot.name,case['at'],case['notes']))
        print('Recorded case provisioned:',case['name'],flush=True)

if __name__=='__main__':
    db.start()
    try: provision()
    finally: db.close()
