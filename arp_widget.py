import sys
import numpy as np
import sounddevice as sd
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QSlider,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QButtonGroup
)
from PySide6.QtCore import Qt
from arp import Arpeggiator, Mode


class ArpeggiatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Arp functionality
        default_rate = 1.  # BPM multiplier
        default_note_len = 0.2
        default_ground_note = 60  # Midi C4
        default_mode = Mode.UP
        default_variants_active = [False, False, False]
        default_variants = [0, 0, 0]
        self.arp = Arpeggiator(
            default_rate,
            default_note_len,
            default_ground_note,
            default_mode,
            default_variants_active,
            default_variants
        )

        # Layout
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ==================== 1) Rate (x BPM) [Discrete: 0.5, 1, 2, 4, 8, 16, 32, 64] ====================
        self.rate_values = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]

        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(0, len(self.rate_values) - 1)
        self.rate_slider.setValue(self.rate_values.index(default_rate))  # default to '1.0'

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(min(self.rate_values), max(self.rate_values))
        self.rate_spin.setDecimals(2)
        self.rate_spin.setSingleStep(0.5)
        self.rate_spin.setValue(default_rate)

        row_layout_rate = QHBoxLayout()
        row_layout_rate.addWidget(self.rate_slider)
        row_layout_rate.addWidget(self.rate_spin)
        form_layout.addRow("Rate (x BPM):         ", row_layout_rate)

        self.rate_slider.valueChanged.connect(self.on_rate_slider_changed)
        self.rate_spin.valueChanged.connect(self.on_rate_spin_changed)

        # ==================== 2) Note Length [0..1, step=0.1] ====================
        self.note_length_slider = QSlider(Qt.Orientation.Horizontal)
        self.note_length_slider.setRange(0, 10)  # each step => 0.1
        self.note_length_slider.setValue(default_note_len * 10)      # default = 0.5

        self.note_length_spin = QDoubleSpinBox()
        self.note_length_spin.setRange(0.0, 1.0)
        self.note_length_spin.setDecimals(1)
        self.note_length_spin.setSingleStep(0.1)
        self.note_length_spin.setValue(default_note_len)

        row_layout_note_length = QHBoxLayout()
        row_layout_note_length.addWidget(self.note_length_slider)
        row_layout_note_length.addWidget(self.note_length_spin)
        form_layout.addRow("Note Length:", row_layout_note_length)

        self.note_length_slider.valueChanged.connect(self.on_note_length_slider_changed)
        self.note_length_spin.valueChanged.connect(self.on_note_length_spin_changed)

        # ==================== 3) Ground Note [C3 (48) to C5 (72)] ====================
        self.ground_note_slider = QSlider(Qt.Orientation.Horizontal)
        self.ground_note_slider.setRange(48, 72)  # C3 to C5
        self.ground_note_slider.setValue(default_ground_note)

        self.ground_note_spin = QSpinBox()
        self.ground_note_spin.setRange(48, 72)
        self.ground_note_spin.setValue(default_ground_note)

        self.ground_note_label = QLabel(f"Ground note {self.midi_to_note_name(default_ground_note)}:")

        row_layout_ground_note = QHBoxLayout()
        row_layout_ground_note.addWidget(self.ground_note_slider)
        row_layout_ground_note.addWidget(self.ground_note_spin)
        form_layout.addRow(self.ground_note_label, row_layout_ground_note)

        self.ground_note_slider.valueChanged.connect(self.on_ground_note_slider_changed)
        self.ground_note_spin.valueChanged.connect(self.on_ground_note_spin_changed)

        # ==================== MODE (Up, Down, Random) EXCLUSIVE BUTTONS ====================
        self.mode_layout = QHBoxLayout()

        # Create a button group for exclusive checkable buttons
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(True)

        self.btn_up = QPushButton("Up")
        self.btn_down = QPushButton("Down")
        self.btn_random = QPushButton("Random")

        # Make them checkable
        self.btn_up.setCheckable(True)
        self.btn_down.setCheckable(True)
        self.btn_random.setCheckable(True)

        # Add them to the button group
        self.mode_button_group.addButton(self.btn_up)
        self.mode_button_group.addButton(self.btn_down)
        self.mode_button_group.addButton(self.btn_random)

        # Set default selection
        self.btn_up.setChecked(default_mode == Mode.UP)
        self.btn_down.setChecked(default_mode == Mode.DOWN)
        self.btn_random.setChecked(default_mode == Mode.RANDOM)

        # Add them horizontally
        self.mode_layout.addWidget(self.btn_up)
        self.mode_layout.addWidget(self.btn_down)
        self.mode_layout.addWidget(self.btn_random)

        # Add row to form layout
        form_layout.addRow("Mode:", self.mode_layout)

        # ==================== ACTIVATION BUTTONS (Variants Active) ====================
        activation_layout = QHBoxLayout()

        self.variant1_button = QPushButton("Variant 1")
        self.variant1_button.setCheckable(True)
        self.variant1_button.setChecked(default_variants_active[0])  # default on
        self.update_button_color(self.variant1_button, default_variants_active[0])
        self.variant1_button.toggled.connect(lambda checked: self.update_button_color(self.variant1_button, checked))

        self.variant2_button = QPushButton("Variant 2")
        self.variant2_button.setCheckable(True)
        self.variant2_button.setChecked(default_variants_active[1])  # default off
        self.update_button_color(self.variant2_button, default_variants_active[1])
        self.variant2_button.toggled.connect(lambda checked: self.update_button_color(self.variant2_button, checked))

        self.variant3_button = QPushButton("Variant 3")
        self.variant3_button.setCheckable(True)
        self.variant3_button.setChecked(default_variants_active[2])  # default off
        self.update_button_color(self.variant3_button, default_variants_active[2])
        self.variant3_button.toggled.connect(lambda checked: self.update_button_color(self.variant3_button, checked))

        activation_layout.addWidget(self.variant1_button)
        activation_layout.addWidget(self.variant2_button)
        activation_layout.addWidget(self.variant3_button)

        form_layout.addRow("Variants Active:", activation_layout)

        # ==================== Variant Offsets: -24..24, integer steps ====================
        self.variant1_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant1_slider.setRange(-24, 24)
        self.variant1_slider.setValue(default_variants[0])

        self.variant1_spin = QSpinBox()
        self.variant1_spin.setRange(-24, 24)
        self.variant1_spin.setValue(default_variants[0])

        row_layout_variant1 = QHBoxLayout()
        row_layout_variant1.addWidget(self.variant1_slider)
        row_layout_variant1.addWidget(self.variant1_spin)
        form_layout.addRow("Variant 1 offset:", row_layout_variant1)

        self.variant1_slider.valueChanged.connect(self.on_variant1_slider_changed)
        self.variant1_spin.valueChanged.connect(self.on_variant1_spin_changed)

        self.variant2_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant2_slider.setRange(-24, 24)
        self.variant2_slider.setValue(default_variants[1])

        self.variant2_spin = QSpinBox()
        self.variant2_spin.setRange(-24, 24)
        self.variant2_spin.setValue(default_variants[1])

        row_layout_variant2 = QHBoxLayout()
        row_layout_variant2.addWidget(self.variant2_slider)
        row_layout_variant2.addWidget(self.variant2_spin)
        form_layout.addRow("Variant 2 offset:", row_layout_variant2)

        self.variant2_slider.valueChanged.connect(self.on_variant2_slider_changed)
        self.variant2_spin.valueChanged.connect(self.on_variant2_spin_changed)

        self.variant3_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant3_slider.setRange(-24, 24)
        self.variant3_slider.setValue(default_variants[2])

        self.variant3_spin = QSpinBox()
        self.variant3_spin.setRange(-24, 24)
        self.variant3_spin.setValue(default_variants[2])

        row_layout_variant3 = QHBoxLayout()
        row_layout_variant3.addWidget(self.variant3_slider)
        row_layout_variant3.addWidget(self.variant3_spin)
        form_layout.addRow("Variant 3 offset:", row_layout_variant3)

        self.variant3_slider.valueChanged.connect(self.on_variant3_slider_changed)
        self.variant3_spin.valueChanged.connect(self.on_variant3_spin_changed)

        main_layout.addLayout(form_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Arpeggiator (Mode + Variant Activation)")

    # ---------------------------------------------------------------------------------------
    # Helper to change button color for Variant toggles
    # ---------------------------------------------------------------------------------------
    def update_button_color(self, button: QPushButton, checked: bool):
        if checked:
            button.setStyleSheet("background-color: green;")
        else:
            button.setStyleSheet("background-color: red;")

    # ---------------------------------------------------------------------------------------
    # RATE
    # ---------------------------------------------------------------------------------------
    def on_rate_slider_changed(self, index: int):
        chosen_rate = self.rate_values[index]
        self.rate_spin.blockSignals(True)
        self.rate_spin.setValue(chosen_rate)
        self.rate_spin.blockSignals(False)

    def on_rate_spin_changed(self, spin_value: float):
        chosen_rate = self.closest_in_list(spin_value, self.rate_values)
        self.rate_spin.blockSignals(True)
        self.rate_spin.setValue(chosen_rate)
        self.rate_spin.blockSignals(False)
        index = self.rate_values.index(chosen_rate)
        self.rate_slider.blockSignals(True)
        self.rate_slider.setValue(index)
        self.rate_slider.blockSignals(False)

    def closest_in_list(self, value, valid_list):
        return min(valid_list, key=lambda x: abs(x - value))

    # ---------------------------------------------------------------------------------------
    # NOTE LENGTH
    # ---------------------------------------------------------------------------------------
    def on_note_length_slider_changed(self, slider_value: int):
        length = slider_value * 0.1
        self.note_length_spin.blockSignals(True)
        self.note_length_spin.setValue(length)
        self.note_length_spin.blockSignals(False)

    def on_note_length_spin_changed(self, spin_value: float):
        snapped = round(spin_value, 1)
        snapped = min(max(snapped, 0.0), 1.0)

        self.note_length_spin.blockSignals(True)
        self.note_length_spin.setValue(snapped)
        self.note_length_spin.blockSignals(False)

        slider_val = int(snapped * 10)
        self.note_length_slider.blockSignals(True)
        self.note_length_slider.setValue(slider_val)
        self.note_length_slider.blockSignals(False)

    # ---------------------------------------------------------------------------------------
    # GROUND NOTE
    # ---------------------------------------------------------------------------------------
    def on_ground_note_slider_changed(self, slider_value: int):
        self.ground_note_spin.blockSignals(True)
        self.ground_note_spin.setValue(slider_value)
        self.ground_note_spin.blockSignals(False)
        self.update_ground_note_label(slider_value)

    def on_ground_note_spin_changed(self, spin_value: int):
        self.ground_note_slider.blockSignals(True)
        self.ground_note_slider.setValue(spin_value)
        self.ground_note_slider.blockSignals(False)
        self.update_ground_note_label(spin_value)

    def update_ground_note_label(self, midi_note: int):
        note_name = self.midi_to_note_name(midi_note)
        self.ground_note_label.setText(f"Ground note {note_name}:")

    def midi_to_note_name(self, midi_note: int) -> str:
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = notes[midi_note % 12]
        return f"{note}{octave}"

    # ---------------------------------------------------------------------------------------
    # VARIANT 1, 2, 3 OFFSETS
    # ---------------------------------------------------------------------------------------
    def on_variant1_slider_changed(self, slider_value: int):
        self.variant1_spin.blockSignals(True)
        self.variant1_spin.setValue(slider_value)
        self.variant1_spin.blockSignals(False)

    def on_variant1_spin_changed(self, spin_value: int):
        self.variant1_slider.blockSignals(True)
        self.variant1_slider.setValue(spin_value)
        self.variant1_slider.blockSignals(False)

    def on_variant2_slider_changed(self, slider_value: int):
        self.variant2_spin.blockSignals(True)
        self.variant2_spin.setValue(slider_value)
        self.variant2_spin.blockSignals(False)

    def on_variant2_spin_changed(self, spin_value: int):
        self.variant2_slider.blockSignals(True)
        self.variant2_slider.setValue(spin_value)
        self.variant2_slider.blockSignals(False)

    def on_variant3_slider_changed(self, slider_value: int):
        self.variant3_spin.blockSignals(True)
        self.variant3_spin.setValue(slider_value)
        self.variant3_spin.blockSignals(False)

    def on_variant3_spin_changed(self, spin_value: int):
        self.variant3_slider.blockSignals(True)
        self.variant3_slider.setValue(spin_value)
        self.variant3_slider.blockSignals(False)

def main():
    app = QApplication(sys.argv)
    window = ArpeggiatorWidget()
    window.resize(600, 300)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
