# top_bar.py
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpinBox, QStyle, QLabel, QFileDialog, QMainWindow
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from save_load import save_project, load_project


class TopBarWidget(QWidget):
    bpm_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout for this widget
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Play/Stop toggle button ---
        self.play_button = QPushButton()
        self.play_button.setCheckable(True)
        self.play_button.setFixedSize(QSize(30, 30))
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setToolTip("Play/Stop (Space)")
        self.play_button.toggled.connect(self.on_play_toggled)

        # Shortcut: pressing space toggles the play_button
        play_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        play_shortcut.activated.connect(self.play_button.toggle)

        # --- BPM label ---
        self.bpm_label = QLabel("BPM:")

        # --- BPM spinbox ---
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(20, 300)
        self.rate_spin.setValue(120)
        self.rate_spin.setToolTip("BPM")
        self.rate_spin.valueChanged.connect(self._on_bpm_changed)

        # --- Loop length info box ---
        self.loop_length_label = QLabel("Loop Length: 0.60s")
        self.loop_length_label.setToolTip("The loop length is determined by the longest arpeggio chain")

        # --- Save & Load buttons (icon‐only) ---
        self.save_button = QPushButton()
        self.save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_button.setToolTip("Save")
        self.save_button.clicked.connect(self.on_save_clicked)

        self.load_button = QPushButton()
        self.load_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.load_button.setToolTip("Load")
        self.load_button.clicked.connect(self.on_load_clicked)

        # Add them to layout
        layout.addWidget(self.play_button)
        layout.addSpacing(16)

        layout.addWidget(self.bpm_label)
        layout.addWidget(self.rate_spin)
        layout.addSpacing(16)

        layout.addWidget(self.loop_length_label)
        layout.addStretch(1)

        layout.addWidget(self.save_button)
        layout.addWidget(self.load_button)

    @property
    def bpm(self):
        """Return the current BPM value."""
        return self.rate_spin.value()
    
    @bpm.setter
    def bpm(self, value: int):
        """Set the BPM value and emit the signal."""
        self.rate_spin.setValue(value)
        self.bpm_changed.emit(value)
    
    def _on_bpm_changed(self, value: int):
        self.bpm_changed.emit(value)
    
    def set_loop_length(self, length_s: float):
        """Set the loop length label text to the given value."""
        self.loop_length_label.setText(f"Loop Length: {length_s:.2f}s")

    def on_play_toggled(self, checked: bool):
        """Switch between the play and stop icon depending on toggle state."""
        if checked:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            print("Start Playing")
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            print("Stopped playing")

    def main_window(self):
        """Find the LoopArpeggiatorMainWindow this widget belongs to."""
        widget = self
        while widget is not None:
            if isinstance(widget, QMainWindow):
                return widget
            widget = widget.parent()
        return None

    def on_save_clicked(self):
        save_dir = os.path.join(os.path.dirname(__file__), "saves")
        os.makedirs(save_dir, exist_ok=True)

        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", save_dir, "JSON Files (*.json)")
        if filename:
            mw = self.main_window()
            if mw:
                save_project(mw, filename=filename)

    def on_load_clicked(self):
        save_dir = os.path.join(os.path.dirname(__file__), "saves")
        os.makedirs(save_dir, exist_ok=True)

        filename, _ = QFileDialog.getOpenFileName(self, "Load Project", save_dir, "JSON Files (*.json)")
        if filename:
            mw = self.main_window()
            if mw:
                load_project(mw, filename=filename)
