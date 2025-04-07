# instrument_arp_row.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from arp_widget import ArpeggiatorBlockWidget
from PySide6.QtCore import Signal

class InstrumentArpPanel(QWidget):
    play_time_changed = Signal()

    def __init__(self, parent=None, row_container=None):
        super().__init__(parent)
        self.row_container = row_container

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.arp_blocks = []
        self.arp_queue = []
        self.arp_queue_idx = 0

        self.btn_add = QPushButton("+")
        self.btn_add.setToolTip("Add arpeggiator block")
        self.btn_add.clicked.connect(lambda: self.add_block(repetitions=1))
        self.layout.addWidget(self.btn_add)

        self.add_block(repetitions=1)

    def _on_block_changed(self):
        self.play_time_changed.emit()

    def add_block(self, repetitions):
        self.layout.removeWidget(self.btn_add)
        block_id = len(self.arp_blocks)
        block = ArpeggiatorBlockWidget(
            parent=self,
            repetitions=repetitions,
            id=block_id,
            velocity=self.row_container.velocity,
            volume_line_signal=self.row_container.volume_line_changed
        )
        block.velocity = self.row_container.velocity
        self.arp_blocks.append(block)

        for _ in range(repetitions):
            self.arp_queue.append(block_id)

        self.layout.addWidget(block)
        self.layout.addWidget(self.btn_add)
        block.play_time_changed.connect(self._on_block_changed)
        self.play_time_changed.emit()

    def set_block_width(self, max_rate):
        print(f"Set block width: {max_rate} max rate")
        print(f"Doing this for {len(self.arp_blocks)} blocks")
        min_block_width = ArpeggiatorBlockWidget.minimal_block_width
        for block in self.arp_blocks:
            arp_width = min_block_width * (max_rate / block.rate)
            block.arp_widget.setFixedWidth(arp_width)
            block.update_size()  # <-- reapply total width (loop-based)

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

    def _rebuild_queue(self):
        self.arp_queue.clear()
        for i, block in enumerate(self.arp_blocks):
            self.arp_queue.extend([i] * block.repetitions)
        self.arp_queue_idx = 0

    def move_block_left(self, block):
        idx = self.arp_blocks.index(block)
        if idx > 0:
            self.arp_blocks[idx], self.arp_blocks[idx - 1] = self.arp_blocks[idx - 1], self.arp_blocks[idx]
            self._rebuild_queue()
            self._rebuild_layout()
            self.play_time_changed.emit()

    def move_block_right(self, block):
        idx = self.arp_blocks.index(block)
        if idx < len(self.arp_blocks) - 1:
            self.arp_blocks[idx], self.arp_blocks[idx + 1] = self.arp_blocks[idx + 1], self.arp_blocks[idx]
            self._rebuild_queue()
            self._rebuild_layout()
            self.play_time_changed.emit()

    def remove_block(self, block):
        if block in self.arp_blocks:
            block_id = self.arp_blocks.index(block)
            self.layout.removeWidget(block)
            block.play_time_changed.disconnect(self._on_block_changed)
            block.deleteLater()
            self.arp_blocks.remove(block)

            # Update IDs
            for i, blk in enumerate(self.arp_blocks):
                blk.id = i

            # Adjust queue
            self.arp_queue = [
                idx if idx < block_id else idx - 1
                for idx in self.arp_queue
                if idx != block_id
            ]
            if self.arp_queue_idx >= len(self.arp_queue):
                self.arp_queue_idx = 0

            self.play_time_changed.emit()
