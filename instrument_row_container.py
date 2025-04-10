# instrument_row_container.py
from PySide6.QtWidgets import QHBoxLayout, QFrame, QSizePolicy
from PySide6.QtCore import Signal
from instrument_settings_widget import InstrumentSettingsPanel
from instrument_arp_row import InstrumentArpPanel


class InstrumentRowContainer(QFrame):
    play_time_changed = Signal()
    volume_line_changed = Signal()

    def __init__(self, synth, row_id, parent=None):
        super().__init__(parent)

        self._parent = parent
        self.synth = synth
        self.id = row_id
        self.instrument = 0

        self.settings_panel = InstrumentSettingsPanel(synth, self.id, parent=self)
        self.settings_panel.update_instrument_list()
        self.arp_panel = InstrumentArpPanel(parent=self, row_container=self)

        # Wire settings panel to volume/instrument change behavior
        self.settings_panel.volume_slider.valueChanged.connect(self.update_arp_volumes)
        self.settings_panel.instrument_combo.currentIndexChanged.connect(self.change_instrument)
        self.settings_panel.btn_del.clicked.connect(self.del_instrument)

        self.arp_panel.play_time_changed.connect(self._on_block_changed)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(340)  # or whatever makes sense visually

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.settings_panel)
        layout.addWidget(self.arp_panel, stretch=1)

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
        if self._parent:
            self._parent.del_instrument(self)

    def _on_block_changed(self):
        self.play_time_changed.emit()

    def update_arp_volumes(self):
        volume = self.settings_panel.volume_slider.value()
        for arp_block in self.arp_panel.arp_blocks:
            arp_block.velocity = volume
        self.volume_line_changed.emit()

    def change_instrument(self, index):
        preset = self.settings_panel.instrument_combo.itemData(index)
        if preset and isinstance(preset, dict):
            self.instrument = preset["program"]
            bank = preset.get("bank", 0)
        else:
            # fallback for old format
            print("Old format in instrument row container change_instrument method")
            self.instrument = preset if isinstance(preset, int) else 0
            bank = 0

        self.synth.change_instrument(self.id, self.instrument, bank=bank)

    def get_play_time(self, bpm):
        return sum(block.get_play_time(bpm) for block in self.arp_panel.arp_blocks)

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
