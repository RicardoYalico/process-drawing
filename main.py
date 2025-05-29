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
    QAbstractItemView 
)
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QPolygonF, 
                         QTransform, QDrag, QIcon, QPixmap, QFontMetrics, 
                         QPainterPath, QPainterPathStroker, QKeySequence, QImage) 
from PyQt5.QtCore import (Qt, QPointF, QRectF, QSizeF, QMimeData, 
                          pyqtSignal, QSize, QLineF, QFileInfo, QBuffer, QIODevice) 

# --- Constantes de Tipos de Ítems ---
ITEM_RECTANGLE = "rectangle"
ITEM_ELLIPSE = "ellipse"
ITEM_DIAMOND = "diamond"
ITEM_TEXT = "text"
ITEM_CONTAINER = "container" 
ITEM_IMAGE = "image" 
ITEM_SCRIPT = "script"
ITEM_PERSONA = "persona" 
USER_IMAGE_PREFIX = "user_image_" 

# --- Clase Base DiagramItem ---
class DiagramItem(QGraphicsItem):
    item_type_signal = pyqtSignal(str) 

    def __init__(self, item_type, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True) 
        self.id = None 
        self._original_pos_on_press = None 
        self._original_geometry_on_press = None 
        
        self.original_item_geometry = QRectF() 
        self.original_scene_pos = QPointF()

        self.properties = {
            "fill_color": "#ddeeff",
            "border_color": "#000000",
            "text": "Item", 
            "font_size": 10
        }
        self.width = 100.0 
        self.height = 50.0 
        self.is_resizing = False
        self.resize_handle_size = 8
        self.current_resize_handle = None 
        self.parent_container_id = None
        self.child_item_ids = [] 

    def clone(self):
        ItemClassToClone = None
        item_class_info = AVAILABLE_ITEM_TYPES.get(self.item_type) 
        if not item_class_info and self.item_type.startswith(USER_IMAGE_PREFIX):
            item_class_info = AVAILABLE_ITEM_TYPES.get(ITEM_IMAGE)

        if item_class_info:
            ItemClassToClone = item_class_info["class"]
        
        if not ItemClassToClone: 
            print(f"Advertencia: No se pudo encontrar la clase para clonar el tipo '{self.item_type}'")
            return None

        cloned_item = None
        if self.item_type == ITEM_IMAGE or self.item_type.startswith(USER_IMAGE_PREFIX):
            cloned_item = ItemClassToClone(image_path=self.properties.get("image_path"))
        elif self.item_type == ITEM_TEXT:
            cloned_item = ItemClassToClone(text=self.properties.get("text", "Texto Clonado"))
        else:
            cloned_item = ItemClassToClone() 

        if cloned_item:
            cloned_item.width = self.width
            cloned_item.height = self.height
            cloned_item.properties = self.properties.copy()
            cloned_item.id = None 
            cloned_item.parent_container_id = None
            if cloned_item.item_type == ITEM_CONTAINER: 
                cloned_item.child_item_ids = list(self.child_item_ids) 
            else:
                cloned_item.child_item_ids = []
        return cloned_item


    def get_properties(self, for_clipboard=False): 
        props = {
            "type": self.item_type,
            "id": getattr(self, 'id', None) if not for_clipboard else None, 
            "x": self.x(),
            "y": self.y(),
            "width": self.width,
            "height": self.height,
            "properties": self.properties.copy(), 
            "parent_container_id": self.parent_container_id 
        }
        if self.item_type == ITEM_CONTAINER:
            props["child_item_ids"] = list(self.child_item_ids) 
        elif self.item_type == ITEM_IMAGE:
            props["image_path"] = self.properties.get("image_path", "")
        elif self.item_type == ITEM_SCRIPT:
            props["paint_script"] = self.properties.get("paint_script", "")
            
        return props

    def set_properties(self, data):
        if "x" in data and "y" in data: 
            self.setPos(data["x"], data["y"])
        
        self.width = float(data.get("width", self.width)) 
        self.height = float(data.get("height", self.height)) 
        
        item_specific_props = data.get("properties", {})
        self.properties.update(item_specific_props) 

        if "id" in data and data["id"] is not None: 
            self.id = data["id"]
        
        self.parent_container_id = data.get("parent_container_id") 
        
        if self.item_type == ITEM_CONTAINER: 
            self.child_item_ids = list(data.get("child_item_ids", []))
        else:
            self.child_item_ids = []

        if self.item_type == ITEM_IMAGE:
            img_path_from_data = data.get("image_path", self.properties.get("image_path"))
            if img_path_from_data:
                 self.properties["image_path"] = img_path_from_data
                 self.load_image_from_path() 
            else: 
                if hasattr(self, 'pixmap'): 
                    self.pixmap = QPixmap()
        elif self.item_type == ITEM_SCRIPT:
            self.properties["paint_script"] = data.get("paint_script", self.properties.get("paint_script",""))
        
        if self.item_type == ITEM_TEXT: 
            if hasattr(self, '_adjust_size_to_text'): 
                self._adjust_size_to_text()

        self.update_appearance()
        self.prepareGeometryChange() 

    def update_appearance(self):
        self.update() 

    def boundingRect(self):
        handle_offset = float(self.resize_handle_size)
        return QRectF(-handle_offset, -handle_offset,
                      self.width + 2 * handle_offset, self.height + 2 * handle_offset)

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            self.draw_resize_handles(painter)

    def draw_resize_handles(self, painter):
        painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
        painter.setBrush(Qt.white)
        size = float(self.resize_handle_size)
        painter.drawRect(QRectF(-size, -size, size, size)) 
        painter.drawRect(QRectF(self.width, -size, size, size)) 
        painter.drawRect(QRectF(-size, self.height, size, size)) 
        painter.drawRect(QRectF(self.width, self.height, size, size)) 
        painter.drawRect(QRectF(self.width / 2.0 - size / 2.0, -size, size, size)) 
        painter.drawRect(QRectF(self.width / 2.0 - size / 2.0, self.height, size, size)) 
        painter.drawRect(QRectF(-size, self.height / 2.0 - size / 2.0, size, size)) 
        painter.drawRect(QRectF(self.width, self.height / 2.0 - size / 2.0, size, size)) 


    def get_resize_handle_at(self, pos: QPointF):
        size = float(self.resize_handle_size)
        if QRectF(-size, -size, size, size).contains(pos): return "top_left"
        if QRectF(self.width, -size, size, size).contains(pos): return "top_right"
        if QRectF(-size, self.height, size, size).contains(pos): return "bottom_left"
        if QRectF(self.width, self.height, size, size).contains(pos): return "bottom_right"
        if QRectF(self.width / 2.0 - size / 2.0, -size, size, size).contains(pos): return "top_middle"
        if QRectF(self.width / 2.0 - size / 2.0, self.height, size, size).contains(pos): return "bottom_middle"
        if QRectF(-size, self.height / 2.0 - size / 2.0, size, size).contains(pos): return "left_middle"
        if QRectF(self.width, self.height / 2.0 - size / 2.0, size, size).contains(pos): return "right_middle"
        return None

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            self.setCursor(Qt.ArrowCursor)
            super().hoverMoveEvent(event)
            return

        handle = self.get_resize_handle_at(event.pos())
        if handle and self.isSelected(): 
            if handle in ["top_left", "bottom_right"]: self.setCursor(Qt.SizeFDiagCursor)
            elif handle in ["top_right", "bottom_left"]: self.setCursor(Qt.SizeBDiagCursor)
            elif handle in ["top_middle", "bottom_middle"]: self.setCursor(Qt.SizeVerCursor)
            elif handle in ["left_middle", "right_middle"]: self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mousePressEvent(event) 
            return

        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_capture_history_state'):
            self.scene().parent()._capture_history_state("Inicio de interacción con ítem")

        self._original_pos_on_press = self.pos() 
        self._original_geometry_on_press = QRectF(0.0, 0.0, self.width, self.height) 

        if self.isSelected(): 
            self.current_resize_handle = self.get_resize_handle_at(event.pos())
            if self.current_resize_handle:
                self.is_resizing = True
                self.resize_start_pos = event.pos() 
                self.original_item_geometry = QRectF(0.0, 0.0, self.width, self.height) 
                self.original_scene_pos = self.pos() 
                event.accept() 
                return
        self.is_resizing = False
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mouseMoveEvent(event) 
            return

        if self.is_resizing and self.current_resize_handle and self.isSelected():
            if not hasattr(self, 'original_item_geometry') or self.original_item_geometry.isNull():
                print("Advertencia: original_item_geometry no está configurado en mouseMoveEvent")
                self.original_item_geometry = QRectF(0.0, 0.0, self.width, self.height) 

            delta = event.pos() - self.resize_start_pos 

            new_x = self.original_scene_pos.x()
            new_y = self.original_scene_pos.y()
            new_width = self.original_item_geometry.width()
            new_height = self.original_item_geometry.height()

            if "left" in self.current_resize_handle:
                new_width -= delta.x()
                new_x += delta.x() 
            elif "right" in self.current_resize_handle:
                new_width += delta.x()

            if "top" in self.current_resize_handle:
                new_height -= delta.y()
                new_y += delta.y()
            elif "bottom" in self.current_resize_handle:
                new_height += delta.y()
            
            min_size = 10.0
            if new_width < min_size:
                if "left" in self.current_resize_handle:
                    new_x = self.original_scene_pos.x() + self.original_item_geometry.width() - min_size
                new_width = min_size
            
            if new_height < min_size:
                if "top" in self.current_resize_handle:
                    new_y = self.original_scene_pos.y() + self.original_item_geometry.height() - min_size
                new_height = min_size

            self.prepareGeometryChange()
            self.setPos(new_x, new_y) 
            self.width = new_width   
            self.height = new_height 
            self.update_appearance()
            event.accept()
        else:
            super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mouseReleaseEvent(event)
            return

        action_description = None
        state_changed = False

        if self.is_resizing:
            self.is_resizing = False
            self.current_resize_handle = None
            self.setCursor(Qt.ArrowCursor)
            if self._original_geometry_on_press != QRectF(0.0, 0.0, self.width, self.height) or \
               self._original_pos_on_press != self.pos():
                action_description = f"Redimensionar {self.properties.get('text', self.item_type)}"
                state_changed = True
            event.accept()
        elif self._original_pos_on_press is not None and self._original_pos_on_press != self.pos():
            action_description = f"Mover {self.properties.get('text', self.item_type)}"
            state_changed = True
        
        self._original_pos_on_press = None 
        self._original_geometry_on_press = None

        if state_changed and self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
            self.scene().parent().on_diagram_modified(capture_state=False, action_description=action_description if action_description else "Cambio de ítem") 
        
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            if hasattr(self, 'id'): 
                if hasattr(self.scene(), 'get_connectors_for_item'):
                     connectors = self.scene().get_connectors_for_item(self)
                     for connector in connectors:
                        connector.update_position()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mouseDoubleClickEvent(event) 
            return

        if self.item_type not in [ITEM_CONTAINER, ITEM_SCRIPT, ITEM_IMAGE, ITEM_TEXT]: 
            parent_widget = None
            if self.scene() and self.scene().views():
                parent_widget = self.scene().views()[0]
            elif self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent():
                parent_widget = self.scene().parent()

            current_text = self.properties.get("text", "")
            
            if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_capture_history_state'):
                self.scene().parent()._capture_history_state(f"Inicio edición texto de {self.properties.get('text', self.item_type)}")

            text, ok = QInputDialog.getText(parent_widget, 
                                            f"Editar Texto de {self.properties.get('text', self.item_type.capitalize())}", 
                                            "Nuevo texto:", 
                                            text=current_text)
            if ok and text != current_text:
                self.properties["text"] = text
                self.update_appearance() 
                if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
                    self.scene().parent().on_diagram_modified(capture_state=False, action_description=f"Texto editado en {getattr(self, 'id', self.item_type)}")
            elif ok and text == current_text: 
                 if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_history_stack') and self.scene().parent()._history_stack: 
                    self.scene().parent()._history_stack.pop() 
                    self.scene().parent()._update_history_list_widget() 

            event.accept()
        else: 
            super().mouseDoubleClickEvent(event)


