# instrument_arp_row.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from arp_widget import ArpeggiatorBlockWidget
from PySide6.QtCore import Signal

from arp import Mode

class InstrumentArpPanel(QWidget):
    play_time_changed = Signal()

    def __init__(self, parent=None, row_container=None):
        super().__init__(parent)
        self.row_container = row_container

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.arp_blocks = []

        self.btn_add = QPushButton("+")
        self.btn_add.setToolTip("Add arpeggiator block")
        self.btn_add.clicked.connect(self.add_block)  # TODO add args to add_block?
        self.layout.addWidget(self.btn_add)

        self.add_block()

    def _on_block_changed(self):
        self.play_time_changed.emit()

    def add_block(
        self,
        mute=False,
        rate=1.0,
        note_length=0.2,
        ground_note=60,
        mode=Mode.UP,
        variants_active=None,
        variants=None,
    ):
        if variants_active is None:
            variants_active = [False, False, False]
        if variants is None:
            variants = [0, 0, 0]

        self.layout.removeWidget(self.btn_add)

        block_id = len(self.arp_blocks)
        block = ArpeggiatorBlockWidget(
            parent=self,
            id=block_id,
            velocity=self.row_container.velocity,
            mute=mute,
            rate=rate,
            note_length=note_length,
            ground_note=ground_note,
            mode=mode,
            variants_active=variants_active,
            variants=variants,
            volume_line_signal=self.row_container.volume_line_changed,
        )

        self.arp_blocks.append(block)
        self.layout.addWidget(block)
        self.layout.addWidget(self.btn_add)

        block.play_time_changed.connect(self._on_block_changed)
        self.play_time_changed.emit()

    def duplicate_arp_block(self, block, config):
        idx = self.arp_blocks.index(block)
        self.layout.removeWidget(self.btn_add)

        new_block = ArpeggiatorBlockWidget(
            parent=self,
            id=len(self.arp_blocks),
            volume_line_signal=self.row_container.volume_line_changed,
            **config  # Values like mute, rate, velocity, note_length, ground_note, ...
        )

        self.arp_blocks.insert(idx + 1, new_block)
        self.layout.insertWidget(idx + 1, new_block)
        self.layout.addWidget(self.btn_add)
        
        new_block.play_time_changed.connect(self._on_block_changed)
        self.play_time_changed.emit()

    def set_block_width(self, max_rate):
        min_block_width = ArpeggiatorBlockWidget.minimal_block_width
        for block in self.arp_blocks:
            arp_width = min_block_width * (max_rate / block.rate)
            block.update_size(arp_width)  # <-- reapply total width (loop-based)

    def _rebuild_layout(self):
        # Remove all widgets
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                self.layout.removeWidget(widget)
                widget.setParent(None)

        # Re-add in new order
        for i, block in enumerate(self.arp_blocks):
            block.id = i
            self.layout.addWidget(block)

        # Add the "+" button at the end again
        self.layout.addWidget(self.btn_add)

    def move_block_left(self, block):
        idx = self.arp_blocks.index(block)
        if idx > 0:
            self.arp_blocks[idx], self.arp_blocks[idx - 1] = self.arp_blocks[idx - 1], self.arp_blocks[idx]
            self._rebuild_layout()
            self.play_time_changed.emit()

    def move_block_right(self, block):
        idx = self.arp_blocks.index(block)
        if idx < len(self.arp_blocks) - 1:
            self.arp_blocks[idx], self.arp_blocks[idx + 1] = self.arp_blocks[idx + 1], self.arp_blocks[idx]
            self._rebuild_layout()
            self.play_time_changed.emit()

    def remove_block(self, block):
        if block in self.arp_blocks:
            self.layout.removeWidget(block)
            block.play_time_changed.disconnect(self._on_block_changed)
            block.deleteLater()
            self.arp_blocks.remove(block)

            for i, blk in enumerate(self.arp_blocks):
                blk.id = i

            self.play_time_changed.emit()
