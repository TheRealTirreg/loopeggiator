# arp_widget.py
import sys
import mido
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QButtonGroup,
    QSizePolicy,
    QCheckBox,
    QSpacerItem,
    QStyle,
    QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, Slot
from PySide6.QtGui import QColor
from arp import Arpeggiator, Mode
from custom_widgets import NoScrollSlider, NoScrollDoubleSpinBox, MuteSpinBox, GroundNoteSpinBox


class ArpeggiatorBlockWidget(QWidget):
    """
    A small widget containing:
      - SpinBox for loop count
      - One ArpeggiatorWidget
      - Surrounded by a tight QFrame
    """
    play_time_changed = Signal()
    mute_change = Signal()

    minimal_block_width = 500  # Minimum width (in pixel) for the arpeggiator block

    def __init__(
        self,
        parent=None,
        id=0,
        velocity=64,
        rate=1.0,
        note_length=0.2,
        ground_note=60,
        mute_ground_note=False,
        mode=None,
        mute=False,
        vibrato=False,
        reverb=False,
        chorus=False,
        variants_active=None,
        chords_active=None,
        variants=None,
        volume_line_signal=None
    ):
        if variants_active is None:
            variants_active = [False, False, False]
        if chords_active is None:
            chords_active = [False, False, False]
        if variants is None:
            variants = [0, 0, 0]

        self.id = id
        self.velocity = velocity
        self._parent = parent

        # ========================= Layout Setup =========================
        super().__init__(parent)

        # Let this widget shrink to fit content (rather than fill spare space).
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Outer layout for this entire block
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Frame so we get a box around each arpeggiator
        self.frame = QFrame()
        self.frame.setObjectName("arp_frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        
        # Outer frame that wraps everything
        self.frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        # Align the frame to the left inside the block
        outer_layout.setAlignment(self.frame, Qt.AlignmentFlag.AlignLeft)

        # Put content into the frame's layout
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)

        # Top row for buttons
        top_row_layout = QHBoxLayout()

        # Duplicate button
        self.duplicate_label = QLabel("Duplicate:")
        self.btn_duplicate = QPushButton("📄")
        self.btn_duplicate.setToolTip("Duplicate this arpeggiator block")
        self.btn_duplicate.setFixedSize(24, 24)
        self.btn_duplicate.clicked.connect(self.duplicate_block)

        # Move left button
        self.move_left_button = QPushButton()
        self.move_left_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.move_left_button.setIconSize(QSize(16, 16))
        self.move_left_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.move_left_button.clicked.connect(self.move_left)

        # Move right button
        self.move_right_button = QPushButton()
        self.move_right_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        self.move_right_button.setIconSize(QSize(16, 16))
        self.move_right_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.move_right_button.clicked.connect(self.move_right)

        # delete button
        spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.delete_button = QPushButton()  # Remplace par ton icône si nécessaire
        self.delete_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.delete_button.setIconSize(QSize(16, 16))
        self.delete_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.delete_button.clicked.connect(self.remove_block)

        # Add widgets side by side
        top_row_layout.addWidget(self.duplicate_label)
        top_row_layout.addWidget(self.btn_duplicate) 
        top_row_layout.addItem(spacer)
        top_row_layout.addWidget(self.move_left_button)
        top_row_layout.addWidget(self.move_right_button)
        top_row_layout.addWidget(self.delete_button)
    
        self.arp_widget = ArpeggiatorWidget(
            parent=self,
            velocity=velocity,
            rate=rate,
            note_length=note_length,
            ground_note=ground_note,
            mute_ground_note=mute_ground_note,
            mode=mode,
            mute=mute,
            vibrato=vibrato,
            reverb=reverb,
            chorus=chorus,
            variants_active=variants_active,
            chords_active=chords_active,
            variants=variants,
            volume_line_signal=volume_line_signal
        )

        # self.arp_widget.setFixedSize(QSize(300, 220))
        self.arp_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Add subwidgets to frame layout
        frame_layout.addLayout(top_row_layout)
        frame_layout.addWidget(self.arp_widget)

        # Finally, put the frame in the outer layout
        outer_layout.addWidget(self.frame)

        # Connect signals
        self.arp_widget.play_time_changed.connect(self._on_arp_widget_changed)

    def _on_arp_widget_changed(self):
        """Give signal from arp widget through to parent"""
        self.play_time_changed.emit()

    @property
    def rate(self):
        return self.arp_widget.rate
    
    def get_config(self):
        arp = self.arp_widget.arp
        return {
            "velocity": arp.velocity,
            "rate": arp.rate,
            "note_length": arp.note_length,
            "ground_note": arp.ground_note,
            "mute_ground_note": arp.mute_ground_note,
            "mode": arp.mode,
            "mute": arp.mute,
            "vibrato": arp.vibrato,
            "reverb": arp.reverb,
            "chorus": arp.chorus,
            "variants_active": arp.variants_active,
            "chords_active": arp.chords_active,
            "variants": arp.variants
        }
    
    def duplicate_block(self):
        if self._parent:
            config = self.get_config()
            self._parent.duplicate_arp_block(self, config)
    
    def update_size(self, arp_width):
        self.setFixedWidth(arp_width)
        self.arp_widget.setFixedWidth(arp_width)

    def get_arpeggio(self, bpm, instrument) -> tuple[list[mido.Message], int]:
        notes, duration = self.arp_widget.arp.get_arpeggio(bpm, instrument)
        block_id = f"{self._parent.row_container.id}#{self.id}"
        marker = mido.MetaMessage("marker", text=block_id, time=0)
        return [marker] + notes, duration
    
    def get_play_time(self, bpm) -> float:
        """Get the play time for this arpeggiator block"""
        # e.g.: If rate=2 => half the time
        total_time = (1 / self.arp_widget.arp.rate) * (60 / bpm)
        return total_time

    def move_left(self):
        if self._parent:
            self._parent.move_block_left(self)

    def move_right(self):
        if self._parent:
            self._parent.move_block_right(self)

    def remove_block(self):
        if self._parent:
            self._parent.remove_block(self)

    @Slot()
    def flash(self):
        try:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(20)
            effect.setOffset(0)
            effect.setColor(QColor("#E50046"))
            self.frame.setGraphicsEffect(effect)
            QTimer.singleShot(100, self.clear_flash)
        except Exception as e:
            print(f"Failed during flash: {e}")

    def clear_flash(self):
        self.frame.setGraphicsEffect(None)


