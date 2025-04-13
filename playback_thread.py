# playback_thread.py
from PySide6.QtCore import QThread


class PlaybackThread(QThread):
    """
    Generates one loop of arpeggios for all rows and plays them.
    """
    def __init__(self, instrument_rows, get_bpm_func, synth, parent=None):
        super().__init__(parent)
        self.instrument_rows = instrument_rows  # list[InstrumentRowWidget]
        self.get_bpm_func = get_bpm_func  # function that returns current BPM
        self.synth = synth
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            bpm = self.get_bpm_func()

            # Build one MIDI track [mido.Messages] for each row
            midi_tracks = []
            for row_index, row in enumerate(self.instrument_rows):
                if row.mute_checkbox.isChecked():
                    # Mute => empty track
                    midi_tracks.append([])
                else:
                    # MIDO track uses delta times! (seconds since the last event)
                    # E.g. [Message('program_change', program=..., time=0),
                    #       Message('note_on', note=..., velocity=..., time=0),
                    #       Message('note_off', note=..., velocity=..., time=1.0),
                    #       ... ]
                    track, play_time = row.get_all_arpeggios(bpm)

                    midi_tracks.append(track)

            # Play MIDI
            if self.running:
                self.synth.play_midi(midi_tracks)

        self.running = False
        self.finished.emit()

    def stop(self):
        self.running = False
        self.synth.interrupt()
        self.synth.stop_all_sounds()
