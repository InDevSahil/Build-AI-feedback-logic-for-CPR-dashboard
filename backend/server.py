import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np

from backend.logic.simulator import CPRSimulator
from backend.logic.signal_processing import preprocess_cpr_signal
from backend.logic.event_detection import analyze_compressions
from backend.logic.rosc_prediction import ROSCPredictor
from backend.logic.gemini_assistant import GeminiAssistant
from backend.logic.vision_processor import VisionProcessor

app = FastAPI(title="CPR AI Dashboard API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Logic Modules
simulator = CPRSimulator(sample_rate=250)
rosc_model = ROSCPredictor()
gemini_ai = GeminiAssistant()
vision_proc = VisionProcessor()

# Buffer for real-time analysis
# We need a rolling buffer to run detection on (e.g. last 3 seconds)
BUFFER_SIZE = 250 * 5 # 5 seconds
data_buffer = []

@app.get("/")
def read_root():
    return {"message": "CPR AI Backend is running"}

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to stream")
    
    # Internal buffer for this connection
    conn_buffer = []
    
    try:
        # Use the simulator's generator
        chunk_gen = simulator.stream_generator(chunk_size=0.1) # 100ms chunks
        
        for raw_chunk in chunk_gen:
            # 1. Update Buffer
            conn_buffer.extend(raw_chunk)
            if len(conn_buffer) > BUFFER_SIZE:
                conn_buffer = conn_buffer[-BUFFER_SIZE:]
            
            # 2. Process Buffer (if we have enough data)
            metrics = {}
            prediction = 0.0
            
            if len(conn_buffer) >= 250 * 2: # At least 2 seconds for detection
                signal_np = np.array(conn_buffer)
                
                # Signal Processing
                clean_signal = preprocess_cpr_signal(signal_np)
                
                # Event Detection
                metrics = analyze_compressions(clean_signal)
                
                # ROSC Prediction
                if metrics["rate_cpm"] > 0:
                    prediction = rosc_model.predict_probability(
                        metrics["rate_cpm"], 
                        metrics["avg_depth"]
                    )
            
            # 3. Send Data to Client
            # Send the raw chunk for visualization + latest metrics
            packet = {
                "waveform": raw_chunk, # Send raw for real-time viz (or clean if preferred)
                "metrics": metrics,
                "rosc_prediction": round(prediction * 100, 1) # percent
            }
            
            await websocket.send_text(json.dumps(packet))
            
            # Helper to allow asyncio loop to breathe (though simulator has sleep inside generator? 
            # Actually generator is synchronous regular iterator in my impl, so we need to be careful.
            # Let's fix the simulator interaction loop below.)
            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"Connection closed: {e}")
        await websocket.close()

# Note: The simulator.stream_generator above is a synchronous generator yielding time.sleep.
# This blocks the async event loop. We should refactor the loop to be async-friendly.
# Rewriting the loop logic inside the endpoint for better async control.

@app.websocket("/ws/simulation")
async def websocket_simulation(websocket: WebSocket):
    await websocket.accept()
    
    # Reset buffer
    conn_buffer = []
    
    try:
        while True:
            # 1. Generate Data (Non-blocking)
            # We determine pattern randomly similar to before
            # For demo, just cycle patterns
            t = int(time.time() // 5) % 4
            pattern = ["normal", "fast", "slow", "shallow"][t]
            
            # Generate 100ms of data
            chunk_size = 0.1
            raw_chunk = simulator.generate_wave(duration_sec=chunk_size, pattern=pattern).tolist()
            
            # 2. Update Rolling Buffer
            conn_buffer.extend(raw_chunk)
            if len(conn_buffer) > BUFFER_SIZE:
                conn_buffer = conn_buffer[-BUFFER_SIZE:]
                
            # 3. Analyze (only every 500ms to save CPU, but send waveform every 100ms)
            # Actually, let's just analyze every frame for simplicity for now, it's fast enough.
            metrics = {}
            prediction = 0.0
            
            if len(conn_buffer) >= 250 * 2:
                signal_np = np.array(conn_buffer)
                clean_signal = preprocess_cpr_signal(signal_np)
                metrics = analyze_compressions(clean_signal)
                
                if metrics["rate_cpm"] > 0:
                     prediction = rosc_model.predict_probability(metrics["rate_cpm"], metrics["avg_depth"])

            # 4. Trigger AI & Vision (Throttle to every 3 seconds)
            ai_message = ""
            current_time = time.time()
            if metrics.get("rate_cpm", 0) > 0 and (current_time - gemini_ai.last_advice_time > 3.0):
                 # Run in background ideally, but await here for demo simplicity
                 ai_message = await gemini_ai.get_feedback(
                     metrics["rate_cpm"], 
                     metrics["avg_depth"], 
                     prediction * 100, 
                     metrics.get("rate_status", "Unknown")
                 )
                 gemini_ai.last_advice_time = current_time

            # Vision Mock
            vision_data = vision_proc.process_frame(None)

            packet = {
                "waveform": raw_chunk, 
                "metrics": metrics,
                "rosc_prediction": round(prediction * 100, 1),
                "ai_feedback": ai_message,
                "vision": vision_data
            }
            
            await websocket.send_text(json.dumps(packet))
            await asyncio.sleep(chunk_size) # Wait for the duration of the chunk

    except Exception as e:
        print(f"Error: {e}")