# --- Ítems Específicos ---
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

class EllipseItem(DiagramItem):
    def __init__(self, parent=None):
        super().__init__(ITEM_ELLIPSE, parent)
        self.properties["text"] = "Elipse"

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(QColor(self.properties["border_color"]), 2))
        painter.setBrush(QBrush(QColor(self.properties["fill_color"])))
        painter.drawEllipse(QRectF(0.0, 0.0, self.width, self.height))
        font = QFont()
        font.setPointSize(self.properties["font_size"])
        painter.setFont(font)
        painter.setPen(Qt.black)
        painter.drawText(QRectF(0.0, 0.0, self.width, self.height), Qt.AlignCenter | Qt.TextWordWrap, self.properties["text"])
        super().paint(painter, option, widget)

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


# Conector entre ítems (Clase Modificada)
class Connector(QGraphicsItem): 
    def __init__(self, start_item, end_item, parent=None):
        super().__init__(parent)
        self.start_item = start_item 
        self.end_item = end_item   
        self.setZValue(-1) 
        self.line_color = QColor("#333333")
        self.line_width = 2.0 
        self.arrow_size = 10.0 
        self.id = None 
        self.text = "" 
        self.font_size = 9

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True) 

        self._dragging_end = None  
        self._original_item_at_drag_end = None 
        self._current_drag_pos = None 
        self.end_point_handle_radius = 6.0 

        self.update_position()

    def get_properties(self, for_clipboard=False): 
        start_id = getattr(self.start_item, 'id', None)
        end_id = getattr(self.end_item, 'id', None)

        if start_id and end_id:
            return {
                "type": "connector", 
                "id": getattr(self, 'id', None) if not for_clipboard else None,
                "start_item_id": start_id,
                "end_item_id": end_id,
                "line_color": self.line_color.name(),
                "line_width": self.line_width,
                "text": self.text, 
                "font_size": self.font_size 
            }
        return None

    def set_properties(self, data, items_by_id): 
        self.line_color = QColor(data.get("line_color", self.line_color.name()))
        self.line_width = float(data.get("line_width", self.line_width))
        self.text = data.get("text", "") 
        self.font_size = data.get("font_size", 9) 

        if "id" in data and data["id"] is not None:
            self.id = data["id"]
        
        if items_by_id: 
            start_item_id = data.get("start_item_id")
            end_item_id = data.get("end_item_id")
            if start_item_id in items_by_id:
                self.start_item = items_by_id[start_item_id]
            if end_item_id in items_by_id:
                self.end_item = items_by_id[end_item_id]
        self.update()

    def _get_intersection_with_boundary(self, line_to_center: QLineF, item: DiagramItem) -> QPointF:
        """Calcula el punto de intersección de la línea con el boundingRect del ítem."""
        if not item or line_to_center.length() == 0:
            return line_to_center.p2() 

        item_rect_local = item.boundingRect() 
        item_scene_poly = item.mapToScene(item_rect_local) 
        item_scene_rect = item_scene_poly.boundingRect()


        sides = [
            QLineF(item_scene_rect.topLeft(), item_scene_rect.topRight()),
            QLineF(item_scene_rect.topRight(), item_scene_rect.bottomRight()),
            QLineF(item_scene_rect.bottomRight(), item_scene_rect.bottomLeft()),
            QLineF(item_scene_rect.bottomLeft(), item_scene_rect.topLeft())
        ]

        closest_intersection = line_to_center.p2() 
        min_dist_sq = float('inf')

        for side in sides:
            intersect_type, intersection_point = line_to_center.intersects(side)
            if intersect_type == QLineF.BoundedIntersection:
                # CORRECCIÓN: Usar .length() * .length() en lugar de .lengthSquared()
                current_dist_line = QLineF(line_to_center.p1(), intersection_point)
                current_dist_sq = current_dist_line.length() * current_dist_line.length()
                if current_dist_sq < min_dist_sq:
                    line_vec = line_to_center.unitVector()
                    p1_to_intersect_vec = intersection_point - line_to_center.p1()
                    dot_product = QPointF.dotProduct(QPointF(line_vec.dx(), line_vec.dy()), p1_to_intersect_vec)
                    
                    if dot_product >= -1e-6 : 
                        min_dist_sq = current_dist_sq
                        closest_intersection = intersection_point
        
        return closest_intersection


    def _calculate_adjusted_endpoints(self):
        p1_center = self.start_item.mapToScene(self.start_item.boundingRect().center())
        p2_center = self.end_item.mapToScene(self.end_item.boundingRect().center())

        if self._dragging_end == 'start' and self._current_drag_pos:
            p1_center = self._current_drag_pos
        if self._dragging_end == 'end' and self._current_drag_pos:
            p2_center = self._current_drag_pos
        
        line_start_to_end = QLineF(p1_center, p2_center)
        line_end_to_start = QLineF(p2_center, p1_center)

        p1_adjusted = p1_center
        p2_adjusted = p2_center

        if self.start_item and not (self._dragging_end == 'start' and self._current_drag_pos):
            p1_adjusted = self._get_intersection_with_boundary(line_end_to_start, self.start_item)
        
        if self.end_item and not (self._dragging_end == 'end' and self._current_drag_pos):
            p2_adjusted = self._get_intersection_with_boundary(line_start_to_end, self.end_item)
            
        return p1_adjusted, p2_adjusted


    def get_line_endpoints_scene(self): 
        p1, p2 = None, None
        if self.start_item:
            p1 = self.start_item.mapToScene(self.start_item.boundingRect().center())
        if self.end_item:
            p2 = self.end_item.mapToScene(self.end_item.boundingRect().center())
        
        if self._dragging_end == 'start' and self._current_drag_pos:
            p1 = self._current_drag_pos
            if not self.end_item and p2 is None:
                 pass
        elif self._dragging_end == 'end' and self._current_drag_pos:
            p2 = self._current_drag_pos
            if not self.start_item and p1 is None:
                 pass
        return p1, p2

    def shape(self):
        path = QPainterPath()
        p1_scene, p2_scene = self._calculate_adjusted_endpoints() 
        
        if p1_scene is None or p2_scene is None: 
            return path 

        p1_local = self.mapFromScene(p1_scene)
        p2_local = self.mapFromScene(p2_scene)
        
        path.moveTo(p1_local)
        path.lineTo(p2_local)
        
        stroker = QPainterPathStroker() 
        stroker.setWidth(self.end_point_handle_radius * 2.5) 
        stroked_path = stroker.createStroke(path)
        
        if self.isSelected():
            stroked_path.addEllipse(p1_local, self.end_point_handle_radius, self.end_point_handle_radius)
            stroked_path.addEllipse(p2_local, self.end_point_handle_radius, self.end_point_handle_radius)
            
        return stroked_path

    def boundingRect(self):
        p1_scene, p2_scene = self._calculate_adjusted_endpoints() 
        if p1_scene is None or p2_scene is None:
            return QRectF()
        
        p1_local = self.mapFromScene(p1_scene)
        p2_local = self.mapFromScene(p2_scene)
        
        text_bound_rect = QRectF()
        if self.text:
            font = QFont()
            font.setPointSize(self.font_size)
            fm = QFontMetrics(font)
            text_rect_size = fm.boundingRect(self.text)
            mid_point = (p1_local + p2_local) / 2.0
            text_bound_rect = QRectF(mid_point - QPointF(text_rect_size.width()/2, text_rect_size.height()/2), 
                                     QSizeF(text_rect_size.width(), text_rect_size.height()))

        line_rect = QRectF(p1_local, p2_local).normalized()
        combined_rect = line_rect.united(text_bound_rect) 

        margin = self.arrow_size + self.line_width + self.end_point_handle_radius
        return combined_rect.adjusted(-margin, -margin, margin, margin)


    def paint(self, painter, option, widget=None):
        p1_scene, p2_scene = self._calculate_adjusted_endpoints()

        if not (p1_scene and p2_scene): 
            return

        p1_local = self.mapFromScene(p1_scene)
        p2_local = self.mapFromScene(p2_scene)
        line_local = QLineF(p1_local, p2_local)

        pen = QPen(self.line_color, self.line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        if self.isSelected():
            pen.setStyle(Qt.DashLine) 
        painter.setPen(pen)
        painter.drawLine(line_local)

        if self.text:
            font = QFont()
            font.setPointSize(self.font_size)
            painter.setFont(font)
            painter.setPen(Qt.black) 
            
            mid_point = line_local.pointAt(0.5)
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(self.text)
            text_height = fm.height()
            
            text_bg_rect = QRectF(mid_point.x() - text_width / 2 - 2, 
                                  mid_point.y() - text_height / 2 - 2,
                                  text_width + 4, text_height + 4)
            painter.setBrush(QColor(255, 255, 255, 180)) 
            painter.setPen(Qt.NoPen) 
            painter.drawRoundedRect(text_bg_rect, 3, 3)

            painter.setPen(Qt.black)
            painter.drawText(text_bg_rect, Qt.AlignCenter, self.text)


        if not (self._dragging_end == 'end' and self._current_drag_pos): 
            if line_local.length() > self.arrow_size: 
                angle_rad = math.atan2(-line_local.dy(), line_local.dx()) 
                arrow_tip_point = line_local.p2() 

                arrow_p1 = arrow_tip_point - QPointF(math.cos(angle_rad + math.pi / 6.0) * self.arrow_size,
                                            -math.sin(angle_rad + math.pi / 6.0) * self.arrow_size) 
                arrow_p2_actual = arrow_tip_point - QPointF(math.cos(angle_rad - math.pi / 6.0) * self.arrow_size,
                                            -math.sin(angle_rad - math.pi / 6.0) * self.arrow_size)
                arrow_head = QPolygonF([arrow_tip_point, arrow_p1, arrow_p2_actual])
                painter.setBrush(QBrush(self.line_color))
                painter.drawPolygon(arrow_head)
        
        if self.isSelected():
            painter.setBrush(Qt.white)
            painter.setPen(Qt.black)
            painter.drawEllipse(p1_local, self.end_point_handle_radius, self.end_point_handle_radius)
            painter.drawEllipse(p2_local, self.end_point_handle_radius, self.end_point_handle_radius)

    def update_position(self):
        self.prepareGeometryChange() 
        self.update() 

    def get_point_at_event(self, event_pos_local: QPointF):
        p1_scene, p2_scene = self._calculate_adjusted_endpoints() 
        if p1_scene is None or p2_scene is None: return None

        p1_local = self.mapFromScene(p1_scene)
        p2_local = self.mapFromScene(p2_scene)

        if QLineF(event_pos_local, p1_local).length() < self.end_point_handle_radius * 1.5: 
            return 'start'
        if QLineF(event_pos_local, p2_local).length() < self.end_point_handle_radius * 1.5:
            return 'end'
        return None

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent): 
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            self.setCursor(Qt.ArrowCursor)
            super().hoverMoveEvent(event)
            return

        if self.isSelected():
            if self.get_point_at_event(event.pos()):
                self.setCursor(Qt.CrossCursor) 
            else:
                self.setCursor(Qt.PointingHandCursor) 
        else:
            if self.shape().contains(event.pos()):
                 self.setCursor(Qt.PointingHandCursor)
            else:
                 self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event) 

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent): 
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mousePressEvent(event)
            return
            
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_capture_history_state'):
            self.scene().parent()._capture_history_state("Inicio interacción con conector")

        if self.isSelected() and event.button() == Qt.LeftButton:
            drag_candidate = self.get_point_at_event(event.pos())
            if drag_candidate == 'start':
                self._dragging_end = 'start'
                self._original_item_at_drag_end = self.start_item
                self._current_drag_pos = event.scenePos()
                self.update()
                event.accept()
                return
            elif drag_candidate == 'end':
                self._dragging_end = 'end'
                self._original_item_at_drag_end = self.end_item
                self._current_drag_pos = event.scenePos()
                self.update()
                event.accept()
                return
        self._dragging_end = None 
        super().mousePressEvent(event) 

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent): 
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mouseMoveEvent(event)
            return

        if self._dragging_end and self.scene():
            self._current_drag_pos = event.scenePos()
            self.update_position() 
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent): 
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and \
           hasattr(self.scene().parent(), 'is_viewing_history') and self.scene().parent().is_viewing_history:
            super().mouseReleaseEvent(event)
            return

        action_description = None 
        state_changed = False

        if self._dragging_end and self.scene():
            if self._current_drag_pos is None:
                 self._current_drag_pos = event.scenePos() 

            item_at_release = self.scene().itemAt(self._current_drag_pos, QTransform())
            
            new_target_item = None
            if isinstance(item_at_release, DiagramItem) and \
               not isinstance(item_at_release, Connector) and \
               item_at_release.isVisible():
                if self._dragging_end == 'start' and item_at_release != self.end_item:
                    new_target_item = item_at_release
                elif self._dragging_end == 'end' and item_at_release != self.start_item:
                    new_target_item = item_at_release
            
            modified_connection = False
            if new_target_item:
                if self._dragging_end == 'start':
                    if self.start_item != new_target_item:
                        self.start_item = new_target_item
                        modified_connection = True
                elif self._dragging_end == 'end':
                    if self.end_item != new_target_item:
                        self.end_item = new_target_item
                        modified_connection = True
            elif self._original_item_at_drag_end: 
                if self._dragging_end == 'start':
                    self.start_item = self._original_item_at_drag_end
                elif self._dragging_end == 'end':
                    self.end_item = self._original_item_at_drag_end
            
            self._dragging_end = None
            self._current_drag_pos = None
            self._original_item_at_drag_end = None
            self.update_position()

            if modified_connection:
                action_description = f"Reconectar {getattr(self, 'id', 'conector')}"
                state_changed = True
            
            self.setCursor(Qt.ArrowCursor) 
            event.accept()
        else:
            super().mouseReleaseEvent(event)
        
        if state_changed and self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
            self.scene().parent().on_diagram_modified(capture_state=False, action_description=action_description) 
            
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
            self.scene().parent()._capture_history_state(f"Inicio edición texto de conector {self.id}")

        text, ok = QInputDialog.getText(parent_widget, "Editar Texto del Conector", 
                                        "Texto:", text=self.text)
        if ok: 
            if self.text != text:
                self.text = text
                self.update_position() 
                if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
                    self.scene().parent().on_diagram_modified(capture_state=False, action_description=f"Texto editado en conector {self.id}") 
        elif ok and self.text == text: 
             if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), '_history_stack') and self.scene().parent()._history_stack: 
                self.scene().parent()._history_stack.pop() 
                self.scene().parent()._update_history_list_widget() 
        event.accept()


