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

from core.constants import ITEM_CONTAINER
from core.diagram_item_base import DiagramItem 

class ContainerItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_CONTAINER, parent)
        self.properties["text"] = "Contenedor"
        self.properties["fill_color"] = "#FFFACD"
        self.properties["border_color"] = "#FFD700"
        self.width = 200.0
        self.height = 150.0

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(self.properties["border_color"]), 2, Qt.DashDotLine)) 
        painter.setBrush(QBrush(QColor(self.properties["fill_color"])))
        painter.drawRect(QRectF(0.0, 0.0, self.width, self.height))
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(Qt.black)
        text_rect = QRectF(5.0, 5.0, self.width - 10.0, float(self.properties["font_size"]) + 10.0) 
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.properties["text"])
        super().paint(painter, option, widget) 

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            if self.scene() and hasattr(self.scene(), 'enter_container_context'):
                 self.scene().enter_container_context(self)
            event.accept()
            return

        if self.scene() and hasattr(self.scene(), 'enter_container_context'):
            self.scene().enter_container_context(self)
        event.accept() 

    def add_child_item(self, item_id):
        if item_id not in self.child_item_ids:
            self.child_item_ids.append(item_id)
            if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
                self.scene().parent().on_diagram_modified()

    def remove_child_item(self, item_id):
        if item_id in self.child_item_ids:
            self.child_item_ids.remove(item_id)
            if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
                self.scene().parent().on_diagram_modified()
