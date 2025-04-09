from PySide6.QtWidgets import QSlider, QComboBox, QSpinBox, QDoubleSpinBox


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