# --- Registro de Tipos de Ítems Disponibles ---
AVAILABLE_ITEM_TYPES = {
    ITEM_RECTANGLE: {"class": RectangleItem, "icon_char": "📦", "name": "Rectángulo"},
    ITEM_ELLIPSE:   {"class": EllipseItem,   "icon_char": "🔵", "name": "Elipse"},
    ITEM_DIAMOND:   {"class": DiamondItem,   "icon_char": "💠", "name": "Decisión"},
    ITEM_TEXT:      {"class": TextItem,      "icon_char": "✍️", "name": "Texto"},
    ITEM_CONTAINER: {"class": ContainerItem, "icon_char": "🗳️", "name": "Contenedor"},
    ITEM_IMAGE:     {"class": ImageItem,     "icon_char": "🖼️", "name": "Imagen (Importar)"}, 
    ITEM_SCRIPT:    {"class": ScriptItem,    "icon_char": "📜", "name": "Script"},
    ITEM_PERSONA:   {"class": PersonaItem,   "icon_char": "👤", "name": "Persona"}, 
}


# Escena Gráfica Personalizada
class DiagramScene(QGraphicsScene):
    item_added = pyqtSignal(QGraphicsItem)
    item_removed = pyqtSignal(QGraphicsItem)
    item_selected = pyqtSignal(QGraphicsItem, bool) 
    items_visibility_changed = pyqtSignal() 

    def __init__(self, parent=None): 
        super().__init__(parent)
        self.setSceneRect(0.0, 0.0, 2000.0, 1500.0) 
        self.setBackgroundBrush(QBrush(QColor("#E8E8E8"))) 
        self.grid_size = 20.0
        self.draw_grid = True
        self.connecting_line = None
        self.start_connection_item = None
        self.next_item_id_counter = 1 
        self.active_container_id = None 
        self.items_by_id = {} 

    def get_next_item_id(self):
        current_id_val = self.next_item_id_counter
        self.next_item_id_counter += 1
        return f"item_{current_id_val}"

    def add_item_to_cache(self, item):
        if hasattr(item, 'id') and item.id:
            self.items_by_id[item.id] = item

    def remove_item_from_cache(self, item):
        if hasattr(item, 'id') and item.id and item.id in self.items_by_id:
            del self.items_by_id[item.id]
            
    def clear(self):
        if self.parent() and hasattr(self.parent(), 'on_diagram_modified'):
            try:
                self.item_added.disconnect()
                self.item_removed.disconnect()
            except TypeError: 
                pass

        items_to_delete = list(self.items())
        for item in items_to_delete:
            if item.scene() == self: 
                self.removeItem(item) 
        
        self.items_by_id.clear()
        self.active_container_id = None
        self.next_item_id_counter = 1
        self.update_all_items_visibility() 

        if self.parent() and hasattr(self.parent(), 'on_diagram_modified'):
            self.item_added.connect(lambda item: self.parent().on_diagram_modified(action_description=f"Añadir {getattr(item, 'item_type', 'elemento')}"))
            self.item_removed.connect(
                lambda item: self.parent().on_diagram_modified(
                    action_description=f"Eliminar {getattr(item, 'item_type', type(item).__name__)}"
                ) if isinstance(item, (DiagramItem, Connector)) else None
            )


    def add_diagram_item(self, item_type_str, position: QPointF, item_data=None):
        item_class_info = AVAILABLE_ITEM_TYPES.get(item_type_str)
        actual_item_type_for_class_lookup = item_type_str 
        is_user_image = False

        if not item_class_info and item_type_str.startswith(USER_IMAGE_PREFIX):
            actual_item_type_for_class_lookup = ITEM_IMAGE 
            item_class_info = AVAILABLE_ITEM_TYPES.get(actual_item_type_for_class_lookup)
            is_user_image = True
            
            if item_data is None: item_data = {}
            item_data['image_path'] = item_type_str.replace(USER_IMAGE_PREFIX, "")
            item_data['type'] = ITEM_IMAGE 

        if not item_class_info:
            print(f"Error: Tipo de ítem desconocido '{item_type_str}'")
            return None
        
        ItemClass = item_class_info["class"]
        item = None

        properties_to_set = item_data.copy() if item_data else {}
        if "x" in properties_to_set and item_data is not None and "id" not in item_data : 
            del properties_to_set["x"] 
        if "y" in properties_to_set and item_data is not None and "id" not in item_data : 
            del properties_to_set["y"]


        if actual_item_type_for_class_lookup == ITEM_IMAGE:
            path_for_constructor = None
            if item_data and "image_path" in item_data: 
                path_for_constructor = item_data["image_path"]
            elif item_data and "properties" in item_data and "image_path" in item_data["properties"]: 
                path_for_constructor = item_data["properties"]["image_path"]
            item = ItemClass(image_path=path_for_constructor)

        elif actual_item_type_for_class_lookup == ITEM_TEXT:
            text_content = "Texto" 
            if item_data and "properties" in item_data and "text" in item_data["properties"]:
                text_content = item_data["properties"]["text"]
            elif item_data and "text" in item_data: 
                 text_content = item_data["text"]
            item = ItemClass(text=text_content)
        else:
            item = ItemClass()
        
        if item:
            item.setPos(position) 
            
            if properties_to_set: 
                item.set_properties(properties_to_set) 
            
            if not hasattr(item, 'id') or not item.id: 
                item.id = self.get_next_item_id()
            
            if is_user_image: 
                item.item_type = ITEM_IMAGE 
            
            self.addItem(item) 
            self.add_item_to_cache(item)
            self.apply_container_visibility(item) 
            self.item_added.emit(item) 
        return item


    def removeItem(self, item_to_remove): 
        self.remove_item_from_cache(item_to_remove)
        if isinstance(item_to_remove, ContainerItem) and hasattr(item_to_remove, 'id') and item_to_remove.id:
            children_ids_to_remove = list(item_to_remove.child_item_ids) 
            for child_id in children_ids_to_remove:
                child_item = self.items_by_id.get(child_id) 
                if child_item and child_item.scene() == self: 
                    self.removeItem(child_item) 

            if self.active_container_id == item_to_remove.id:
                self.leave_container_context()

        if hasattr(item_to_remove, 'parent_container_id') and item_to_remove.parent_container_id:
            parent_container = self.items_by_id.get(item_to_remove.parent_container_id)
            if isinstance(parent_container, ContainerItem):
                if hasattr(item_to_remove, 'id') and item_to_remove.id in parent_container.child_item_ids:
                     parent_container.remove_child_item(item_to_remove.id)
        
        connectors = self.get_connectors_for_item(item_to_remove)
        for connector in list(connectors): 
            if connector.scene() == self:
                self.removeItem(connector) 

        super().removeItem(item_to_remove) 
        self.item_removed.emit(item_to_remove)


    def drawBackground(self, painter, rect: QRectF):
        super().drawBackground(painter, rect)
        if self.draw_grid:
            left = float(int(rect.left()) - (int(rect.left()) % int(self.grid_size)))
            top = float(int(rect.top()) - (int(rect.top()) % int(self.grid_size)))
            
            lines = []
            for x_coord in range(int(left), int(rect.right()), int(self.grid_size)):
                lines.append(QLineF(float(x_coord), rect.top(), float(x_coord), rect.bottom()))
            for y_coord in range(int(top), int(rect.bottom()), int(self.grid_size)):
                lines.append(QLineF(rect.left(), float(y_coord), rect.right(), float(y_coord)))
            
            pen = QPen(QColor("#D0D0D0"), 0.5) 
            painter.setPen(pen)
            painter.drawLines(lines)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        item_at_click = self.itemAt(event.scenePos(), QTransform())
        
        if isinstance(item_at_click, Connector):
            super().mousePressEvent(event) 
            return 

        if event.button() == Qt.RightButton and isinstance(item_at_click, DiagramItem):
            self.start_connection_item = item_at_click
            start_point = self.start_connection_item.mapToScene(self.start_connection_item.boundingRect().center())
            self.connecting_line = QGraphicsLineItem(QLineF(start_point, event.scenePos()))
            self.connecting_line.setPen(QPen(Qt.black, 2, Qt.DashLine))
            self.connecting_line.setZValue(0) 
            self.addItem(self.connecting_line)
            event.accept() 
        else:
            super().mousePressEvent(event) 

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.connecting_line and self.start_connection_item:
            start_point = self.start_connection_item.mapToScene(self.start_connection_item.boundingRect().center())
            self.connecting_line.setLine(QLineF(start_point, event.scenePos()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.connecting_line and self.start_connection_item:
            if self.connecting_line.scene() == self: 
                 self.removeItem(self.connecting_line) 
            self.connecting_line = None
            
            item_at_release = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item_at_release, DiagramItem) and \
               not isinstance(item_at_release, Connector) and \
               item_at_release != self.start_connection_item:
                
                if self.parent() and hasattr(self.parent(), '_capture_history_state'):
                    self.parent()._capture_history_state("Conector añadido") 

                connector = Connector(self.start_connection_item, item_at_release)
                connector.id = self.get_next_item_id() 
                self.addItem(connector)
                self.add_item_to_cache(connector)
                self.apply_container_visibility(connector) 
                self.item_added.emit(connector) 
                if self.parent() and hasattr(self.parent(), 'on_diagram_modified'):
                    self.parent().on_diagram_modified(capture_state=False) 
            
            self.start_connection_item = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def get_connectors_for_item(self, diagram_item):
        connectors = []
        if not diagram_item or not hasattr(diagram_item, 'id'): return connectors
        item_id = diagram_item.id
        for conn_id, potential_connector in self.items_by_id.items():
            if isinstance(potential_connector, Connector):
                if hasattr(potential_connector.start_item, 'id') and \
                   hasattr(potential_connector.end_item, 'id') and \
                   potential_connector.start_item.id and \
                   potential_connector.end_item.id: 
                    if potential_connector.start_item.id == item_id or potential_connector.end_item.id == item_id:
                        connectors.append(potential_connector)
        return connectors

    def remove_selected(self):
        selected_graphics_items = self.selectedItems() 
        if not selected_graphics_items:
            return

        all_items_to_remove_recursively = set()
        
        def find_all_children_recursively(container_item, items_set):
            if isinstance(container_item, ContainerItem):
                for child_id in container_item.child_item_ids:
                    child = self.items_by_id.get(child_id)
                    if child and child not in items_set:
                        items_set.add(child)
                        find_all_children_recursively(child, items_set) 

        for q_item in selected_graphics_items:
            item_id = getattr(q_item, 'id', None)
            actual_item = self.items_by_id.get(item_id) if item_id else None
            if actual_item is None and isinstance(q_item, (DiagramItem, Connector)):
                actual_item = q_item 

            if actual_item:
                all_items_to_remove_recursively.add(actual_item)
                if isinstance(actual_item, DiagramItem):
                    for conn in self.get_connectors_for_item(actual_item):
                        all_items_to_remove_recursively.add(conn)
                    find_all_children_recursively(actual_item, all_items_to_remove_recursively)
        
        for item_to_check_connectors in list(all_items_to_remove_recursively): 
            if isinstance(item_to_check_connectors, DiagramItem):
                 for conn in self.get_connectors_for_item(item_to_check_connectors):
                    all_items_to_remove_recursively.add(conn)


        connectors_first = sorted(list(all_items_to_remove_recursively), key=lambda x: isinstance(x, Connector), reverse=True)
        
        for item_to_delete in connectors_first:
            if item_to_delete.scene() == self: 
                self.removeItem(item_to_delete) 
    
    def selectionChanged(self):
        selected = self.selectedItems()
        if selected:
            self.item_selected.emit(selected[0], True) 
        else:
            self.item_selected.emit(None, False) 
        super().selectionChanged()

    def enter_container_context(self, container_item):
        if isinstance(container_item, ContainerItem) and container_item.id:
            self.active_container_id = container_item.id
            self.update_all_items_visibility()
            if self.parent() and hasattr(self.parent(), 'update_navigation_buttons'):
                self.parent().update_navigation_buttons()


    def leave_container_context(self):
        if self.active_container_id:
            self.active_container_id = None 
            self.update_all_items_visibility()
            if self.parent() and hasattr(self.parent(), 'update_navigation_buttons'):
                self.parent().update_navigation_buttons()


    def update_all_items_visibility(self):
        for item_id, item in list(self.items_by_id.items()): 
            if isinstance(item, DiagramItem): 
                 self.apply_container_visibility(item)
            elif isinstance(item, Connector): 
                 self.apply_container_visibility(item)
        self.items_visibility_changed.emit() 

    def apply_container_visibility(self, item): 
        if isinstance(item, DiagramItem):
            if self.active_container_id is None: 
                item.setVisible(item.parent_container_id is None)
            else: 
                if item.id == self.active_container_id: 
                    item.setVisible(False) 
                else: 
                    item.setVisible(item.parent_container_id == self.active_container_id)
        elif isinstance(item, Connector):
            if hasattr(item, 'start_item') and item.start_item and \
               hasattr(item, 'end_item') and item.end_item:
                item.setVisible(item.start_item.isVisible() and item.end_item.isVisible())
            else: 
                item.setVisible(False)

    def get_visible_items_bounding_rect(self):
        overall_rect = QRectF()
        first_item = True
        for item_id, item in self.items_by_id.items():
            if item.isVisible():
                if first_item:
                    overall_rect = item.sceneBoundingRect()
                    first_item = False
                else:
                    overall_rect = overall_rect.united(item.sceneBoundingRect())
        return overall_rect


    def get_current_path_string(self):
        if not self.active_container_id:
            return "/"
        
        path_parts = []
        current_id_for_path = self.active_container_id
        temp_visited_ids = set() 
        
        while current_id_for_path and current_id_for_path not in temp_visited_ids:
            temp_visited_ids.add(current_id_for_path)
            container = self.items_by_id.get(current_id_for_path)
            if container and isinstance(container, ContainerItem): 
                path_parts.append(container.properties.get("text", container.id))
                current_id_for_path = container.parent_container_id 
            else: 
                break 
        
        return "/ " + " / ".join(reversed(path_parts)) if path_parts else "/"


# Vista Gráfica Personalizada
class DiagramView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing) 
        self.setRenderHint(QPainter.TextAntialiasing) 
        self.setDragMode(QGraphicsView.RubberBandDrag) 
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse) 
        self.zoom_factor = 1.15
        self.current_zoom = 1.0

        self.setAcceptDrops(True) 

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_view(self.zoom_factor)
            else:
                self.scale_view(1.0 / self.zoom_factor)
            event.accept() 
        else:
            super().wheelEvent(event) 

    def scale_view(self, factor):
        self.scale(factor, factor)
        self.current_zoom *= factor


    def keyPressEvent(self, event):
        main_app = self.scene().parent() if self.scene() else None
        if not main_app:
            super().keyPressEvent(event)
            return

        if main_app.is_viewing_history: 
            if event.modifiers() == Qt.ControlModifier:
                if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                    self.scale_view(self.zoom_factor)
                elif event.key() == Qt.Key_Minus or event.key() == Qt.Key_Underscore: 
                    self.scale_view(1.0 / self.zoom_factor)
                elif event.key() == Qt.Key_0: 
                    self.resetTransform()
                    self.current_zoom = 1.0
            elif event.key() == Qt.Key_Escape: 
                if isinstance(self.scene(), DiagramScene) and self.scene().active_container_id:
                    self.scene().leave_container_context() 
                else:
                    main_app.exit_history_view_mode() 
            super().keyPressEvent(event) 
            return

        if event.key() == Qt.Key_Delete:
            if isinstance(self.scene(), DiagramScene):
                if hasattr(main_app, 'delete_selected_items'):
                    main_app.delete_selected_items()
        
        elif event.matches(QKeySequence.Copy): 
            if hasattr(main_app, 'copy_selected_item'):
                main_app.copy_selected_item()
        elif event.matches(QKeySequence.Paste): 
            if hasattr(main_app, 'paste_item'):
                paste_pos = self.mapToScene(self.viewport().rect().center())
                main_app.paste_item(paste_pos)
        # Ctrl+Z y Ctrl+Y se manejan por acciones de menú/toolbar en DiagramApp

        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.scale_view(self.zoom_factor)
            elif event.key() == Qt.Key_Minus or event.key() == Qt.Key_Underscore: 
                self.scale_view(1.0 / self.zoom_factor)
            elif event.key() == Qt.Key_0: 
                self.resetTransform()
                self.current_zoom = 1.0 
        elif event.key() == Qt.Key_Escape: 
            if isinstance(self.scene(), DiagramScene) and self.scene().active_container_id:
                self.scene().leave_container_context()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-diagram-item-type"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-diagram-item-type"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        main_app = self.scene().parent() if self.scene() else None
        if main_app and hasattr(main_app, 'is_viewing_history') and main_app.is_viewing_history:
            event.ignore() 
            return

        if event.mimeData().hasFormat("application/x-diagram-item-type"):
            item_type_data = event.mimeData().data("application/x-diagram-item-type")
            item_type_str = str(item_type_data, encoding='utf-8') 
            
            drop_scene_pos = self.mapToScene(event.pos()) 
            target_graphics_item = self.scene().itemAt(drop_scene_pos, self.transform()) 

            if isinstance(self.scene(), DiagramScene):
                item_data_for_add = {} 
                
                if item_type_str == ITEM_TEXT:
                    text, ok = QInputDialog.getText(self, "Añadir Texto", "Texto inicial:")
                    if ok and text is not None: 
                        item_data_for_add["text"] = text 
                    else: 
                        event.ignore()
                        return
                elif item_type_str.startswith(USER_IMAGE_PREFIX):
                    item_data_for_add["image_path"] = item_type_str.replace(USER_IMAGE_PREFIX, "")

                if self.scene().parent() and hasattr(self.scene().parent(), '_capture_history_state'):
                    self.scene().parent()._capture_history_state(f"Añadir {item_type_str}")

                new_item = self.scene().add_diagram_item(item_type_str, drop_scene_pos, item_data_for_add)


                if new_item:
                    parent_assigned = False
                    if isinstance(target_graphics_item, ContainerItem) and new_item.id != target_graphics_item.id:
                        new_item.parent_container_id = target_graphics_item.id
                        target_graphics_item.add_child_item(new_item.id)
                        parent_assigned = True
                    elif self.scene().active_container_id: 
                        new_item.parent_container_id = self.scene().active_container_id
                        active_container_object = self.scene().items_by_id.get(self.scene().active_container_id)
                        if active_container_object and isinstance(active_container_object, ContainerItem):
                            active_container_object.add_child_item(new_item.id)
                        parent_assigned = True
                    else:
                        new_item.parent_container_id = None
                        parent_assigned = True 

                    if parent_assigned:
                        self.scene().apply_container_visibility(new_item)
                        if self.scene().parent() and hasattr(self.scene().parent(), 'on_diagram_modified'):
                             self.scene().parent().on_diagram_modified(capture_state=False) 

            event.acceptProposedAction()
        else:
            super().dropEvent(event)

