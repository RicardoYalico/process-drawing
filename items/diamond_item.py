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

from core.diagram_item_base import DiagramItem
from demo import ITEM_DIAMOND 

class DiamondItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_DIAMOND, parent)
        self.properties["text"] = "Decisión"

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(self.properties["border_color"]), 2))
        painter.setBrush(QBrush(QColor(self.properties["fill_color"])))
        polygon = QPolygonF()
        polygon.append(QPointF(self.width / 2.0, 0.0))
        polygon.append(QPointF(self.width, self.height / 2.0)) 
        polygon.append(QPointF(self.width / 2.0, self.height)) 
        polygon.append(QPointF(0.0, self.height / 2.0)) 
        painter.drawPolygon(polygon)
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(Qt.black)
        text_rect = QRectF(self.width * 0.15, self.height * 0.15, self.width * 0.7, self.height * 0.7)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.properties["text"])
        super().paint(painter, option, widget)
