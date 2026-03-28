import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro Full Suite", layout="centered")

st.title("🚗 ADAS Pro: Rahmah Edition")
st.markdown("Tracking: **White Lines**, **Pedestrians**, and **Road Signs**.")

JS_CODE = """
<div style="position: relative; width: 100%; border-radius: 15px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <button id="startBtn" style="padding: 15px 30px; font-size: 20px; border-radius: 10px; border: none; background: #00FF00; color: black; font-weight: bold;">START SYSTEM</button>
        <p id="status" style="color: white; margin-top: 10px;">Loading Vision Engines...</p>
    </div>

    <div id="pede_warning" style="position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); padding: 20px; background: rgba(255,0,0,0.9); color: white; font-weight: bold; font-size: 24px; border-radius: 10px; display: none; width: 80%; text-align: center; border: 4px solid white;">🛑 BRAKE: OBJECT DETECTED</div>
    <div id="sign_indicator" style="position: absolute; top: 20px; right: 20px; width: 70px; height: 70px; background: white; border: 5px solid red; border-radius: 50%; display: none; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; color: black; text-align: center;">SIGN</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {alpha: false});
const status = document.getElementById('status');
const startBtn = document.getElementById('startBtn');
const overlay = document.getElementById('overlay');
const pedeWarn = document.getElementById('pede_warning');
const signInd = document.getElementById('sign_indicator');

let model;
let frameCount = 0;

async function init() {
    model = await cocoSsd.load();
    status.innerText = "All Models Loaded. Ready.";
    
    startBtn.onclick = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment', width: { ideal: 640 } } 
        });
        video.srcObject = stream;
        overlay.style.display = "none";
        video.onloadedmetadata = () => { render(); };
    };
}

function render() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // --- 1. WHITE LINE TRACKER (RUNS EVERY FRAME) ---
    const roadTop = Math.floor(canvas.height * 0.65);
    const roadHeight = Math.floor(canvas.height * 0.35);
    const imageData = ctx.getImageData(0, roadTop, canvas.width, roadHeight);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
        // High RGB values = White
        if (data[i] > 215 && data[i+1] > 215 && data[i+2] > 215) { 
            data[i] = 0; data[i+1] = 100; data[i+2] = 255; // Blue Marker
        }
    }
    ctx.putImageData(imageData, 0, roadTop);

    // --- 2. AI OBJECTS & SIGNS (RUNS EVERY 7TH FRAME FOR SMOOTHNESS) ---
    if (frameCount % 7 === 0) {
        model.detect(video).then(preds => {
            let personDanger = false;
            let signFound = false;
            let signLabel = "";

            preds.forEach(p => {
                // Check for Pedestrians
                if (p.class === 'person' && p.score > 0.5) {
                    const centerX = p.bbox[0] + (p.bbox[2]/2);
                    if (centerX > canvas.width * 0.25 && centerX < canvas.width * 0.75) personDanger = true;
                }
                // Check for Traffic Signs
                if (['stop sign', 'traffic light'].includes(p.class) && p.score > 0.4) {
                    signFound = true;
                    signLabel = p.class.toUpperCase();
                }
            });

            pedeWarn.style.display = personDanger ? "block" : "none";
            if (signFound) {
                signInd.style.display = "flex";
                signInd.innerText = signLabel;
            } else {
                signInd.style.display = "none";
            }
        });
    }

    frameCount++;
    requestAnimationFrame(render);
}
init();
</script>
"""

components.html(JS_CODE, height=550)

st.divider()
st.sidebar.header("PhD Project Controls")
st.sidebar.write("System: **Mobile Edge AI**")
st.sidebar.write("Architecture: **Hybrid WASM/Python**")
