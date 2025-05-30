import sys
import json
import math 
import base64 
import time 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QAction, QToolBar, QFileDialog, QMessageBox, QColorDialog, QLabel, 
    QListWidget, QListWidgetItem, QHBoxLayout, QWidget, QVBoxLayout,
    QPushButton, QDialog, QInputDialog, QGraphicsPolygonItem, QGraphicsLineItem,
    QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QTextEdit, 
    QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, QSizePolicy, QDockWidget,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem, QMenu 
)
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QPolygonF, 
                         QTransform, QDrag, QIcon, QPixmap, QFontMetrics, 
                         QPainterPath, QPainterPathStroker, QKeySequence, QImage) 
from PyQt5.QtCore import (Qt, QPointF, QRectF, QSizeF, QMimeData, 
                          pyqtSignal, QSize, QLineF, QFileInfo, QBuffer, QIODevice)

from core.constants import ITEM_PERSONA
from core.diagram_item_base import DiagramItem

class C4PersonaItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_PERSONA, parent)
        self.properties["text"] = "Persona"
        self.properties["fill_color"] = "#E0E0E0"
        self.properties["border_color"] = "#505050"
        self.properties["font_size"] = 10
        self.width = 80.0
        self.height = 100.0

    def paint(self, painter, option, widget=None):
        # Configuración de colores
        painter.setPen(QPen(QColor(self.properties["border_color"]), 2))
        painter.setBrush(QBrush(QColor(self.properties["fill_color"])))

        # Cabeza (círculo)
        head_radius = self.width * 0.2
        head_center_x = self.width / 2
        head_center_y = self.height * 0.2
        painter.drawEllipse(QPointF(head_center_x, head_center_y), head_radius, head_radius)

        # Cuerpo (rectángulo)
        body_width = self.width * 0.4
        body_height = self.height * 0.4
        body_x = (self.width - body_width) / 2
        body_y = head_center_y + head_radius + 5
        painter.drawRect(QRectF(body_x, body_y, body_width, body_height))

        # Texto
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(QColor(self.properties.get("text_color", Qt.black)))

        text = self.properties["text"]
        text_rect = QRectF(0, body_y + body_height + 5, self.width, 20)
        painter.drawText(text_rect, Qt.AlignCenter, text)

        super().paint(painter, option, widget)
