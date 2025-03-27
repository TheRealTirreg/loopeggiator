from PySide6.QtCore import Qt
import time
import fluidsynth
from concurrent.futures import ThreadPoolExecutor
import mido


class SynthPlayer:
    def __init__(self, soundfont_path, bpm=100):
        self.fs = fluidsynth.Synth()
        self.fs.start()
        self.sfid = self.fs.sfload(soundfont_path)  # Load the soundfont
        self.fs.program_select(0, self.sfid, 0, 0)  # Bank 0, preset 0 by default
        self.threadpool = ThreadPoolExecutor(max_workers=4)
        self.num_channels = 0
        self.bpm = bpm

    def add_channel(self, bank=0, preset=0):
        """
        bank: 0 = normal instrument, 128 = percussion
        preset: select instrument (0=Piano, 40=Violin, ...)
        """
        print(f"Add channel {self.num_channels}")
        self.fs.program_select(self.num_channels, self.sfid, bank, preset)
        self.num_channels += 1

    def change_instrument(self, channel, instrument, bank=0):
        print(f"Change instrument on channel {channel} to {instrument}")
        self.fs.program_select(channel, self.sfid, bank, instrument)

    def play_note(self, midi_note, duration=1.0, velocity=100, channel=0):
        print(f"Playing note {midi_note} for {duration} seconds on channel {channel}")
        self.threadpool.submit(self.play_note_threaded, midi_note, duration, velocity, channel)

    def play_note_threaded(self, midi_note, duration, velocity, channel):
        self.fs.noteon(channel, midi_note, velocity)
        time.sleep(duration)
        self.fs.noteoff(channel, midi_note)

    def play_midi(self, midi_messages):
        """
        Plays a list of MIDI messages in parallel.
        Each track is played in a separate thread.

        midi_messages: list of tracks, each track is a list of mido.Message
        e.g. 
        midi_messages = [
            [Message('program_change', program=0, time=0), Message('note_on', note=60, velocity=64, time=0), ...],
            [Message('program_change', program=40, time=0), Message('note_on', note=64, velocity=64, time=0), ...]
        ]
        """
        # Loop through all tracks (which can have different instruments)
        for channel, track in enumerate(midi_messages):
            # Each track is played in a separate thread
            self.threadpool.submit(self._play_track, track, channel)

    def _play_track(self, track, channel):
        for msg in track:
            time.sleep(msg.time)
            if msg.type == 'program_change':
                self.fs.program_select(channel, self.sfid, 0, msg.program)
            elif msg.type == 'note_on':
                scaled_velocity = min(msg.velocity, 80)  # Avoid too loud notes (overmodulation)
                self.fs.noteon(channel, msg.note, scaled_velocity)
            elif msg.type == 'note_off':
                self.fs.noteoff(channel, msg.note)

    def close(self):
        self.fs.delete()
        self.threadpool.shutdown()


midi_messages = [
    [
        mido.Message('program_change', program=0, time=0),  # Piano
        mido.Message('note_on', note=60, velocity=64, time=0),  # Middle C
        mido.Message('note_off', note=60, velocity=64, time=1),  # Release Middle C after 1 second
    ],
    [
        mido.Message('program_change', program=40, time=0),  # Violin
        mido.Message('note_on', note=64, velocity=64, time=0),  # E
        mido.Message('note_off', note=64, velocity=64, time=1),  # Release E after 1 second
    ]
]
player = SynthPlayer('/usr/share/sounds/sf2/FluidR3_GM.sf2')
player.play_midi(midi_messages)



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
