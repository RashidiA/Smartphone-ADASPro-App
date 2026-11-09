"""ADAS Pro (Level-2 style driver-assistance DEMO) - runs fully in the phone's browser (edge computing).

Features : vehicles / pedestrians / traffic lights / stop signs (COCO-SSD lite on WebGL, small input),
           white lane lines -> continuous BLUE overlay (scanline fit, dotted lines bridged), lane-departure warning,
           forward-collision warning (distance + time-to-collision), sound + vibration alerts, GPS speed.
Note     : a learning / prototype tool. NOT a certified safety system - the driver stays fully responsible.
"""
import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Rahmah Version", layout="wide")

# ----------------------------------------------------------------------------- sidebar
st.sidebar.title("🛠️ ADAS Controls")
st.sidebar.subheader("Detect")
use_lane = st.sidebar.toggle("Lane keeping (blue overlay + departure warning)", value=True)
use_veh = st.sidebar.toggle("Vehicles + collision warning", value=True)
use_ped = st.sidebar.toggle("Pedestrians / cyclists", value=True)
use_sign = st.sidebar.toggle("Traffic lights + stop signs", value=True)
st.sidebar.subheader("Alerts")
sound = st.sidebar.toggle("Sound", value=True)
vibrate = st.sidebar.toggle("Vibration (Android)", value=True)
lane_thr = st.sidebar.slider("Lane warning sensitivity (lower = earlier)", 20, 70, 35, help="Warn when the car centre is this % of half-lane-width away from lane centre. ~50% means the wheel is on the line.") / 100
lane_min_kmh = st.sidebar.slider("Mute lane warning below (km/h, GPS)", 0, 60, 15)
unknown_moving = st.sidebar.checkbox("If GPS speed is unknown, assume moving", value=True)
ttc = st.sidebar.slider("Collision warning: time-to-collision (s)", 1.0, 5.0, 2.5, 0.1)
min_dist = st.sidebar.slider("Collision warning: minimum gap (m)", 3, 30, 8)
st.sidebar.subheader("Performance")
perf = st.sidebar.selectbox("Mode", ["Fast (recommended for phones)", "Balanced", "Accurate (slower)"])
det_w = st.sidebar.select_slider("AI input width (px) - smaller = faster", [224, 256, 320, 416], value=320)
det_fps = st.sidebar.slider("Max AI rate (per second)", 5, 30, 15)
cam_w = st.sidebar.select_slider("Camera width (px)", [480, 640, 800], value=640)
st.sidebar.subheader("Camera set-up")
horizon = st.sidebar.slider("Horizon height (% from top)", 30, 70, 50, help="Where the road meets the sky. Lane search starts just below this line.") / 100
hood = st.sidebar.slider("Bonnet cut-off (% from top)", 70, 100, 92, help="Ignore the dashboard / bonnet at the bottom of the picture.") / 100
fov = st.sidebar.slider("Camera horizontal field of view (°)", 50, 90, 68, help="Used for the distance estimate. Typical phone main camera: 65-75°.")
st.sidebar.divider()
st.sidebar.warning("Driver-assistance DEMO for learning. Not certified, not a replacement for driver attention.")

cfg = {
    "useLane": use_lane, "useVeh": use_veh, "usePed": use_ped, "useSign": use_sign,
    "sound": sound, "vibrate": vibrate, "laneThr": lane_thr, "laneMinKmh": lane_min_kmh, "unknownMoving": unknown_moving,
    "ttc": ttc, "minDist": min_dist, "detW": det_w, "detFps": det_fps, "camW": cam_w,
    "base": {"Fast (recommended for phones)": "lite_mobilenet_v2", "Balanced": "mobilenet_v1", "Accurate (slower)": "mobilenet_v2"}[perf],
    "horizon": horizon, "hood": hood, "fov": fov, "minScore": 0.45, "laneEvery": 2,
}

