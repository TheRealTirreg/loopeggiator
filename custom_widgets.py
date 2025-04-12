# custom_widgets.py
from PySide6.QtWidgets import QSlider, QComboBox, QSpinBox, QDoubleSpinBox, QCompleter
from PySide6.QtGui import QValidator
from PySide6.QtCore import Qt, QStringListModel


class NoWheelEventMixin:
    def wheelEvent(self, event):
        event.ignore()  # Prevent value from changing via scroll

class NoScrollSlider(NoWheelEventMixin, QSlider):
    pass

class NoScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(16)

        # Setup completer
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)  # <- This enables substring search
        self.setCompleter(self.completer)

        # Connect editing signal
        self.lineEdit().textEdited.connect(self.on_text_edited)

    def on_text_edited(self, text):
        items = [self.itemText(i) for i in range(self.count())]
        self.completer.setModel(QStringListModel(items))
        all_items = [self.itemText(i) for i in range(self.count())]
        if not text:
            self.completer.setModel(QStringListModel(all_items))
            return

        search_terms = text.lower().split()
        matches = []

        for item_text in all_items:
            # Remove the (bank/program) prefix for matching
            if ")" in item_text:
                name_only = item_text.split(")", 1)[1].strip().lower()
            else:
                name_only = item_text.lower()

            # Match if ALL search terms appear somewhere in the name
            if all(term in name_only for term in search_terms):
                matches.append(item_text)

        self.completer.setModel(QStringListModel(matches))

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

