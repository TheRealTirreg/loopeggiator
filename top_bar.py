from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpinBox, QStyle
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QShortcut, QKeySequence


class TopBarWidget(QWidget):
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

        # --- BPM spinbox ---
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(20, 300)
        self.rate_spin.setValue(100)
        self.rate_spin.setToolTip("BPM")

        # --- Save & Load buttons (icon‐only) ---
        self.save_button = QPushButton()
        self.save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_button.setToolTip("Save")

        self.load_button = QPushButton()
        self.load_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.load_button.setToolTip("Load")

        # Add them to layout
        layout.addWidget(self.play_button)
        layout.addWidget(self.rate_spin)
        layout.addStretch(1)
        layout.addWidget(self.save_button)
        layout.addWidget(self.load_button)

    def on_play_toggled(self, checked: bool):
        """Switch between the play and stop icon depending on toggle state."""
        if checked:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
            print("Start Playing")
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            print("Stopped playing")
