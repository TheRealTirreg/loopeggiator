import sys
import platform
import argparse

import mido
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
    QSizePolicy,
    QStyle
)
from PySide6.QtCore import Qt

import os_check
from top_bar import TopBarWidget
from arp_widget import ArpeggiatorWidget
from synthplayer import SynthPlayer
from playback_thread import PlaybackThread


INSTRUMENTS = {
    "Piano": 0,
    "Guitar": 24,
    "Flute": 73
}

class ArpeggiatorBlockWidget(QWidget):
    """
    A small widget containing:
      - SpinBox for loop count
      - One ArpeggiatorWidget
      - Surrounded by a tight QFrame
    """
    def __init__(self, parent=None, repetitions=1, id=0):
        self.id = id
        self.iteration = 0  # Current iteration of the arpeggiator, up to repetitions - 1

        # ========================= Layout Setup =========================
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
        self.loop_spin.setValue(self.repetitions)
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

    @property
    def repetitions(self):
        """Get the total loop count"""
        return self.loop_spin.value()

    def get_arpeggio(self, bpm, instrument) -> tuple[list[mido.Message], int]:
        """Get mido note list for this arpeggiator"""
        arp, total_time = self.arp_widget.arp.get_arpeggio(bpm, instrument)
        return arp, total_time


class InstrumentRowWidget(QWidget):
    """
    One “instrument row”:
      - Narrow left side for Mute/Volume/Instrument selection
      - Horizontal list of ArpeggiatorBlockWidget(s) + a (+) button at the end

      - Holds at least one, but potentially many ArpeggiatorBlockWidget(s)
      - Plays the arpeggios of each arp block in after each other
    """
    def __init__(self, synth, instrument_row_id, parent=None):
        # ========================= Layout Setup =========================
        super().__init__(parent)

        # This row should also shrink to fit, not fill horizontally.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))

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
        self.btn_add_arp.clicked.connect(lambda: self.add_arpeggiator_block(repetitions=1))

        # Put the button in first. New blocks get inserted before it.
        self.arps_layout.addWidget(self.btn_add_arp)

        # Add everything to main_layout
        main_layout.addWidget(settings_frame)
        main_layout.addLayout(self.arps_layout)

        # ========================= Functionality ========================

        # Set the synth with instrument
        self.synth = synth
        self.id = instrument_row_id
        self.instrument = 0  # Default Piano
        self.synth.add_channel()

        self.arp_blocks = []  # List of ArpeggiatorBlockWidget(s) in this row
        self.arp_queue = []  # Queue of arpeggios to play. E.g. if ArpWidget1 has 2 repetitions, add this to the queue 2 times
        self.arp_queue_idx = 0  # Hold idx of arp_queue. Start with the first arpeggiator

        # Add an initial ArpeggiatorBlock by default
        self.add_arpeggiator_block(repetitions=1)

    def add_arpeggiator_block(self, repetitions):
        # Insert a new ArpeggiatorBlockWidget before the "+" button
        self.arps_layout.removeWidget(self.btn_add_arp)

        arp_id = len(self.arp_blocks)
        new_block = ArpeggiatorBlockWidget(repetitions=repetitions, id=arp_id)
        self.arp_blocks.append(new_block)

        # Add the index of the new block to the queue for each repetition
        for i in range(repetitions):
            self.arp_queue.append(arp_id)
        
        # Add the new block to the layout
        self.arps_layout.addWidget(new_block)

        # Reinsert the "+" button at the end
        self.arps_layout.addWidget(self.btn_add_arp)
    
    def change_instrument(self, index):
        instrument = self.instrument_combo.itemData(index)
        self.synth.change_instrument(self.id, instrument)  # bank=0

    def get_next_arpeggio(self, bpm):
        """
        Get arpeggio of the next (arpeggio, play_time) in line
        """
        # Get the current arpeggio
        arp_id = self.arp_queue[self.arp_queue_idx]
        arpeggio, time = self.arp_blocks[arp_id].get_arpeggio(bpm, self.instrument)

        # Increment the arp_queue_idx, and wrap around if necessary
        self.arp_queue_idx += 1
        if self.arp_queue_idx >= len(self.arp_queue):
            self.arp_queue_idx = 0

        return arpeggio, time


