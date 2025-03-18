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


class ArpeggiatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ==================== 1) Rate (x BPM) [Discrete: 0.5, 1, 2, 4, 8, 16, 32, 64] ====================
        self.rate_values = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
        
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

        self.rate_slider.valueChanged.connect(self.on_rate_slider_changed)
        self.rate_spin.valueChanged.connect(self.on_rate_spin_changed)

        # ==================== 2) Note Length [0..1, step=0.1] ====================
        self.note_length_slider = QSlider(Qt.Orientation.Horizontal)
        self.note_length_slider.setRange(0, 10)  # each step => 0.1
        self.note_length_slider.setValue(5)      # default = 0.5
        
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

        # Set default selection: "Up"
        self.btn_up.setChecked(True)

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
        self.variant1_button.setChecked(True)  # default on
        self.update_button_color(self.variant1_button, True)
        self.variant1_button.toggled.connect(lambda checked: self.update_button_color(self.variant1_button, checked))
        
        self.variant2_button = QPushButton("Variant 2")
        self.variant2_button.setCheckable(True)
        self.variant2_button.setChecked(False)  # default off
        self.update_button_color(self.variant2_button, False)
        self.variant2_button.toggled.connect(lambda checked: self.update_button_color(self.variant2_button, checked))
        
        self.variant3_button = QPushButton("Variant 3")
        self.variant3_button.setCheckable(True)
        self.variant3_button.setChecked(False)  # default off
        self.update_button_color(self.variant3_button, False)
        self.variant3_button.toggled.connect(lambda checked: self.update_button_color(self.variant3_button, checked))

        activation_layout.addWidget(self.variant1_button)
        activation_layout.addWidget(self.variant2_button)
        activation_layout.addWidget(self.variant3_button)

        form_layout.addRow("Variants Active:", activation_layout)

        # ==================== Variant Offsets: -24..24, integer steps ====================
        self.variant1_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant1_slider.setRange(-24, 24)
        self.variant1_slider.setValue(0)
        
        self.variant1_spin = QSpinBox()
        self.variant1_spin.setRange(-24, 24)
        self.variant1_spin.setValue(0)

        row_layout_variant1 = QHBoxLayout()
        row_layout_variant1.addWidget(self.variant1_slider)
        row_layout_variant1.addWidget(self.variant1_spin)
        form_layout.addRow("Variant 1 offset:", row_layout_variant1)

        self.variant1_slider.valueChanged.connect(self.on_variant1_slider_changed)
        self.variant1_spin.valueChanged.connect(self.on_variant1_spin_changed)

        self.variant2_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant2_slider.setRange(-24, 24)
        self.variant2_slider.setValue(0)
        
        self.variant2_spin = QSpinBox()
        self.variant2_spin.setRange(-24, 24)
        self.variant2_spin.setValue(0)

        row_layout_variant2 = QHBoxLayout()
        row_layout_variant2.addWidget(self.variant2_slider)
        row_layout_variant2.addWidget(self.variant2_spin)
        form_layout.addRow("Variant 2 offset:", row_layout_variant2)

        self.variant2_slider.valueChanged.connect(self.on_variant2_slider_changed)
        self.variant2_spin.valueChanged.connect(self.on_variant2_spin_changed)

        self.variant3_slider = QSlider(Qt.Orientation.Horizontal)
        self.variant3_slider.setRange(-24, 24)
        self.variant3_slider.setValue(0)
        
        self.variant3_spin = QSpinBox()
        self.variant3_spin.setRange(-24, 24)
        self.variant3_spin.setValue(0)

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
    # Do button plays a note Do
    # ---------------------------------------------------------------------------------------
        self.btn_do = QPushButton("Do")
        self.btn_do.clicked.connect(lambda: self.play_note(261.63))

        form_layout.addRow(self.btn_do)


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


    #---------------------------------------------------------------------------------------
    # Play note
    # ---------------------------------------------------------------------------------------
    
    def ADSR(self, duree, fe, A, D, S, R): # fonction créant une enveloppe ADSR
        t = np.linspace(0, duree, int(duree*fe))
        envelope = np.zeros(len(t))
        for i in range(0, len(t)):
            if t[i] < A:
                envelope[i] = t[i]/A
            elif t[i] < A+D:
                envelope[i] = 1 - (1-S)*(t[i]-A)/D
            elif t[i] < duree-R:
                envelope[i] = S
            else:
                envelope[i] = S - S*(t[i]-(duree-R))/R
        
        return envelope


    def play_note(self, frequency):
        
        duree = self.note_length_slider.value()  
        sample_rate = 44100  

        attack_time = 0.05
        decay_time = 0.1
        sustain_level = 0.7
        release_time = 0.2

        envelope = self.ADSR(duree, sample_rate, attack_time, decay_time, sustain_level, release_time)

        t = np.linspace(0, duree, int(sample_rate * duree), endpoint=False)
        audio_signal = 0.5 * np.sin(2 * np.pi * frequency * t)  

        audio_signal_with_envelope = audio_signal * envelope

        sd.play(audio_signal_with_envelope, samplerate=sample_rate)
        sd.wait()


    # ---------------------------------------------------------------------------------------
    # First arpeggio
    #----------------------------------------------------------------------------------------
    notes_freq = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
    def third(self, f):
        if self.btn_up.isChecked():
            
            for i in range(3):
                self.play_note(f)
                self.play_note(self.notes_freq[(self.notes_freq.index(f)+2) % 8])
                
        
        else:
            print("Not implemented yet")
            self.play_note(f)

    # ---------------------------------------------------------------------------------------
    # Keyboard shortcuts
    # ---------------------------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C:  # Touche "C" → Do
            self.third(261.63)
            #self.play_note(261.63)
        elif event.key() == Qt.Key_D:  # Touche "D" → Ré
            self.third(293.66)
            #self.play_note(293.66)
        elif event.key() == Qt.Key_E:  # Touche "E" → Mi
            self.third(329.63)
            #self.play_note(329.63)
        elif event.key() == Qt.Key_F:  # Touche "F" → Fa
            self.third(349.23)
            #self.play_note(349.23)
        elif event.key() == Qt.Key_G:  # Touche "G" → Sol
            self.third(392.00)
            #self.play_note(392.00)
        elif event.key() == Qt.Key_A:  # Touche "A" → La
            self.third(440.00)
            #self.play_note(440.00)
        elif event.key() == Qt.Key_B:  # Touche "B" → Si
            self.third(493.88)
            #self.play_note(493.88)
        elif event.key() == Qt.Key_N:  # Touche "N" → Do (octave supérieur)
            self.third(523.25)
            #self.play_note(523.25)
        else:
            super().keyPressEvent(event)

    

def main():
    app = QApplication(sys.argv)
    window = ArpeggiatorWidget()
    window.resize(600, 300)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
