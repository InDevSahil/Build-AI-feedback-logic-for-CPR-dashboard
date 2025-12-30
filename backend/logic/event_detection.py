import numpy as np
from scipy.signal import find_peaks

def analyze_compressions(signal, fs=250):
    """
    Detect compressions and calculate metrics: Rate, Depth, Recoil (simplified).
    
    Args:
        signal (np.array): Processed CPR signal (Force/Displacement).
        fs (int): Sampling rate.
        
    Returns:
        dict: Metrics including rate, average depth, and good/bad classifications.
    """
    # Adaptive threshold: 50% of the max signal amplitude in this window
    # or a minimum floor to avoid noise detection (e.g., 20 units)
    dynamic_threshold = max(0.4 * np.max(signal), 10.0) 
    
    # Min distance between peaks: 0.3s (implies max rate 200 cpm, filters high freq noise)
    min_dist = int(0.3 * fs)
    
    peaks, properties = find_peaks(signal, height=dynamic_threshold, distance=min_dist)
    
    if len(peaks) < 2:
        return {
            "rate_cpm": 0,
            "avg_depth": 0,
            "consistency_score": 0,
            "feedback": "No compressions detected"
        }

    # 1. Calculate Rate (Compressions Per Minute)
    # Intervals in seconds
    intervals = np.diff(peaks) / fs
    avg_interval = np.mean(intervals)
    rate_cpm = 60.0 / avg_interval if avg_interval > 0 else 0
    
    # 2. Calculate Depth (Amplitude of peaks)
    # Assuming the signal is Displacement (mm) or Force that proxies depth
    # If signal is Force, we'd need a stiffness constant (Hooke's law: F=kx).
    # For this demo, let's assume the input signal is calibrated to ~ Depth units (mm).
    depths = signal[peaks]
    avg_depth = np.mean(depths)
    
    # 3. Assessment Logic
    # Guidelines: Rate 100-120 cpm, Depth 50-60 mm (adult)
    rate_status = "Good"
    if rate_cpm < 100: rate_status = "Too Slow"
    elif rate_cpm > 120: rate_status = "Too Fast"
    
    depth_status = "Good"
    # depth thresholds in mm
    if avg_depth < 50: depth_status = "Push Harder"
    elif avg_depth > 60: depth_status = "Push Softer"
    
    return {
        "rate_cpm": round(rate_cpm, 1),
        "avg_depth": round(avg_depth, 1),
        "rate_status": rate_status,
        "depth_status": depth_status,
        "peak_indices": peaks.tolist()
    }
