# EEG-to-MIDI
My attempt at creating an EEG-MIDI interface, whereby a participant's EEG signals would create/modulate music in Ableton Live.

My aim is to create two functional bridge scripts for both (1) live EEG-to-MIDI conversion and (2) EEG-to-MIDI conversion for pre-recorded EEG data.


## Requirements
### Hardware
- PC/Laptop
- Muse S Athena (if undertaking live EEG-to-MIDI)

### Software
- VScode (with Python and Jupyter extensions)
- Python
- Ableton Live
- [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)


## Proposed Setup: Live EEG-to-MIDI
1. Use [OpenMuse](https://github.com/DominiqueMakowski/OpenMuse) to stream Muse S Athena EEG signals
2. Run a Python bridge script to extract the live EEG signals and convert them to MIDI output
3. Direct the MIDI output into loopMIDI, creating a virtual port
4. Send the information from loopMIDI into Ableton Live
5. Once the output is in Ableton Live, parameters to be modulated by the EEG signal can be mapped


## Proposed Setup: Pre-recorded EEG-to-MIDI
1. Locate .csv file containing EEG data
2. Run a Python bridge script to extract the pre-recorded EEG signals and convert them to MIDI output
3. Direct the MIDI output into loopMIDI, creating a virtual port
4. Send the information from loopMIDI into Ableton Live
5. Once the output is in Ableton Live, parameters to be modulated by the EEG signal can be mapped


## Usage: Live EEG-to-MIDI

(TBC)


## Usage: Pre-recorded EEG-to-MIDI

