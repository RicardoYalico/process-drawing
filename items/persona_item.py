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
from demo import ITEM_PERSONA 

class PersonaItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_PERSONA, parent)
        self.properties["text"] = "Persona"
        self.properties["fill_color"] = "#E0E0E0" 
        self.properties["border_color"] = "#505050" 
        self.width = 60.0  
        self.height = 100.0 

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(self.properties["border_color"]), 2))
        painter.setBrush(QBrush(QColor(self.properties["fill_color"])))

        body_height = self.height * 0.6
        body_width = self.width * 0.5
        body_x = (self.width - body_width) / 2
        body_y = self.height * 0.3 
        painter.drawRect(QRectF(body_x, body_y, body_width, body_height))

        head_radius_x = self.width * 0.25
        head_radius_y = self.height * 0.15
        head_center_x = self.width / 2
        head_center_y = self.height * 0.15 + head_radius_y
        painter.drawEllipse(QPointF(head_center_x, head_center_y), head_radius_x, head_radius_y)
        
        arm_y = body_y + body_height * 0.2
        painter.drawLine(QPointF(body_x, arm_y), QPointF(0, arm_y + 10))
        painter.drawLine(QPointF(body_x + body_width, arm_y), QPointF(self.width, arm_y + 10))

        leg_start_y = body_y + body_height
        painter.drawLine(QPointF(body_x + body_width * 0.25, leg_start_y), QPointF(body_x, self.height))
        painter.drawLine(QPointF(body_x + body_width * 0.75, leg_start_y), QPointF(body_x + body_width, self.height))

        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(QColor(self.properties.get("text_color", Qt.black)))

        super().paint(painter, option, widget) 
