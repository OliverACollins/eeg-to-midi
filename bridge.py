# firstly, run OpenMuse in terminal

import numpy as np
from mne_lsl import StreamInlet, resolve_stream
import mido
import time
from scipy.signal import welch

# --- Connect to the OpenMuse LSL EEG stream ---
print("Looking for Muse EEG stream...")
streams = resolve_stream('type', 'EEG')
inlet = StreamInlet(streams[0])
print("Connected to EEG stream")

# --- Open MIDI output ---
midi_out = mido.open_output('MuseEEG')  # must match your loopMIDI port name

# --- Helper: compute alpha power (8–12 Hz) ---
def band_power(data, fs, band):
    freqs, psd = welch(data, fs=fs, nperseg=fs)
    idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.mean(psd[idx])

fs = 256  # Muse S sampling rate
buffer = []

while True:
    sample, timestamp = inlet.pull_sample()
    buffer.append(sample)
    # keep only the last second of data
    if len(buffer) > fs:
        buffer = buffer[-fs:]

        data = np.array(buffer)
        ch_mean = np.mean(data, axis=1)
        alpha = band_power(ch_mean, fs, (8, 12))
        beta = band_power(ch_mean, fs, (13, 30))

        # Map to MIDI 0-127
        alpha_val = int(np.clip(np.interp(alpha, [0, 50], [0, 127]), 0, 127))
        beta_val  = int(np.clip(np.interp(beta,  [0, 50], [0, 127]), 0, 127))

        # Send as two MIDI Control Changes (CC10 = alpha, CC11 = beta)
        midi_out.send(mido.Message('control_change', control=10, value=alpha_val))
        midi_out.send(mido.Message('control_change', control=11, value=beta_val))

        print(f"Alpha={alpha_val}  Beta={beta_val}")
    time.sleep(0.05)
