# synthplayer.py
import os_check  # Ensures this script also works on Windows
import os
import time
import mido
import fluidsynth
from sf2utils.sf2parse import Sf2File
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Signal, QObject


class SynthPlayer(QObject):
    presets_updated = Signal()

    def __init__(self, soundfont_path, max_rows):
        super().__init__()
        self.interrupt_flag = False

        self.sf_path = soundfont_path
        self.max_rows = max_rows

        self.instrument_banks = [0 for i in range(self.max_rows)]

        self.presets = self.extract_presets(soundfont_path)
        self.presets_updated.emit()

        self.fs = fluidsynth.Synth()
        self.fs.start()  # Start audio driver (is smart enough to choose depending on os)
        self.sfid = self.fs.sfload(soundfont_path)  # Charger la soundfont
        for ch in range(self.max_rows):
            self.fs.program_select(ch, self.sfid, 0, 0)
        self.on_marker = None  # Will be set by UI

    def interrupt(self):
        self.interrupt_flag = True

    def change_instrument(self, channel, instrument, bank=0):
        print(f"Change instrument on channel {channel} to {instrument}")
        self.fs.program_select(channel, self.sfid, bank, instrument)
        self.instrument_banks[channel] = bank

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
            if self.interrupt_flag:
                self.interrupt_flag = False
                print("Playback interrupted.")
                break

            # Wait until it's time for this event
            now = time.time()
            wait_time = event_time - (now - start_wall_time)
            if wait_time > 0:
                time.sleep(wait_time)

            # Dispatch to fluidsynth
            if msg.type == 'program_change':
                print(f"Bank: {self.instrument_banks[channel]}, Program: {msg.program} in channel {channel}")
                self.fs.program_select(channel, self.sfid, self.instrument_banks[channel], msg.program)
            elif msg.type == 'control_change':
                if msg.control == 1:  # Modulation wheel
                    #mido.Message('control_change', control=vibrato_cc, value=value)
                    self.fs.cc(channel, 1, msg.value)
                elif msg.control == 91:  # Reverb
                    self.fs.cc(channel, 91, msg.value)
                elif msg.control == 93:  # chorus
                    self.fs.cc(channel, 93, msg.value)
            elif msg.type == 'note_on':
                if msg.note == 0:  # Ignore note 0 (placeholder for silence)
                    continue
                
                velocity = max(0, min(msg.velocity, 127))  # clip velocity
                self.fs.noteon(channel, msg.note, velocity)

            elif isinstance(msg, mido.MetaMessage) and msg.type == "marker":
                if self.on_marker:
                    self.on_marker(msg.text)  # Send block id like '2#0' to make ui flash
            elif msg.type == 'note_off':
                self.fs.noteoff(channel, msg.note)
                self.fs.cc(channel, 1, 0)  # Reset modulation
                self.fs.cc(channel, 91, 0)  # Reset reverb
                self.fs.cc(channel, 93, 0)
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

    def load_soundfont(self, path):
        """Try to load a soundfont. If it fails, prompt the user to select a valid one."""
        while True:
            try:
                new_sfid = self.fs.sfload(path)
                for ch in range(self.max_rows):
                    self.fs.program_select(ch, new_sfid, 0, 0)
                self.sfid = new_sfid
                self.sf_path = path
                self.presets = self.extract_presets(path)
                print(f"Loaded SoundFont: {path}")
                self.presets_updated.emit()
                return True
            except Exception as e:
                print(f"Failed to load SoundFont: {path}\n{e}")
                path = self.ask_user_for_soundfont()
                if not path:
                    print("No SoundFont selected. Exiting.")
                    return False  # Let caller handle exit logic

    def ask_user_for_soundfont(self):
        """Open a file dialog asking the user to select a valid SoundFont."""
        default_dir = os.path.expanduser("~") if os_check.is_windows() else "/usr/share/sounds/sf2"
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Select a valid SoundFont (.sf2)",
            default_dir,
            "SoundFont Files (*.sf2)"
        )
        return filename if filename else None
    
    @staticmethod
    def extract_presets(soundfont_path, allowed_banks=None):
        with open(soundfont_path, 'rb') as sf2:
            soundfont = Sf2File(sf2)
            presets = []
            for p in soundfont.presets:
                bank = getattr(p, "bank", None)
                program = getattr(p, "preset", None)
                name = getattr(p, "name", "Unknown")

                if bank is None or program is None:
                    print(f"Skipping invalid preset: {name} (bank: {bank}, program: {program})") if name != "EOP" else None
                    continue

                if allowed_banks is None or bank in allowed_banks:
                    presets.append({
                        "name": name,
                        "bank": bank,
                        "program": program
                    })
            
            print(f"Extracted {len(presets)} presets from {soundfont_path}")
            presets.sort(key=lambda x: (x["bank"], x["program"]))

            return presets



if __name__ == "__main__":    
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

