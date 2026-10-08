import math
from collections import Counter
from datetime import datetime,timezone
from . import db


def sample_values(source_id,job_id,video_seconds,tracks,vision_ms,stamp,observed=None):
    observed=observed or datetime.now(timezone.utc)
    counts=Counter(track['class'] for track in tracks)
    bucket=math.floor((video_seconds if job_id else observed.timestamp())/5)
    return (source_id,str(job_id) if job_id else 'live',job_id,bucket,observed,observed,
            video_seconds,video_seconds,1,len(tracks),len(tracks),counts['car'],counts['motorcycle'],
            counts['bus'],counts['truck'],vision_ms,stamp)


# This is part of the existing frame transaction, without an extra database round trip.
SAMPLE_CTE='''INSERT INTO analysis_buckets AS b
 (source_id,session_key,job_id,bucket_index,observed_start,observed_end,video_start,video_end,
 samples,vehicle_sum,vehicle_peak,car_sum,motorcycle_sum,bus_sum,truck_sum,vision_ms_sum,last_stamp)
 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
 ON CONFLICT(source_id,session_key,bucket_index) DO UPDATE SET
 observed_end=excluded.observed_end,video_end=excluded.video_end,
 samples=b.samples+1,vehicle_sum=b.vehicle_sum+excluded.vehicle_sum,
 vehicle_peak=greatest(b.vehicle_peak,excluded.vehicle_peak),
 car_sum=b.car_sum+excluded.car_sum,motorcycle_sum=b.motorcycle_sum+excluded.motorcycle_sum,
 bus_sum=b.bus_sum+excluded.bus_sum,truck_sum=b.truck_sum+excluded.truck_sum,
 vision_ms_sum=b.vision_ms_sum+excluded.vision_ms_sum,last_stamp=excluded.last_stamp
 WHERE b.last_stamp<>excluded.last_stamp RETURNING bucket_index'''


def read(source_id,job_id,minutes):
    row=db.query('''WITH filtered AS MATERIALIZED (
      SELECT * FROM analysis_buckets WHERE source_id=%s AND session_key=%s
       AND (%s::uuid IS NOT NULL OR observed_end>=now()-(%s * interval '1 minute'))
    ), stride AS (SELECT greatest(1,ceil((max(bucket_index)-min(bucket_index)+1)/300.0)) AS n,min(bucket_index) AS origin FROM filtered),
    grouped AS (
      SELECT floor((bucket_index-origin)/n) AS group_id,min(observed_start) AS at,max(observed_end) AS end_at,
       min(video_start) AS video_seconds,max(video_end) AS video_end_seconds,sum(samples) AS samples,
       round(sum(vehicle_sum)::numeric/nullif(sum(samples),0),2) AS vehicles,
       max(vehicle_peak) AS peak,round(sum(vision_ms_sum)::numeric/nullif(sum(samples),0),2) AS vision_ms
      FROM filtered CROSS JOIN stride GROUP BY floor((bucket_index-origin)/n)
    ), summary AS (
      SELECT coalesce(sum(samples),0) AS samples,coalesce(max(vehicle_peak),0) AS peak,
       coalesce(round(sum(vehicle_sum)::numeric/nullif(sum(samples),0),2),0) AS average_vehicles,
       coalesce(round(sum(vision_ms_sum)::numeric/nullif(sum(samples),0),2),0) AS average_vision_ms,
       coalesce(sum(car_sum),0) AS cars,coalesce(sum(motorcycle_sum),0) AS motorcycles,
       coalesce(sum(bus_sum),0) AS buses,coalesce(sum(truck_sum),0) AS trucks,
       min(observed_start) AS first_at,max(observed_end) AS last_at,
       min(video_start) AS first_video_seconds,max(video_end) AS last_video_seconds
      FROM filtered
    ) SELECT (SELECT row_to_json(summary) FROM summary) AS summary,
       coalesce((SELECT json_agg(g ORDER BY group_id) FROM grouped g),'[]'::json) AS points,
       (SELECT n*5 FROM stride) AS bucket_seconds''',
      (source_id,str(job_id) if job_id else 'live',job_id,minutes),one=True)
    return {**row,'job_id':job_id,'window_minutes':minutes,'retention_hours':24}
