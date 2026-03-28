import streamlit as st
import streamlit.components.v1 as components

# --- App Config ---
st.set_page_config(page_title="ADAS Pro AI", layout="centered")

st.title("🚗 ADAS Pro: Vision Safety")
st.markdown("Developed for **Mobile ADAS App**.")

# --- The JavaScript "Java-Speed" Engine ---
# This code runs directly on the phone's GPU using WebGL.
JS_CODE = """
<div style="position: relative; width: 100%; border-radius: 15px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div id="pede_warning" style="position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); padding: 20px; background: rgba(255,0,0,0.9); color: white; font-weight: bold; font-size: 24px; border-radius: 10px; display: none; border: 4px solid white; text-align: center; width: 80%;">🛑 BRAKE: PEDESTRIAN</div>
    <div id="lane_warning" style="position: absolute; top: 10%; left: 10px; padding: 10px; background: rgba(255,165,0,0.8); color: white; border-radius: 5px; display: none;">⚠️ LANE DRIFT</div>
    <div id="speed_sign" style="position: absolute; top: 20px; right: 20px; width: 60px; height: 60px; background: white; border: 4px solid red; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px; color: black;">--</div>
</div>

<audio id="alert_sound" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>
<script async src="https://docs.opencv.org/4.x/opencv.js" type="text/javascript"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: false});
const pedeWarn = document.getElementById('pede_warning');
const laneWarn = document.getElementById('lane_warning');
const speedSign = document.getElementById('speed_sign');
const beep = document.getElementById('alert_sound');

let model;

// 1. Setup AI Model
async function init() {
    model = await cocoSsd.load();
    const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } } 
    });
    video.srcObject = stream;
    video.onloadedmetadata = () => { predict(); };
}

// 2. High-Frequency Prediction Loop
async function predict() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const predictions = await model.detect(video);
    let pedestrianInDanger = false;

    predictions.forEach(p => {
        const [x, y, w, h] = p.bbox;
        const centerX = x + (w / 2);

        // Pedestrian Logic
        if (p.class === 'person' && p.score > 0.5) {
            ctx.strokeStyle = "#FF0000";
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, w, h);
            
            // Check if in "Collision Zone" (Center 40% of view)
            if (centerX > canvas.width * 0.3 && centerX < canvas.width * 0.7) {
                pedestrianInDanger = true;
            }
        }

        // Speed Sign Detection (Approximation)
        if (p.class === 'stop sign') speedSign.innerText = "STOP";
    });

    // Lane Detection (Simplified Intensity Check)
    const frame = ctx.getImageData(0, canvas.height * 0.8, canvas.width, 20);
    let leftWhite = 0;
    for (let i = 0; i < frame.data.length / 2; i += 4) {
        if (frame.data[i] > 200) leftWhite++;
    }
    
    // UI Updates
    if (pedestrianInDanger) { pedeWarn.style.display = "block"; beep.play(); }
    else { pedeWarn.style.display = "none"; }
    
    laneWarn.style.display = (leftWhite > 50) ? "block" : "none";

    requestAnimationFrame(predict);
}

init();
</script>
"""

# Render the component
components.html(JS_CODE, height=500)

st.divider()
st.info("**Research Mode:** Logs are captured in real-time. Pedestrian detection uses the COCO-SSD MobileNetV2 architecture for low-latency inference.")
