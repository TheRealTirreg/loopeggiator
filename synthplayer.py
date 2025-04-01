import os_check  # Ensures this script also works on Windows
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
        self.active_channels = []  # List of ints (>1, 1, 0). 0 = no arpeggio queued, 1 = last arpeggio playing, >1 = enough arpeggios queued
    
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
            [Message('program_change', program=0, time=0), Message('note_on', note=60, velocity=64, time=0), ...],  # Track 1
            [Message('program_change', program=40, time=0), Message('note_on', note=60, velocity=64, time=0), ...]  # Track 2
            ...
        ]
        """
        # Initialize:
        # Collect all events into a single list of (absolute_time, channel, msg).
        # Each track is assigned a unique channel index.
        all_events = []
        for channel, track in enumerate(midi_messages):
            self.active_channels.append(1)  # Initialize active channels
            for msg in track:
                all_events.append((msg.time, channel, msg))

        # 2) Sort by absolute_time
        all_events.sort(key=lambda x: x[0])

        print(f"Playing {len(all_events)} events in total:")
        for event_time, channel, msg in all_events:
            print(f"Time: {event_time:.2f}, Channel: {channel}, Message: {msg}", flush=True)

        # 3) Step through all events in chronological order
        start_wall_time = time.time()
        for i, (event_time, channel, msg) in enumerate(all_events):
            # Wait until it's time for this event
            # figure out how many seconds from now
            now = time.time()
            target_wall_time = start_wall_time + event_time
            sleep_time = target_wall_time - now
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Send the event to fluidsynth
            # (Same logic as your old _play_track() code)
            if msg.type == 'program_change':
                self.fs.program_select(channel, self.sfid, 0, msg.program)
            elif msg.type == 'note_on':
                scaled_velocity = min(msg.velocity, 80)
                self.fs.noteon(channel, msg.note, scaled_velocity)
            elif msg.type == 'note_off':
                self.fs.noteoff(channel, msg.note)

            # Optional debug print
            # (Will be in perfect chronological order)
            print(f"[{time.time() - start_wall_time:.2f}] {msg}")

    def close(self):
        self.fs.delete()
        self.threadpool.shutdown()


if __name__ == "__main__":
    import mido
    
    midi_messages = [
        [
            mido.Message('program_change', program=0, time=0),  # Piano
            mido.Message('note_on', note=60, velocity=64, time=0),  # Middle C
            mido.Message('note_off', note=60, velocity=64, time=1.5),  # Release Middle C after 1.5 seconds
            mido.Message('note_on', note=62, velocity=64, time=3),  # D
            mido.Message('note_off', note=62, velocity=64, time=4.5),  # Release D after 1.5 seconds
        ],
        [
            mido.Message('program_change', program=40, time=0),  # Violin
            mido.Message('note_on', note=64, velocity=64, time=0),  # E
            mido.Message('note_off', note=64, velocity=64, time=1.5),  # Release E after 1.5 seconds
            mido.Message('note_on', note=62, velocity=64, time=1.5),  # E
            mido.Message('note_off', note=62, velocity=64, time=3),  # Release E after 1.5 seconds
        ]
    ]
    path = r"C:\tools\fluidsynth\soundfonts\FluidR3_GM.sf2"
    # path = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
    print(f"using path {path}")
    player = SynthPlayer(path)
    player.play_midi(midi_messages)

