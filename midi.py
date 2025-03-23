from mido import Message, MidiFile, MidiTrack

def play_midi_arp(duration_s, instruments, notes):
    """
    duration_s: duration of the whole arp
    instruments: list of all instruments. For example, [0, 0] meaning two tracks of piano
    notes: the notes of the current arpeggio for each instrument. E.g.: [[60], [60, 67]]
           This wouls play C4 (60) for duration_s using the first instrument, 
           and in parallel play first 60 for duration_s/2 and then 67 for duration_s/2 using instrument 2.
    """
    duration_s = 1  # test
    notes = [60]  # test
    instruments = [0]  # test

    mid = MidiFile(type=1)
    for i in instruments:
        track = MidiTrack()
        mid.tracks.append(track)

    for i, notes in enumerate(notes):
        for note in notes:
            mid.tracks[i].append(Message('note_on', note=note, velocity=64, time=0))
            mid.tracks[i].append(Message('note_off', note=note, velocity=64, time=duration_s))

    
