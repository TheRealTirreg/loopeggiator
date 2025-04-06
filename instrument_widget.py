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
    volume_line_changed = Signal()
    def __init__(self, synth, instrument_row_id, parent=None):
        # ========================= Layout Setup =========================
        super().__init__(parent)
        self.parent = parent
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
        self.volume_slider.setRange(0, 127)
        self.volume_slider.setValue(64)
        self.volume_slider.valueChanged.connect(self.update_arp_volumes)
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

        # "Delete instrument" row
        self.btn_del_instrument = QPushButton("Delete instrument")
        self.btn_del_instrument.clicked.connect(self.del_instrument)

        # Add them to settings_layout
        settings_layout.addWidget(self.mute_checkbox)
        settings_layout.addLayout(volume_layout)
        settings_layout.addWidget(instrument_label)
        settings_layout.addWidget(self.instrument_combo)
        settings_layout.addWidget(self.btn_do)
        settings_layout.addWidget(self.btn_del_instrument)
        settings_layout.addStretch()

        # ---------- Horizontal area for Arpeggiator blocks ----------
        # (No scroll area here, we rely on ONE global QScrollArea in the main window.)
        self.arps_layout = QHBoxLayout()
        self.arps_layout.setContentsMargins(5, 5, 5, 5)

        # “Add Arpeggiator” button at the end
        self.btn_add_arp = QPushButton("+")
        self.btn_add_arp.setToolTip("Add another Arpeggiator block")
        self.btn_add_arp.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
        new_block = ArpeggiatorBlockWidget(parent=self, repetitions=repetitions, id=arp_id)
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

    def set_block_width(self, max_rate):
        """
        Sets the width of each arpeggiator block based on its rate.
        If the max_rate (the largest rate of any arp block in any instrument row) is e.g. 2,
            then we want any block with a rate of 1 to have twice the width of a block with a rate of 2.
            (And a block with a rate of 0.5 should have 4 times the width of a block with a rate of 2 and so on.)
        """
        min_block_width = ArpeggiatorBlockWidget.minimal_block_width
        for block in self.arp_blocks:
            width = min_block_width * (max_rate / block.rate)  # In pixels
            block.setFixedWidth(width)

    def remove_arp_block(self, block):
        """
        Remove an arpeggiator block from this instrument row.
        Args:
            block: The ArpeggiatorBlockWidget to remove
        """
        if block in self.arp_blocks:
            # Get the block ID
            block_id = self.arp_blocks.index(block)
            
            # Remove from layout and disconnect signals
            self.arps_layout.removeWidget(block)
            block.play_time_changed.disconnect(self._on_block_changed)
            block.deleteLater()  # Schedule the widget for deletion
            
            # Remove from our list
            self.arp_blocks.remove(block)
            
            # Update IDs for remaining blocks
            for i, remaining_block in enumerate(self.arp_blocks):
                remaining_block.id = i
            
            # Update arp_queue to remove references to this block
            # and update indices for blocks that come after it
            new_queue = []
            for idx in self.arp_queue:
                if idx < block_id:
                    new_queue.append(idx)  # Keep the same index for blocks before
                elif idx > block_id:
                    new_queue.append(idx - 1)  # Reduce index for blocks after
                # Skip indexes that match block_id
                
            self.arp_queue = new_queue
            
            # Reset queue index if needed
            if self.arp_queue and self.arp_queue_idx >= len(self.arp_queue):
                self.arp_queue_idx = 0
            
            # Notify that play time has changed
            self.play_time_changed.emit()

    def del_instrument(self):
        if self.parent:
            self.parent.del_instrument(self)
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

        # Increment the arp_queue_idx, and wrap around if necessary
        self.arp_queue_idx += 1
        if self.arp_queue_idx >= len(self.arp_queue):
            self.arp_queue_idx = 0

        return arpeggio, time
    
    def get_all_arpeggios(self, bpm):
        all_arpeggios = []
        total_time = 0
        for block in self.arp_blocks:
            arpeggio, time = block.get_arpeggio(bpm, self.instrument)
            all_arpeggios.extend(arpeggio)
            total_time += time
        
        return all_arpeggios, total_time
    
    def get_play_time(self, bpm):
        """Adds the play_time of all arpeggiators in this row."""
        play_time = 0
        for block in self.arp_blocks:
            play_time += block.get_play_time(bpm)

        return play_time


    def update_arp_volumes(self):
        """Propage les changements de volume à tous les blocs d'arpège"""
        volume = self.volume_slider.value()
        self.volume_slider.blockSignals(True)
        for arp_block in self.arp_blocks:
            arp_block.velocity = volume
        self.volume_slider.blockSignals(False)
        self.volume_line_changed.emit()