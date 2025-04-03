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
    def __init__(self, bpm_multiplier: float, note_length: float, ground_note: int, mode: Mode, mute: bool, volume: int, variants_active, variants):
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
        # e.g. [7, 5, 0] Describes the offset in relation to the gound note. Only relevant if variants_active is True
        self.variants = variants
        # about the mute
        self.mute = mute

    def get_arpeggio(self, bpm, instrument) -> Tuple[list[mido.Message], int]:
        track = [
            mido.Message('program_change', program=instrument, time=0)  # Set instrument
        ]
        
        # Determine the notes to play
        notes = [self.ground_note]
        for i, offset in enumerate(self.variants):
            if self.variants_active[i]:
                notes.append(self.ground_note + offset)

        if self.mode == Mode.UP:
            notes.sort()
        elif self.mode == Mode.DOWN:
            notes.sort(reverse=True)
        elif self.mode == Mode.RANDOM:
            random.shuffle(notes)

        # Calculate the duration of a single note. The total length of the arpeggio is one full note length.
        # Calculate each note's duration based on the note length and the rate.
        # e.g. if rate=2, the arpeggio plays twice as fast as the song
        #      if note_length=0.5, the arpeggio plays each note half as long
        #      if note_length=1 (max value), the arpeggio plays legato
        note_duration = (60*4 / bpm) * (self.note_length / self.rate)

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

            # add gap to account for note_length (pause between notes)
            if i < len(notes) - 1:
                gap = time_step - note_duration
                if gap < 0:
                    gap = 0  # If note_length is bigger than the step, no gap

                # Insert a dummy MetaMessage to carry the gap
                # so the next note_on in the next iteration starts after 'gap' seconds
                track.append(mido.Message('note_off', note=0, velocity=0, time=gap))

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
        variants=[7, 5, 0]
    )
    for msg in arp.get_arpeggio(120, 0):
        print(msg)
