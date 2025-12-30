import numpy as np
import time

class CPRSimulator:
    def __init__(self, sample_rate=250):
        self.fs = sample_rate
        self.t = 0
        
    def generate_wave(self, duration_sec=1.0, pattern="normal"):
        """
        Generate a chunk of CPR waveform data.
        
        Patterns:
        - 'normal': ~110 cpm, ~55mm depth
        - 'fast': ~140 cpm
        - 'slow': ~80 cpm
        - 'shallow': ~110 cpm, ~30mm depth
        - 'idle': logic noise, no compressions
        """
        timestamps = np.linspace(self.t, self.t + duration_sec, int(duration_sec * self.fs), endpoint=False)
        self.t += duration_sec
        
        # Base parameters
        if pattern == "normal":
            freq = 110 / 60.0 # ~1.83 Hz
            amp = 55.0
        elif pattern == "fast":
            freq = 140 / 60.0
            amp = 50.0
        elif pattern == "slow":
            freq = 80 / 60.0
            amp = 55.0
        elif pattern == "shallow":
            freq = 110 / 60.0
            amp = 30.0
        elif pattern == "idle":
            freq = 0
            amp = 0
        else:
            freq = 110/60.0
            amp = 55.0

        # Generate Waveform (Sine wave approximation for simplicity, or slightly sharper for realism)
        # Real CPR is more like a half-sine or triangular pulse, but sine is okay for basic testing.
        if freq > 0:
            # Add some harmonics for "sharp" compression look
            wave = amp * 0.5 * (1 - np.cos(2 * np.pi * freq * timestamps)) 
            # 1 - cos starts at 0, goes to 2, so * 0.5 makes it 0 to 1. * amp makes it 0 to amp.
        else:
            wave = np.zeros_like(timestamps)

        # Add Noise
        noise = np.random.normal(0, 1.5, size=len(timestamps)) # 1.5mm noise
        
        return wave + noise

    def stream_generator(self, chunk_size=0.1):
        """
        Yields small chunks of data to simulate real-time streaming.
        """
        while True:
            # Randomly switch patterns for demo purposes
            r = np.random.rand()
            if r < 0.1: pattern = "idle"
            elif r < 0.2: pattern = "fast"
            elif r < 0.3: pattern = "slow"
            elif r < 0.4: pattern = "shallow"
            else: pattern = "normal"
            
            # Generate a 2-second block of this pattern
            data_block = self.generate_wave(duration_sec=2.0, pattern=pattern)
            
            # Yield in smaller chunks
            samples_per_chunk = int(chunk_size * self.fs)
            for i in range(0, len(data_block), samples_per_chunk):
                yield data_block[i:i+samples_per_chunk].tolist()
                time.sleep(chunk_size) # Real-time simulation
