import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="ADAS Pro: Rahmah Version", layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🛠️ ADAS Controls")
enable_signs = st.sidebar.toggle("Detect Speed Signs", value=False)
st.sidebar.divider()
st.sidebar.info("Priority: High Performance / Low Lag")

# Pass the toggle state to JavaScript
sign_mode = "true" if enable_signs else "false"

JS_CODE = f"""
<div style="position: relative; width: 100%; max-width: 640px; margin: auto; border-radius: 12px; overflow: hidden; background: #000;">
    <video id="video" autoplay playsinline style="width: 100%; height: auto; display: block;"></video>
    <canvas id="output" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    
    <div style="position: absolute; bottom: 20px; left: 20px; background: rgba(0,0,0,0.7); color: #00FF00; padding: 10px; border-radius: 8px; font-family: monospace; border: 1px solid #00FF00; font-size: 18px;">
        SPEED: <span id="speedVal">0.0</span> km/h
    </div>

    <div id="overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 100;">
        <button id="startBtn" style="padding: 15px 30px; font-size: 18px; border-radius: 8px; background: #28a745; color: white; border: none; cursor: pointer;">🚀 START SYSTEM</button>
    </div>

    <div id="signBox" style="position: absolute; top: 20px; right: 20px; width: 80px; height: 80px; background: white; border: 6px solid red; border-radius: 50%; display: none; align-items: center; justify-content: center; font-weight: bold; color: black; font-size: 12px; text-align: center;">SIGN</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
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
let lastLines = null; // Buffer for continuous dotted lines

async function init() {{
    model = await cocoSsd.load();
    
    startBtn.onclick = async () => {{
        const stream = await navigator.mediaDevices.getUserMedia({{ 
            video: {{ facingMode: 'environment', width: 640 }} 
        }});
        video.srcObject = stream;
        document.getElementById('overlay').style.display = 'none';
        
        // GPS Speedometer
        navigator.geolocation.watchPosition(pos => {{
            let s = pos.coords.speed || 0;
            speedText.innerText = (s * 3.6).toFixed(1);
        }}, null, {{enableHighAccuracy: true}});

        video.onloadedmetadata = () => render();
    }};
}}

function render() {{
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // 1. WHITE LINE DETECTION (Continuous Dotted Logic)
    const roadTop = Math.floor(canvas.height * 0.7);
    const roadData = ctx.getImageData(0, roadTop, canvas.width, Math.floor(canvas.height * 0.3));
    const pixels = roadData.data;
    let foundThisFrame = false;

    for (let i = 0; i < pixels.length; i += 4) {{
        if (pixels[i] > 205 && pixels[i+1] > 205 && pixels[i+2] > 205) {{
            pixels[i] = 0; pixels[i+1] = 120; pixels[i+2] = 255; 
            foundThisFrame = true;
        }} else if (lastLines && lastLines[i+2] === 255) {{
            // Persistence: If gap (dotted), use buffer from last frame
            pixels[i] = 0; pixels[i+1] = 80; pixels[i+2] = 200; 
        }}
    }}
    
    if (foundThisFrame) lastLines = new Uint8ClampedArray(pixels);
    ctx.putImageData(roadData, 0, roadTop);

    // 2. AI TASKS (Every 10th frame for ULTRA LOW LAG)
    if (frameCount % 10 === 0) {{
        model.detect(video).then(preds => {{
            let hasSign = false;
            preds.forEach(p => {{
                if ({sign_mode} && (p.class === 'stop sign' || p.class === 'traffic light')) {{
                    hasSign = true;
                    signBox.innerText = p.class.toUpperCase();
                }}
            }});
            signBox.style.display = hasSign ? "flex" : "none";
        }});
    }}

    frameCount++;
    requestAnimationFrame(render);
}}
init();
</script>
"""

components.html(JS_CODE, height=600)
