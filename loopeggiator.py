# loopeggiator.py
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QSpinBox,
    QFrame,
    QCheckBox,
)
from PySide6.QtCore import Qt

# Use your existing ArpeggiatorWidget from arp.py
from arp import ArpeggiatorWidget


class ArpBlock(QWidget):
    """
    A single "Arp Block" that embeds:
      - An ArpeggiatorWidget
      - (Optional) Loop-count or remove button if you like
    For now, it’s just the ArpeggiatorWidget itself.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.arp_widget = ArpeggiatorWidget(self)
        layout.addWidget(self.arp_widget)
        self.setLayout(layout)


class InstrumentPanel(QFrame):
    """
    A single "instrument row" with:
      - Left: Mute/Volume settings
      - Right: a horizontal row of ArpBlocks + a button to add more
    Wrapped in a QFrame for a colored background rectangle.
    """
    def __init__(self, name="Instrument", parent=None):
        super().__init__(parent)
        self.setObjectName(name)

        # Give each instrument a colored background (adjust as desired)
        # Also a small border to distinguish instruments
        self.setStyleSheet("""
            QFrame#""" + name + """ {
                background-color: #E8F8FF; 
                border: 1px solid #AAAAAA; 
                border-radius: 5px;
            }
        """)

        self.main_layout = QHBoxLayout(self)
        self.setLayout(self.main_layout)

        # --- Left: Instrument Settings
        settings_layout = QVBoxLayout()
        self.main_layout.addLayout(settings_layout)

        # Instrument label
        self.instrument_label = QLabel(name)
        settings_layout.addWidget(self.instrument_label)

        # Mute checkbox
        self.mute_checkbox = QCheckBox("Mute")
        settings_layout.addWidget(self.mute_checkbox)

        # Volume slider
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Vol:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        settings_layout.addLayout(volume_layout)

        # Add stretch so settings stay at top
        settings_layout.addStretch()

        # --- Right: a horizontal row of ArpBlocks
        # We'll keep them in a HBox so they align left to right
        self.arp_blocks_layout = QHBoxLayout()
        self.main_layout.addLayout(self.arp_blocks_layout)

        # Add Arpeggiator button at the end
        self.add_arp_button = QPushButton("+ Arp")
        self.add_arp_button.clicked.connect(self.add_arpeggiator_block)
        self.main_layout.addWidget(self.add_arp_button)

    def add_arpeggiator_block(self):
        """
        Dynamically add a new ArpBlock side by side.
        """
        block = ArpBlock(self)
        self.arp_blocks_layout.addWidget(block)


class LoopEggiatorWindow(QMainWindow):
    """
    Main window with:
      - A central widget containing a vertical list of InstrumentPanels
      - A button at the bottom to add new instruments
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LoopEggiator")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Vertical layout for all instruments + "Add Instrument" button
        self.main_layout = QVBoxLayout(central_widget)

        # Container for instruments
        self.instruments_layout = QVBoxLayout()
        self.main_layout.addLayout(self.instruments_layout)

        # "Add Instrument" at the bottom
        self.add_instrument_button = QPushButton("+ Add Instrument")
        self.add_instrument_button.clicked.connect(self.add_instrument_panel)
        self.main_layout.addWidget(self.add_instrument_button)

        self.instruments = []

    def add_instrument_panel(self):
        """
        Creates a new instrument row (QFrame) and adds it to the vertical layout.
        """
        index = len(self.instruments) + 1
        instrument_name = f"Instrument {index}"
        panel = InstrumentPanel(name=instrument_name)
        self.instruments_layout.addWidget(panel)
        self.instruments.append(panel)


def main():
    app = QApplication(sys.argv)
    window = LoopEggiatorWindow()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
