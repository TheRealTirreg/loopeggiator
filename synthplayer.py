# synthplayer.py
import os_check  # Ensures this script also works on Windows
import time
import fluidsynth


class SynthPlayer:
    def __init__(self, soundfont_path, max_rows):
        self.max_rows = max_rows
        self.fs = fluidsynth.Synth()
        self.fs.start()  # Start audio driver (is smart enough to choose depending on os)
        self.sfid = self.fs.sfload(soundfont_path)  # Charger la soundfont
        for ch in range(self.max_rows):
            self.fs.program_select(ch, self.sfid, 0, 0)

    def change_instrument(self, channel, instrument, bank=0):
        print(f"Change instrument on channel {channel} to {instrument}")
        self.fs.program_select(channel, self.sfid, bank, instrument)

    def play_note(self, note, duration=1, velocity=100, channel=0):
        self.fs.noteon(channel, note, velocity)
        time.sleep(duration)
        self.fs.noteoff(channel, note)

    def play_midi(self, tracks):
        """
        `tracks` is a list of MIDO tracks, one track per instrument row.
        Each track is a list of mido.Message objects.
        `msg.time` is as a delta-time (seconds since the last event)!
        The track index => channel #.
        """
        all_events = []
        for channel, track in enumerate(tracks):
            abs_time = 0.0
            for msg in track:
                abs_time += msg.time  # Convert delta-time to absolute time
                all_events.append((abs_time, channel, msg))

        # Sort events by ascending time
        all_events.sort(key=lambda x: x[0])

        start_wall_time = time.time()

        for (event_time, channel, msg) in all_events:
            # Wait until it's time for this event
            now = time.time()
            wait_time = event_time - (now - start_wall_time)
            if wait_time > 0:
                time.sleep(wait_time)

            # Dispatch to fluidsynth
            if msg.type == 'program_change':
                self.fs.program_select(channel, self.sfid, 0, msg.program)
            elif msg.type == 'note_on':
                velocity = max(0, min(msg.velocity, 127))  # clip velocity
                self.fs.noteon(channel, msg.note, velocity)
            elif msg.type == 'note_off':
                self.fs.noteoff(channel, msg.note)
            else:
                print(f"Unknown message type: {msg.type}")

    def stop_all_sounds(self):
        """
        Send note-off to all possible notes on all channels.
        Useful for "panic" or stopping early.
        """
        for ch in range(self.max_rows):
            for note in range(128):  # MIDI note range
                self.fs.noteoff(ch, note)

    def close(self):
        """Properly clean up fluidsynth resources"""
        self.fs.delete()


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
    player = SynthPlayer(path, max_rows=16)
    player.play_midi(midi_messages)