class ArpeggiatorWidget(QWidget):
    play_time_changed = Signal()

    def __init__(
        self,
        parent=None,
        velocity=64,
        rate=1.0,  # BPM multiplier
        note_length=0.2,
        ground_note=60,  # Midi C4
        mute_ground_note=False,
        mode=None,
        mute=False,
        vibrato=False,
        reverb=False,
        chorus=False,
        variants_active=None,
        variants=None,
        chords_active=None,
        volume_line_signal=None
    ):
        if variants_active is None:
            variants_active = [False, False, False]
        if chords_active is None:
            chords_active = [False, False, False]
        if variants is None:
            variants = [0, 0, 0]

        super().__init__(parent)
        self._parent = parent

        if volume_line_signal:
            volume_line_signal.connect(self.change_arp_volume)

        self.arp = Arpeggiator(
            rate,
            note_length,
            ground_note,
            mute_ground_note,
            mode,
            mute,
            vibrato,
            reverb,
            chorus,
            velocity,
            variants_active,
            chords_active,
            variants
        )
        
        # Layout
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # === Mute & Vibrato on the same row ===
        checkbox_row = QHBoxLayout()

        self.mute_checkbox = QCheckBox("Mute")
        self.mute_checkbox.setChecked(mute)
        self.mute_checkbox.stateChanged.connect(self.on_mute_changed)

        self.vibrato_checkbox = QCheckBox("Vibrato")
        self.vibrato_checkbox.setChecked(vibrato)
        self.vibrato_checkbox.stateChanged.connect(self.on_vibrato_changed)

        self.reverb_checkbox = QCheckBox("Reverb")
        self.reverb_checkbox.setChecked(reverb)
        self.reverb_checkbox.stateChanged.connect(self.on_reverb_changed)

        self.chorus_checkbox = QCheckBox("Chorus")
        self.chorus_checkbox.setChecked(chorus)
        self.chorus_checkbox.stateChanged.connect(self.on_chorus_changed)

        checkbox_row.addWidget(self.mute_checkbox)
        checkbox_row.addWidget(self.vibrato_checkbox)
        checkbox_row.addWidget(self.reverb_checkbox)
        checkbox_row.addWidget(self.chorus_checkbox)

        form_layout.addRow(checkbox_row)
        # ==================== 1) Rate (x BPM) [Discrete: 0.5, 1, 2, 4, 8, 16, 32, 64] ====================
        self.rate_values = [0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]

        self.rate_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(0, len(self.rate_values) - 1)
        self.rate_slider.setValue(self.rate_values.index(rate))  # default to '1.0'

        self.rate_spin = NoScrollDoubleSpinBox()
        self.rate_spin.setRange(min(self.rate_values), max(self.rate_values))
        self.rate_spin.setDecimals(2)
        self.rate_spin.setSingleStep(0.5)
        self.rate_spin.setValue(rate)

        row_layout_rate = QHBoxLayout()
        row_layout_rate.addWidget(self.rate_slider)
        row_layout_rate.addWidget(self.rate_spin)
        form_layout.addRow("Rate (x BPM):         ", row_layout_rate)  # set width for whole column

        self.rate_slider.valueChanged.connect(self.on_rate_slider_changed)
        self.rate_spin.valueChanged.connect(self.on_rate_spin_changed)
        
        # ==================== 2) Note Length [0..1, step=0.1] ====================
        self.note_length_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.note_length_slider.setRange(0, 10)  # each step => 0.1
        self.note_length_slider.setValue(note_length * 10)      # set default value (e.g. 0.2)

        self.note_length_spin = NoScrollDoubleSpinBox()
        self.note_length_spin.setRange(0.0, 1.0)
        self.note_length_spin.setDecimals(1)
        self.note_length_spin.setSingleStep(0.1)
        self.note_length_spin.setValue(note_length)

        row_layout_note_length = QHBoxLayout()
        row_layout_note_length.addWidget(self.note_length_slider)
        row_layout_note_length.addWidget(self.note_length_spin)
        form_layout.addRow("Note Length:", row_layout_note_length)

        self.note_length_slider.valueChanged.connect(self.on_note_length_slider_changed)
        self.note_length_spin.valueChanged.connect(self.on_note_length_spin_changed)

        # ==================== 3) Ground Note [C1 (24) to C7 (96)] ====================
        self.ground_note_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.ground_note_slider.setRange(24, 96)  # C1 (24) to C7 (96)
        self.ground_note_slider.setValue(ground_note)

        self.ground_note_spin = GroundNoteSpinBox()
        self.ground_note_spin.setValue(ground_note)

        self.mute_ground_checkbox = QCheckBox()
        self.mute_ground_checkbox.setChecked(False)
        self.mute_ground_checkbox.stateChanged.connect(self.on_mute_ground_note_changed)

        self.ground_note_label = QLabel(f"Ground note {self.midi_to_note_name(ground_note)}:")

        row_layout_ground_note = QHBoxLayout()
        row_layout_ground_note.addWidget(self.ground_note_slider)
        row_layout_ground_note.addWidget(self.mute_ground_checkbox)
        row_layout_ground_note.addWidget(self.ground_note_spin)

        form_layout.addRow(self.ground_note_label, row_layout_ground_note)

        self.ground_note_slider.valueChanged.connect(self.on_ground_note_slider_changed)
        self.ground_note_spin.valueChanged.connect(self.on_ground_note_spin_changed)

        # ==================== MODE (Up, Down, Random) EXCLUSIVE BUTTONS ====================
        self.mode_layout = QHBoxLayout()

        # Create a button group for exclusive checkable buttons
        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.setExclusive(False)

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
        self.btn_up.setChecked(mode == Mode.UP)
        self.btn_down.setChecked(mode == Mode.DOWN)
        self.btn_random.setChecked(mode == Mode.RANDOM)

        # Add them horizontally
        self.mode_layout.addWidget(self.btn_up)
        self.mode_layout.addWidget(self.btn_down)
        self.mode_layout.addWidget(self.btn_random)

        # Add row to form layout
        form_layout.addRow("Mode:", self.mode_layout)

        # Connect buttons to the same slot
        self.btn_up.clicked.connect(self.on_mode_button_clicked)
        self.btn_down.clicked.connect(self.on_mode_button_clicked)
        self.btn_random.clicked.connect(self.on_mode_button_clicked)

        # ==================== CHORD SHORTCUT BUTTONS =====================
        self.variant_layout = QHBoxLayout()

        # Create a button group for variants (non-exclusive, so user can toggle multiple)
        self.variant_button_group = QButtonGroup(self)
        self.variant_button_group.setExclusive(False)

        # Create buttons
        self.btn_major = QPushButton("major")
        self.btn_minor = QPushButton("minor")
        self.btn_penta = QPushButton("pentatonic")

        # Make them checkable
        self.btn_major.setCheckable(True)
        self.btn_minor.setCheckable(True)
        self.btn_penta.setCheckable(True)

        # Set initial checked states from chords_active
        self.btn_major.setChecked(chords_active[0])
        self.btn_minor.setChecked(chords_active[1])
        self.btn_penta.setChecked(chords_active[2])

        # Add buttons to button group
        self.variant_button_group.addButton(self.btn_major)
        self.variant_button_group.addButton(self.btn_minor)
        self.variant_button_group.addButton(self.btn_penta)

        # Update button colors initially
        self.update_button_color(self.btn_major, chords_active[0])
        self.update_button_color(self.btn_minor, chords_active[1])
        self.update_button_color(self.btn_penta, chords_active[2])

        # Connect toggles to handlers
        self.btn_major.toggled.connect(self.on_major_button_toggled)
        self.btn_minor.toggled.connect(self.on_minor_button_toggled)
        self.btn_penta.toggled.connect(self.on_penta_button_toggled)

        # Add buttons to layout
        self.variant_layout.addWidget(self.btn_major)
        self.variant_layout.addWidget(self.btn_minor)
        self.variant_layout.addWidget(self.btn_penta)

        # Add to form layout
        form_layout.addRow("Chords:", self.variant_layout)

        # ==================== Variant Offsets: -24..24, integer steps ====================
        self.variant1_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.variant1_slider.setRange(-25, 24)
        self.variant1_slider.setValue(variants[0])

        self.variant1_spin = MuteSpinBox()
        self.variant1_spin.setValue(variants[0])

        row_layout_variant1 = QHBoxLayout()
        self.active1_checkbox = QCheckBox()
        self.active1_checkbox.setChecked(variants_active[0])
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges inutiles
        label_layout.addWidget(QLabel("Variant 1:"))
        label_layout.addWidget(self.active1_checkbox)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)

        row_layout_variant1.addWidget(self.variant1_slider)
        row_layout_variant1.addWidget(self.variant1_spin)
        self.active1_checkbox.stateChanged.connect(lambda checked: self.on_variant1_checkbox_toggled(checked))

        form_layout.addRow(label_widget, row_layout_variant1)
        self.variant1_slider.valueChanged.connect(self.on_variant1_slider_changed)
        self.variant1_spin.valueChanged.connect(self.on_variant1_spin_changed)

        self.variant2_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.variant2_slider.setRange(-25, 24)
        self.variant2_slider.setValue(variants[1])

        self.variant2_spin = MuteSpinBox()
        self.variant2_spin.setValue(variants[1])

        row_layout_variant2 = QHBoxLayout()
        self.active2_checkbox = QCheckBox()
        self.active2_checkbox.setChecked(variants_active[1])
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges inutiles
        label_layout.addWidget(QLabel("Variant 2:"))
        label_layout.addWidget(self.active2_checkbox)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)

        row_layout_variant2.addWidget(self.variant2_slider)
        row_layout_variant2.addWidget(self.variant2_spin)
        self.active2_checkbox.stateChanged.connect(lambda checked: self.on_variant2_checkbox_toggled(checked))

        form_layout.addRow(label_widget, row_layout_variant2)
        
        self.variant2_slider.valueChanged.connect(self.on_variant2_slider_changed)
        self.variant2_spin.valueChanged.connect(self.on_variant2_spin_changed)

        self.variant3_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.variant3_slider.setRange(-25, 24)
        self.variant3_slider.setValue(variants[2])

        self.variant3_spin = MuteSpinBox()
        self.variant3_spin.setValue(variants[2])

        row_layout_variant3 = QHBoxLayout()
        self.active3_checkbox = QCheckBox()
        self.active3_checkbox.setChecked(variants_active[2])
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges inutiles
        label_layout.addWidget(QLabel("Variant 3:"))
        label_layout.addWidget(self.active3_checkbox)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)

        row_layout_variant3.addWidget(self.variant3_slider)
        row_layout_variant3.addWidget(self.variant3_spin)
        self.active3_checkbox.stateChanged.connect(lambda checked: self.on_variant3_checkbox_toggled(checked))

        form_layout.addRow(label_widget, row_layout_variant3)

        self.variant3_slider.valueChanged.connect(self.on_variant3_slider_changed)
        self.variant3_spin.valueChanged.connect(self.on_variant3_spin_changed)

        main_layout.addLayout(form_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Arpeggiator (Mode + Variant Activation)")

    @property
    def rate(self):
        return self.arp.rate

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
        self.arp.rate = chosen_rate
        self.play_time_changed.emit()  # Emit signal to update play time

    def on_rate_spin_changed(self, spin_value: float):
        chosen_rate = self.closest_in_list(spin_value, self.rate_values)
        self.rate_spin.blockSignals(True)
        self.rate_spin.setValue(chosen_rate)
        self.rate_spin.blockSignals(False)
        index = self.rate_values.index(chosen_rate)
        self.rate_slider.blockSignals(True)
        self.rate_slider.setValue(index)
        self.rate_slider.blockSignals(False)
        self.arp.rate = chosen_rate
        self.play_time_changed.emit()  # Emit signal to update play time

    def closest_in_list(self, value, valid_list):
        return min(valid_list, key=lambda x: abs(x - value))
    
    # ---------------------------------------------------------------------------------------
    # Mute changed
    # ---------------------------------------------------------------------------------------
    def on_mute_changed(self, state: int):
        checked = state == 2  # Qt.Checked
        self.arp.mute = checked
        
    def change_arp_volume(self):
        self.arp.velocity = self._parent.velocity

    # ---------------------------------------------------------------------------------------
    # Vibrato changed
    # ---------------------------------------------------------------------------------------
    def on_vibrato_changed(self, state: int):
        checked = state == 2
        self.arp.vibrato = checked

    # ---------------------------------------------------------------------------------------
    # Chorus changed
    # ---------------------------------------------------------------------------------------
    def on_chorus_changed(self, state: int):
        checked = state == 2
        self.arp.chorus = checked
        
    # ---------------------------------------------------------------------------------------
    # Reverb changed
    # ---------------------------------------------------------------------------------------
    def on_reverb_changed(self, state: int):
        checked = state == 2
        self.arp.reverb = checked

    # ---------------------------------------------------------------------------------------
    # NOTE LENGTH
    # ---------------------------------------------------------------------------------------
    def on_note_length_slider_changed(self, slider_value: int):
        length = slider_value * 0.1
        self.note_length_spin.blockSignals(True)
        self.note_length_spin.setValue(length)
        self.note_length_spin.blockSignals(False)
        self.arp.note_length = length

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
        self.arp.note_length = snapped

    # ---------------------------------------------------------------------------------------
    # GROUND NOTE
    # ---------------------------------------------------------------------------------------
    def on_ground_note_slider_changed(self, slider_value: int):
        self.ground_note_spin.blockSignals(True)
        self.ground_note_spin.setValue(slider_value)
        self.ground_note_spin.blockSignals(False)
        self.update_ground_note_label(slider_value)
        self.arp.ground_note = slider_value
        self.update_chord_button_states()

    def on_ground_note_spin_changed(self, spin_value: int):
        self.ground_note_slider.blockSignals(True)
        self.ground_note_slider.setValue(spin_value)
        self.ground_note_slider.blockSignals(False)
        self.update_ground_note_label(spin_value)
        self.arp.ground_note = spin_value
        self.update_chord_button_states()

    def update_ground_note_label(self, midi_note: int):
        note_name = self.midi_to_note_name(midi_note)
        self.ground_note_label.setText(f"Ground note {note_name}:")

    def midi_to_note_name(self, midi_note: int) -> str:
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = notes[midi_note % 12]
        return f"{note}{octave}"
    
    def on_mute_ground_note_changed(self, state: int):
        checked = state == 2  # Qt.Checked
        self.arp.mute_ground_note = checked
    
    # ---------------------------------------------------------------------------------------
    # MODE
    # ---------------------------------------------------------------------------------------
    def on_mode_button_clicked(self):
        sender = self.sender()
        clicked_mode = self.get_mode_from_button(sender)

        if self.arp.mode == clicked_mode:
            # Toggle OFF: same mode clicked again
            self.arp.mode = None
            for btn in self.mode_button_group.buttons():
                btn.setChecked(False)
        else:
            # Toggle ON: different mode clicked
            self.arp.mode = clicked_mode
            for btn in self.mode_button_group.buttons():
                btn.setChecked(btn == sender)

    def get_mode_from_button(self, button):
        if button == self.btn_up:
            return Mode.UP
        elif button == self.btn_down:
            return Mode.DOWN
        elif button == self.btn_random:
            return Mode.RANDOM
        return None

    # ---------------------------------------------------------------------------------------
    # VARIANT 1, 2, 3 ACTIVATION
    # ---------------------------------------------------------------------------------------
    def on_variant1_checkbox_toggled(self, checked: int):
        checked = checked == 2  # Qt.Checked
        self.arp.variants_active[0] = checked
        self.update_chord_button_states()

    def on_variant2_checkbox_toggled(self, checked: int):
        checked = checked == 2  # Qt.Checked
        self.arp.variants_active[1] = checked
        self.update_chord_button_states()

    def on_variant3_checkbox_toggled(self, checked: int):
        checked = checked == 2  # Qt.Checked
        self.arp.variants_active[2] = checked
        self.update_chord_button_states()

    # ---------------------------------------------------------------------------------------
    # CHORDS 1, 2, 3 ACTIVATION
    # ---------------------------------------------------------------------------------------
    major_scale = [2, 4, 5, 7, 9, 11, 12]       # C D E F G A B C
    minor_scale = [2, 3, 5, 7, 8, 10, 12]       # C D Eb F G Ab Bb C
    pentatonic_scale = {2, 4, 7, 9, 12}         # C D E G A C
    
    def on_major_button_toggled(self, checked: bool):
        self.handle_chord_button_pressed(index=0, checked=checked)

    def on_minor_button_toggled(self, checked: bool):
        self.handle_chord_button_pressed(index=1, checked=checked)

    def on_penta_button_toggled(self, checked: bool):
        self.handle_chord_button_pressed(index=2, checked=checked)

    def handle_chord_button_pressed(self, index: int, checked: bool):
        """Applies a triad or scale fragment when a chord button is pressed."""
        buttons = [self.btn_major, self.btn_minor, self.btn_penta]
        sliders = [self.variant1_slider, self.variant2_slider, self.variant3_slider]
        checkboxes = [self.active1_checkbox, self.active2_checkbox, self.active3_checkbox]

        triads = {
            0: [4, 7],  # Major triad
            1: [3, 7],  # Minor triad
            2: [2, 4, 7],  # Pentatonic fragment (C-D-E-G)
        }

        # Block button signals to avoid recursion
        for btn in buttons:
            btn.blockSignals(True)

        if checked:
            # Turn off other buttons
            for i, btn in enumerate(buttons):
                btn.setChecked(i == index)
                self.arp.chords_active[i] = (i == index)
                self.update_button_color(btn, i == index)

            # Apply chord pattern to first 3 variants
            intervals = triads[index]
            for i in range(3):
                active = i < len(intervals)
                checkboxes[i].setChecked(active)
                sliders[i].setValue(intervals[i] if active else 0)
                self.arp.variants_active[i] = active
                self.arp.variants[i] = intervals[i] if active else 0
        else:
            # Toggle off: deactivate all
            for i in range(3):
                checkboxes[i].setChecked(False)
                sliders[i].setValue(0)
                self.arp.variants_active[i] = False
                self.arp.variants[i] = 0
            self.arp.chords_active[index] = False
            self.update_button_color(buttons[index], False)

        for btn in buttons:
            btn.blockSignals(False)

        self.update_chord_button_states()

    def update_chord_button_states(self):
        """Visually highlight chord buttons if current variants match a known chord."""

        intervals = [
            self.arp.variants[i]
            for i in range(3)
            if self.arp.variants_active[i]
        ]
        intervals_set = set(intervals)

                # Pentatonic match = at least 3 intervals in penta set
        penta_set = {2, 4, 7, 9, 12, -3, -5, -7}
        is_penta = len(intervals_set & penta_set) >= 3

        # Major and minor are only valid if penta is not matched
        is_major = not is_penta and 4 in intervals_set and 7 in intervals_set
        is_minor = not is_penta and not is_major and 3 in intervals_set and 7 in intervals_set


        # Block button signals to avoid recursion
        self.btn_major.blockSignals(True)
        self.btn_minor.blockSignals(True)
        self.btn_penta.blockSignals(True)

        # Update button states + visuals
        self.btn_major.setChecked(is_major)
        self.update_button_color(self.btn_major, is_major)
        self.arp.chords_active[0] = is_major

        self.btn_minor.setChecked(is_minor)
        self.update_button_color(self.btn_minor, is_minor)
        self.arp.chords_active[1] = is_minor

        self.btn_penta.setChecked(is_penta)
        self.update_button_color(self.btn_penta, is_penta)
        self.arp.chords_active[2] = is_penta

        # Unblock signals
        self.btn_major.blockSignals(False)
        self.btn_minor.blockSignals(False)
        self.btn_penta.blockSignals(False)

    # ---------------------------------------------------------------------------------------
    # VARIANT 1, 2, 3 OFFSETS
    # ---------------------------------------------------------------------------------------
    def on_variant1_slider_changed(self, slider_value: int):
        self.variant1_spin.blockSignals(True)
        self.variant1_spin.setValue(slider_value)
        self.variant1_spin.blockSignals(False)
        self.arp.variants[0] = slider_value
        self.update_chord_button_states()

    def on_variant1_spin_changed(self, spin_value: int):
        self.variant1_slider.blockSignals(True)
        self.variant1_slider.setValue(spin_value)
        self.variant1_slider.blockSignals(False)
        self.arp.variants[0] = spin_value
        self.update_chord_button_states()

    def on_variant2_slider_changed(self, slider_value: int):
        self.variant2_spin.blockSignals(True)
        self.variant2_spin.setValue(slider_value)
        self.variant2_spin.blockSignals(False)
        self.arp.variants[1] = slider_value
        self.update_chord_button_states()

    def on_variant2_spin_changed(self, spin_value: int):
        self.variant2_slider.blockSignals(True)
        self.variant2_slider.setValue(spin_value)
        self.variant2_slider.blockSignals(False)
        self.arp.variants[1] = spin_value
        self.update_chord_button_states()

    def on_variant3_slider_changed(self, slider_value: int):
        self.variant3_spin.blockSignals(True)
        self.variant3_spin.setValue(slider_value)
        self.variant3_spin.blockSignals(False)
        self.arp.variants[2] = slider_value
        self.update_chord_button_states()

    def on_variant3_spin_changed(self, spin_value: int):
        self.variant3_slider.blockSignals(True)
        self.variant3_slider.setValue(spin_value)
        self.variant3_slider.blockSignals(False)
        self.arp.variants[2] = spin_value
        self.update_chord_button_states()

    # ---------------------------------------------------------------------------------------
    # VARIANTS again
    # ---------------------------------------------------------------------------------------
    def set_variants(self, active: list[bool], values: list[int]):
        """Set variant activations and offsets safely without toggling signals."""

        if len(active) != 3 or len(values) != 3:
            print(f"Warning: set_variants called with invalid data: {active}, {values}")
            return  # ignore malformed data

        self.arp.variants_active = active
        self.arp.variants = values

        # Variant 1
        self.active1_checkbox.blockSignals(True)
        self.active1_checkbox.setChecked(active[0])
        self.active1_checkbox.blockSignals(False)

        self.variant1_slider.blockSignals(True)
        self.variant1_slider.setValue(values[0])
        self.variant1_slider.blockSignals(False)

        self.variant1_spin.blockSignals(True)
        self.variant1_spin.setValue(values[0])
        self.variant1_spin.blockSignals(False)

        # Variant 2
        self.active2_checkbox.blockSignals(True)
        self.active2_checkbox.setChecked(active[1])
        self.active2_checkbox.blockSignals(False)

        self.variant2_slider.blockSignals(True)
        self.variant2_slider.setValue(values[1])
        self.variant2_slider.blockSignals(False)

        self.variant2_spin.blockSignals(True)
        self.variant2_spin.setValue(values[1])
        self.variant2_spin.blockSignals(False)

        # Variant 3
        self.active3_checkbox.blockSignals(True)
        self.active3_checkbox.setChecked(active[2])
        self.active3_checkbox.blockSignals(False)

        self.variant3_slider.blockSignals(True)
        self.variant3_slider.setValue(values[2])
        self.variant3_slider.blockSignals(False)

        self.variant3_spin.blockSignals(True)
        self.variant3_spin.setValue(values[2])
        self.variant3_spin.blockSignals(False)

        self.update_chord_button_states()


def main():
    app = QApplication(sys.argv)
    window = ArpeggiatorWidget()
    window.resize(600, 300)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
