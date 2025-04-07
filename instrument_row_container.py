# instrument_row_container.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QScrollArea, QSizePolicy
from PySide6.QtCore import Signal, Qt
from instrument_settings_widget import InstrumentSettingsPanel
from instrument_arp_row import InstrumentArpPanel


class InstrumentRowContainer(QWidget):
    play_time_changed = Signal()
    volume_line_changed = Signal()

    def __init__(self, synth, row_id, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.synth = synth
        self.id = row_id
        self.instrument = 0

        self.settings_panel = InstrumentSettingsPanel(synth, self.id, parent=self)
        self.arp_panel = InstrumentArpPanel(parent=self, row_container=self)

        # Wire settings panel to volume/instrument change behavior
        self.settings_panel.volume_slider.valueChanged.connect(self.update_arp_volumes)
        self.settings_panel.instrument_combo.currentIndexChanged.connect(self.change_instrument)
        self.settings_panel.btn_del.clicked.connect(self.del_instrument)

        self.arp_panel.play_time_changed.connect(self._on_block_changed)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(340)  # or whatever makes sense visually

        # Scrollable ArpPanel only
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(self.arp_panel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.settings_panel)
        layout.addWidget(scroll_area, stretch=1)

        self.change_instrument(self.settings_panel.instrument_combo.currentIndex())  # initial assignment

    @property
    def velocity(self):
        return self.settings_panel.volume_slider.value()

    @property
    def arp_blocks(self):
        return self.arp_panel.arp_blocks
    
    @property
    def mute_checkbox(self):
        return self.settings_panel.mute_checkbox

    def del_instrument(self):
        if self.parent:
            self.parent.del_instrument(self)

    def _on_block_changed(self):
        self.play_time_changed.emit()

    def update_arp_volumes(self):
        volume = self.settings_panel.volume_slider.value()
        for arp_block in self.arp_panel.arp_blocks:
            arp_block.velocity = volume
        self.volume_line_changed.emit()

    def change_instrument(self, index):
        self.instrument = self.settings_panel.instrument_combo.itemData(index)
        self.synth.change_instrument(self.id, self.instrument)

    def get_play_time(self, bpm):
        return sum(block.get_play_time(bpm) for block in self.arp_panel.arp_blocks)

    def get_next_arpeggio(self, bpm):
        arp_id = self.arp_panel.arp_queue[self.arp_panel.arp_queue_idx]
        arpeggio, time = self.arp_panel.arp_blocks[arp_id].get_arpeggio(bpm, self.instrument)

        self.arp_panel.arp_queue_idx = (self.arp_panel.arp_queue_idx + 1) % len(self.arp_panel.arp_queue)
        return arpeggio, time

    def get_all_arpeggios(self, bpm):
        all_notes = []
        total_time = 0
        for block in self.arp_panel.arp_blocks:
            notes, duration = block.get_arpeggio(bpm, self.instrument)
            all_notes.extend(notes)
            total_time += duration
        return all_notes, total_time

    def set_block_width(self, max_rate):
        self.arp_panel.set_block_width(max_rate)

    def remove_arp_block(self, block):
        self.arp_panel.remove_block(block)
