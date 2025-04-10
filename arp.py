# arp.py
from enum import Enum
import mido
import random
from typing import Tuple


class Mode(Enum):
    UP = 0
    DOWN = 1
    RANDOM = 2


class Arpeggiator():
    """
    Implements the arpeggiator functionality.
    An Arpeggiator can:
    - Play a sequence of notes in a specific mode (up, down, random)
    - Change the rate of the arpeggio (bpm_multiplier), e.g. 0.5 = half speed, 2 = double speed
    - Play with a shortened note length or a longer note length
    - Change the ground note of the arpeggio (e.g. C4 = 60)
    - Have variants:
        - Variants are notes defined by offsets in relation to the ground note
    """
    def __init__(self, bpm_multiplier: float, note_length: float, ground_note: int, mode: Mode, mute: bool, vibrato: bool, volume: int, variants_active, chords_active, variants):
        # rate: If rate 1, the arpeggio plays at the same speed as the song
        self.rate = bpm_multiplier
        # Determines if the arpeggio is more staccato or legato
        self.note_length = note_length
        # e.g. midi C4 = 60
        self.ground_note = ground_note
        # Mode of the arpeggio (up, down, random)
        self.mode = mode
        self.velocity = volume
        # e.g. [True, False, False] for one out of three variants active
        self.variants_active = variants_active
        # e.g. [True, False, False] for one out of three variants active
        self.chords_active = chords_active
        # e.g. [7, 5, 0] Describes the offset in relation to the gound note. Only relevant if variants_active is True
        self.variants = variants
        # about the mute
        self.mute = mute
        # about the vibrato
        self.vibrato = vibrato

    def get_arpeggio(self, bpm, instrument) -> Tuple[list[mido.Message], int]:
        vibrato_cc = 70
        value = 127 if self.vibrato else 0
        track = [
            mido.Message('program_change', program=instrument, time=0),  # Set instrument
        ]
        track.append(mido.Message('control_change', control=vibrato_cc, value=value))  # Set vibrato

        major_scale = [0, 2, 4, 5, 7, 9, 11, 12]       # C D E F G A B C
        minor_scale = [0, 2, 3, 5, 7, 8, 10, 12]       # C D Eb F G Ab Bb C
        pentatonic_scale = [0, 2, 4, 7, 9, 12]         # C D E G A C

        # Determine the notes to play
        notes = [self.ground_note] if self.ground_note != 47 else []  # 47 is a special case for silence (48 is C3)
        for i, offset in enumerate(self.variants):
            # Special case: If offset is -25, interpret as silence
            if self.variants_active[i]:
                if offset == -99:
                    notes.append(0)  # Silence
                else:
                    notes.append(self.ground_note + offset)

        if not notes:
            t = (60 / bpm) * (1 / self.rate)  # 1 full note length
            return [
                mido.Message('note_off', note=0, velocity=self.velocity, time=0), 
                mido.Message('note_off', note=0, velocity=self.velocity, time=t)
            ], t

        """
        # Chord modes override variants if active
        if self.chords_active[0]:  # Major
            notes = [self.ground_note + i for i in major_scale[:4]]
        elif self.chords_active[1]:  # Minor
            notes = [self.ground_note + i for i in minor_scale[:4]]
        elif self.chords_active[2]:  # Pentatonic
            notes = [self.ground_note + i for i in pentatonic_scale[:4]]
        """

        if self.mode == Mode.UP:
            notes.sort()
        elif self.mode == Mode.DOWN:
            notes.sort(reverse=True)
        elif self.mode == Mode.RANDOM:
            random.shuffle(notes)
        # If self.mode is None, keep the notes in input order (default: ground note + variant1 + variant2 + variant3)

        # Calculate the duration of a single note. The total length of the arpeggio is one full note length.
        # Calculate each note's duration based on the note length and the rate.
        # e.g. if rate=2, the arpeggio plays twice as fast as the song
        #      if note_length=0.5, the arpeggio plays each note half as long
        #      if note_length=1 (max value), the arpeggio plays legato
        note_duration = (60 / bpm) * (self.note_length / self.rate) / len(notes)
        max_note_duration = (60 / bpm) * (1 / self.rate) / len(notes)  # max note length is 1 (legato)

        # Not to be confused with note_duration
        # time_step is the time between each note in the arpeggio
        # note_duration is the time each note is played
        total_time = 0
        time_step = (60 / bpm) * self.rate

        # 4) Build note-on / note-off pairs with correct delta times
        # We want each note_on -> note_off after note_duration,
        # and then we wait (time_step - note_duration) before the next note_on
        for i, note in enumerate(notes):
            if not self.mute:
                track.append(mido.Message('note_on', note=note, velocity=self.velocity, time=0))
            else:
                track.append(mido.Message('note_off', note=note, velocity=self.velocity, time=0))
            track.append(mido.Message('note_off', note=note, velocity=self.velocity, time=note_duration))
            # Wait until the next note is played to enable shorter note lengths
            track.append(mido.Message('note_off', note=note, velocity=self.velocity, time=max_note_duration - note_duration))

            # Calculate the total time for the arpeggio
            total_time += time_step
        return track, total_time


if __name__ == "__main__":
    arp = Arpeggiator(
        bpm_multiplier=1,
        note_length=0.5,
        ground_note=60,
        mode=Mode.UP,
        variants_active=[False, False, False],
        chords_active=[False, False, False],
        variants=[7, 5, 0]
    )
    for msg in arp.get_arpeggio(120, 0):
        print(msg)
