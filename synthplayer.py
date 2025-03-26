import time
import fluidsynth
from concurrent.futures import ThreadPoolExecutor


class SynthPlayer:
    def __init__(self, soundfont_path):
        self.fs = fluidsynth.Synth()
        self.fs.start()
        self.sfid = self.fs.sfload(soundfont_path)  # Charger la soundfont
        self.fs.program_select(0, self.sfid, 0, 0)  # Banque 0, preset 0 par défaut
        self.threadpool = ThreadPoolExecutor(max_workers=4)
        self.num_channels = 0
    
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

    def close(self):
        self.fs.delete()
        self.threadpool.shutdown()