HTML = r'''
<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html,body{margin:0;background:#0b0f14;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  #wrap{position:relative;width:100%;max-width:900px;margin:auto;background:#000;border-radius:12px;overflow:hidden;user-select:none}
  #v{width:100%;height:auto;display:block;min-height:240px;background:#000}
  #ov{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
  .chip{background:rgba(0,0,0,.65);color:#7CFC00;font:600 14px monospace;padding:5px 9px;border-radius:8px;border:1px solid rgba(124,252,0,.6)}
  #hud{position:absolute;top:8px;left:8px;display:flex;gap:6px;flex-wrap:wrap;max-width:75%}
  #speedBox{position:absolute;bottom:10px;left:10px;font-size:20px}
  #banner{position:absolute;top:10px;left:50%;transform:translateX(-50%);padding:10px 18px;border-radius:12px;font:800 20px system-ui;color:#fff;display:none;text-align:center;box-shadow:0 0 18px rgba(0,0,0,.6);max-width:80%}
  .l1{background:#e69f00}.l2{background:#e5481f}.l3{background:#d00000;animation:blink .35s infinite alternate}
  @keyframes blink{from{opacity:1}to{opacity:.55}}
  #btns{position:absolute;bottom:10px;right:10px;display:flex;gap:6px}
  #btns button{padding:9px 11px;border-radius:10px;border:1px solid #888;background:rgba(0,0,0,.65);color:#fff;font:600 13px system-ui;cursor:pointer}
  #btns button.on{background:#1565c0;border-color:#64b5f6}
  #start{position:absolute;inset:0;background:rgba(0,0,0,.82);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;z-index:50;color:#ddd;text-align:center;padding:18px}
  #startBtn{padding:16px 34px;font-size:19px;border-radius:10px;background:#28a745;color:#fff;border:none;cursor:pointer}
  #status{font-size:14px;max-width:520px;line-height:1.4}
</style></head>
<body>
<div id="wrap">
  <video id="v" autoplay muted playsinline></video>
  <canvas id="ov"></canvas>
  <div id="hud"><span class="chip" id="laneChip">LANE: --</span><span class="chip" id="fpsChip">-- fps</span><span class="chip" id="detChip">AI -- ms</span></div>
  <div id="banner"></div>
  <div class="chip" id="speedBox">SPEED <span id="speedVal">--</span> km/h</div>
  <div id="btns"><button id="btnMute">&#8596; Lane change</button><button id="btnCal">&#8982; Set centre</button><button id="btnFs">&#9974;</button></div>
  <div id="start"><button id="startBtn">&#128640; START ADAS</button><div id="status">Mount the phone at the centre of the windscreen, camera level with the road. Driver assistance only &ndash; you stay responsible for driving.</div></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd@2.2.3/dist/coco-ssd.min.js"></script>
<script>
const CFG = __CFG__;
const $ = id => document.getElementById(id);
const video = $('v'), ov = $('ov'), octx = ov.getContext('2d');

/* ------------------------------------------------------------------ constants */
const LW = 320;                                   // lane-analysis width (px) -> tiny and fast
const laneCv = document.createElement('canvas'), lctx = laneCv.getContext('2d', {willReadFrequently: true});
const detCv  = document.createElement('canvas'), dctx = detCv.getContext('2d');
const tlCv   = document.createElement('canvas'); tlCv.width = 12; tlCv.height = 24;
const tctx   = tlCv.getContext('2d', {willReadFrequently: true});
const VEH = new Set(['car', 'truck', 'bus', 'motorcycle']);
const PED = new Set(['person', 'bicycle']);
const REALH = {person: 1.7, bicycle: 1.5, car: 1.5, motorcycle: 1.4, bus: 3.2, truck: 3.0, 'stop sign': 0.75};

/* ------------------------------------------------------------------ state */
let model = null, running = false, audioCtx = null;
let egoSpeed = null;                              // m/s from GPS (null if unknown)
let tracks = [], nextId = 1, lastDetT = 0, detMs = 0, fpsCount = 0, fpsVal = 0, fpsT = performance.now();
let laneMute = false;
const alerts = new Map();                         // key -> {text, level, until}
const lastBeep = {};
const lane = {L: null, R: null, tL: 0, tR: 0, W: 0.6 * LW, offset: 0, bias: 0, status: 'NO LANE', warn: false, cnt: 0, dir: 0, ready: false, yb: 0, yh: 0, y0: 0, LH: 0};

/* ------------------------------------------------------------------ lane detection (pure functions) */
function fitLine(pts) {
  const n = pts.length; if (n < 4) return null;
  let sy = 0, sx = 0, syy = 0, sxy = 0;
  for (const p of pts) { sy += p[0]; sx += p[1]; syy += p[0] * p[0]; sxy += p[0] * p[1]; }
  const den = n * syy - sy * sy; if (Math.abs(den) < 1e-6) return null;
  const a = (n * sxy - sy * sx) / den, b = (sx - a * sy) / n;
  return {a, b, n};
}
function fitRobust(pts) {
  let f = fitLine(pts); if (!f) return null;
  let err = 0; for (const p of pts) { const e = p[1] - (f.a * p[0] + f.b); err += e * e; }
  err = Math.sqrt(err / pts.length);
  const keep = pts.filter(p => Math.abs(p[1] - (f.a * p[0] + f.b)) <= 2.2 * err + 1.5);
  if (keep.length < pts.length && keep.length >= 4) { f = fitLine(keep); if (!f) return null; pts = keep; }
  let e2 = 0; for (const p of pts) { const e = p[1] - (f.a * p[0] + f.b); e2 += e * e; }
  f.err = Math.sqrt(e2 / pts.length);
  f.span = Math.max(...pts.map(p => p[0])) - Math.min(...pts.map(p => p[0]));
  return f;
}
/* data = RGBA of the ROI (w x rh) ; P = {y0,yh,yb,W,prevL,prevR,w} (lane-canvas coordinates) */
function findLaneLines(data, w, rh, P) {
  const hist = new Uint32Array(256); let n = 0;
  for (let y = 0; y < rh; y += 2) for (let x = 0; x < w; x += 3) {
    const i = (y * w + x) * 4; hist[Math.min(255, (0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]) | 0)]++; n++;
  }
  let acc = 0, p97 = 255; for (let v = 255; v >= 0; v--) { acc += hist[v]; if (acc >= n * 0.03) { p97 = v; break; } }
  const T = Math.max(135, Math.min(235, p97 * 0.9));                // adaptive "white" threshold
  const cx = w / 2, NR = 18, Lp = [], Rp = [];
  for (let k = 0; k < NR; k++) {
    const t = k / (NR - 1), y = Math.min(rh - 1, Math.round(t * (rh - 1))), yAbs = y + P.y0;
    const persp = Math.max(0.05, (yAbs - P.yh) / (P.yb - P.yh));       // 0 at horizon -> 1 at bottom
    const maxW = 2 + 0.07 * w * persp, half = 0.5 * P.W * persp;
    const segs = []; let s = -1, gap = 0;
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4, r = data[i], g = data[i + 1], b = data[i + 2];
      const white = (0.299 * r + 0.587 * g + 0.114 * b) > T && (Math.max(r, g, b) - Math.min(r, g, b)) < 70;
      if (white) { if (s < 0) s = x; gap = 0; }
      else if (s >= 0) { if (++gap > 2) { segs.push([s, x - gap]); s = -1; gap = 0; } }
    }
    if (s >= 0) segs.push([s, w - 1]);
    const cands = segs.filter(sg => (sg[1] - sg[0] + 1) <= maxW + 1).map(sg => (sg[0] + sg[1]) / 2);
    for (const side of ['L', 'R']) {
      const prev = side === 'L' ? P.prevL : P.prevR;
      const exp = prev ? prev.a * yAbs + prev.b : (side === 'L' ? cx - half : cx + half);
      const gate = prev ? Math.max(5, 0.07 * w * persp + 4) : 0.20 * w * persp + 6;
      let best = null, bd = 1e9;
      for (const c of cands) {
        if (side === 'L' && c > cx + 0.06 * w) continue; if (side === 'R' && c < cx - 0.06 * w) continue;
        const d = Math.abs(c - exp); if (d < gate && d < bd) { bd = d; best = c; }
      }
      if (best !== null) (side === 'L' ? Lp : Rp).push([yAbs, best]);
    }
  }
  const out = {L: null, R: null, T};
  const fl = fitRobust(Lp), fr = fitRobust(Rp), minSpan = 0.22 * rh;
  if (fl && fl.span >= minSpan && fl.err < 0.03 * w && fl.a < -0.25) out.L = fl;     // left line leans right going up
  if (fr && fr.span >= minSpan && fr.err < 0.03 * w && fr.a > 0.25) out.R = fr;
  return out;
}
/* lateral offset of the camera centre inside the lane: -1 (left line) .. +1 (right line) */
function laneOffset(L, R, W, yb, cx) {
  const xl = L ? L.a * yb + L.b : null, xr = R ? R.a * yb + R.b : null;
  let centre, half;
  if (xl !== null && xr !== null) { centre = (xl + xr) / 2; half = (xr - xl) / 2; }
  else if (xl !== null) { centre = xl + W / 2; half = W / 2; }
  else if (xr !== null) { centre = xr - W / 2; half = W / 2; }
  else return null;
  return (cx - centre) / Math.max(10, half);
}

/* ------------------------------------------------------------------ lane update + warning logic */
function runLane(now) {
  const vw = video.videoWidth, vh = video.videoHeight; if (!vw) return;
  const LH = Math.round(LW * vh / vw);
  if (laneCv.width !== LW || laneCv.height !== LH) { laneCv.width = LW; laneCv.height = LH; }
  lane.LH = LH; lane.yh = CFG.horizon * LH; lane.y0 = Math.round((CFG.horizon + 0.05) * LH); lane.yb = Math.round(CFG.hood * LH);
  const rh = lane.yb - lane.y0; if (rh < 20) return;
  lctx.drawImage(video, 0, 0, LW, LH);
  const img = lctx.getImageData(0, lane.y0, LW, rh);
  const res = findLaneLines(img.data, LW, rh, {y0: lane.y0, yh: lane.yh, yb: lane.yb, W: lane.W, prevL: lane.L, prevR: lane.R});
  const HOLD = 900, al = 0.35;
  for (const s of ['L', 'R']) {
    const f = res[s];
    if (f) { if (lane[s]) { lane[s].a += al * (f.a - lane[s].a); lane[s].b += al * (f.b - lane[s].b); } else lane[s] = {a: f.a, b: f.b}; lane['t' + s] = now; }
    else if (now - lane['t' + s] > HOLD) lane[s] = null;           // dotted line: keep last fit for 0.9 s
  }
  if (lane.L && lane.R) {
    const w = (lane.R.a * lane.yb + lane.R.b) - (lane.L.a * lane.yb + lane.L.b);
    if (w > 0.25 * LW && w < 0.95 * LW) lane.W += 0.1 * (w - lane.W);
  }
  const off = laneOffset(lane.L, lane.R, lane.W, lane.yb, LW / 2);
  lane.ready = off !== null;
  if (!lane.ready) { lane.status = 'NO LANE'; lane.warn = false; lane.cnt = 0; return; }
  lane.offset = off - lane.bias;
  lane.status = (lane.L && lane.R) ? 'LANE OK' : 'LANE 1 LINE';
  const speedOk = egoSpeed === null ? CFG.unknownMoving : egoSpeed * 3.6 >= CFG.laneMinKmh;
  const thr = CFG.laneThr;
  if (CFG.useLane && speedOk && !laneMute) {
    if (Math.abs(lane.offset) > thr) lane.cnt = Math.min(lane.cnt + 1, 10);
    else if (Math.abs(lane.offset) < thr * 0.75) lane.cnt = Math.max(0, lane.cnt - 1);
    lane.warn = lane.cnt >= 3;
  } else { lane.warn = false; lane.cnt = 0; }
  if (lane.warn) {
    lane.dir = lane.offset < 0 ? -1 : 1;
    setAlert('lane', lane.dir < 0 ? '⬅ LANE DEPARTURE (LEFT)' : 'LANE DEPARTURE (RIGHT) ➡', 2, 450);
  }
}

/* ------------------------------------------------------------------ detections */
function iou(a, b) {
  const x1 = Math.max(a.x, b.x), y1 = Math.max(a.y, b.y), x2 = Math.min(a.x + a.w, b.x + b.w), y2 = Math.min(a.y + a.h, b.y + b.h);
  const i = Math.max(0, x2 - x1) * Math.max(0, y2 - y1); return i / (a.w * a.h + b.w * b.h - i + 1e-6);
}
function laneXAt(side, yl) {                                       // lane line x at lane-canvas row yl (uses width memory if one line is missing)
  const f = side === 'L' ? lane.L : lane.R; if (f) return f.a * yl + f.b;
  const o = side === 'L' ? lane.R : lane.L; if (!o) return null;
  const persp = Math.max(0.05, (yl - lane.yh) / (lane.yb - lane.yh)), x = o.a * yl + o.b;
  return side === 'L' ? x - lane.W * persp : x + lane.W * persp;
}
function corridorAt(yv, widen) {                                   // ego corridor in video pixels at row yv
  const vw = video.videoWidth, vh = video.videoHeight, s = vw / LW;
  if (lane.ready && lane.LH) {
    const yl = yv / s, xl = laneXAt('L', yl), xr = laneXAt('R', yl);
    if (xl !== null && xr !== null) { const m = (xr - xl) * (0.10 + widen); return [(xl - m) * s, (xr + m) * s]; }
  }
  const hy = CFG.horizon * vh, t = Math.min(1, Math.max(0, (yv - hy) / (vh - hy))), half = vw * (0.04 + 0.18 * t) * (1 + widen * 2);
  return [vw / 2 - half, vw / 2 + half];
}
function classifyLight(box) {                                      // red / yellow / green from the pixels inside the box
  try {
    const vw = video.videoWidth; tctx.drawImage(video, Math.max(0, box.x), Math.max(0, box.y), Math.max(2, box.w), Math.max(2, box.h), 0, 0, 12, 24);
    const d = tctx.getImageData(0, 0, 12, 24).data; let R = 0, G = 0, Y = 0;
    for (let i = 0; i < d.length; i += 4) {
      const r = d[i], g = d[i + 1], b = d[i + 2];
      if (r > 190 && g < 130 && b < 130) R++; else if (r > 190 && g > 160 && b < 120) Y++; else if (g > 170 && r < 150 && b > 80 && b < 230) G++;
    }
    const m = Math.max(R, Y, G); if (m < 3) return 'unknown'; return m === R ? 'red' : (m === Y ? 'yellow' : 'green');
  } catch (e) { return 'unknown'; }
}
function handleDetections(preds, sx, sy, now) {
  const vw = video.videoWidth, vh = video.videoHeight, f = (vw / 2) / Math.tan(CFG.fov * Math.PI / 360);
  const objs = [];
  for (const p of preds) {
    const c = p.class; if (p.score < CFG.minScore) continue;
    const kind = VEH.has(c) ? 'veh' : PED.has(c) ? 'ped' : (c === 'traffic light' || c === 'stop sign') ? 'sign' : null;
    if (!kind) continue;
    if (kind === 'veh' && !CFG.useVeh) continue; if (kind === 'ped' && !CFG.usePed) continue; if (kind === 'sign' && !CFG.useSign) continue;
    const o = {cls: c, kind, score: p.score, x: p.bbox[0] * sx, y: p.bbox[1] * sy, w: p.bbox[2] * sx, h: p.bbox[3] * sy};
    o.cx = o.x + o.w / 2; o.by = o.y + o.h;
    o.dist = REALH[c] ? Math.max(1, f * REALH[c] / Math.max(4, o.h)) : null;
    const [cl, cr] = corridorAt(o.by, 0); o.inPath = o.cx > cl && o.cx < cr;
    const [wl, wr] = corridorAt(o.by, 0.35); o.nearPath = o.cx > wl && o.cx < wr;
    objs.push(o);
  }
  // simple tracking -> closing speed / time-to-collision
  const used = new Set();
  for (const o of objs) {
    let best = null, bi = 0.25;
    for (const t of tracks) { if (used.has(t) || t.cls !== o.cls) continue; const v = iou(o, t.box); if (v > bi) { bi = v; best = t; } }
    if (!best) { best = {id: nextId++, cls: o.cls, hist: [], d: o.dist, v: 0}; tracks.push(best); }
    used.add(best); best.box = o; best.seen = now;
    if (o.dist !== null) {
      best.d = best.d === null ? o.dist : best.d + 0.5 * (o.dist - best.d);
      best.hist.push({t: now, d: best.d}); while (best.hist.length && now - best.hist[0].t > 1400) best.hist.shift();
      const old = best.hist.find(h => now - h.t >= 450);
      if (old) { const v = (old.d - best.d) / ((now - old.t) / 1000); best.v += 0.4 * (v - best.v); }
    }
    o.d = best.d; o.closing = best.v; o.ttc = (o.d !== null && best.v > 0.6) ? o.d / best.v : null; o.id = best.id;
    if (o.cls === 'traffic light') o.light = classifyLight(o);
  }
  tracks = tracks.filter(t => now - t.seen < 800);
  lastObjs = objs; lastDetT = now;
  evaluate(objs);
}
let lastObjs = [];
function evaluate(objs) {
  const vEgo = egoSpeed || 0, minD = Math.max(CFG.minDist, vEgo * 1.0);
  let lightObj = null;
  for (const o of objs) {
    const dTxt = o.d ? ` ${o.d.toFixed(0)} m` : '';
    if (o.kind === 'veh' && o.inPath) {
      if ((o.ttc !== null && o.ttc < CFG.ttc) || (o.d !== null && o.d < minD)) setAlert('fcw' + o.id, 'COLLISION WARNING' + dTxt, 3, 700);
      else if (o.d !== null && o.d < Math.max(25, vEgo * 2)) setAlert('veh' + o.id, 'VEHICLE AHEAD' + dTxt, 1, 700);
    } else if (o.kind === 'ped') {
      if (o.inPath && o.d !== null && o.d < 15) setAlert('ped' + o.id, 'PEDESTRIAN IN PATH' + dTxt, 3, 700);
      else if (o.nearPath || o.inPath) setAlert('ped' + o.id, 'PEDESTRIAN' + dTxt, 2, 700);
      else if (o.d !== null && o.d < 30) setAlert('ped' + o.id, 'PEDESTRIAN NEARBY' + dTxt, 1, 700);
    } else if (o.cls === 'stop sign' && o.nearPath) setAlert('stop', 'STOP SIGN AHEAD', 2, 900);
    else if (o.cls === 'traffic light' && Math.abs(o.cx - video.videoWidth / 2) < 0.3 * video.videoWidth) {
      if (!lightObj || o.h > lightObj.h) lightObj = o;
    }
  }
  if (lightObj) {
    if (lightObj.light === 'red') setAlert('tl', 'RED LIGHT', 2, 900);
    else if (lightObj.light === 'yellow') setAlert('tl', 'YELLOW LIGHT', 1, 900);
    else if (lightObj.light === 'green') setAlert('tlg', 'GREEN LIGHT', 0, 900);
    else setAlert('tl', 'TRAFFIC LIGHT AHEAD', 1, 900);
  }
}

/* ------------------------------------------------------------------ alerts: banner, beep, vibration */
function setAlert(key, text, level, ms) {
  const now = performance.now(), a = alerts.get(key);
  alerts.set(key, {text, level, until: now + ms});
  if (level > 0 && (!a || a.until < now)) fire(key, level);
}
function fire(key, level) {
  const now = performance.now(), gap = level >= 3 ? 700 : 1800;
  if (lastBeep[key] && now - lastBeep[key] < gap) return; lastBeep[key] = now;
  if (CFG.sound && audioCtx) {
    const n = level >= 3 ? 3 : level === 2 ? 2 : 1, f = level >= 3 ? 1400 : level === 2 ? 1000 : 780;
    for (let i = 0; i < n; i++) {
      const t0 = audioCtx.currentTime + i * 0.16, o = audioCtx.createOscillator(), g = audioCtx.createGain();
      o.frequency.value = f; o.type = 'square'; g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.25, t0 + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.12);
      o.connect(g).connect(audioCtx.destination); o.start(t0); o.stop(t0 + 0.14);
    }
  }
  if (CFG.vibrate && navigator.vibrate) { try { navigator.vibrate(level >= 3 ? [120, 60, 120, 60, 120] : [140]); } catch (e) {} }
}
function updateBanner(now) {
  let top = null;
  for (const [k, a] of alerts) { if (a.until < now) { alerts.delete(k); continue; } if (!top || a.level > top.level) top = a; }
  const b = $('banner');
  if (!top) { b.style.display = 'none'; return; }
  b.style.display = 'block'; b.textContent = top.text;
  b.className = top.level >= 3 ? 'l3' : top.level === 2 ? 'l2' : top.level === 1 ? 'l1' : '';
  if (top.level === 0) b.style.background = '#2e7d32'; else b.style.background = '';
}

/* ------------------------------------------------------------------ drawing */
function drawLane() {
  if (!lane.ready) return;
  const vw = video.videoWidth, s = vw / LW, y0 = lane.y0, y1 = lane.yb;
  const xl0 = laneXAt('L', y0), xl1 = laneXAt('L', y1), xr0 = laneXAt('R', y0), xr1 = laneXAt('R', y1);
  const warn = lane.warn, fill = warn ? 'rgba(255,40,40,0.35)' : 'rgba(0,120,255,0.30)', line = warn ? 'rgba(255,70,70,0.95)' : 'rgba(30,150,255,0.95)';
  octx.lineCap = 'round';
  if (xl0 !== null && xr0 !== null) {
    octx.fillStyle = fill; octx.beginPath(); octx.moveTo(xl0 * s, y0 * s); octx.lineTo(xr0 * s, y0 * s); octx.lineTo(xr1 * s, y1 * s); octx.lineTo(xl1 * s, y1 * s); octx.closePath(); octx.fill();
  }
  octx.lineWidth = Math.max(4, vw * 0.009);
  for (const [s0, s1, real] of [[xl0, xl1, !!lane.L], [xr0, xr1, !!lane.R]]) {
    if (s0 === null) continue; octx.strokeStyle = line; octx.setLineDash(real ? [] : [14, 12]);
    octx.beginPath(); octx.moveTo(s0 * s, y0 * s); octx.lineTo(s1 * s, y1 * s); octx.stroke();
  }
  octx.setLineDash([]);
}
function drawObjs(now) {
  if (now - lastDetT > 1200) return;
  octx.font = `600 ${Math.max(13, video.videoWidth * 0.026)}px system-ui`; octx.textBaseline = 'bottom';
  for (const o of lastObjs) {
    const danger = (o.kind === 'veh' && o.inPath && ((o.ttc !== null && o.ttc < CFG.ttc) || (o.d !== null && o.d < CFG.minDist))) || (o.kind === 'ped' && o.inPath && o.d !== null && o.d < 15);
    const col = danger ? '#ff2d2d' : o.kind === 'veh' ? '#39ff14' : o.kind === 'ped' ? '#ff4dd2' : '#ffd400';
    octx.strokeStyle = col; octx.lineWidth = danger ? 5 : 3; octx.strokeRect(o.x, o.y, o.w, o.h);
    let label = o.cls === 'traffic light' && o.light && o.light !== 'unknown' ? 'light ' + o.light : o.cls;
    if (o.d) label += ' ' + o.d.toFixed(0) + 'm'; if (o.ttc !== null && o.ttc < 6) label += ' TTC ' + o.ttc.toFixed(1) + 's';
    const tw = octx.measureText(label).width + 8, ty = Math.max(18, o.y);
    octx.fillStyle = col; octx.fillRect(o.x, ty - 20, tw, 20); octx.fillStyle = '#000'; octx.fillText(label, o.x + 4, ty);
  }
}
function frame(now) {
  if (!running) return;
  const vw = video.videoWidth, vh = video.videoHeight;
  if (vw) {
    if (ov.width !== vw || ov.height !== vh) { ov.width = vw; ov.height = vh; }
    octx.clearRect(0, 0, vw, vh);
    if (CFG.useLane && (frame.n = (frame.n || 0) + 1) % CFG.laneEvery === 0) runLane(now);
    if (CFG.useLane) drawLane();
    drawObjs(now); updateBanner(now);
    fpsCount++;
    if (now - fpsT > 1000) { fpsVal = fpsCount * 1000 / (now - fpsT); fpsCount = 0; fpsT = now;
      $('fpsChip').textContent = fpsVal.toFixed(0) + ' fps'; $('detChip').textContent = model ? 'AI ' + detMs.toFixed(0) + ' ms' : 'AI off';
      const lc = $('laneChip'); lc.textContent = lane.status + (lane.ready ? ' ' + (lane.offset >= 0 ? '+' : '') + lane.offset.toFixed(2) : ''); lc.style.color = lane.warn ? '#ff6b6b' : '#7CFC00'; }
  }
  if (video.requestVideoFrameCallback) video.requestVideoFrameCallback((t) => frame(t)); else requestAnimationFrame(frame);
}

/* ------------------------------------------------------------------ detection loop (separate from rendering, never overlaps itself) */
async function detectLoop() {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  while (running) {
    const t0 = performance.now();
    if (model && video.readyState >= 2 && !document.hidden && (CFG.useVeh || CFG.usePed || CFG.useSign)) {
      try {
        const vw = video.videoWidth, vh = video.videoHeight, dw = CFG.detW, dh = Math.round(dw * vh / vw);
        if (detCv.width !== dw || detCv.height !== dh) { detCv.width = dw; detCv.height = dh; }
        dctx.drawImage(video, 0, 0, dw, dh);                         // small input = much faster SSD
        const preds = await model.detect(detCv, 20);
        detMs += 0.3 * ((performance.now() - t0) - detMs);
        handleDetections(preds, vw / dw, vh / dh, performance.now());
      } catch (e) { console.warn(e); }
    }
    await sleep(Math.max(1, 1000 / CFG.detFps - (performance.now() - t0)));
  }
}

/* ------------------------------------------------------------------ start-up */
$('btnMute').onclick = () => { laneMute = !laneMute; $('btnMute').classList.toggle('on', laneMute); if (laneMute) alerts.delete('lane'); };
$('btnCal').onclick = () => { if (lane.ready) { lane.bias += lane.offset; } };
$('btnFs').onclick = () => { const w = $('wrap'); (w.requestFullscreen || w.webkitRequestFullscreen || function () {}).call(w); };
$('startBtn').onclick = async () => {
  const st = $('status'), btn = $('startBtn'); btn.disabled = true;
  try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {}
  try {
    st.textContent = 'Starting camera...';
    const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'environment', width: {ideal: CFG.camW}, height: {ideal: Math.round(CFG.camW * 3 / 4)}, frameRate: {ideal: 30}}, audio: false});
    video.srcObject = stream; await video.play();
  } catch (e) { st.textContent = 'Camera error: ' + e.message + ' (allow camera access, use HTTPS).'; btn.disabled = false; return; }
  try { navigator.geolocation.watchPosition(p => { egoSpeed = (p.coords.speed === null || isNaN(p.coords.speed)) ? null : p.coords.speed; $('speedVal').textContent = egoSpeed === null ? '--' : (egoSpeed * 3.6).toFixed(0); }, null, {enableHighAccuracy: true, maximumAge: 500}); } catch (e) {}
  try { if (navigator.wakeLock) navigator.wakeLock.request('screen').catch(() => {}); } catch (e) {}
  running = true; $('start').style.display = 'none';
  frame(performance.now());                                          // lane overlay runs immediately, even before the AI model is ready
  if (CFG.useVeh || CFG.usePed || CFG.useSign) {
    try {
      try { await tf.setBackend('webgl'); } catch (e) {} await tf.ready();
      model = await cocoSsd.load({base: CFG.base});
      await model.detect(detCv.width ? detCv : video, 5);            // warm-up compiles the GPU shaders
    } catch (e) { console.warn('model load failed', e); model = null; setAlert('info', 'AI model not loaded - lane only', 1, 4000); }
  }
  detectLoop();
};
</script>
</body></html>
'''

components.html(HTML.replace("__CFG__", json.dumps(cfg)), height=760, scrolling=False)
st.caption("Tip: open the app URL on the phone (HTTPS), allow camera + location, mount the phone centred on the windscreen, then press START. "
           "Use '↔ Lane change' when you signal a lane change and '⌖ Set centre' once while driving centred.")
