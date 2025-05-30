
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

from core.constants import ITEM_IMAGE
from core.diagram_item_base import DiagramItem

class ImageItem(DiagramItem):
    def __init__(self, image_path=None, parent=None):
        super().__init__(ITEM_IMAGE, parent)
        self.properties["text"] = "Imagen" 
        self.properties["image_path"] = image_path
        self.pixmap = QPixmap()
        if image_path:
            self.load_image_from_path(image_path)
        
        if not self.pixmap.isNull():
            self.width = float(self.pixmap.width())
            self.height = float(self.pixmap.height())
            max_initial_dim = 200.0 
            if self.width > max_initial_dim or self.height > max_initial_dim:
                aspect_ratio = self.width / self.height if self.height > 0 else 1.0
                if self.width > self.height:
                    self.width = max_initial_dim
                    self.height = max_initial_dim / aspect_ratio if aspect_ratio > 0 else max_initial_dim
                else:
                    self.height = max_initial_dim
                    self.width = max_initial_dim * aspect_ratio
        else: 
            self.width = 100.0
            self.height = 100.0


    def load_image_from_path(self, path=None):
        image_path_to_load = path if path else self.properties.get("image_path")
        if image_path_to_load:
            loaded = self.pixmap.load(image_path_to_load)
            if loaded:
                self.properties["image_path"] = image_path_to_load 
                self.properties["text"] = QFileInfo(image_path_to_load).fileName()
            else:
                print(f"Error: No se pudo cargar la imagen desde {image_path_to_load}")
                self.pixmap = QPixmap() 
            self.prepareGeometryChange()
            self.update()
        else:
            self.pixmap = QPixmap() 

    def paint(self, painter, option, widget=None):
        if not self.pixmap.isNull():
            target_rect = QRectF(0.0, 0.0, self.width, self.height)
            scaled_pixmap = self.pixmap.scaled(target_rect.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x_offset = (target_rect.width() - scaled_pixmap.width()) / 2.0
            y_offset = (target_rect.height() - scaled_pixmap.height()) / 2.0
            painter.drawPixmap(target_rect.topLeft() + QPointF(x_offset, y_offset), scaled_pixmap)
        else:
            painter.setPen(Qt.gray)
            painter.setBrush(Qt.lightGray)
            painter.drawRect(QRectF(0.0, 0.0, self.width, self.height))
            painter.drawText(QRectF(0.0, 0.0, self.width, self.height), Qt.AlignCenter, "Sin Imagen")
        
        if self.isSelected():
            painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush) 
            painter.drawRect(QRectF(0.0, 0.0, self.width, self.height))

        super().paint(painter, option, widget) 
    
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        event.accept()