class LoopArpeggiatorMainWindow(QMainWindow):
    """
    A main window with:
      - A top bar (play/stop button, BPM spin, save/load buttons)
      - A single QScrollArea for everything (so only one horizontal scrollbar)
      - A vertical list of InstrumentRowWidgets inside that scroll area
      - A button at the bottom to add more instruments
    """
    def __init__(self, soundfont_path):
        # ===================== Functionality ========================
        self.synth = SynthPlayer(soundfont_path)

        # ==================== Base Window Setup =====================
        super().__init__()
        self.setWindowTitle("Loop Arpeggiator")
        self.resize(1200, 600)

        # ============================================================
        # Create a top-level widget with a vertical layout.
        # The top bar goes at the top, then the QScrollArea underneath.
        # ============================================================
        main_widget = QWidget()
        self.main_layout = QVBoxLayout(main_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # ============================================================
        # 1) TOP BAR
        # ============================================================
        self.top_bar = TopBarWidget()
        self.main_layout.addWidget(self.top_bar)

        # ============================================================
        # 2) CENTRAL AREA (scrollable Instrument rows + "Add Instrument")
        # ============================================================
        self.container = QWidget()
        self.vlayout = QVBoxLayout(self.container)
        self.vlayout.setContentsMargins(5, 5, 5, 5)

        # We'll keep a list of row widgets
        self.instrument_rows = []

        # "Add Instrument" button at bottom
        self.btn_add_instrument = QPushButton("Add Instrument")
        self.btn_add_instrument.clicked.connect(self.add_instrument)

        # Add the first instrument row by default
        self.add_instrument()

        # Then add the button at the bottom
        self.vlayout.addWidget(self.btn_add_instrument, alignment=Qt.AlignmentFlag.AlignLeft)

        # Put the container inside a single QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.container)

        # Add the scroll area to main_layout
        self.main_layout.addWidget(scroll_area)

        # Finally, set main_widget as the central widget
        self.setCentralWidget(main_widget)

        # Playback thread
        self.playback_thread = None

        # Connect the play button to the playback function
        self.top_bar.play_button.toggled.connect(self.on_play_toggled)

    def on_play_toggled(self, checked):
        """Switch between play and stop icons depending on toggle state."""
        if checked:
            self.top_bar.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            self.start_playback()
        else:
            self.top_bar.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.stop_playback()

    def start_playback(self):
        if self.playback_thread and self.playback_thread.isRunning():
            return  # already running

        def get_bpm():
            return self.top_bar.bpm

        self.playback_thread = PlaybackThread(
            instrument_rows=self.instrument_rows,
            get_bpm_func=get_bpm,
            synth=self.synth
        )
        self.playback_thread.start()

    def stop_playback(self):
        if self.playback_thread:
            self.playback_thread.stop()
            self.playback_thread.wait()
            self.playback_thread = None
        
    def closeEvent(self, event):
        """Called when the user closes the main window."""
        self.stop_playback()
        super().closeEvent(event)

    def add_instrument(self):
        row = InstrumentRowWidget(self.synth, len(self.instrument_rows))
        self.instrument_rows.append(row)
        index_for_button = self.vlayout.count() - 1
        self.vlayout.insertWidget(index_for_button, row)


def main():
    parser = argparse.ArgumentParser(description="Run the Loop Arpeggiator.")
    if platform.system() == "Windows":
        default_sf = r"C:\tools\fluidsynth\soundfonts\FluidR3_GM.sf2"
    else:
        default_sf = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

    parser.add_argument(
        "-sf", "--soundfont",
        help="Path to the SoundFont file to use.",
        default=default_sf
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = LoopArpeggiatorMainWindow(soundfont_path=args.soundfont)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
