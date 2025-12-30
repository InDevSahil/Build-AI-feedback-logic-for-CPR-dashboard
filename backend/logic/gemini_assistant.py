import google.generativeai as genai
import os
import asyncio

# Hardcoding key for this session as provided by user
# In production, this should be an env var
API_KEY = "AIzaSyCn3BNVcGF-vqLP3V0xwg92AILbn09XYw4"

class GeminiAssistant:
    def __init__(self):
        try:
            genai.configure(api_key=API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.chat = self.model.start_chat()
            self.last_advice_time = 0
            print("Gemini Assistant Initialized")
        except Exception as e:
            print(f"Failed to init Gemini: {e}")
            self.model = None

    async def get_feedback(self, rate, depth, rosc_prob, status):
        """
        Get concise feedback from Gemini based on current metrics.
        """
        if not self.model:
            return "AI Offline"

        prompt = f"""
        You are a critical care assistant monitoring CPR in real-time.
        Current Vitals:
        - Compression Rate: {rate} cpm (Target: 100-120)
        - Depth: {depth} mm (Target: 50-60)
        - ROSC Probability: {rosc_prob:.1f}%
        - Status: {status}

        Give ONE short, urgent command (max 10 words) to the rescuer to improve survival. 
        If everything is perfect, offer encouragement. 
        Focus on mechanics (lean, recoil, speed).
        """
        
        try:
            # Run in executor to avoid blocking async loop since the lib is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "Connection Error"
