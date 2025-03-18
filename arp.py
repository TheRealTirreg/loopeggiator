import sys
import math

# For PySide6, just change the imports accordingly
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QSlider,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QDoubleSpinBox,
    QSpinBox
)
from PySide6.QtCore import Qt

class ArpeggiatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ==================== 1) Rate (x BPM) [Discrete: 0.5, 1, 2, 4, 8, 16, 32, 64] ====================
        self.rate_values = [0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
        
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(0, len(self.rate_values) - 1)
        self.rate_slider.setValue(self.rate_values.index(1.0))  # default to '1.0'
        
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(min(self.rate_values), max(self.rate_values))
        self.rate_spin.setDecimals(2)
        self.rate_spin.setSingleStep(0.5)  
        self.rate_spin.setValue(1.0)

        row_layout_rate = QHBoxLayout()
        row_layout_rate.addWidget(self.rate_slider)
        row_layout_rate.addWidget(self.rate_spin)
        form_layout.addRow("Rate (x BPM):", row_layout_rate)

        # Signals
        self.rate_slider.valueChanged.connect(self.on_rate_slider_changed)
        self.rate_spin.valueChanged.connect(self.on_rate_spin_changed)

        # ==================== 2) Note Length [0..1, step=0.1] ====================
        self.note_length_slider = QSlider(Qt.Orientation.Horizontal)
        self.note_length_slider.setRange(0, 10)  # integer steps => 0..10 => 0.0..1.0
        self.note_length_slider.setValue(5)      # default: 0.5
        
        self.note_length_spin = QDoubleSpinBox()
        self.note_length_spin.setRange(0.0, 1.0)
        self.note_length_spin.setDecimals(1)
        self.note_length_spin.setSingleStep(0.1)
        self.note_length_spin.setValue(0.5)

        row_layout_note_length = QHBoxLayout()
        row_layout_note_length.addWidget(self.note_length_slider)
        row_layout_note_length.addWidget(self.note_length_spin)
        form_layout.addRow("Note Length:", row_layout_note_length)

        self.note_length_slider.valueChanged.connect(self.on_note_length_slider_changed)
        self.note_length_spin.valueChanged.connect(self.on_note_length_spin_changed)

        # ==================== 3) Number of Variants [0..3, integer] ====================
        self.num_variants_slider = QSlider(Qt.Orientation.Horizontal)
        self.num_variants_slider.setRange(0, 3)
        self.num_variants_slider.setValue(0)
        
        self.num_variants_spin = QSpinBox()
        self.num_variants_spin.setRange(0, 3)
        self.num_variants_spin.setValue(0)

        row_layout_variants = QHBoxLayout()
        row_layout_variants.addWidget(self.num_variants_slider)
        row_layout_variants.addWidget(self.num_variants_spin)
        form_layout.addRow("Number of Variants:", row_layout_variants)

        self.num_variants_slider.valueChanged.connect(self.on_num_variants_slider_changed)
        self.num_variants_spin.valueChanged.connect(self.on_num_variants_spin_changed)

        # ==================== 4) Variant 1 [-24..24, integer] ====================
        self.variant1_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant1_slider.setRange(-24, 24)
        self.variant1_slider.setValue(0)
        
        self.variant1_spin = QSpinBox()
        self.variant1_spin.setRange(-24, 24)
        self.variant1_spin.setValue(0)

        row_layout_variant1 = QHBoxLayout()
        row_layout_variant1.addWidget(self.variant1_slider)
        row_layout_variant1.addWidget(self.variant1_spin)
        form_layout.addRow("Variant 1:", row_layout_variant1)

        self.variant1_slider.valueChanged.connect(self.on_variant1_slider_changed)
        self.variant1_spin.valueChanged.connect(self.on_variant1_spin_changed)

        # ==================== 5) Variant 2 [-24..24, integer] ====================
        self.variant2_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant2_slider.setRange(-24, 24)
        self.variant2_slider.setValue(0)
        
        self.variant2_spin = QSpinBox()
        self.variant2_spin.setRange(-24, 24)
        self.variant2_spin.setValue(0)

        row_layout_variant2 = QHBoxLayout()
        row_layout_variant2.addWidget(self.variant2_slider)
        row_layout_variant2.addWidget(self.variant2_spin)
        form_layout.addRow("Variant 2:", row_layout_variant2)

        self.variant2_slider.valueChanged.connect(self.on_variant2_slider_changed)
        self.variant2_spin.valueChanged.connect(self.on_variant2_spin_changed)

        # ==================== 6) Variant 3 [-24..24, integer] ====================
        self.variant3_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant3_slider.setRange(-24, 24)
        self.variant3_slider.setValue(0)
        
        self.variant3_spin = QSpinBox()
        self.variant3_spin.setRange(-24, 24)
        self.variant3_spin.setValue(0)

        row_layout_variant3 = QHBoxLayout()
        row_layout_variant3.addWidget(self.variant3_slider)
        row_layout_variant3.addWidget(self.variant3_spin)
        form_layout.addRow("Variant 3:", row_layout_variant3)

        self.variant3_slider.valueChanged.connect(self.on_variant3_slider_changed)
        self.variant3_spin.valueChanged.connect(self.on_variant3_spin_changed)

        main_layout.addLayout(form_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Arpeggiator (Discrete Steps)")

    # -------------------------------------------------------------------
    # RATE: Use discrete values from rate_values.
    # Slider index -> actual rate, SpinBox -> closest in rate_values.
    # -------------------------------------------------------------------
    def on_rate_slider_changed(self, index: int):
        """When the slider moves, pick the corresponding discrete rate."""
        chosen_rate = self.rate_values[index]
        self.rate_spin.blockSignals(True)
        self.rate_spin.setValue(chosen_rate)
        self.rate_spin.blockSignals(False)
    
    def on_rate_spin_changed(self, spin_value: float):
        """
        When the spin box changes, snap to the closest discrete entry in rate_values.
        """
        chosen_rate = self.closest_in_list(spin_value, self.rate_values)
        # Update spin to the discrete value (in case user typed something else)
        self.rate_spin.blockSignals(True)
        self.rate_spin.setValue(chosen_rate)
        self.rate_spin.blockSignals(False)
        # Also update the slider index
        index = self.rate_values.index(chosen_rate)
        self.rate_slider.blockSignals(True)
        self.rate_slider.setValue(index)
        self.rate_slider.blockSignals(False)

    def closest_in_list(self, value, valid_list):
        """Return the closest item in `valid_list` to the given `value`."""
        return min(valid_list, key=lambda x: abs(x - value))

    # -------------------------------------------------------------------
    # NOTE LENGTH: 0..1 in steps of 0.1
    # -------------------------------------------------------------------
    def on_note_length_slider_changed(self, slider_value: int):
        # slider_value in [0..10] => 0.0..1.0 in steps of 0.1
        length = slider_value * 0.1
        self.note_length_spin.blockSignals(True)
        self.note_length_spin.setValue(length)
        self.note_length_spin.blockSignals(False)

    def on_note_length_spin_changed(self, spin_value: float):
        # Snap typed value to 0.1 steps
        # e.g. rounding to 1 decimal
        snapped = round(spin_value, 1)
        # Also clamp if user typed >1.0 or <0.0:
        snapped = min(max(snapped, 0.0), 1.0)

        self.note_length_spin.blockSignals(True)
        self.note_length_spin.setValue(snapped)
        self.note_length_spin.blockSignals(False)

        slider_val = int(snapped * 10)
        self.note_length_slider.blockSignals(True)
        self.note_length_slider.setValue(slider_val)
        self.note_length_slider.blockSignals(False)

    # -------------------------------------------------------------------
    # NUMBER OF VARIANTS: integer 0..3
    # -------------------------------------------------------------------
    def on_num_variants_slider_changed(self, slider_value: int):
        self.num_variants_spin.blockSignals(True)
        self.num_variants_spin.setValue(slider_value)
        self.num_variants_spin.blockSignals(False)

    def on_num_variants_spin_changed(self, spin_value: int):
        self.num_variants_slider.blockSignals(True)
        self.num_variants_slider.setValue(spin_value)
        self.num_variants_slider.blockSignals(False)

    # -------------------------------------------------------------------
    # VARIANT #1, #2, #3: integer -24..24
    # -------------------------------------------------------------------
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
    window.resize(550, 300)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