# Paleta de Ítems (para arrastrar y soltar)
class ItemPalette(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True) 
        self.setViewMode(QListWidget.IconMode) 
        self.setIconSize(QSize(80, 60)) 
        self.setSpacing(10)
        self.setFlow(QListWidget.LeftToRight) 
        self.setWrapping(True) 
        self.user_image_items = {} 

        self.populate_standard_items()

    def populate_standard_items(self):
        for item_type_const, item_info in AVAILABLE_ITEM_TYPES.items():
            if item_type_const != ITEM_IMAGE: 
                 self.add_palette_item_entry(item_info["name"], item_type_const, item_info["icon_char"])

    def add_user_image_to_palette(self, image_path, image_name):
        item_type_str = f"{USER_IMAGE_PREFIX}{image_path}" 
        if item_type_str not in self.user_image_items:
            list_item = self.add_palette_item_entry(image_name, item_type_str, "🖼️", is_user_image=True, image_path_for_icon=image_path)
            if list_item:
                self.user_image_items[item_type_str] = list_item
            return True
        return False 

    def remove_user_image_from_palette(self, image_path): 
        item_type_str = f"{USER_IMAGE_PREFIX}{image_path}"
        if item_type_str in self.user_image_items:
            list_item_to_remove = self.user_image_items.pop(item_type_str)
            row = self.row(list_item_to_remove)
            if row != -1:
                self.takeItem(row)
            return True
        return False

    def clear_user_images_from_palette(self):
        for item_type_str, list_item in list(self.user_image_items.items()): 
            row = self.row(list_item)
            if row != -1:
                self.takeItem(row)
        self.user_image_items.clear()


    def add_palette_item_entry(self, name, item_type_str, icon_char="?", is_user_image=False, image_path_for_icon=None):
        list_widget_item = QListWidgetItem(name)
        list_widget_item.setData(Qt.UserRole, item_type_str) 
        list_widget_item.setToolTip(f"Añadir: {name}")

        pixmap = QPixmap(self.iconSize()) 
        pixmap.fill(Qt.transparent) 
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect_area = QRectF(pixmap.rect()).adjusted(5.0, 5.0, -5.0, -5.0)

        if is_user_image and image_path_for_icon:
            img_pixmap = QPixmap(image_path_for_icon)
            if not img_pixmap.isNull():
                scaled_icon = img_pixmap.scaled(rect_area.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x_offset = (rect_area.width() - scaled_icon.width()) / 2.0
                y_offset = (rect_area.height() - scaled_icon.height()) / 2.0
                painter.drawPixmap(rect_area.topLeft() + QPointF(x_offset, y_offset), scaled_icon)
            else: 
                painter.setFont(QFont("Arial", 24))
                painter.drawText(rect_area, Qt.AlignCenter, icon_char)
        elif item_type_str in AVAILABLE_ITEM_TYPES:
            ItemClass = AVAILABLE_ITEM_TYPES[item_type_str]["class"]
            temp_item_instance = ItemClass() 
            temp_item_instance.id = "palette_preview" 

            item_bound_rect = temp_item_instance.boundingRect()
            if not item_bound_rect.isEmpty() and item_bound_rect.width() > 0 and item_bound_rect.height() > 0 :
                preview_width = rect_area.width() * 0.9 
                preview_height = rect_area.height() * 0.9
                
                original_item_width = temp_item_instance.width 
                original_item_height = temp_item_instance.height

                item_aspect_ratio = original_item_width / original_item_height if original_item_height > 0 else 1
                
                scaled_width = preview_width
                scaled_height = preview_width / item_aspect_ratio if item_aspect_ratio > 0 else preview_width
                if scaled_height > preview_height:
                    scaled_height = preview_height
                    scaled_width = preview_height * item_aspect_ratio

                temp_item_instance.width = scaled_width
                temp_item_instance.height = scaled_height
                
                painter.save()
                dx = (rect_area.width() - temp_item_instance.width) / 2.0
                dy = (rect_area.height() - temp_item_instance.height) / 2.0
                painter.translate(rect_area.left() + dx, rect_area.top() + dy)
                
                temp_item_instance.paint(painter, None, None) 
                painter.restore()
            else: 
                painter.setFont(QFont("Arial", 24))
                painter.drawText(rect_area, Qt.AlignCenter, icon_char)
        else: 
            painter.setFont(QFont("Arial", 24))
            painter.drawText(rect_area, Qt.AlignCenter, icon_char)
        
        painter.end()
        list_widget_item.setIcon(QIcon(pixmap))
        self.addItem(list_widget_item)
        return list_widget_item


    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            item_type = item.data(Qt.UserRole) 
            
            mime_data = QMimeData()
            mime_data.setData("application/x-diagram-item-type", item_type.encode('utf-8'))
            
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            drag.setPixmap(item.icon().pixmap(self.iconSize())) 
            drag.setHotSpot(QPointF(self.iconSize().width() / 2.0, self.iconSize().height() / 2.0).toPoint()) 

            drag.exec_(supportedActions, Qt.CopyAction)
    
    def filter_items(self, text):
        search_text = text.lower()
        for i in range(self.count()):
            item = self.item(i)
            item_name = item.text().lower()
            if search_text in item_name:
                item.setHidden(False)
            else:
                item.setHidden(True)


# Ventana Principal de la Aplicación
class DiagramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagramador Básico con PyQt5") 
        self.setGeometry(100, 100, 1200, 800)
        icon = QIcon.fromTheme("applications-graphics")
        if icon.isNull(): 
            fallback_pixmap = QPixmap(32,32)
            fallback_pixmap.fill(QColor(Qt.gray)) 
            p = QPainter(fallback_pixmap)
            p.setFont(QFont("Arial", 16))
            p.drawText(fallback_pixmap.rect(), Qt.AlignCenter, "📈")
            p.end()
            icon = QIcon(fallback_pixmap)
        self.setWindowIcon(icon)

        self._clipboard_item_data = None 
        self._clipboard_children_data = [] 
        self.imported_image_paths = [] 
        self._history_stack = [] 
        self._history_current_index = -1 
        self.is_viewing_history = False 
        self._current_work_state_before_history_view = None 
        self._viewing_history_list_index = -1 


        main_v_layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(main_v_layout)
        self.setCentralWidget(main_widget)

        top_h_layout = QHBoxLayout()
        
        self.scene = DiagramScene(self) 
        self.view = DiagramView(self.scene, self)
        
        self.up_level_button = QPushButton("⬆️ Subir Nivel")
        self.up_level_button.clicked.connect(self.scene.leave_container_context)
        self.up_level_button.setEnabled(False) 

        palette_v_layout = QVBoxLayout() 
        self.search_palette_input = QLineEdit() 
        self.search_palette_input.setPlaceholderText("Buscar ítems...")
        palette_v_layout.addWidget(self.search_palette_input)

        self.palette = ItemPalette()
        palette_v_layout.addWidget(self.palette, 1) 
        palette_v_layout.addWidget(self.up_level_button, 0) 

        palette_widget = QWidget()
        palette_widget.setLayout(palette_v_layout)
        palette_widget.setFixedWidth(250) 

        top_h_layout.addWidget(palette_widget)
        top_h_layout.addWidget(self.view, 1) 

        main_v_layout.addLayout(top_h_layout) 

        # Panel de Historial de Cambios (Derecha)
        self.history_dock = QDockWidget("Historial de Cambios", self)
        self.history_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        history_panel_widget = QWidget()
        history_panel_layout = QVBoxLayout(history_panel_widget)
        
        self.history_list_widget = QListWidget()
        self.history_list_widget.itemClicked.connect(self.view_history_state_from_list_click) 
        self.history_list_widget.itemDoubleClicked.connect(self.restore_history_state_from_list) 
        history_panel_layout.addWidget(self.history_list_widget)
        
        self.clear_history_button = QPushButton("Limpiar Historial Anterior")
        self.clear_history_button.clicked.connect(self.clear_previous_history_action)
        history_panel_layout.addWidget(self.clear_history_button)

        self.exit_history_view_button = QPushButton("Volver al Presente")
        self.exit_history_view_button.clicked.connect(self.exit_history_view_mode)
        self.exit_history_view_button.setEnabled(False) 
        history_panel_layout.addWidget(self.exit_history_view_button)


        self.history_dock.setWidget(history_panel_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.history_dock)
        self.history_dock.setVisible(True) 


        self._create_actions()
        self._create_toolbars()
        self._create_menus()
        self._connect_signals() 

        self.current_file_path = None
        self.set_modified(False) 
        self.new_file() 

    def _create_actions(self):
        self.new_action = QAction(QIcon.fromTheme("document-new"), "Nuevo", self)
        self.new_action.setShortcut("Ctrl+N")
        self.open_action = QAction(QIcon.fromTheme("document-open"), "Abrir...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.save_action = QAction(QIcon.fromTheme("document-save"), "Guardar", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_as_action = QAction(QIcon.fromTheme("document-save-as"), "Guardar Como...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.export_image_action = QAction(QIcon.fromTheme("document-export", QIcon()), "Exportar como Imagen...", self) 
        self.exit_action = QAction(QIcon.fromTheme("application-exit"), "Salir", self)
        self.exit_action.setShortcut("Ctrl+Q")
        
        self.copy_action = QAction(QIcon.fromTheme("edit-copy"), "Copiar", self)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.paste_action = QAction(QIcon.fromTheme("edit-paste"), "Pegar", self)
        self.paste_action.setShortcut(QKeySequence.Paste)

        self.delete_action = QAction(QIcon.fromTheme("edit-delete"), "Eliminar", self)
        self.delete_action.setShortcut(Qt.Key_Delete) 
        self.properties_action = QAction(QIcon.fromTheme("document-properties"), "Propiedades...", self)
        
        self.import_image_action = QAction(QIcon.fromTheme("insert-image"), "Importar Imagen...", self)

        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in"), "Acercar", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out"), "Alejar", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_reset_action = QAction(QIcon.fromTheme("zoom-original"), "Zoom Original", self)
        self.zoom_reset_action.setShortcut("Ctrl+0")

    def _create_toolbars(self):
        file_toolbar = self.addToolBar("Archivo")
        file_toolbar.addAction(self.new_action)
        file_toolbar.addAction(self.open_action)
        file_toolbar.addAction(self.save_action)
        file_toolbar.addAction(self.import_image_action)
        file_toolbar.addAction(self.export_image_action)


        edit_toolbar = self.addToolBar("Editar")
        edit_toolbar.addAction(self.copy_action)
        edit_toolbar.addAction(self.paste_action)
        edit_toolbar.addAction(self.delete_action)
        edit_toolbar.addSeparator()
        edit_toolbar.addAction(self.properties_action) 

        view_toolbar = self.addToolBar("Vista")
        view_toolbar.addAction(self.zoom_in_action)
        view_toolbar.addAction(self.zoom_out_action)
        view_toolbar.addAction(self.zoom_reset_action)


    def _create_menus(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("&Archivo") 
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.import_image_action)
        file_menu.addAction(self.export_image_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = menu_bar.addMenu("&Editar")
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.delete_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.properties_action)
        
        view_menu = menu_bar.addMenu("&Ver")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.zoom_reset_action)
        view_menu.addSeparator()
        self.toggle_grid_action = QAction("Mostrar Cuadrícula", self, checkable=True) 
        self.toggle_grid_action.setChecked(self.scene.draw_grid)
        view_menu.addAction(self.toggle_grid_action)
        view_menu.addSeparator()
        toggle_history_action = self.history_dock.toggleViewAction() 
        toggle_history_action.setText("Mostrar/Ocultar Historial")
        view_menu.addAction(toggle_history_action)


    def _connect_signals(self): 
        self.new_action.triggered.connect(self.new_file)
        self.open_action.triggered.connect(self.open_file)
        self.save_action.triggered.connect(self.save_file)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.export_image_action.triggered.connect(self.export_diagram_as_image)
        self.exit_action.triggered.connect(self.close) 

        self.copy_action.triggered.connect(self.copy_selected_item)
        self.paste_action.triggered.connect(lambda: self.paste_item()) 
        self.delete_action.triggered.connect(self.delete_selected_items) 
        self.properties_action.triggered.connect(self.edit_item_properties) 
        self.import_image_action.triggered.connect(self.import_image)
        
        self.zoom_in_action.triggered.connect(lambda: self.view.scale_view(self.view.zoom_factor))
        self.zoom_out_action.triggered.connect(lambda: self.view.scale_view(1.0 / self.view.zoom_factor))
        self.zoom_reset_action.triggered.connect(lambda: (self.view.resetTransform(), setattr(self.view, 'current_zoom', 1.0)))
        
        self.toggle_grid_action.triggered.connect(self.toggle_grid) 
        self.search_palette_input.textChanged.connect(self.palette.filter_items) 

        self.scene.item_added.connect(lambda item: self.on_diagram_modified(action_description=f"Añadir {getattr(item, 'item_type', 'elemento')}"))
        self.scene.item_removed.connect(self.handle_item_removed_for_history) 
        self.scene.items_visibility_changed.connect(self.update_navigation_buttons)
        self.scene.item_selected.connect(self.update_preview_panel_if_container) 


    def handle_item_removed_for_history(self, item):
        """Manejador para la señal item_removed, para construir una descripción segura."""
        if isinstance(item, (DiagramItem, Connector)):
            item_type_desc = getattr(item, 'item_type', type(item).__name__)
            item_id_desc = getattr(item, 'id', 'N/A')
            text_desc = ""
            if hasattr(item, 'properties') and 'text' in item.properties:
                text_desc = item.properties['text']
            elif hasattr(item, 'text') and item.text: # Para conectores
                 text_desc = item.text
            
            description = f"Eliminar {item_type_desc}"
            if text_desc:
                description += f" '{text_desc}'"
            description += f" (ID:{item_id_desc})"
            self.on_diagram_modified(action_description=description)
        # No hacer nada para otros tipos de QGraphicsItem como la línea de conexión temporal


    def toggle_grid(self, checked):
        self.scene.draw_grid = checked
        self.scene.invalidate(self.scene.sceneRect(), QGraphicsScene.BackgroundLayer) 


    def new_file(self):
        if self.is_modified(): 
            reply = QMessageBox.question(self, 'Diagrama sin Guardar',
                                       "¿Desea guardar los cambios en el diagrama actual?",
                                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                if not self.save_file(): 
                    return
            elif reply == QMessageBox.Cancel:
                return
        
        self.scene.clear() 
        self.current_file_path = None
        self._clipboard_item_data = None 
        self._clipboard_children_data = []
        self.imported_image_paths = [] 
        self.palette.clear_user_images_from_palette() 
        self._history_stack = []
        self._history_current_index = -1 
        self.set_modified(False) 
        self.update_title()
        self.update_navigation_buttons()
        self.exit_history_view_mode(capture_new_state=False) 
        self._capture_history_state("Diagrama inicial") 


    def open_file(self):
        if self.is_modified():
             reply = QMessageBox.question(self, 'Diagrama sin Guardar',
                                       "¿Desea guardar los cambios en el diagrama actual?",
                                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
             if reply == QMessageBox.Save:
                if not self.save_file(): return
             elif reply == QMessageBox.Cancel:
                return

        path, _ = QFileDialog.getOpenFileName(self, "Abrir Diagrama", "", "JSON Files (*.json);;All Files (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f: 
                    data = json.load(f)
                
                self._load_scene_from_data(data) 
                self.current_file_path = path
                self.set_modified(False) 
                self._history_stack = [(time.strftime("%H:%M:%S"), "Archivo cargado", json.dumps(data))] 
                self._history_current_index = 0
                self._update_history_list_widget()
                self.update_title()
                self.update_navigation_buttons()
                self.exit_history_view_mode(capture_new_state=False) 
            except Exception as e:
                QMessageBox.critical(self, "Error al Abrir", f"No se pudo cargar el archivo '{path}':\n{e}")
                self.new_file() 

    def _get_current_scene_data(self):
        """Serializa el estado actual de la escena a un diccionario."""
        items_data_list = [] 
        connectors_data_list = [] 
        
        for item_id, item_in_scene in self.scene.items_by_id.items(): 
            if isinstance(item_in_scene, DiagramItem) : 
                props = item_in_scene.get_properties()
                if props: items_data_list.append(props)
            elif isinstance(item_in_scene, Connector):
                props = item_in_scene.get_properties()
                if props: connectors_data_list.append(props)

        return { 
            "items": items_data_list,
            "connectors": connectors_data_list,
            "scene_properties": { 
                "width": self.scene.width(),
                "height": self.scene.height(),
                "next_item_id": self.scene.next_item_id_counter,
                "active_container_id": self.scene.active_container_id,
                "imported_images": list(self.imported_image_paths) 
            }
        }

    def _load_scene_from_data(self, data_dict, for_history_view=False): 
        """Carga la escena desde un diccionario de datos."""
        target_scene = self.scene 
        
        target_scene.clear() 
        
        if not for_history_view: 
            self.imported_image_paths = [] 
            self.palette.clear_user_images_from_palette()
            scene_props = data_dict.get("scene_properties", {})
            self.imported_image_paths = scene_props.get("imported_images", []) 
            for img_path in self.imported_image_paths: 
                self.palette.add_user_image_to_palette(img_path, QFileInfo(img_path).fileName())

        scene_props = data_dict.get("scene_properties", {})
        target_scene.next_item_id_counter = scene_props.get("next_item_id", 1)
        
        items_data = data_dict.get("items", [])
        connectors_data = data_dict.get("connectors", [])
        
        max_loaded_id_num = 0
        id_map = {} 

        for item_data_dict_load in items_data: 
            item_type = item_data_dict_load.get("type")
            old_id = item_data_dict_load.get("id") 
            
            new_item = target_scene.add_diagram_item(item_type, QPointF(item_data_dict_load["x"],item_data_dict_load["y"]), item_data_dict_load) 
            
            if new_item and hasattr(new_item, 'id') and new_item.id:
                if old_id: 
                    id_map[old_id] = new_item.id
                try: 
                    id_num = int(new_item.id.split('_')[-1])
                    if id_num > max_loaded_id_num: max_loaded_id_num = id_num
                except ValueError: pass 
        
        for conn_data_dict_load in connectors_data: 
            old_start_id = conn_data_dict_load.get("start_item_id")
            old_end_id = conn_data_dict_load.get("end_item_id")

            new_start_id = id_map.get(old_start_id) 
            new_end_id = id_map.get(old_end_id)     
            
            start_item = target_scene.items_by_id.get(new_start_id) 
            end_item = target_scene.items_by_id.get(new_end_id)
            
            if start_item and end_item:
                connector = Connector(start_item, end_item)
                conn_id_from_data = conn_data_dict_load.get("id")
                if conn_id_from_data:
                    connector.id = conn_id_from_data
                    try:
                        id_num = int(connector.id.split('_')[-1])
                        if id_num > max_loaded_id_num: max_loaded_id_num = id_num
                    except ValueError: pass
                else:
                    connector.id = target_scene.get_next_item_id() 

                connector.set_properties(conn_data_dict_load, target_scene.items_by_id) 
                target_scene.addItem(connector)
                target_scene.add_item_to_cache(connector) 
            else:
                print(f"Advertencia: No se pudo re-enlazar el conector. Start ID: {old_start_id}->{new_start_id}, End ID: {old_end_id}->{new_end_id}")
        
        target_scene.next_item_id_counter = max(target_scene.next_item_id_counter, max_loaded_id_num + 1)
        target_scene.active_container_id = scene_props.get("active_container_id", None)
        
        target_scene.update_all_items_visibility() 
        if not for_history_view:
            self.update_navigation_buttons() 
            self.update_preview_panel_if_container(None, False) 


    def save_file_data(self, path):
        diagram_content = self._get_current_scene_data()
        try:
            with open(path, 'w', encoding='utf-8') as f: 
                json.dump(diagram_content, f, indent=4, ensure_ascii=False)
            self.current_file_path = path
            self.set_modified(False)
            self.update_title()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo '{path}':\n{e}")
            return False

    def save_file(self):
        if not self.is_modified() and self.current_file_path: 
            return True
        if self.current_file_path:
            return self.save_file_data(self.current_file_path)
        else:
            return self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Diagrama Como...", self.current_file_path or "diagrama.json", "JSON Files (*.json);;All Files (*)")
        if path:
            if not path.lower().endswith(".json"): 
                path += ".json"
            if self.save_file_data(path):
                 return True
        return False


    def delete_selected_items(self):
        if self.is_viewing_history: return
        if self.scene.selectedItems():
            self._capture_history_state("Eliminar selección") 
            self.scene.remove_selected()
            self.on_diagram_modified(capture_state=False) 

    def edit_item_properties(self):
        if self.is_viewing_history: return
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
        
        item_to_edit = selected_items[0] 
        original_props_json = json.dumps(item_to_edit.get_properties(), sort_keys=True) 
        
        self._capture_history_state(f"Inicio edición props de {item_to_edit.properties.get('text', item_to_edit.item_type)}")

        dialog_modified_item = False 

        if isinstance(item_to_edit, ScriptItem):
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Propiedades de Script: {item_to_edit.properties.get('text', 'Script')}")
            layout = QVBoxLayout(dialog)
            label = QLabel("Script de Pintura (usa 'painter' y 'self'):") 
            layout.addWidget(label)
            script_edit = QTextEdit()
            script_edit.setPlainText(item_to_edit.properties.get("paint_script", ""))
            script_edit.setFont(QFont("Courier New", 10))
            script_edit.setMinimumHeight(200)
            layout.addWidget(script_edit)
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            if dialog.exec_() == QDialog.Accepted:
                new_script = script_edit.toPlainText()
                if item_to_edit.properties.get("paint_script") != new_script:
                    item_to_edit.properties["paint_script"] = new_script
                    item_to_edit.update_appearance()
                    dialog_modified_item = True
        elif isinstance(item_to_edit, DiagramItem): 
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Propiedades de '{item_to_edit.properties.get('text', 'Ítem')}'")
            form_layout = QFormLayout() 
            if "text" in item_to_edit.properties:
                text_edit = QLineEdit(item_to_edit.properties["text"])
                form_layout.addRow("Texto:", text_edit)
            else: text_edit = None
            fill_color_button = QPushButton(item_to_edit.properties.get("fill_color", "#ddeeff"))
            fill_color_button.setStyleSheet(f"background-color: {fill_color_button.text()}; color: {self.get_text_color_for_bg(fill_color_button.text())}; border: 1px solid black;")
            fill_color_button.clicked.connect(lambda: self.select_color_property_dialog(item_to_edit, "fill_color", fill_color_button))
            form_layout.addRow("Color de Relleno:", fill_color_button)
            border_color_button = QPushButton(item_to_edit.properties.get("border_color", "#000000"))
            border_color_button.setStyleSheet(f"background-color: {border_color_button.text()}; color: {self.get_text_color_for_bg(border_color_button.text())}; border: 1px solid black;")
            border_color_button.clicked.connect(lambda: self.select_color_property_dialog(item_to_edit, "border_color", border_color_button))
            form_layout.addRow("Color de Borde:", border_color_button)
            font_size_spin = QSpinBox()
            font_size_spin.setRange(6, 72)
            font_size_spin.setValue(item_to_edit.properties.get("font_size", 10))
            form_layout.addRow("Tamaño de Fuente:", font_size_spin)
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            main_dialog_layout = QVBoxLayout(dialog)
            main_dialog_layout.addLayout(form_layout)
            main_dialog_layout.addWidget(button_box)
            self._temp_color_modified_dialog_flag = False 
            if dialog.exec_() == QDialog.Accepted:
                if text_edit: item_to_edit.properties["text"] = text_edit.text()
                item_to_edit.properties["font_size"] = font_size_spin.value()
                current_props_json = json.dumps(item_to_edit.get_properties(), sort_keys=True)
                if original_props_json != current_props_json or self._temp_color_modified_dialog_flag:
                    dialog_modified_item = True
                if dialog_modified_item:
                    item_to_edit.update_appearance()
                    if isinstance(item_to_edit, TextItem): 
                        item_to_edit._adjust_size_to_text()
                    else:
                        item_to_edit.prepareGeometryChange()
        elif isinstance(item_to_edit, Connector):
            dialog = QDialog(self)
            dialog.setWindowTitle("Propiedades del Conector")
            form_layout = QFormLayout()
            text_edit_conn = QLineEdit(item_to_edit.text)
            form_layout.addRow("Texto:", text_edit_conn)
            line_color_button = QPushButton(item_to_edit.line_color.name())
            line_color_button.setStyleSheet(f"background-color: {line_color_button.text()}; color: {self.get_text_color_for_bg(line_color_button.text())}; border: 1px solid black;")
            line_color_button.clicked.connect(lambda: self.select_connector_color_property_dialog(item_to_edit, "line_color", line_color_button))
            form_layout.addRow("Color de Línea:", line_color_button)
            line_width_spin = QSpinBox()
            line_width_spin.setRange(1, 10)
            line_width_spin.setValue(int(item_to_edit.line_width))
            form_layout.addRow("Ancho de Línea:", line_width_spin)
            font_size_conn_spin = QSpinBox()
            font_size_conn_spin.setRange(6, 24)
            font_size_conn_spin.setValue(item_to_edit.font_size)
            form_layout.addRow("Tamaño Fuente Texto:", font_size_conn_spin)
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            main_dialog_layout = QVBoxLayout(dialog)
            main_dialog_layout.addLayout(form_layout)
            main_dialog_layout.addWidget(button_box)
            self._temp_color_modified_dialog_flag = False
            if dialog.exec_() == QDialog.Accepted:
                item_to_edit.text = text_edit_conn.text()
                item_to_edit.line_width = float(line_width_spin.value())
                item_to_edit.font_size = font_size_conn_spin.value()
                current_props_json = json.dumps(item_to_edit.get_properties(), sort_keys=True)
                if original_props_json != current_props_json or self._temp_color_modified_dialog_flag:
                     dialog_modified_item = True
                if dialog_modified_item:
                    item_to_edit.update_position() 
        
        if dialog_modified_item:
            self.on_diagram_modified(capture_state=False, action_description=f"Propiedades de {getattr(item_to_edit, 'id', 'item')} cambiadas") 
        else: 
            if self._history_stack: self._history_stack.pop() 
            self._update_history_list_widget() 

        self._temp_color_modified_dialog_flag = False 


    _temp_color_modified_dialog_flag = False 

    def get_text_color_for_bg(self, bg_color_hex):
        try:
            color = QColor(bg_color_hex)
            if not color.isValid(): return "#000000" 
            luminance = (0.299 * color.redF() + 0.587 * color.greenF() + 0.114 * color.blueF()) 
            return "#000000" if luminance > 0.5 else "#FFFFFF"
        except Exception: 
            return "#000000" 

    def select_color_property_dialog(self, item, prop_name, button_to_update):
        current_color_hex = item.properties.get(prop_name, "#FFFFFF")
        current_color = QColor(current_color_hex)
        if not current_color.isValid(): current_color = QColor("#FFFFFF") 

        new_color = QColorDialog.getColor(current_color, self, f"Seleccionar {prop_name.replace('_', ' ').title()}")
        if new_color.isValid() and new_color.name() != current_color_hex:
            item.properties[prop_name] = new_color.name()
            button_to_update.setText(new_color.name())
            button_to_update.setStyleSheet(f"background-color: {new_color.name()}; color: {self.get_text_color_for_bg(new_color.name())}; border: 1px solid black;")
            self._temp_color_modified_dialog_flag = True 

    def select_connector_color_property_dialog(self, connector, prop_name, button_to_update):
        current_color_obj = getattr(connector, prop_name, QColor("#000000"))
        current_color = QColor(current_color_obj) 
        if not current_color.isValid(): current_color = QColor("#000000")

        new_color = QColorDialog.getColor(current_color, self, f"Seleccionar {prop_name.replace('_', ' ').title()}")
        if new_color.isValid() and new_color.name() != current_color.name():
            setattr(connector, prop_name, new_color)
            button_to_update.setText(new_color.name())
            button_to_update.setStyleSheet(f"background-color: {new_color.name()}; color: {self.get_text_color_for_bg(new_color.name())}; border: 1px solid black;")
            self._temp_color_modified_dialog_flag = True


    def update_title(self):
        title = "Diagramador Básico"
        filename = "Nuevo Diagrama"
        if self.current_file_path:
            filename = QFileInfo(self.current_file_path).fileName()
        
        modified_star = "*" if self.is_modified() else ""
        
        path_string = self.scene.get_current_path_string()
        
        history_mode_indicator = " [VISTA HISTORIAL]" if self.is_viewing_history else ""

        if path_string != "/": 
            self.setWindowTitle(f"{title} - {filename} [{path_string}]{modified_star}{history_mode_indicator}")
        else:
            self.setWindowTitle(f"{title} - {filename}{modified_star}{history_mode_indicator}")


    def is_modified(self):
        return getattr(self, '_modified_flag', False)

    def set_modified(self, modified_status):
        if getattr(self, '_modified_flag', False) != modified_status:
            self._modified_flag = modified_status
            self.update_title()

    def closeEvent(self, event):
        if self.is_modified():
            reply = QMessageBox.question(self, 'Salir', 
                                         "El diagrama tiene cambios sin guardar.\n¿Desea guardar los cambios?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                if not self.save_file(): 
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()

    def on_diagram_modified(self, capture_state=True, action_description="Cambio"):
        if self.is_viewing_history: 
            return
        self.set_modified(True)
        if capture_state:
            self._capture_history_state(action_description)
    
    def update_navigation_buttons(self):
        if self.scene.active_container_id:
            self.up_level_button.setEnabled(True)
            self.up_level_button.setToolTip(f"Volver del contexto actual")
        else:
            self.up_level_button.setEnabled(False)
            self.up_level_button.setToolTip("")
        self.update_title() 

    def copy_selected_item(self):
        selected_items = self.scene.selectedItems()
        if not selected_items:
            self._clipboard_item_data = None
            self._clipboard_children_data = []
            return

        item_to_copy = selected_items[0] 

        if isinstance(item_to_copy, DiagramItem): 
            self._clipboard_item_data = item_to_copy.get_properties(for_clipboard=True)
            self._clipboard_children_data = [] 

            if item_to_copy.item_type == ITEM_CONTAINER:
                for child_id in item_to_copy.child_item_ids:
                    child_item = self.scene.items_by_id.get(child_id)
                    if child_item and isinstance(child_item, DiagramItem):
                        child_data = child_item.get_properties(for_clipboard=True)
                        if "parent_container_id" in child_data:
                            del child_data["parent_container_id"]
                        self._clipboard_children_data.append(child_data)
            
            print(f"Copiado: {self._clipboard_item_data.get('type') if self._clipboard_item_data else 'Nada'}")
            if self._clipboard_children_data:
                print(f"  con {len(self._clipboard_children_data)} hijos.")
        elif isinstance(item_to_copy, Connector):
             self._clipboard_item_data = item_to_copy.get_properties(for_clipboard=True)
             self._clipboard_children_data = [] 
             print(f"Copiado Conector: {self._clipboard_item_data.get('id') if self._clipboard_item_data else 'Nada'}")
        else:
            self._clipboard_item_data = None
            self._clipboard_children_data = []


    def paste_item(self, position_override=None):
        if self.is_viewing_history:
            QMessageBox.warning(self, "Modo Vista Historial", "No se puede pegar en modo de vista de historial.")
            return
        if not self._clipboard_item_data:
            return
        
        self._capture_history_state("Pegar ítem(s)") 

        data_to_paste = json.loads(json.dumps(self._clipboard_item_data)) 
        children_data_to_paste = [json.loads(json.dumps(child_data)) for child_data in self._clipboard_children_data]

        offset_x, offset_y = 20, 20 
        if position_override:
            data_to_paste["x"] = position_override.x()
            data_to_paste["y"] = position_override.y()
        else: 
            data_to_paste["x"] = data_to_paste.get("x", 0) + offset_x
            data_to_paste["y"] = data_to_paste.get("y", 0) + offset_y
        
        item_type = data_to_paste.get("type")

        if item_type == "connector":
            start_item_id_original = data_to_paste.get("start_item_id") 
            end_item_id_original = data_to_paste.get("end_item_id")   
            
            start_item = self.scene.items_by_id.get(start_item_id_original)
            end_item = self.scene.items_by_id.get(end_item_id_original)

            if start_item and end_item:
                new_connector = Connector(start_item, end_item)
                new_connector.id = self.scene.get_next_item_id()
                conn_props_to_set = {k:v for k,v in data_to_paste.items() if k not in ['start_item_id', 'end_item_id', 'id', 'type']}
                new_connector.set_properties(conn_props_to_set, self.scene.items_by_id) 
                
                self.scene.addItem(new_connector)
                self.scene.add_item_to_cache(new_connector)
                self.scene.apply_container_visibility(new_connector)
                self.scene.clearSelection()
                new_connector.setSelected(True)
                self.on_diagram_modified(capture_state=False) 
                print(f"Conector pegado: {new_connector.id}")
            else:
                print("No se pudo pegar el conector: ítems de inicio/fin no encontrados con los IDs originales.")
            return
        
        new_main_item = self.scene.add_diagram_item(item_type, 
                                                   QPointF(data_to_paste["x"], data_to_paste["y"]), 
                                                   data_to_paste)
        
        if new_main_item:
            if self.scene.active_container_id:
                new_main_item.parent_container_id = self.scene.active_container_id
                active_container = self.scene.items_by_id.get(self.scene.active_container_id)
                if active_container and isinstance(active_container, ContainerItem):
                    active_container.add_child_item(new_main_item.id)
            
            if new_main_item.item_type == ITEM_CONTAINER and children_data_to_paste:
                for child_data in children_data_to_paste:
                    child_original_x = child_data.get("x",0) 
                    child_original_y = child_data.get("y",0)
                    
                    relative_x = child_original_x - self._clipboard_item_data.get("x", 0) 
                    relative_y = child_original_y - self._clipboard_item_data.get("y", 0)

                    child_pos_x = new_main_item.x() + relative_x
                    child_pos_y = new_main_item.y() + relative_y
                    
                    if "id" in child_data: del child_data["id"]
                    
                    pasted_child = self.scene.add_diagram_item(child_data["type"], 
                                                              QPointF(child_pos_x, child_pos_y), 
                                                              child_data)
                    if pasted_child:
                        pasted_child.parent_container_id = new_main_item.id 
                        new_main_item.add_child_item(pasted_child.id)
                        self.scene.apply_container_visibility(pasted_child)

            self.scene.clearSelection()
            new_main_item.setSelected(True)
            self.scene.apply_container_visibility(new_main_item) 
            self.on_diagram_modified(capture_state=False) 
            print(f"Pegado: {new_main_item.id}")


    def import_image(self):
        if self.is_viewing_history:
            QMessageBox.warning(self, "Modo Vista Historial", "No se puede importar imagen en modo de vista de historial.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Imagen", "", 
                                                   "Imágenes (*.png *.jpg *.jpeg *.bmp);;Todos los Archivos (*)")
        if file_path:
            self._capture_history_state(f"Importar imagen: {QFileInfo(file_path).fileName()}")
            center_view = self.view.mapToScene(self.view.viewport().rect().center())
            
            if file_path not in self.imported_image_paths:
                self.imported_image_paths.append(file_path)
                self.palette.add_user_image_to_palette(file_path, QFileInfo(file_path).fileName())
            
            item_data = {"image_path": file_path} 
            new_image_item = self.scene.add_diagram_item(ITEM_IMAGE, center_view, item_data)
            
            if new_image_item:
                if self.scene.active_container_id:
                    new_image_item.parent_container_id = self.scene.active_container_id
                    active_container = self.scene.items_by_id.get(self.scene.active_container_id)
                    if active_container and isinstance(active_container, ContainerItem):
                        active_container.add_child_item(new_image_item.id)
                
                self.scene.clearSelection()
                new_image_item.setSelected(True)
                self.scene.apply_container_visibility(new_image_item)
                self.on_diagram_modified(capture_state=False) 
    
    def export_diagram_as_image(self):
        if not self.scene.items():
            QMessageBox.information(self, "Exportar Imagen", "El diagrama está vacío.")
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(self, "Exportar Diagrama como Imagen", 
                                                                "diagrama.png", 
                                                                "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
        if not file_path:
            return

        source_rect = self.scene.get_visible_items_bounding_rect()
        if source_rect.isEmpty():
            QMessageBox.information(self, "Exportar Imagen", "No hay ítems visibles para exportar.")
            return

        margin = 20
        source_rect = source_rect.adjusted(-margin, -margin, margin, margin)

        scale_factor = 3.0 
        img_width = int(source_rect.width() * scale_factor)
        img_height = int(source_rect.height() * scale_factor)

        if img_width <= 0 or img_height <= 0:
            QMessageBox.warning(self, "Error al Exportar", "Dimensiones inválidas para la imagen.")
            return

        image = QImage(img_width, img_height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white) 

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        target_render_rect = QRectF(0, 0, img_width, img_height)
        self.scene.render(painter, target_render_rect, source_rect)
        painter.end()

        if image.save(file_path):
            QMessageBox.information(self, "Exportar Imagen", f"Diagrama guardado como:\n{file_path}")
        else:
            QMessageBox.warning(self, "Error al Exportar", f"No se pudo guardar la imagen en:\n{file_path}")

    def update_preview_panel_if_container(self, selected_item, is_selected):
        # Este método está obsoleto ya que la vista previa se eliminó.
        pass

    def populate_preview_scene(self, container_item: ContainerItem):
        # Obsoleto
        pass


    def fit_preview_in_view(self):
        # Obsoleto
        pass

    def _capture_history_state(self, description="Cambio"):
        """Captura el estado actual de la escena para el historial."""
        if self.is_viewing_history: 
            return

        if self._history_current_index < len(self._history_stack) - 1:
            self._history_stack = self._history_stack[:self._history_current_index + 1]

        current_state_data = self._get_current_scene_data()
        current_state_json = json.dumps(current_state_data, sort_keys=True)

        if self._history_stack and self._history_current_index >=0 and \
           self._history_current_index < len(self._history_stack) and \
           self._history_stack[self._history_current_index][2] == current_state_json:
            return

        timestamp = time.strftime("%H:%M:%S")
        self._history_stack.append((timestamp, description, current_state_json))
        self._history_current_index = len(self._history_stack) - 1
        
        if len(self._history_stack) > 50: 
            self._history_stack.pop(0)
            self._history_current_index -=1 

        self._update_history_list_widget()

    def _update_history_list_widget(self):
        self.history_list_widget.clear()
        last_hour_str = ""
        for i, (timestamp, desc, state_json) in enumerate(self._history_stack):
            current_hour_str = timestamp.split(":")[0]
            if current_hour_str != last_hour_str:
                hour_item = QListWidgetItem(f"--- {current_hour_str}:00 ---")
                font = hour_item.font()
                font.setItalic(True)
                hour_item.setFont(font)
                hour_item.setForeground(Qt.gray)
                hour_item.setFlags(hour_item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled) 
                self.history_list_widget.addItem(hour_item)
                last_hour_str = current_hour_str

            item_text = f"{timestamp} - {desc}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, i) 
            
            if self.is_viewing_history and i == self._viewing_history_list_index:
                font = list_item.font()
                font.setBold(False) 
                list_item.setFont(font)
                list_item.setForeground(QColor("darkGreen")) 
            elif i == self._history_current_index and not self.is_viewing_history: 
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)
                list_item.setForeground(QColor("blue")) 
            self.history_list_widget.addItem(list_item)
        
        idx_to_scroll = self._viewing_history_list_index if self.is_viewing_history else self._history_current_index
        if idx_to_scroll >= 0:
            actual_list_widget_item_to_scroll = None
            for list_idx in range(self.history_list_widget.count()):
                lw_item = self.history_list_widget.item(list_idx)
                if lw_item.data(Qt.UserRole) == idx_to_scroll:
                    actual_list_widget_item_to_scroll = lw_item
                    break
            if actual_list_widget_item_to_scroll:
                self.history_list_widget.setCurrentItem(actual_list_widget_item_to_scroll) 
                self.history_list_widget.scrollToItem(actual_list_widget_item_to_scroll, QAbstractItemView.PositionAtCenter)


    def view_history_state_from_list_click(self, list_item_clicked: QListWidgetItem):
        history_index = list_item_clicked.data(Qt.UserRole)
        if history_index is None or not (0 <= history_index < len(self._history_stack)):
            return 

        if not self.is_viewing_history: 
            self._current_work_state_before_history_view = self._get_current_scene_data()
        
        self.is_viewing_history = True
        self._viewing_history_list_index = history_index 
        self.exit_history_view_button.setEnabled(True)
        
        timestamp, desc, state_json_to_view = self._history_stack[history_index]
        data_to_view = json.loads(state_json_to_view)
        
        self._load_scene_from_data(data_to_view, for_history_view=True) 
        self.set_main_view_read_only(True) 
        self.update_title() 
        self._update_history_list_widget() 


    def restore_history_state_from_list(self, list_item_clicked: QListWidgetItem):
        history_index = list_item_clicked.data(Qt.UserRole)
        if history_index is None or not (0 <= history_index < len(self._history_stack)):
            return

        timestamp, desc, state_json_to_restore = self._history_stack[history_index]
        
        self.exit_history_view_mode(capture_new_state=False) 

        self._load_scene_from_data(json.loads(state_json_to_restore))
        
        self._capture_history_state(f"Restaurado a: {timestamp} - {desc}")
        
        self.set_modified(True) 
        self._update_history_list_widget()
        print(f"Restaurado estado de: {timestamp} - {desc} como estado actual.")

    def exit_history_view_mode(self, capture_new_state=True): 
        if self.is_viewing_history:
            if self._current_work_state_before_history_view:
                self._load_scene_from_data(self._current_work_state_before_history_view)
                self._current_work_state_before_history_view = None 
            else: 
                if self._history_stack and self._history_current_index >= 0 and self._history_current_index < len(self._history_stack):
                     _, _, last_real_state_json = self._history_stack[self._history_current_index]
                     self._load_scene_from_data(json.loads(last_real_state_json))

            self.is_viewing_history = False
            self._viewing_history_list_index = -1 
            self.exit_history_view_button.setEnabled(False)
            self.set_main_view_read_only(False)
            self.update_title()
            self._update_history_list_widget() 


    def set_main_view_read_only(self, read_only):
        """Configura la escena principal para ser de solo lectura o editable."""
        self.import_image_action.setEnabled(not read_only)
        self.paste_action.setEnabled(not read_only)
        self.delete_action.setEnabled(not read_only)
        self.properties_action.setEnabled(not read_only)
        self.palette.setEnabled(not read_only)
        
        for item in self.scene.items():
            if isinstance(item, DiagramItem) or isinstance(item, Connector):
                item.setFlag(QGraphicsItem.ItemIsMovable, not read_only)

        print(f"Modo Solo Lectura de Escena Principal: {read_only}")


    def clear_previous_history_action(self):
        if self.is_viewing_history:
            QMessageBox.warning(self, "Limpiar Historial", "Salga del modo de vista de historial antes de limpiar.")
            return

        if self._history_current_index < 0 or not self._history_stack or self._history_current_index == 0 :
            QMessageBox.information(self, "Limpiar Historial", "No hay historial anterior para limpiar o está en el estado inicial.")
            return
        
        reply = QMessageBox.question(self, "Limpiar Historial",
                                     "¿Está seguro de que desea eliminar todos los cambios anteriores al estado actual?\n"
                                     "Esta acción no se puede deshacer.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            current_timestamp, current_desc, current_state_json = self._history_stack[self._history_current_index]
            
            self._history_stack = [(current_timestamp, f"Punto de partida (Historial limpiado)", current_state_json)]
            self._history_current_index = 0
            self.set_modified(False) 
            self._update_history_list_widget()
            QMessageBox.information(self, "Limpiar Historial", "El historial anterior ha sido limpiado.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = DiagramApp() 
    main_win.show()
    sys.exit(app.exec_())

