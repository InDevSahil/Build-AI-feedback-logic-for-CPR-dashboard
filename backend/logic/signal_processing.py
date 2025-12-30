import numpy as np
from scipy.signal import butter, filtfilt

def butter_bandpass(lowcut, highcut, fs, order=4):
    """
    Design a Butterworth bandpass filter.
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def preprocess_cpr_signal(signal, fs=250):
    """
    Apply bandpass filtering and baseline correction to the raw CPR signal.
    
    Args:
        signal (np.array): Raw sensor data (Force or Acceleration).
        fs (int): Sampling rate in Hz.
        
    Returns:
        np.array: Cleaned signal.
    """
    # 1. Bandpass filter 0.5-15 Hz (focus on compression frequencies)
    lowcut = 0.5
    highcut = 15.0
    
    # Check if signal is long enough for filtering
    if len(signal) < 3 * 4: # generic rule of thumb for filtfilt order
         # Return raw or handle gracefully if too short
         return signal - np.mean(signal)

    b, a = butter_bandpass(lowcut, highcut, fs, order=4)
    filtered = filtfilt(b, a, signal)

    # 2. Baseline Correction (remove drift)
    # Simple subtraction of the mean of the initial segment or moving average
    # For this implementation, we use a simple mean subtraction of the window
    baseline = np.mean(filtered) 
    corrected = filtered - baseline
    
    return corrected
