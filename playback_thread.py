import time
from PySide6.QtCore import QThread, Signal


class PlaybackThread(QThread):
    """
    Continuously triggers each row's next arpeggio 
    aligned to a measure boundary defined by the BPM.
    """

    def __init__(self, instrument_rows, get_bpm_func, synth, parent=None):
        super().__init__(parent)
        self.instrument_rows = instrument_rows  # list[InstrumentRowWidget]
        self.get_bpm_func = get_bpm_func        # function that returns current BPM
        self.synth = synth                      # your SynthPlayer
        self.running = False

        # For each row, store:
        #   - next start time (absolute time)
        #   - the "next arpeggio" data
        self.start_times = []
        self.next_arpeggios = []
        
        # Track the last set instrument for each channel
        self.current_instruments = {}

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
            
            # Initialize the instrument tracking for each row
            self.current_instruments[row.id] = row.instrument_combo.currentData()

        # 2) Main loop
        while self.running:
            now = time.time()
            any_waiting = False
            
            # Collect all arpeggios that are ready to play
            arpeggios_to_play = []
            
            # Check for instrument changes
            for i, row in enumerate(self.instrument_rows):
                # Get the current instrument for this row
                current_instrument = row.instrument_combo.currentData()
                
                # If the instrument has changed, update it
                if row.id in self.current_instruments and self.current_instruments[row.id] != current_instrument:
                    print(f"Instrument change detected for row {row.id}: {self.current_instruments[row.id]} -> {current_instrument}", flush=True)
                    # Update our tracking
                    self.current_instruments[row.id] = current_instrument
                    # Make sure the synth knows about this change
                    self.synth.change_instrument(row.id, current_instrument)

            # Go through each row to see if it's time to start the next arpeggio
            for i, row in enumerate(self.instrument_rows):
                # If the row is muted, skip it
                if row.mute_checkbox.isChecked():
                    continue

                # If the user just added a new row, we need to increase the size of our lists
                if len(self.start_times) < len(self.instrument_rows):
                    self.start_times.append(current_time)
                    self.next_arpeggios.append(None)
                    # Initialize the instrument for the new row
                    self.current_instruments[row.id] = row.instrument_combo.currentData()
                    # Set the instrument in the synth
                    self.synth.change_instrument(row.id, row.instrument_combo.currentData())

                # If we have no queued arpeggio, skip.
                if self.next_arpeggios[i] is None:
                    print(f"Row {i} has no arpeggio queued.", flush=True)  
                    continue

                # If it's time to start row[i]'s next arpeggio:
                if now >= self.start_times[i]:
                    print("Starting arpeggio for row", i, flush=True)
                    # 1) Retrieve the next arpeggio (already stored)
                    arpeggio, arp_time = self.next_arpeggios[i]
                    
                    # Add to the list of arpeggios to play
                    # Make sure each arpeggio has its channel set correctly
                    # Get the volume level from the slider
                    volume = row.volume_slider.value() / 100.0  # Convert to 0.0-1.0 range
                    
                    # Process each message in the arpeggio to set the correct channel and adjust velocity
                    for msg in arpeggio:
                        if hasattr(msg, 'channel'):
                            msg.channel = row.id
                        # If it's a note_on message, adjust the velocity based on the volume slider
                        if hasattr(msg, 'type') and msg.type == 'note_on' and hasattr(msg, 'velocity'):
                            msg.velocity = int(msg.velocity * volume)
                    
                    arpeggios_to_play.append(arpeggio)

                    # 3) Update row's next start time
                    self.start_times[i] += arp_time

                    # 4) Fetch the *following* arpeggio (the next in the queue)
                    new_arpeggio, new_arp_time = row.get_next_arpeggio(bpm)
                    self.next_arpeggios[i] = (new_arpeggio, new_arp_time)

                else:
                    # Not time yet; we have at least one row waiting
                    any_waiting = True
            
            # Play all ready arpeggios at once
            if arpeggios_to_play:
                self.synth.play_midi(arpeggios_to_play)

            # Sleep a little so we don't spin the CPU at 100%
            # Adjust the sleep time for your needs (e.g. 5 ms)
            if any_waiting:
                time.sleep(0.005)
            else:
                # If for some reason all rows are done or muted, 
                # you could sleep longer or break out. 
                time.sleep(0.01)

    def stop(self):
        self.running = False