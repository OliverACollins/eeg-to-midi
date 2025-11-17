# eeg_to_midi.py
"""
EEG -> MIDI bridge (LSL -> loopMIDI)
Dependencies: pylsl, mido, python-rtmidi, numpy, scipy (optional but recommended)
pip install pylsl mido python-rtmidi numpy scipy
"""

import time
import numpy as np
from pylsl import StreamInlet, resolve_byprop
import mido
from collections import deque

# Optional: from scipy.signal import welch, butter, filtfilt
from scipy.signal import welch

# ---- CHECKING AVAILABLE PORTS ----

import mido

print("MIDI Input Ports:")
for name in mido.get_input_names():
    print("  ", name)

print("\nMIDI Output Ports:")
for name in mido.get_output_names():
    print("  ", name)

# ---- LSL streams ----
from pylsl import resolve_streams

print("Scanning for all LSL streams...")
streams = resolve_streams()
for s in streams:
    print(f"Name: {s.name()}  |  Type: {s.type()}  |  Channels: {s.channel_count()}")






# ---- USER CONFIG ----
LSL_STREAM_TYPE = "EEG"          # change if your stream has a different type/name
LOOPMIDI_PORT_NAME = "EEG_MIDI 1"   # name of the loopMIDI output port you created
SAMPLE_WINDOW_SEC = 1.0          # time window for feature computation (seconds)
BAND = (8.0, 12.0)               # frequency band to use (alpha = 8-12 Hz)
MIDI_BASE_NOTE = 60              # MIDI note for channel 0, channel i -> note = base + i
MIDI_CHANNEL = 0                 # 0-15
POWER_TO_VEL_EXP = 1.0           # exponent to shape mapping curve (1 = linear)
ON_THRESHOLD = 0.4               # normalized threshold to send Note On
OFF_THRESHOLD = 0.30             # hysteresis lower threshold for Note Off
MIN_VEL = 10
MAX_VEL = 127
MAX_NOTES_PER_CHANNEL = 1        # how many simultaneous notes per EEG channel
SILENCE_AFTER = 1.0              # seconds of inactivity to auto-send NoteOff (safety)
# ----------------------

def find_lsl_stream():
    print("Resolving LSL streams...")
    streams = resolve_byprop('type', LSL_STREAM_TYPE, timeout=5)
    if not streams:
        print(f"No LSL stream with type '{LSL_STREAM_TYPE}' found. Trying any EEG stream name...")
        streams = resolve_byprop('name', 'EEG', timeout=5)
    if not streams:
        raise RuntimeError("No suitable LSL EEG stream found. Make sure LabRecorder / your device is streaming.")
    print(f"Found stream: {streams[0].name()} ({streams[0].type()})")
    return streams[0]

def bandpower_from_window(signal_window, sfreq, band):
    # Use Welch's method for band power estimation
    fmin, fmax = band
    if len(signal_window) < 4:
        return 0.0
    freqs, psd = welch(signal_window, fs=sfreq, nperseg=min(256, len(signal_window)))
    # integrate PSD over band
    band_mask = (freqs >= fmin) & (freqs <= fmax)
    bp = np.trapz(psd[band_mask], freqs[band_mask]) if np.any(band_mask) else 0.0
    return bp

def normalize_array(arr):
    arr = np.array(arr, dtype=float)
    if np.max(arr) == 0:
        return np.zeros_like(arr)
    # simple min-max normalization with small floor
    arr -= np.min(arr)
    mx = np.max(arr)
    if mx <= 1e-9:
        return np.zeros_like(arr)
    return arr / mx

def open_midi_out(port_name):
    out_ports = mido.get_output_names()
    print("Available MIDI outputs:", out_ports)
    if port_name not in out_ports:
        raise RuntimeError(f"MIDI output '{port_name}' not visible. Make sure loopMIDI is running and port exists.")
    out = mido.open_output(port_name)
    print(f"Opened MIDI output: {port_name}")
    return out

def main():
    stream_info = find_lsl_stream()
    inlet = StreamInlet(stream_info, max_chunklen=1024)
    sfreq = float(stream_info.nominal_srate())
    n_chan = int(stream_info.channel_count())
    print(f"Sampling rate: {sfreq} Hz, channels: {n_chan}")

    midi_out = open_midi_out(LOOPMIDI_PORT_NAME)

    # buffers for each channel
    window_samples = int(max(1, SAMPLE_WINDOW_SEC * sfreq))
    buffers = [deque(maxlen=window_samples) for _ in range(n_chan)]

    # state per channel for Note On/Off
    is_on = [False] * n_chan
    last_on_time = [0.0] * n_chan

    print("Starting main loop (press Ctrl-C to exit)...")
    try:
        while True:
            samples, timestamps = inlet.pull_chunk(timeout=1.0, max_samples=window_samples)
            if not samples:
                # no new data, small sleep and continue
                time.sleep(0.01)
                continue
            # samples is list of sample arrays (n_samples x n_chan)
            arr = np.array(samples)
            # append to per-channel buffers
            for ch in range(n_chan):
                col = arr[:, ch]
                buffers[ch].extend(col.tolist())

            # If we have enough samples, compute bandpower for each channel
            if any(len(buff) >= window_samples for buff in buffers):
                powers = []
                for ch in range(n_chan):
                    buff = np.array(buffers[ch])
                    bp = bandpower_from_window(buff, sfreq, BAND)
                    powers.append(bp)
                # normalize powers across channels (so mapping doesn't saturate)
                norm = normalize_array(powers)  # 0..1
                # map to MIDI velocities
                velocities = [int(MIN_VEL + (MAX_VEL - MIN_VEL) * (v ** POWER_TO_VEL_EXP)) for v in norm]

                now = time.time()
                for ch in range(n_chan):
                    vel = velocities[ch]
                    note = MIDI_BASE_NOTE + ch  # one note per channel
                    p = norm[ch]
                    # Hysteresis thresholding
                    if not is_on[ch] and p >= ON_THRESHOLD:
                        # send note on
                        msg = mido.Message('note_on', note=note, velocity=vel, channel=MIDI_CHANNEL)
                        midi_out.send(msg)
                        is_on[ch] = True
                        last_on_time[ch] = now
                        # debug
                        print(f"[{now:.3f}] CH{ch}: NOTE ON {note} vel={vel} p={p:.3f}")
                    elif is_on[ch]:
                        # if falls below off threshold or hasn't been active for a while, send note_off
                        if p <= OFF_THRESHOLD or (now - last_on_time[ch] > SILENCE_AFTER and p < OFF_THRESHOLD + 0.05):
                            msg = mido.Message('note_off', note=note, velocity=0, channel=MIDI_CHANNEL)
                            midi_out.send(msg)
                            is_on[ch] = False
                            print(f"[{now:.3f}] CH{ch}: NOTE OFF {note} p={p:.3f}")
                        else:
                            # you might want to send velocity/aftertouch/CC updates while note is on
                            # as an example, update velocity via MIDI CC (or send note_on with velocity to retrigger)
                            # Example: send Channel Pressure (not all synths support)
                            # midi_out.send(mido.Message('polytouch', note=note, value=vel, channel=MIDI_CHANNEL))
                            pass

            # Very small sleep to avoid busy-looping
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Interrupted, sending pending Note Offs...")
        for ch in range(n_chan):
            if is_on[ch]:
                note = MIDI_BASE_NOTE + ch
                midi_out.send(mido.Message('note_off', note=note, velocity=0, channel=MIDI_CHANNEL))
        midi_out.close()
        print("Exit cleanly.")

if __name__ == "__main__":
    main()
