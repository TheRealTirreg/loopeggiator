import time
from PySide6.QtCore import QThread, Signal


class PlaybackThread(QThread):
    """
    Continuously triggers each row's next arpeggio 
    aligned to a measure boundary defined by the BPM.
    """
    # TODO maybe try Signals? e.g. playbackProgress = Signal(int)

    def __init__(self, instrument_rows, get_bpm_func, synth, parent=None):
        super().__init__(parent)
        self.instrument_rows = instrument_rows  # list[InstrumentRowWidget]
        self.get_bpm_func = get_bpm_func        # function that returns current BPM
        self.synth = synth                      # your SynthPlayer
        self.running = False

        # For each row, store:
        #   - next start time (absolute time)
        #   - the “next arpeggio” data
        self.start_times = []
        self.next_arpeggios = []

    def run(self):
        self.running = True

        # 1) Initialize the start_times + next_arpeggios
        current_time = time.time()
        bpm = self.get_bpm_func()

        # For each instrument row, fetch the first arpeggio
        self.start_times = [current_time for _ in self.instrument_rows]
        self.next_arpeggios = []
        for row in self.instrument_rows:
            # We'll store None if the row is muted or has no arpeggio
            if row.mute_checkbox.isChecked():
                self.next_arpeggios.append(None)
            else:
                arpeggio, arp_time = row.get_next_arpeggio(bpm)
                self.next_arpeggios.append((arpeggio, arp_time))

        # 2) Main loop
        while self.running:
            now = time.time()
            any_waiting = False

            # Go through each row to see if it’s time to start the next arpeggio
            for i, row in enumerate(self.instrument_rows):
                # If the row is muted, skip it
                if row.mute_checkbox.isChecked():
                    continue

                # If we have no queued arpeggio, skip.
                # This should never be the case, as we just loop through each arp in the row.
                if self.next_arpeggios[i] is None:
                    print(f"Row {i} has no arpeggio queued.", flush=True)
                    continue

                # If it's time to start row[i]'s next arpeggio:
                if now >= self.start_times[i]:
                    print("Starting arpeggio for row", i, flush=True)
                    # 1) Retrieve the next arpeggio (already stored)
                    arpeggio, arp_time = self.next_arpeggios[i]

                    # 2) Actually play it (non‐blocking or schedule, depending on your SynthPlayer)
                    self.synth.play_midi([arpeggio])  
                    # or some scheduling approach that sets note on/off at the right times

                    # 3) Update row’s next start time
                    #    If you want each row to keep playing back‐to‐back:
                    self.start_times[i] += arp_time

                    # 4) Fetch the *following* arpeggio (the next in the queue)
                    new_arpeggio, new_arp_time = row.get_next_arpeggio(bpm)
                    self.next_arpeggios[i] = (new_arpeggio, new_arp_time)

                else:
                    # Not time yet; we have at least one row waiting
                    any_waiting = True

            # Sleep a little so we don’t spin the CPU at 100%
            # Adjust the sleep time for your needs (e.g. 5 ms)
            if any_waiting:
                time.sleep(0.005)
            else:
                # If for some reason all rows are done or muted, 
                # you could sleep longer or break out. 
                time.sleep(0.01)

    def stop(self):
        self.running = False