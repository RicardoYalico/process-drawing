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

from core.constants import ITEM_SCRIPT
from core.diagram_item_base import DiagramItem

class ScriptItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_SCRIPT, parent)
        self.properties["text"] = "Script"
        self.properties["paint_script"] = "painter.setBrush(Qt.cyan)\npainter.drawEllipse(QRectF(0, 0, self.width, self.height))"
        self.width = 100.0
        self.height = 60.0

    def paint(self, painter, option, widget=None):
        script = self.properties.get("paint_script", "")
        if script:
            try:
                local_env = {'painter': painter, 'self': self, 'Qt': Qt, 'QColor': QColor, 'QRectF': QRectF, 'QPen': QPen, 'QFont': QFont, 'QBrush': QBrush}
                exec(script, {"__builtins__": {}}, local_env) 
            except Exception as e:
                item_id_str = getattr(self, 'id', 'N/A_en_paleta')
                print(f"Error al ejecutar script de pintura para {item_id_str}: {e}")
                painter.setPen(Qt.red)
                painter.drawText(QRectF(0,0, self.width, self.height), Qt.AlignCenter | Qt.TextWordWrap, f"Error en script:\n{e}")
        else:
            painter.setPen(Qt.darkGray)
            painter.setBrush(Qt.lightGray)
            painter.drawRect(QRectF(0,0,self.width, self.height))
            painter.drawText(QRectF(0,0, self.width, self.height), Qt.AlignCenter, "Script Vacío")
        super().paint(painter, option, widget) 
    
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        event.accept()
