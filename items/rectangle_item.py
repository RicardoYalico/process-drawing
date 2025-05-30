from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QRectF

from core.constants import ITEM_RECTANGLE
from core.diagram_item_base import DiagramItem

class RectangleItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_RECTANGLE, parent)
        self.properties["text"] = "Rectángulo"

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(self.properties["border_color"]), 2))
        painter.setBrush(QBrush(QColor(self.properties["fill_color"])))
        painter.drawRect(QRectF(0.0, 0.0, self.width, self.height))
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(0.0, 0.0, self.width, self.height), Qt.AlignCenter | Qt.TextWordWrap, self.properties["text"])
        super().paint(painter, option, widget) 

