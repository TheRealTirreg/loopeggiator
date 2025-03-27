from enum import Enum


class Mode(Enum):
    UP = 0
    DOWN = 1
    RANDOM = 2


class Arpeggiator():
    """"""
    def __init__(self, bpm_multiplier: float, note_length: float, ground_note: int, mode: Mode, variants_active, variants):
        self.rate = bpm_multiplier
        self.note_length = note_length
        self.ground_note = ground_note  # e.g. midi C4 = 60
        self.mode = mode
        self.variants_active = variants_active
        self.variants = variants  # Describes the offset in relation to the gound note

    def get_arpeggio(self, bpm):
        pass


if __name__ == "__main__":
    pass
