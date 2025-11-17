# --- CHECKING PORTS ---
import mido
print("Available MIDI output ports:")
print(mido.get_output_names())

# --- DEPENDENCIES ---
import pandas as pd
import numpy as np
import time
from scipy.signal import welch

# --- SETTINGS ---
CSV_FILE = "cleaned_eeg.csv"
CHANNEL = "AF7"           # EEG electrode channel
FS = 256                  # Muse sample rate (Hz)
WINDOW_SEC = 0.25         # sliding window in seconds
MIDI_PORT = "EEG_MIDI 2"  # virtual port name (loopMIDI)

# MIDI settings
NOTE_RANGE_LOW = 48       # C3
NOTE_RANGE_HIGH = 72      # C5
VELOCITY_MIN = 20
VELOCITY_MAX = 80

# EEG bands and corresponding MIDI CCs or note channels
EEG_BANDS = {
    'delta': (0.5, 4),
    'theta': (4, 8),
    'alpha': (8, 12),
    'beta':  (12, 30),
    'gamma': (30, 45)
}

# --- FUNCTION: compute bandpower ---
def bandpower(data, fs, band):
    freqs, psd = welch(data, fs=fs, nperseg=len(data))
    idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.mean(psd[idx])

# --- LOAD EEG CSV ---
eeg = pd.read_csv(CSV_FILE)
if "Time" in eeg.columns:
    eeg = eeg.drop(columns=["Time"])

signal = eeg[CHANNEL].values
print(f"Loaded {len(signal)} samples from {CHANNEL}")

# --- OPEN MIDI PORT ---
import mido
try:
    outport = mido.open_output(MIDI_PORT)
    print(f"✅ Connected to MIDI port: {MIDI_PORT}")
except IOError:
    ports = mido.get_output_names()
    if ports:
        outport = mido.open_output(ports[0])
        print(f"⚠️ Using fallback MIDI port: {ports[0]}")
    else:
        raise RuntimeError("No MIDI output ports available!")

# --- STREAM EEG TO MULTI-BAND MIDI ---
window_size = int(FS * WINDOW_SEC)
start_time = time.time()

for i in range(0, len(signal) - window_size, window_size):
    chunk = signal[i:i + window_size]

    for j, (band_name, band_range) in enumerate(EEG_BANDS.items()):
        power = bandpower(chunk, FS, band_range)

        # Map power to MIDI note
        midi_value = int(np.clip(np.interp(power, [0, 100], [0, 127]), 0, 127))
        note_val = NOTE_RANGE_LOW + (midi_value * (NOTE_RANGE_HIGH - NOTE_RANGE_LOW) // 127)
        velocity = int(np.clip(midi_value, VELOCITY_MIN, VELOCITY_MAX))

        # Option: offset each band slightly so multiple bands play different notes
        note_val_band = note_val + j * 2  # small offset per band

        # Send note
        outport.send(mido.Message('note_on', note=note_val_band, velocity=velocity))
        time.sleep(WINDOW_SEC / 2)
        outport.send(mido.Message('note_off', note=note_val_band, velocity=velocity))

        print(f"t={i/FS:.2f}s | {band_name.capitalize()}={power:.2f} | Note={note_val_band} | Vel={velocity}")

    # Keep timing aligned with EEG
    elapsed = time.time() - start_time
    target_time = (i + window_size) / FS
    time.sleep(max(0, target_time - elapsed))
