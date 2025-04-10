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
from custom_widgets import NoScrollSlider, NoScrollSpinBox, NoScrollDoubleSpinBox, MuteSpinBox, GroundNoteSpinBox


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
        mode=Mode.UP,
        mute=False,
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
            mode=mode,
            mute=mute,
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
            "mode": arp.mode,
            "mute": arp.mute,
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
        mode=Mode.UP,
        mute=False,
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
            mode,
            mute,
            velocity,
            variants_active,
            chords_active,
            variants
        )
        
        # Layout
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        ## Mute box
        self.mute_checkbox = QCheckBox("Mute")
        self.mute_checkbox.setChecked(mute)
        self.mute_checkbox.stateChanged.connect(self.on_mute_changed)
        form_layout.addRow(self.mute_checkbox)
        # ==================== 1) Rate (x BPM) [Discrete: 0.5, 1, 2, 4, 8, 16, 32, 64] ====================
        self.rate_values = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]

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
        form_layout.addRow("Rate (x BPM):         ", row_layout_rate)

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

        # ==================== 3) Ground Note [C3 (48) to C5 (72)] ====================
        self.ground_note_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.ground_note_slider.setRange(47, 72)  # mute(47), then C3(48) to C5(72)
        self.ground_note_slider.setValue(ground_note)

        self.ground_note_spin = GroundNoteSpinBox()
        self.ground_note_spin.setValue(ground_note)

        self.ground_note_label = QLabel(f"Ground note {self.midi_to_note_name(ground_note)}:")

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

        # ==================== ACTIVATION BUTTONS (Variants Active) ====================
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
        self.btn_major.toggled.connect(lambda checked: self.on_major_button_toggled(checked))
        self.btn_minor.toggled.connect(lambda checked: self.on_minor_button_toggled(checked))
        self.btn_penta.toggled.connect(lambda checked: self.on_penta_button_toggled(checked))

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
        self.active1_checkbox.setChecked(False)
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges inutiles
        label_layout.addWidget(QLabel("Variant 1:"))
        label_layout.addWidget(self.active1_checkbox)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)

        row_layout_variant1.addWidget(self.variant1_slider)
        row_layout_variant1.addWidget(self.variant1_spin)
        self.active1_checkbox.stateChanged.connect(lambda checked: self.on_variant1_button_toggled(checked))

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
        self.active2_checkbox.setChecked(False)
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges inutiles
        label_layout.addWidget(QLabel("Variant 2:"))
        label_layout.addWidget(self.active2_checkbox)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)

        row_layout_variant2.addWidget(self.variant2_slider)
        row_layout_variant2.addWidget(self.variant2_spin)
        self.active2_checkbox.stateChanged.connect(lambda checked: self.on_variant2_button_toggled(checked))

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
        self.active3_checkbox.setChecked(False)
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)  # Pas de marges inutiles
        label_layout.addWidget(QLabel("Variant 3:"))
        label_layout.addWidget(self.active3_checkbox)
        label_widget = QWidget()
        label_widget.setLayout(label_layout)

        row_layout_variant3.addWidget(self.variant3_slider)
        row_layout_variant3.addWidget(self.variant3_spin)
        self.active3_checkbox.stateChanged.connect(lambda checked: self.on_variant3_button_toggled(checked))

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

    def on_ground_note_spin_changed(self, spin_value: int):
        self.ground_note_slider.blockSignals(True)
        self.ground_note_slider.setValue(spin_value)
        self.ground_note_slider.blockSignals(False)
        self.update_ground_note_label(spin_value)
        self.arp.ground_note = spin_value

    def update_ground_note_label(self, midi_note: int):
        note_name = self.midi_to_note_name(midi_note)
        self.ground_note_label.setText(f"Ground note {note_name}:")

    def midi_to_note_name(self, midi_note: int) -> str:
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = midi_note // 12 - 1
        note = notes[midi_note % 12]
        return f"{note}{octave}"
    
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
    def on_variant1_button_toggled(self, checked: bool):
        self.arp.variants_active[0] = checked
        #self.update_button_color(self.variant1_button, checked)

    def on_variant2_button_toggled(self, checked: bool):
        self.arp.variants_active[1] = checked
        #self.update_button_color(self.variant2_button, checked)

    def on_variant3_button_toggled(self, checked: bool):
        self.arp.variants_active[2] = checked
        #self.update_button_color(self.variant3_button, checked)


    # ---------------------------------------------------------------------------------------
    # CHORDS 1, 2, 3 ACTIVATION
    # ---------------------------------------------------------------------------------------
    major_scale = [2, 4, 5, 7, 9, 11, 12]       # C D E F G A B C
    minor_scale = [2, 3, 5, 7, 8, 10, 12]       # C D Eb F G Ab Bb C
    pentatonic_scale = [2, 4, 7, 9, 12]         # C D E G A C
    
    def on_major_button_toggled(self, checked: bool):
        self.handle_variant_toggle(index=0, checked=checked)

    def on_minor_button_toggled(self, checked: bool):
        self.handle_variant_toggle(index=1, checked=checked)

    def on_penta_button_toggled(self, checked: bool):
        self.handle_variant_toggle(index=2, checked=checked)

    def handle_variant_toggle(self, index: int, checked: bool):
        buttons = [self.btn_major, self.btn_minor, self.btn_penta]
        sliders = [self.variant1_slider, self.variant2_slider, self.variant3_slider]
        checkboxes = [self.active1_checkbox, self.active2_checkbox, self.active3_checkbox]
        scales = [self.major_scale, self.minor_scale, self.pentatonic_scale]

        if checked:
            # Set this one active, others off
            for i, btn in enumerate(buttons):
                state = (i == index)
                self.arp.chords_active[i] = state
                btn.setChecked(state)
                self.update_button_color(btn, state)

            # Activate all checkboxes and variant flags
            for i in range(3):
                self.arp.variants_active[i] = True
                checkboxes[i].setChecked(True)

            # Set scale preset
            for slider, val in zip(sliders, scales[index][:3]):
                slider.setValue(val)

        else:
            # Turn this chord type off
            self.arp.chords_active[index] = False
            self.update_button_color(buttons[index], False)

            # Check if all chord types are now off
            if not any(self.arp.chords_active):
                for i in range(3):
                    self.arp.variants_active[i] = False
                    checkboxes[i].setChecked(False)
                    sliders[i].setValue(0)


    # ---------------------------------------------------------------------------------------
    # VARIANT 1, 2, 3 OFFSETS
    # ---------------------------------------------------------------------------------------
    def on_variant1_slider_changed(self, slider_value: int):
        self.variant1_spin.blockSignals(True)
        self.variant1_spin.setValue(slider_value)
        self.variant1_spin.blockSignals(False)
        self.arp.variants[0] = slider_value

    def on_variant1_spin_changed(self, spin_value: int):
        self.variant1_slider.blockSignals(True)
        self.variant1_slider.setValue(spin_value)
        self.variant1_slider.blockSignals(False)
        self.arp.variants[0] = spin_value

    def on_variant2_slider_changed(self, slider_value: int):
        self.variant2_spin.blockSignals(True)
        self.variant2_spin.setValue(slider_value)
        self.variant2_spin.blockSignals(False)
        self.arp.variants[1] = slider_value

    def on_variant2_spin_changed(self, spin_value: int):
        self.variant2_slider.blockSignals(True)
        self.variant2_slider.setValue(spin_value)
        self.variant2_slider.blockSignals(False)
        self.arp.variants[1] = spin_value

    def on_variant3_slider_changed(self, slider_value: int):
        self.variant3_spin.blockSignals(True)
        self.variant3_spin.setValue(slider_value)
        self.variant3_spin.blockSignals(False)
        self.arp.variants[2] = slider_value

    def on_variant3_spin_changed(self, spin_value: int):
        self.variant3_slider.blockSignals(True)
        self.variant3_slider.setValue(spin_value)
        self.variant3_slider.blockSignals(False)
        self.arp.variants[2] = spin_value

    # ---------------------------------------------------------------------------------------
    # VARIANTS again
    # ---------------------------------------------------------------------------------------
    def set_variants(self, active: list[bool], values: list[int]):
        """Set variant activations and offsets safely without toggling signals."""

        if len(active) != 3 or len(values) != 3:
            return  # ignore malformed data

        self.arp.variants_active = active
        self.arp.variants = values

        # Buttons
        self.variant1_button.setChecked(active[0])
        self.update_button_color(self.variant1_button, active[0])

        self.variant2_button.setChecked(active[1])
        self.update_button_color(self.variant2_button, active[1])

        self.variant3_button.setChecked(active[2])
        self.update_button_color(self.variant3_button, active[2])

        # Spin boxes
        self.variant1_spin.setValue(values[0])
        self.variant2_spin.setValue(values[1])
        self.variant3_spin.setValue(values[2])

        # Sliders
        self.variant1_slider.setValue(values[0])
        self.variant2_slider.setValue(values[1])
        self.variant3_slider.setValue(values[2])


def main():
    app = QApplication(sys.argv)
    window = ArpeggiatorWidget()
    window.resize(600, 300)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
