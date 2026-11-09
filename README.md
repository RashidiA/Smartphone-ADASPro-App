# ADAS Pro: Rahmah Version 🚗📱

A phone-based **driver-assistance (ADAS Level-2 style) demo**. It opens the phone's rear camera in the browser, shows the live road view and draws **camera-overlay (AR-style)** boxes, a **blue lane overlay** and **audible / visual / vibration warnings**. All processing runs **on the phone** (edge computing) – no video is sent to a server.

> ⚠️ **Learning / prototype tool – not a certified safety system.** The driver stays fully responsible. Do not rely on it, and do not operate it while driving; have a passenger set it up.

**Live app:** https://smartphone-adaspro-app-2uumyn58jvniwsku8uspgu.streamlit.app/

## What it detects and warns

| Feature | How | Warning |
|---|---|---|
| **Lane lines** | White lines found by scanline analysis, fitted to straight lines; dotted lines bridged for 0.9 s | Continuous **blue overlay**; **LANE DEPARTURE (LEFT/RIGHT)** when the car centre drifts beyond the set sensitivity (overlay turns red) |
| **Vehicles** (car, truck, bus, motorcycle) | COCO-SSD lite, WebGL | **VEHICLE AHEAD**, **COLLISION WARNING** from estimated distance and time-to-collision (TTC) |
| **Pedestrians / cyclists** | COCO-SSD | **PEDESTRIAN**, **PEDESTRIAN IN PATH** |
| **Animals** (dog, cat, horse, cow, sheep) | COCO-SSD | **ANIMAL ON ROAD**, **ANIMAL IN PATH** |
| **Traffic lights** | COCO-SSD + red/yellow/green pixel check | **RED LIGHT**, **YELLOW LIGHT**, green info |
| **Stop signs** | COCO-SSD | **STOP SIGN AHEAD** |
| **Speed-limit signs** | *Optional custom model* (see below) | **SPEED LIMIT n**, **OVER SPEED LIMIT** (GPS speed) |

Alerts: top banner (amber = caution, orange = warning, flashing red = danger), beeps (more beeps = higher level) and vibration (Android Chrome).

## Why it is fast

* The video is displayed natively; boxes and lanes are drawn on a transparent canvas on top (no per-frame pixel copy of the whole image).
* AI runs on a **small 320 px copy** of the frame, on the GPU (WebGL), in its own loop that never overlaps itself (max rate adjustable).
* Lane detection reads only ~18 rows of a 320 px image every 2nd frame (≈1 ms).
* In a headless-browser test with a stubbed model the page rendered at 30 fps. Real speed depends on the phone: expect roughly 10–20 AI frames per second on a good phone with the *Fast* mode.

## Install and run

```bash
pip install streamlit
streamlit run adas_pro.py
```

Camera and GPS need **HTTPS**. Deploy to Streamlit Community Cloud (only `streamlit` in `requirements.txt`), open the app URL (https://smartphone-adaspro-app-2uumyn58jvniwsku8uspgu.streamlit.app/) on the phone in **Chrome**, allow **camera** and **location**, and press **START ADAS**. The first start downloads the AI model (a few MB).

## Set-up in the car

1. Mount the phone **centred on the windscreen**, camera level with the road, in landscape.
2. In the sidebar set **Horizon height** (where road meets sky) and **Bonnet cut-off** so the lane search sees only the road.
3. Set the camera **field of view** (typically 65–75°) – used for the distance estimate.
4. While driving centred, press **⌖ Set centre** once if the camera is not exactly in the middle.
5. Press **↔ Lane change** while signalling to mute the lane warning.

## Sidebar controls

Feature toggles (lane, vehicles, pedestrians, animals, signs), sound, vibration, lane sensitivity, minimum speed for lane warning (GPS), TTC and minimum gap for collision warning, performance mode (*Fast* = lite MobileNet, *Balanced*, *Accurate*), AI input width, AI rate, camera width, horizon, bonnet and field of view.

## Optional: speed-limit signs (custom model)

COCO has no speed-limit class. To add it:

1. Train a small detector (e.g. YOLO nano) on speed-limit signs, ideally including **Malaysian** signs, and convert it to **TensorFlow.js** (`model.json`).
2. Host it over HTTPS and paste the URL into **Custom sign model** in the sidebar.
3. Edit `customSignDetect()` in `adas_pro.py` to decode your model's output and return `{class: "speed limit 50", score, bbox:[x, y, w, h]}`. Class names starting with `speed limit` plus a number trigger the limit display and the over-speed warning.

## Limits

* Straight-line lane model, assumes white lines, a roughly centred camera and decent light. Curves, worn paint, night rain and glare reduce accuracy.
* Distance and TTC come from box size and the field of view you set – approximate only.
* Traffic-light colour is a simple pixel check and can fail in glare.
* No pose skeletons or segmentation outlines (they would slow a phone too much).
* Web browsers limit camera frame rate, background running and sensor access.

## For true real-time

Port the same logic to a **native app**: Android (Kotlin, CameraX, TensorFlow Lite / LiteRT with GPU or NNAPI delegate, YOLOv8n / YOLO11n INT8 at 320–416 px) or iOS (Swift, Core ML). Expect 25–40 fps. Python does not run on the phone; Streamlit only serves the page.

## Part of the Automotive Knowledge Hub

Collaborators welcome: developers, ADAS / computer-vision engineers, educators and students.
