# EEG-to-MIDI
My attempt at creating an EEG-MIDI interface, whereby a participant's live EEG signals would modulate the qualities of music in Ableton Live.

My aim is to create two functional scripts for both live EEG-to-MIDI conversion, as well as EEG-to-MIDI conversion for pre-recorded EEG data.

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