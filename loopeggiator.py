# loopeggiator.py
import sys
import platform
import argparse

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QScrollArea,
    QStyle
)
from PySide6.QtCore import Qt, QMetaObject, QTimer

import os_check  # Ensures this script also works on Windows
from instrument_row_container import InstrumentRowContainer
from top_bar import TopBarWidget
from synthplayer import SynthPlayer
from playback_thread import PlaybackThread


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
        self.synth = SynthPlayer(soundfont_path, max_rows=16)
        self.synth.on_marker = self.highlight_block

        # ==================== Base Window Setup =====================
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowTitle("Arpeggiator Loop Station")
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
        self.top_bar = TopBarWidget(self)
        self.main_layout.addWidget(self.top_bar)
        self.top_bar.bpm_changed.connect(self._on_play_time_changed)  # Connect to signal

        # ============================================================
        # 2) CENTRAL AREA (scrollable Instrument rows + "Add Instrument")
        # ============================================================
        self.container = QWidget()
        self.vlayout = QVBoxLayout(self.container)
        self.vlayout.setContentsMargins(5, 5, 5, 5)
        self.vlayout.setAlignment(Qt.AlignTop)

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
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.container)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Add the scroll area to main_layout
        self.main_layout.addWidget(self.scroll_area)

        # Finally, set main_widget as the central widget
        self.setCentralWidget(main_widget)

        # Playback thread
        self.playback_thread = None

        # Connect the play button to the playback function
        self.top_bar.play_button.toggled.connect(self.on_play_toggled)

    def _on_play_time_changed(self):
        """Called when the play time changes in any row."""
        self.update_loop_length()
        self.setArpBlockWidth()

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

    def setArpBlockWidth(self):
        """Set the width of the arpeggiator blocks based on their rate."""
        max_rate = 0
        for row in self.instrument_rows:
            for block in row.arp_blocks:
                max_rate = max(max_rate, block.rate)
        
        for row in self.instrument_rows:
            row.set_block_width(max_rate)

    def add_instrument(self):
        if len(self.instrument_rows) >= self.synth.max_rows:
            return
        
        row = InstrumentRowContainer(self.synth, len(self.instrument_rows), parent=self)
        self.instrument_rows.append(row)
        index_for_button = self.vlayout.count() - 1
        self.vlayout.insertWidget(index_for_button, row)
        row.play_time_changed.connect(self._on_play_time_changed)  # Connect to signal
        self._on_play_time_changed()

        QTimer.singleShot(10, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))  # Scroll to the bottom
        
        if len(self.instrument_rows) >= self.synth.max_rows:
            self.btn_add_instrument.hide()  # Hide the button if max rows reached
            
        return row

    def del_instrument(self, instrument):
        """
        Remove an instrument row from the main window without stopping playback.
        Args:
            instrument: The InstrumentRowWidget to remove
        """
        if instrument in self.instrument_rows:
            # Get the row index
            row_index = self.instrument_rows.index(instrument)
            
            # Remove from layout and disconnect signals
            self.vlayout.removeWidget(instrument)
            instrument.play_time_changed.disconnect(self._on_play_time_changed)
            
            # Clean up the instrument's resources
            instrument.deleteLater()
            
            # Remove from our list
            self.instrument_rows.remove(instrument)
            
            # Update channel IDs for remaining instruments
            for i, row in enumerate(self.instrument_rows):
                row.id = i
                # Update the instrument in the synth to use the new channel
                row.synth.change_instrument(i, row.instrument)
            
            # Update the loop length and block widths
            self._on_play_time_changed()

            if len(self.instrument_rows) < self.synth.max_rows:
                self.btn_add_instrument.show()  # Show the button again if we have space

    def update_loop_length(self):
        """Update the loop length label in the top bar."""
        if not self.instrument_rows:
            self.top_bar.set_loop_length(0)
            return
        
        times = [row.get_play_time(self.top_bar.bpm) for row in self.instrument_rows]
        max_time = max(times) if times else 0

        self.top_bar.set_loop_length(max_time)

    def highlight_block(self, block_id: str):
        try:  # Expected format: "row#block"
            row_idx, block_idx = map(int, block_id.split("#"))
            row = self.instrument_rows[row_idx]
            block = row.arp_blocks[block_idx]
            QMetaObject.invokeMethod(block, "flash", Qt.QueuedConnection)  # Queued because this is called from synthplayer thread
        except Exception as e:
            print(f"Failed to highlight block {block_id}: {e}")

    def keyPressEvent(self, event):
        """Mute/unmute instrument rows using number keys [And t, [y/z], u, i, o, p]."""
        key_map = {
            Qt.Key_1: 0,
            Qt.Key_2: 1,
            Qt.Key_3: 2,
            Qt.Key_4: 3,
            Qt.Key_5: 4,
            Qt.Key_6: 5,
            Qt.Key_7: 6,
            Qt.Key_8: 7,
            Qt.Key_9: 8,
            Qt.Key_0: 9,
            Qt.Key_T: 10,
            Qt.Key_Z: 11,
            Qt.Key_Y: 11,  # support QWERTY, QWERTZ and AZERTY
            Qt.Key_U: 12,
            Qt.Key_I: 13,
            Qt.Key_O: 14,
            Qt.Key_P: 15,
        }

        if event.key() in key_map:
            idx = key_map[event.key()]
            if idx < len(self.instrument_rows):
                checkbox = self.instrument_rows[idx].mute_checkbox
                checkbox.setChecked(not checkbox.isChecked())


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
