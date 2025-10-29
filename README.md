# EEG-to-MIDI
My attempt at creating an EEG-MIDI interface, whereby a participant's live EEG signals would modulate the qualities of music.

## Proposed Setup
1 - Use OpenMuse to stream Muse S Athena EEG signals
2 - Write a Python bridge script to extract the EEG signals and convert them to MIDI output
3 - Direct the MIDI output into loopMIDI, creating a virtual port
4 - Send the information from loopMIDI into Ableton Live
5 - Once the output is in Ableton Live, parameters to be modulated by the EEG signal can be mapped
