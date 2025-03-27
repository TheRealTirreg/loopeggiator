from mido import Message, MidiFile, MidiTrack
from PySide6.QtCore import Qt


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

# ====================================
# ---------------------------------------------------------------------------------------
# First arpeggio
#----------------------------------------------------------------------------------------

# Définir les notes en MIDI
notes_midi = [60, 62, 64, 65, 67, 69, 71, 72]  # Do, Ré, Mi, Fa, Sol, La, Si, Do

def third2(self, note):
    if isinstance(note, float):
        idx = self.notes_freq.index(note)
        note_midi = self.notes_midi[idx]
    else:
        note_midi = note
        idx = self.notes_midi.index(note_midi)
        
    if self.btn_up.isChecked():
        for i in range(3):
            self.play_note_pygame(note_midi)
            # Jouer une tierce majeure (4 demi-tons plus haut)
            next_idx = (idx + 2) % 8
            self.play_note_pygame(self.notes_midi[next_idx])
    else:
        print("Not implemented yet")
        self.play_note_pygame(note_midi)


# ---------------------------------------------------------------------------------------
# Keyboard shortcuts
# ---------------------------------------------------------------------------------------
def keyPressEvent(self, event):
    if event.key() == Qt.Key_C:  # Touche "C" → Do
        self.third2(60)
        #self.play_note(261.63)
    elif event.key() == Qt.Key_D:  # Touche "D" → Ré
        self.third2(self.notes_midi[1])
        #self.play_note(293.66)
    elif event.key() == Qt.Key_E:  # Touche "E" → Mi
        self.third2(self.notes_midi[2])
        #self.play_note(329.63)
    elif event.key() == Qt.Key_F:  # Touche "F" → Fa
        self.third2(self.notes_midi[3])
        #self.play_note(349.23)
    elif event.key() == Qt.Key_G:  # Touche "G" → Sol
        self.third2(self.notes_midi[4])
        #self.play_note(392.00)
    elif event.key() == Qt.Key_A:  # Touche "A" → La
        self.third2(self.notes_midi[5])
        #self.play_note(440.00)
    elif event.key() == Qt.Key_B:  # Touche "B" → Si
        self.third2(self.notes_midi[6])
        #self.play_note(493.88)
    elif event.key() == Qt.Key_N:  # Touche "N" → Do (octave supérieur)
        self.third2(notes_midi[7])
        #self.play_note(523.25)
    else:
        super().keyPressEvent(event)
