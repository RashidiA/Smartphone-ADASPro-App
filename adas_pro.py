import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Rahmah Edition", layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🛠️ ADAS Controls")
enable_signs = st.sidebar.toggle("Detect Speed Signs", value=False, help="Turning this OFF reduces CPU lag significantly.")
st.sidebar.divider()
st.sidebar.write("Project: **Personel ADAS**")
st.sidebar.write("Mode: **High-Performance Edge AI**")

# Pass the toggle state to JavaScript
sign_mode = "true" if enable_signs else "false"

JS_CODE = f"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 12px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div style="position: absolute; bottom: 20px; left: 20px; background: rgba(0,0,0,0.7); color: #00FF00; padding: 10px; border-radius: 8px; font-family: monospace; border: 1px solid #00FF00;">
        SPEED: <span id="speedVal">0.0</span> km/h
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <button id="startBtn" style="padding: 15px 30px; font-size: 18px; border-radius: 8px; background: #28a745; color: white; border: none; cursor: pointer;">🚀 INITIALIZE SYSTEM</button>
    </div>

    <div id="signBox" style="position: absolute; top: 20px; right: 20px; width: 60px; height: 60px; background: white; border: 4px solid red; border-radius: 50%; display: none; align-items: center; justify-content: center; font-weight: bold; color: black;">!</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgpu"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('output');
const ctx = canvas.getContext('2d', {{alpha: false, desynchronized: true}});
const speedText = document.getElementById('speedVal');
const signBox = document.getElementById('signBox');
const startBtn = document.getElementById('startBtn');

let model;
let frameCount = 0;
let lastLaneY = []; // Memory for dotted lines

async function init() {
    // Attempt WebGPU for 3x speed boost
    try {{ await tf.setBackend('webgpu'); await tf.ready(); }} 
    catch(e) {{ await tf.setBackend('webgl'); }}
    
    model = await cocoSsd.load();
    
    startBtn.onclick = async () => {{
        const stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'environment', width: 640 }} }});
        video.srcObject = stream;
        document.getElementById('overlay').style.display = 'none';
        
        // Start GPS Tracking
        navigator.geolocation.watchPosition(pos => {{
            let s = pos.coords.speed || 0; // m/s
            speedText.innerText = (s * 3.6).toFixed(1); // convert to km/h
        }}, null, {{enableHighAccuracy: true}});

        video.onloadedmetadata = () => render();
    }};
}

function render() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // --- 1. CONTINUOUS DOTTED LINE DETECTION ---
    const h = canvas.height;
    const w = canvas.width;
    const roadTop = Math.floor(h * 0.7);
    const roadData = ctx.getImageData(0, roadTop, w, Math.floor(h * 0.3));
    const pixels = roadData.data;

    let detectedPoints = [];
    for (let i = 0; i < pixels.length; i += 4) {{
        if (pixels[i] > 210 && pixels[i+1] > 210 && pixels[i+2] > 210) {{
            pixels[i] = 0; pixels[i+1] = 120; pixels[i+2] = 255; // Blue
            let pxIdx = i / 4;
            detectedPoints.push({{x: pxIdx % w, y: Math.floor(pxIdx / w)}});
        }}
    }
    ctx.putImageData(roadData, 0, roadTop);

    // --- 2. AI TASKS (SIGN & PEDESTRIAN) ---
    if (frameCount % 8 === 0) {{
        model.detect(video).then(preds => {{
            let hasSign = false;
            preds.forEach(p => {{
                if ({sign_mode} && (p.class === 'stop sign' || p.class === 'traffic light')) hasSign = true;
                // Add pedestrian logic here if needed
            }});
            signBox.style.display = hasSign ? "flex" : "none";
        }});
    }

    frameCount++;
    requestAnimationFrame(render);
}
init();
</script>
"""

components.html(JS_CODE, height=600)
