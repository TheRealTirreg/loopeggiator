from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QCheckBox,
    QComboBox,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from arp_widget import ArpeggiatorBlockWidget


class InstrumentRowWidget(QWidget):
    """
    One “instrument row”:
      - Narrow left side for Mute/Volume/Instrument selection
      - Horizontal list of ArpeggiatorBlockWidget(s) + a (+) button at the end

      - Holds at least one, but potentially many ArpeggiatorBlockWidget(s)
      - Plays the arpeggios of each arp block in after each other
    """
    play_time_changed = Signal()

    def __init__(self, synth, instrument_row_id, parent=None):
        # ========================= Layout Setup =========================
        super().__init__(parent)

        # This row should also shrink to fit, not fill horizontally.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # ---------- Left “Instrument Settings” panel ----------
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.Shape.StyledPanel)
        settings_frame.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum))
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(5, 5, 5, 5)

        # Mute checkbox
        self.mute_checkbox = QCheckBox("Mute")
        self.mute_checkbox.setChecked(False)

        # Volume slider + label
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(75)

        # Horizontal mini‐layout for volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)

        # Play Do Button
        self.btn_do = QPushButton("Play a Do (C4)")
        self.btn_do.clicked.connect(lambda: self.synth.play_note(60, 1, channel=self.id))

        # Instrument combo
        instrument_label = QLabel("Instrument:")
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItem("Piano", 0)       # Acoustic Grand Piano (ID 0)
        self.instrument_combo.addItem("Guitare", 24)    # Acoustic Guitar (nylon) (ID 24)
        self.instrument_combo.addItem("Flûte", 73)      # Flute (ID 73)
        self.instrument_combo.setCurrentIndex(0)
        self.instrument_combo.currentIndexChanged.connect(self.change_instrument)

        # Add them to settings_layout
        settings_layout.addWidget(self.mute_checkbox)
        settings_layout.addLayout(volume_layout)
        settings_layout.addWidget(instrument_label)
        settings_layout.addWidget(self.instrument_combo)
        settings_layout.addWidget(self.btn_do)
        settings_layout.addStretch()

        # ---------- Horizontal area for Arpeggiator blocks ----------
        # (No scroll area here, we rely on ONE global QScrollArea in the main window.)
        self.arps_layout = QHBoxLayout()
        self.arps_layout.setContentsMargins(5, 5, 5, 5)

        # “Add Arpeggiator” button at the end
        self.btn_add_arp = QPushButton("+")
        self.btn_add_arp.setToolTip("Add another Arpeggiator block")
        self.btn_add_arp.clicked.connect(lambda: self.add_arpeggiator_block(repetitions=1))

        # Put the button in first. New blocks get inserted before it.
        self.arps_layout.addWidget(self.btn_add_arp)

        # Add everything to main_layout
        main_layout.addWidget(settings_frame)
        main_layout.addLayout(self.arps_layout)

        # ========================= Functionality ========================

        # Set the synth with instrument
        self.synth = synth
        self.id = instrument_row_id
        self.instrument = 0  # Default Piano

        self.arp_blocks = []  # List of ArpeggiatorBlockWidget(s) in this row
        self.arp_queue = []  # Queue of arpeggios to play. E.g. if ArpWidget1 has 2 repetitions, add this to the queue 2 times
        self.arp_queue_idx = 0  # Hold idx of arp_queue. Start with the first arpeggiator

        # Add an initial ArpeggiatorBlock by default
        self.add_arpeggiator_block(repetitions=1)

    def add_arpeggiator_block(self, repetitions):
        # Insert a new ArpeggiatorBlockWidget before the "+" button
        self.arps_layout.removeWidget(self.btn_add_arp)

        arp_id = len(self.arp_blocks)
        new_block = ArpeggiatorBlockWidget(repetitions=repetitions, id=arp_id)
        self.arp_blocks.append(new_block)

        # Add the index of the new block to the queue for each repetition
        for i in range(repetitions):
            self.arp_queue.append(arp_id)
        
        # Add the new block to the layout
        self.arps_layout.addWidget(new_block)

        # Reinsert the "+" button at the end
        self.arps_layout.addWidget(self.btn_add_arp)

        # Connect signals
        new_block.play_time_changed.connect(self._on_block_changed)
        self.play_time_changed.emit()

    def _on_block_changed(self):
        self.play_time_changed.emit()
    
    def change_instrument(self, index):
        self.instrument = self.instrument_combo.itemData(index)
        self.synth.change_instrument(self.id, self.instrument)  # bank=0

    def get_next_arpeggio(self, bpm):
        """
        Get arpeggio of the next (arpeggio, play_time) in line
        """
        # Get the current arpeggio
        arp_id = self.arp_queue[self.arp_queue_idx]
        arpeggio, time = self.arp_blocks[arp_id].get_arpeggio(bpm, self.instrument)

        # Debug prints
        print(f"Row {self.id} plays Arpeggio ID {arp_id} for time {time}. The q-idx: {self.arp_queue_idx}/{self.arp_queue}", flush=True)

        # Increment the arp_queue_idx, and wrap around if necessary
        self.arp_queue_idx += 1
        if self.arp_queue_idx >= len(self.arp_queue):
            self.arp_queue_idx = 0

        return arpeggio, time
    
    def get_play_time(self, bpm):
        """Adds the play_time of all arpeggiators in this row."""
        play_time = 0
        for block in self.arp_blocks:
            play_time += block.get_play_time(bpm)

        return play_time
