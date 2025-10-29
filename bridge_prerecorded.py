# --- CHECKING PORTS ---
import mido
print("Available MIDI output ports:")
print(mido.get_output_names())

# --- DEPENDENCIES ---
import pandas as pd
import numpy as np
import time
import mido
from scipy.signal import welch

# --- SETTINGS ---
CSV_FILE = "cleaned_eeg.csv"
CHANNEL = "AF8"           # EEG electrode channel
FS = 256                  # Muse sample rate (Hz)
WINDOW_SEC = 1          # sliding window in seconds (smaller = more notes)
MIDI_PORT = "EEG_MIDI 2"    # virtual port name (through loopMIDI)

NOTE_RANGE_LOW = 48       # C3
NOTE_RANGE_HIGH = 72      # C5
VELOCITY_MIN = 40
VELOCITY_MAX = 80

# --- FUNCTION: compute EEG bandpower ---
def bandpower(data, fs, band=(8, 12)):
    freqs, psd = welch(data, fs=fs, nperseg=len(data))
    idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.mean(psd[idx])

# --- LOAD EEG .csv ---
eeg = pd.read_csv(CSV_FILE)
if "Time" in eeg.columns:
    eeg = eeg.drop(columns=["Time"])

signal = eeg[CHANNEL].values
print(f"Loaded {len(signal)} samples from {CHANNEL}")

# --- OPEN MIDI PORT ---
print("Available MIDI outputs:", mido.get_output_names())
try:
    outport = mido.open_output(MIDI_PORT)
    print(f"✅ Connected to MIDI port: {MIDI_PORT}")
except IOError:
    ports = mido.get_output_names()
    if ports:
        outport = mido.open_output(ports[0])
        print(f"⚠️ Using fallback MIDI port: {ports[0]}")
    else:
        raise RuntimeError("No MIDI output ports available! Create one via loopMIDI or IAC.")

# --- STREAM EEG TO MIDI NOTES ---
window_size = int(FS * WINDOW_SEC)
start_time = time.time()

for i in range(0, len(signal) - window_size, window_size):
    chunk = signal[i:i + window_size]
    alpha = bandpower(chunk, FS, band=(8,12))

    # Map alpha power to MIDI note
    midi_value = int(np.clip(np.interp(alpha, [0, 100], [0, 127]), 0, 127))
    note_val = NOTE_RANGE_LOW + (midi_value * (NOTE_RANGE_HIGH - NOTE_RANGE_LOW) // 127) # dynamic with EEG intensity
    velocity = int(np.clip(midi_value, VELOCITY_MIN, VELOCITY_MAX)) # dynamic with EEG intensity

    # Send note_on and note_off quickly
    outport.send(mido.Message('note_on', note=note_val, velocity=velocity))
    time.sleep(WINDOW_SEC / 2)  # short note duration - allows overlapping notes
    outport.send(mido.Message('note_off', note=note_val, velocity=velocity))

    # Keep timing aligned with EEG
    elapsed = time.time() - start_time
    target_time = (i + window_size) / FS
    time.sleep(max(0, target_time - elapsed))

    print(f"t={i/FS:.2f}s | Alpha={alpha:.2f} | Note={note_val} | Vel={velocity}")
