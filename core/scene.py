# diagramador_app/core/scene.py
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsItem, QInputDialog, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent
from PyQt5.QtGui import QBrush, QColor, QPen, QTransform
from PyQt5.QtCore import pyqtSignal, QPointF, QRectF, QLineF, Qt

from items.container_item import ContainerItem

from .diagram_item_base import DiagramItem 
from .connector import Connector
from items import AVAILABLE_ITEM_TYPES # Importación absoluta desde el paquete 'items'
from .constants import ITEM_IMAGE, ITEM_TEXT, USER_IMAGE_PREFIX, ITEM_CONTAINER

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
        app_parent = self.parent()
        if app_parent and hasattr(app_parent, 'on_diagram_modified') and hasattr(app_parent, 'handle_item_removed_for_history'):
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

        if app_parent and hasattr(app_parent, 'on_diagram_modified') and hasattr(app_parent, 'handle_item_removed_for_history'):
            self.item_added.connect(lambda item: app_parent.on_diagram_modified(action_description=f"Añadir {getattr(item, 'item_type', 'elemento')}"))
            self.item_removed.connect(app_parent.handle_item_removed_for_history)


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
