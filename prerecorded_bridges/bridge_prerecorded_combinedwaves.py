import mido
import pandas as pd
import numpy as np
import time

# --- SETTINGS ---
CSV_FILE = "cleaned_eeg.csv"
CHANNELS = ["AF7", "AF8", "TP9", "TP10"]
FS = 256
WINDOW_SEC_BASE = 1.0      # base window (seconds)
MIDI_PORT = "EEG_MIDI 2"

NOTE_RANGE_LOW = 48        # C3
NOTE_RANGE_HIGH = 84       # C6 — wider range for intensity
VELOCITY_MIN = 40
VELOCITY_MAX = 100
SENSITIVITY = 5.0          # larger = more reactive to small EEG changes
TEMPO_SCALE = 0.6          # how strongly brain power affects tempo

# --- LOAD EEG ---
eeg = pd.read_csv(CSV_FILE)
if "Time" in eeg.columns:
    eeg = eeg.drop(columns=["Time"])

missing = [ch for ch in CHANNELS if ch not in eeg.columns]
if missing:
    raise ValueError(f"Missing channels in CSV: {missing}")

print(f"Loaded EEG with {len(eeg)} samples and channels: {', '.join(CHANNELS)}")

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

# --- BASELINE STATS ---
window_size = int(FS * WINDOW_SEC_BASE)
combined_powers = []
for i in range(0, len(eeg) - window_size, window_size):
    segment = eeg.iloc[i:i + window_size][CHANNELS].values
    combined_powers.append(np.mean(segment ** 2))
mean_power = np.mean(combined_powers)
std_power = np.std(combined_powers)
if std_power < 1e-12:
    std_power = 1e-12
print(f"Baseline: mean={mean_power:.6e}, std={std_power:.6e}")

# --- MAIN LOOP ---
start_time = time.time()
for i in range(0, len(eeg) - window_size, window_size):
    chunk = eeg.iloc[i:i + window_size][CHANNELS].values
    power = np.mean(chunk ** 2)

    # Normalize power
    z = (power - mean_power) / std_power
    scaled = np.clip((z * SENSITIVITY + 5), 0, 10)

    # Map to MIDI parameters
    midi_value = int(np.clip(np.interp(scaled, [0, 10], [0, 127]), 0, 127))
    note_val = NOTE_RANGE_LOW + (midi_value * (NOTE_RANGE_HIGH - NOTE_RANGE_LOW) // 127)
    velocity = int(np.clip(np.interp(midi_value, [0, 127],
                                     [VELOCITY_MIN, VELOCITY_MAX]),
                           VELOCITY_MIN, VELOCITY_MAX))

    # Tempo modulation — faster when more intense
    window_dynamic = WINDOW_SEC_BASE * np.clip(1.0 - (TEMPO_SCALE * (scaled / 10.0)), 0.3, 1.0)
    duration = window_dynamic / 2

    # Send MIDI note
    outport.send(mido.Message('note_on', note=note_val, velocity=velocity))
    time.sleep(duration)
    outport.send(mido.Message('note_off', note=note_val, velocity=velocity))

    # Align with EEG timing
    elapsed = time.time() - start_time
    target_time = (i + window_size) / FS
    time.sleep(max(0, target_time - elapsed))

    print(f"t={i/FS:.2f}s | Power={power:.6e} | z={z:.2f} | "
          f"Note={note_val} | Vel={velocity} | Window={window_dynamic:.2f}s")
