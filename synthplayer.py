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
        """
        USE PLAY_MIDI INSTEAD
        Plays a single note on the given channel using a separate thread.
        """
        print(f"Playing note {midi_note} for {duration} seconds on channel {channel}")
        self.threadpool.submit(self._play_note_threaded, midi_note, duration, velocity, channel)

    def _play_note_threaded(self, midi_note, duration, velocity, channel):
        """Deprecated: Use play_midi instead."""
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
        print(f"Playing on channel {channel}. Track:")
        for msg in track:
            print(msg)
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


if __name__ == "__main__":
    synth = SynthPlayer("/usr/share/sounds/sf2/FluidR3_GM.sf2")
    synth.add_channel()
    synth.play_note(60, 1, channel=0)
    time.sleep(1)
    synth.close()

