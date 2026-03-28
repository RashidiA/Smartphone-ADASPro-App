🚗 ADAS Pro: Smartphone-Based AI Driving Assistant

Project Overview

ADAS Pro is a high-performance, edge-computing application designed to turn a standard smartphone into an Advanced Driver Assistance System (ADAS). By leveraging Computer Vision (CV) and Machine Learning (ML), the system provides real-time safety alerts to prevent accidents.

Key Features  
•	🛣️ Lane Departure Warning (LDW): Uses Canny Edge detection and intensity analysis to monitor white road markings and alert the driver of drifting.  
•	🚶 Pedestrian Collision Warning (PCW): Employs a TensorFlow.js COCO-SSD model to detect pedestrians in the vehicle's "Collision Zone."  
•	🛑 Speed Sign Recognition: Real-time identification of traffic and speed signs using localized object detection.  
•	🔊 Multi-Modal Alerts: Visual AR overlays combined with low-latency audio "beeps" for immediate driver feedback.  
________________________________________

Technical Architecture

To achieve "Java-level" performance on a mobile device without excessive battery drain, this project utilizes a Hybrid Edge Computing model:  
1.	Frontend (JavaScript/WebAssembly): * The heavy image processing (OpenCV.js) and AI inference (TF.js) run directly on the client's handphone GPU/CPU.  
o	This eliminates the latency of sending video frames to a server, ensuring <100ms response times.  
2.	Backend (Python/Streamlit): * Acts as the lightweight orchestration layer.  
o	Manages the UI, session states, and log reporting.  
3.	Optimization: Uses requestAnimationFrame to synchronize the AI clock with the mobile screen's refresh rate, preventing memory overflows.  
________________________________________

Installation & Deployment  
1. Clone the Repository  
Bash  
git clone https://github.com/yourusername/adas-pro.git  
cd adas-pro  
2. Install Dependencies  
Bash  
pip install -r requirements.txt  
3. Run the Application  
Bash  
streamlit run adas_pro.py  
________________________________________

Hardware Requirements  
•	Device: Android (Chrome) or iOS (Safari).  
•	Mounting: Stable dashboard mount (center-aligned).  
•	Connectivity: HTTPS is mandatory for camera access.  

