# diagramador_app/core/diagram_item_base.py
from PyQt5.QtWidgets import QGraphicsItem, QInputDialog, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPixmap, QFontMetrics
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QFileInfo

# Importaciones que se harán de forma tardía o se asumirá que están en el ámbito correcto
# al ser usadas por la aplicación principal.
# from ..items import AVAILABLE_ITEM_TYPES # Ejemplo de importación tardía
# from .constants import ITEM_IMAGE, USER_IMAGE_PREFIX, ITEM_TEXT, ITEM_CONTAINER

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
        # Importación tardía para evitar dependencia circular si AVAILABLE_ITEM_TYPES
        # se define en items/__init__.py y este a su vez importa DiagramItem.
        # Para que esto funcione, main.py debe asegurarse de que items.__init__ se cargue
        # antes de que se llame a clone por primera vez, o pasar AVAILABLE_ITEM_TYPES.
        from items import AVAILABLE_ITEM_TYPES # Asume que 'items' es un paquete en el mismo nivel que 'core'
        from core.constants import ITEM_IMAGE, USER_IMAGE_PREFIX, ITEM_TEXT, ITEM_CONTAINER

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
            cloned_item.setZValue(self.zValue()) 
        return cloned_item

    def get_properties(self, for_clipboard=False): 
        from .constants import ITEM_CONTAINER, ITEM_IMAGE, ITEM_SCRIPT 
        props = {
            "type": self.item_type,
            "id": getattr(self, 'id', None) if not for_clipboard else None, 
            "x": self.x(),
            "y": self.y(),
            "z": self.zValue(), 
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
        from .constants import ITEM_CONTAINER, ITEM_IMAGE, ITEM_SCRIPT, ITEM_TEXT 
        if "x" in data and "y" in data: 
            self.setPos(data["x"], data["y"])
        if "z" in data: 
            self.setZValue(float(data["z"]))
        
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
                 if hasattr(self, 'load_image_from_path'): self.load_image_from_path() 
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
        if self.scene() and hasattr(self.scene(), 'parent') and self.scene().parent() and hasattr(self.scene().parent(), 'hierarchy_panel') and self.scene().parent().hierarchy_panel:
            # El método en hierarchy_panel espera el ítem completo
            self.scene().parent().hierarchy_panel.update_item_text_in_tree(
                self, self.properties.get("text", ""), self.item_type
            )


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
        from .constants import ITEM_CONTAINER, ITEM_SCRIPT, ITEM_IMAGE, ITEM_TEXT 

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
