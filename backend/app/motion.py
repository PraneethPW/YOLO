"""Pixel-space temporal evidence. Scores are heuristic, never calibrated probabilities."""
from collections import defaultdict, deque
from itertools import combinations
import math
import statistics


def iou(a, b):
    x = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = x * y
    return intersection / max(1, (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1])-intersection)


class MotionVerifier:
    def __init__(self):
        self.history = defaultdict(lambda: deque(maxlen=16))
        self.evidence = defaultdict(lambda: deque(maxlen=8))
        self.last_alert = {}

    def update(self, tracks, timestamp):
        motion = {}
        for track in tracks:
            box = track['box']
            center = ((box[0]+box[2])/2, (box[1]+box[3])/2)
            hist = self.history[track['id']]
            if hist and timestamp - hist[-1][0] > 3:
                hist.clear()
            hist.append((timestamp, center, box))
            velocities = []
            for previous, current in zip(hist, list(hist)[1:]):
                dt = current[0] - previous[0]
                if dt > 0:
                    scale = max(20, current[2][3] - current[2][1])
                    velocities.append(((current[1][0]-previous[1][0])/dt/scale,
                                       (current[1][1]-previous[1][1])/dt/scale))
            if len(velocities) < 5:
                continue
            speeds = [math.hypot(*v) for v in velocities]
            baseline = statistics.median(speeds[:-2])
            deceleration = baseline > 0.25 and speeds[-1] < baseline * 0.3
            v1, v2 = velocities[-3], velocities[-1]
            product = math.hypot(*v1) * math.hypot(*v2)
            turn = product > 0.08 and (v1[0]*v2[0]+v1[1]*v2[1])/product < 0.25
            motion[track['id']] = {'deceleration': deceleration, 'direction_change': turn,
                                   'relative_speed': round(speeds[-1], 3), 'baseline': round(baseline,3)}
        candidates = []
        active_pairs = set()
        for a,b in combinations(tracks, 2):
            pair = tuple(sorted((a['id'], b['id'])))
            active_pairs.add(pair)
            overlap = iou(a['box'], b['box'])
            signals = [motion.get(a['id'], {}), motion.get(b['id'], {})]
            abrupt = any(m.get('deceleration') or m.get('direction_change') for m in signals)
            # Overlap alone can mean occlusion. Require independent motion evidence.
            suspicious = overlap > 0.10 and abrupt
            history = self.evidence[pair]
            history.append((timestamp, suspicious, overlap, signals))
            recent = [x for x in history if timestamp - x[0] <= 2.5]
            hits = sum(x[1] for x in recent)
            required = 4 if overlap < 0.25 else 3
            span = recent[-1][0] - recent[0][0] if recent else 0
            if hits >= required and span >= 0.35 and timestamp-self.last_alert.get(pair,-999) > 30:
                self.last_alert[pair] = timestamp
                candidates.append({'score': min(0.95, 0.45 + hits*0.055 + overlap*0.2),
                                   'signals': {'track_ids': list(pair), 'overlap': round(overlap,3),
                                               'supporting_frames': hits, 'required_frames': required,
                                               'window_seconds': round(span,2), 'motion': signals,
                                               'method': 'adaptive motion verification',
                                               'score_type': 'heuristic evidence score'}})
        for key in list(self.evidence):
            if key not in active_pairs:
                del self.evidence[key]
        for key in list(self.history):
            if timestamp-self.history[key][-1][0] > 5:
                del self.history[key]
        return candidates
