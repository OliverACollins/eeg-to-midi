# EEG-to-MIDI
My attempt at creating an EEG-MIDI interface, whereby a participant's EEG signals would create/modulate music in Ableton Live.

My aim is to create functional bridge scripts for both (1) live EEG-to-MIDI conversion and (2) EEG-to-MIDI conversion for pre-recorded EEG data.


## Requirements
### Hardware
- PC/Laptop
- Muse S Athena (if undertaking live EEG-to-MIDI)

### Software
- VScode (with Python and Jupyter extensions)
- Python
- [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
- Ableton Live

## Proposed Setup: Live EEG-to-MIDI
1. Use [OpenMuse](https://github.com/DominiqueMakowski/OpenMuse) to stream Muse S Athena EEG signals
2. Run a Python bridge script to extract the live EEG signals and convert them to MIDI output
3. Direct the MIDI output into loopMIDI, creating a virtual port
4. Send the information from loopMIDI into Ableton Live
5. Once the output is in Ableton Live, parameters to be modulated by the EEG signal can be mapped

### Roadmap
- [ ] Create bridge script that runs using one electrode
- [ ] Create bridge script that runs using more than one electrode


## Proposed Setup: Pre-recorded EEG-to-MIDI
1. Locate .csv file containing EEG data
2. Run a Python bridge script to extract the pre-recorded EEG signals and convert them to MIDI output
3. Direct the MIDI output into loopMIDI, creating a virtual port
4. Send the information from loopMIDI into Ableton Live
5. Once the output is in Ableton Live, parameters to be modulated by the EEG signal can be mapped

### Roadmap
- [x] Create bridge script that runs using one electrode
- [ ] Create bridge script that runs using more than one electrode


## Usage: Live EEG-to-MIDI

(TBC)


## Usage: Pre-recorded EEG-to-MIDI
### Specifying .csv file
```python
CSV_FILE = "cleaned_eeg.csv"
```

### Specifying electrode channel
Using the Muse S Athena, four electrodes can be specified (AF7, AF8, TP9, TP10):
```python
CHANNEL = "AF7"
```

### Change notes per second
```python
WINDOW_SEC = 0.25
```



## Ideas for both live and pre-recorded EEG-to-MIDI conversion
- EEG signals converted to notes
- EEG signals converted to volume control for live music
- EEG signals converted to signal filtering (low-pass/high-pass, depending on signal frequency) for live music
- Create a live EEG-to-MIDI paradigm where an increasing amount of gamma/beta waves leads to an intensifying synth sound (e.g., more concentration = more pressure)
- Create a neurofeedback paradigm for meditation/relaxation (e.g., increasing amount of alpha waves = more relaxing music. Could subject people to high-concentration tasks before this (leading to beta waves) and see the increasing presence of alpha waves from relaxation task)

Could do all this for ECG too!