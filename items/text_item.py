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
from demo import ITEM_TEXT 

class TextItem(DiagramItem):
    def __init__(self, text="Texto", parent=None):
        super().__init__(ITEM_TEXT, parent)
        self.properties["text"] = text
        self.properties["font_size"] = 12
        self.properties["fill_color"] = "transparent" 
        self.properties["border_color"] = "transparent" 
        self._adjust_size_to_text()

    def _adjust_size_to_text(self):
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        metrics = QFontMetrics(font) 
        text_width = float(metrics.horizontalAdvance(self.properties["text"]))
        text_height = float(metrics.height())
        self.width = text_width + 10.0 
        self.height = text_height + 5.0
        self.prepareGeometryChange()
        self.update_appearance()

    def paint(self, painter, option, widget=None):
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(QColor(self.properties.get("text_color", "#000000"))) 
        painter.drawText(QRectF(0.0, 0.0, self.width, self.height), Qt.AlignCenter | Qt.TextWordWrap, self.properties["text"])
        if self.isSelected():
            super().paint(painter, option, widget) 

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            event.accept() 
            return

        parent_widget = None
        if self.scene() and self.scene().views():
            parent_widget = self.scene().views()[0] 
        elif self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent():
             parent_widget = self.scene().parent() 
        
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_capture_history_state'):
            self.scene().parent()._capture_history_state(f"Inicio edición de {self.properties.get('text', 'Texto')}")

        text, ok = QInputDialog.getText(parent_widget, 
                                        "Editar Texto", "Nuevo texto:", 
                                        text=self.properties["text"])
        if ok and text is not None: 
            if self.properties["text"] != text:
                self.properties["text"] = text
                self._adjust_size_to_text() 
                if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
                    self.scene().parent().on_diagram_modified(capture_state=False) 
        elif ok and self.properties["text"] == text: 
             if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_history_stack') and self.scene().parent()._history_stack:
                self.scene().parent()._history_stack.pop() 
                self.scene().parent()._update_history_list_widget()
        event.accept() 

    def set_properties(self, data):
        super().set_properties(data)
        # _adjust_size_to_text se llama desde el set_properties de DiagramItem si es TextItem
