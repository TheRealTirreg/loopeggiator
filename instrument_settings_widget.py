# instrument_settings_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton
from PySide6.QtCore import Qt
from custom_widgets import NoScrollSlider, NoScrollComboBox

class InstrumentSettingsPanel(QWidget):
    def __init__(self, synth, row_id, parent=None):
        super().__init__(parent)
        self.synth = synth
        self.row_id = row_id
        self.setFixedWidth(180)  # Fixed width for sticky left panel

        # Update instrument ComboBox when presets are updated (e.g. new soundfont loaded)
        self.synth.presets_updated.connect(self.update_instrument_list)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.mute_checkbox = QCheckBox("Mute")
        layout.addWidget(self.mute_checkbox)

        volume_label = QLabel("Volume:")
        self.volume_slider = NoScrollSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 127)
        self.volume_slider.setValue(64)
        layout.addWidget(volume_label)
        layout.addWidget(self.volume_slider)

        layout.addWidget(QLabel("Instrument:"))
        self.instrument_combo = NoScrollComboBox()
        self.instrument_combo.setMinimumWidth(140)
        self.instrument_combo.setMaxVisibleItems(16)  # Todo: Play with this value
        layout.addWidget(self.instrument_combo)

        self.btn_test = QPushButton("Test sound")
        self.btn_test.setToolTip("Preview the selected instrument")
        self.btn_test.clicked.connect(self.test_selected_instrument)
        layout.addWidget(self.btn_test)

        self.btn_del = QPushButton("Delete instrument")
        layout.addWidget(self.btn_del)

        layout.addStretch()

    def test_selected_instrument(self):
        preset = self.instrument_combo.currentData()
        if preset:
            self.synth.change_instrument(self.row_id, preset["program"], bank=preset["bank"])
            self.synth.play_note(60, 1, channel=self.row_id)

    def update_instrument_list(self):
        self.instrument_combo.clear()
        if not self.synth.presets:
            print("No presets available in update_instrument_list")
            return
        
        for preset in self.synth.presets:
            label = f"({preset['bank']}/{preset['program']}) {preset['name']}"
            self.instrument_combo.addItem(label, preset)

        if self.instrument_combo.count() > 0:
            self.instrument_combo.setCurrentIndex(0)
            self.instrument_combo.currentIndexChanged.emit(0)