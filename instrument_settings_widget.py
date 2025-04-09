# instrument_settings_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton
from PySide6.QtCore import Qt
from no_scrolling import NoScrollSlider, NoScrollComboBox

class InstrumentSettingsPanel(QWidget):
    def __init__(self, synth, row_id, parent=None):
        super().__init__(parent)
        self.synth = synth
        self.row_id = row_id
        self.setFixedWidth(180)  # Fixed width for sticky left panel

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
        self.instrument_combo.addItem("Piano", 0)
        self.instrument_combo.addItem("Guitare", 24)
        self.instrument_combo.addItem("Flûte", 73)
        layout.addWidget(self.instrument_combo)

        self.btn_do = QPushButton("Play a Do (C4)")
        self.btn_do.clicked.connect(lambda: self.synth.play_note(60, 1, channel=self.row_id))
        layout.addWidget(self.btn_do)

        self.btn_del = QPushButton("Delete instrument")
        layout.addWidget(self.btn_del)

        layout.addStretch()
