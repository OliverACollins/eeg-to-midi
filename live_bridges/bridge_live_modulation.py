# eeg_to_midi_cc1_parallel.py
"""
EEG -> MIDI bridge: MIDI CC1 changes in parallel with smoothed alpha power
Combines channels 0-3 alpha power, smooths it, and maps linearly to MIDI CC1
Dependencies: pylsl, mido, python-rtmidi, numpy, scipy, matplotlib
"""

import time
import numpy as np
from pylsl import StreamInlet, resolve_streams
import mido
from collections import deque
from scipy.signal import welch
import matplotlib.pyplot as plt

# ---- CONFIG ----
LOOPMIDI_PORT_NAME = "EEG_MIDI 1"
SAMPLE_WINDOW_SEC = 1.0
ALPHA_BAND = (8.0, 12.0)
CHANNELS_TO_COMBINE = [0, 1, 2, 3]
MIDI_CHANNEL = 0
MIDI_CC = 113
MIN_CC = 0
MAX_CC = 127
SEND_INTERVAL = 0.02
ALPHA_SMOOTH = 0.3       # smoothing for alpha power
ROLLING_NORM_SEC = 5.0   # running min/max for adaptive scaling
PLOT_LENGTH = 200
# ----------------

# ---- FIND EEG STREAM ----
streams = resolve_streams()
eeg_streams = [s for s in streams if s.type() == "EEG"]
if not eeg_streams:
    raise RuntimeError("No EEG streams found.")
eeg_info = eeg_streams[0]
print(f"Using EEG stream: {eeg_info.name()} with {eeg_info.channel_count()} channels.")

# ---- OPEN MIDI ----
midi_out = mido.open_output(LOOPMIDI_PORT_NAME)
print(f"Opened MIDI output: {LOOPMIDI_PORT_NAME}")

# ---- SETUP EEG INLET ----
inlet = StreamInlet(eeg_info, max_chunklen=1024)
sfreq = eeg_info.nominal_srate()
window_samples = int(SAMPLE_WINDOW_SEC * sfreq)
buffer = deque(maxlen=window_samples)

# Running history for adaptive min/max normalization
norm_window_samples = int(ROLLING_NORM_SEC * sfreq)
bp_history = deque(maxlen=norm_window_samples)

last_send_time = 0
smoothed_alpha = None

# ---- BANDPOWER FUNCTION ----
def bandpower(signal_window, sfreq, band):
    fmin, fmax = band
    if len(signal_window) < 4:
        return 0.0
    signal_window = signal_window - np.mean(signal_window)
    freqs, psd = welch(signal_window, fs=sfreq, nperseg=min(256, len(signal_window)))
    mask = (freqs >= fmin) & (freqs <= fmax)
    return np.trapz(psd[mask], freqs[mask]) if np.any(mask) else 0.0

# ---- LIVE PLOT SETUP ----
plt.ion()
fig, ax = plt.subplots()
line_power, = ax.plot([], [], label="Smoothed Alpha Power")
line_cc, = ax.plot([], [], label="MIDI CC1")
ax.set_ylim(0, 130)
ax.set_xlim(0, PLOT_LENGTH)
ax.set_xlabel("Samples")
ax.set_ylabel("Value")
ax.legend()
power_data = []
cc_data = []

print("Starting EEG -> MIDI CC1 in parallel with smoothed alpha power... (Ctrl-C to exit)")

try:
    while True:
        samples, ts = inlet.pull_chunk(timeout=1.0, max_samples=window_samples)
        if not samples:
            continue
        arr = np.array(samples)

        # Combine channels 0-3
        combined = np.mean(arr[:, CHANNELS_TO_COMBINE], axis=1)
        buffer.extend(combined.tolist())
        if len(buffer) < window_samples:
            continue

        # Compute alpha bandpower
        window = np.array(buffer)
        bp = bandpower(window, sfreq, ALPHA_BAND)

        # Smooth alpha power to reduce spikes
        if smoothed_alpha is None:
            smoothed_alpha = bp
        else:
            smoothed_alpha = ALPHA_SMOOTH * bp + (1 - ALPHA_SMOOTH) * smoothed_alpha

        # Update running history for adaptive scaling
        bp_history.append(smoothed_alpha)
        min_bp = min(bp_history)
        max_bp = max(bp_history)
        # Map smoothed alpha to 0-1
        norm = (smoothed_alpha - min_bp) / max(1e-12, max_bp - min_bp)
        norm = np.clip(norm, 0, 1)

        # Map normalized alpha directly to CC1 (parallel change)
        cc_value = int(MIN_CC + (MAX_CC - MIN_CC) * norm)

        # Send MIDI CC at controlled rate
        now = time.time()
        if now - last_send_time >= SEND_INTERVAL:
            midi_out.send(mido.Message('control_change', control=MIDI_CC, value=cc_value, channel=MIDI_CHANNEL))
            last_send_time = now

        # ---- UPDATE LIVE PLOT ----
        power_data.append(smoothed_alpha)
        cc_data.append(cc_value)
        if len(power_data) > PLOT_LENGTH:
            power_data = power_data[-PLOT_LENGTH:]
            cc_data = cc_data[-PLOT_LENGTH:]
        line_power.set_ydata(power_data)
        line_power.set_xdata(range(len(power_data)))
        line_cc.set_ydata(cc_data)
        line_cc.set_xdata(range(len(cc_data)))
        ax.set_xlim(0, max(PLOT_LENGTH, len(power_data)))
        ax.figure.canvas.draw()
        ax.figure.canvas.flush_events()

        time.sleep(0.005)

except KeyboardInterrupt:
    print("Interrupted, closing MIDI output...")
    midi_out.close()
    print("Exit cleanly.")
