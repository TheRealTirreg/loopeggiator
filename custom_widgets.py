# custom_widgets.py
from PySide6.QtWidgets import QSlider, QComboBox, QSpinBox, QDoubleSpinBox
from PySide6.QtGui import QValidator


class NoWheelEventMixin:
    def wheelEvent(self, event):
        event.ignore()  # Prevent value from changing via scroll

class NoScrollSlider(NoWheelEventMixin, QSlider):
    pass

class NoScrollComboBox(NoWheelEventMixin, QComboBox):
    pass

class NoScrollSpinBox(NoWheelEventMixin, QSpinBox):
    pass

class NoScrollDoubleSpinBox(NoWheelEventMixin, QDoubleSpinBox):
    pass

class MuteSpinBox(NoScrollSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-25, 24)

    def textFromValue(self, value):
        return "mute" if value == -25 else str(value)

    def valueFromText(self, text):
        return -25 if text.lower() == "mute" else int(text)

    def validate(self, text, pos):
        if text.lower() == "mute":
            return (QValidator.Acceptable, text, pos)
        return super().validate(text, pos)
    
class GroundNoteSpinBox(NoScrollSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(47, 72)  # 48 = C3, 72 = C5, 47 will mean "mute" (leftmost value)

    def textFromValue(self, value):
        return "mute" if value == 47 else str(value)

    def valueFromText(self, text):
        return 47 if text.lower() == "mute" else int(text)

    def validate(self, text, pos):
        if text.lower() == "mute":
            return (QValidator.Acceptable, text, pos)
        return super().validate(text, pos)

