import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QLabel,
    QSlider,
    QCheckBox,
    QComboBox,
    QFrame,
    QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from arpygo import ArpeggiatorWidget
from synthplayer import SynthPlayer


INSTRUMENTS = {
    "Piano": 0,
    "Guitar": 24,
    "Flute": 73
}

# TODO: Handle instrument selection here.
# Synthplayer should

class ArpeggiatorBlockWidget(QWidget):
    """
    A small widget containing:
      - SpinBox for loop count
      - One ArpeggiatorWidget
      - Surrounded by a tight QFrame
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Let this widget shrink to fit content (rather than fill spare space).
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Outer layout for this entire block
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Frame so we get a box around each arpeggiator
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        # Also prefer minimal sizing
        frame.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Put content into the frame's layout
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)

        # Top row: loop count
        loop_layout = QHBoxLayout()
        loop_label = QLabel("Loop count:")
        self.loop_spin = QSpinBox()
        self.loop_spin.setRange(1, 16)
        self.loop_spin.setValue(3)
        loop_layout.addWidget(loop_label)
        loop_layout.addWidget(self.loop_spin)
        loop_layout.addStretch()

        # The ArpeggiatorWidget with an optional fixed or min size
        self.arp_widget = ArpeggiatorWidget()
        # If you want a strict fixed size, uncomment:
        # self.arp_widget.setFixedSize(QSize(300, 220))
        # Or if you want it to be just enough for the controls:
        self.arp_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        # Add subwidgets to frame layout
        frame_layout.addLayout(loop_layout)
        frame_layout.addWidget(self.arp_widget)

        # Finally, put the frame in the outer layout
        outer_layout.addWidget(frame)


class InstrumentRowWidget(QWidget):
    """
    One “instrument row”:
      - Narrow left side for Mute/Volume/Instrument selection
      - Horizontal list of ArpeggiatorBlockWidget(s) + a (+) button at the end
    """
    def __init__(self, synth, instrument_row_id, parent=None):
        super().__init__(parent)

        self.synth = synth
        self.id = instrument_row_id
        self.instrument = 0
        self.synth.add_channel()

        # This row should also shrink to fit, not fill horizontally.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.arp_blocks = []

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
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(75)

        # Horizontal mini‐layout for volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)

        # Play Do Button
        self.btn_do = QPushButton("Do")
        self.btn_do.clicked.connect(lambda: self.synth.play_note(60, 1, channel=self.id))

        # Instrument combo
        instrument_label = QLabel("Instrument:")
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItem("Piano", 0)       # Acoustic Grand Piano (ID 0)
        self.instrument_combo.addItem("Guitare", 24)    # Acoustic Guitar (nylon) (ID 24)
        self.instrument_combo.addItem("Flûte", 73)      # Flute (ID 73)
        self.instrument_combo.setCurrentIndex(0)
        self.instrument_combo.currentIndexChanged.connect(self.change_instrument)

        # Add them to settings_layout
        settings_layout.addWidget(self.mute_checkbox)
        settings_layout.addLayout(volume_layout)
        settings_layout.addWidget(instrument_label)
        settings_layout.addWidget(self.instrument_combo)
        settings_layout.addWidget(self.btn_do)
        settings_layout.addStretch()

        # ---------- Horizontal area for Arpeggiator blocks ----------
        # (No scroll area here, we rely on ONE global QScrollArea in the main window.)
        self.arps_layout = QHBoxLayout()
        self.arps_layout.setContentsMargins(5, 5, 5, 5)

        # “Add Arpeggiator” button at the end
        self.btn_add_arp = QPushButton("+")
        self.btn_add_arp.setToolTip("Add another Arpeggiator block")
        self.btn_add_arp.clicked.connect(self.add_arpeggiator_block)

        # Put the button in first. New blocks get inserted before it.
        self.arps_layout.addWidget(self.btn_add_arp)

        # Add everything to main_layout
        main_layout.addWidget(settings_frame)
        main_layout.addLayout(self.arps_layout)

        # Add an initial ArpeggiatorBlock by default
        self.add_arpeggiator_block()

    def add_arpeggiator_block(self):
        # Insert a new ArpeggiatorBlockWidget before the "+" button
        self.arps_layout.removeWidget(self.btn_add_arp)

        new_block = ArpeggiatorBlockWidget()
        self.arp_blocks.append(new_block)
        self.arps_layout.addWidget(new_block)

        self.arps_layout.addWidget(self.btn_add_arp)
    
    def change_instrument(self, index):
        instrument = self.instrument_combo.itemData(index)
        self.synth.change_instrument(self.id, instrument)  # bank=0


class LoopArpeggiatorMainWindow(QMainWindow):
    """
    A main window with:
      - A single QScrollArea for everything (so only one horizontal scrollbar)
      - A vertical list of InstrumentRowWidgets inside that scroll area
      - A button at the bottom to add more instruments
    """
    def __init__(self):
        # ===================== Functionality ========================
        self.synth = SynthPlayer("/usr/share/sounds/sf2/FluidR3_GM.sf2")

        # ==================== Layout ================
        super().__init__()
        self.setWindowTitle("Loop Arpeggiator")
        self.resize(1200, 600)

        # A container widget that will hold all the instrument rows + bottom button
        self.container = QWidget()
        self.vlayout = QVBoxLayout(self.container)
        self.vlayout.setContentsMargins(5, 5, 5, 5)

        # We'll keep a list of row widgets
        self.instrument_rows = []

        # "Add Instrument" button
        self.btn_add_instrument = QPushButton("Add Instrument")
        self.btn_add_instrument.clicked.connect(self.add_instrument)

        # Add the first instrument row by default
        self.add_instrument()

        # Then add the button at the bottom
        self.vlayout.addWidget(self.btn_add_instrument, alignment=Qt.AlignmentFlag.AlignLeft)

        # Put the container inside a single QScrollArea (one scrollbar for everything)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.container)

        self.setCentralWidget(scroll_area)


    def add_instrument(self):
        row = InstrumentRowWidget(self.synth, len(self.instrument_rows))
        self.instrument_rows.append(row)
        # Insert it above the "Add Instrument" button in the layout
        # (i.e. place it just before the last widget in vlayout)
        index_for_button = self.vlayout.count() - 1
        self.vlayout.insertWidget(index_for_button, row)


def main():
    app = QApplication(sys.argv)
    window = LoopArpeggiatorMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
