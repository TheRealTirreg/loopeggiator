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
        min_block_width = ArpeggiatorBlockWidget.minimal_block_width
        for block in self.arp_blocks:
            block.setFixedWidth(min_block_width * (max_rate / block.rate))

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
