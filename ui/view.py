# ui/view.py
from PyQt5.QtWidgets import QGraphicsView, QInputDialog
from PyQt5.QtGui import QPainter, QKeySequence
from PyQt5.QtCore import Qt

from core.scene import DiagramScene  # Necesario para isinstance check
from items.container_item import ContainerItem # Para dropEvent
from core.constants import ITEM_TEXT, USER_IMAGE_PREFIX # Para dropEvent

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

    # ... (Copiar aquí TODOS los métodos de DiagramView del archivo main.py original) ...
    # ... (wheelEvent, scale_view, keyPressEvent, dragEnterEvent, dragMoveEvent, dropEvent) ...
    # Asegúrate de ajustar las importaciones dentro de estos métodos si es necesario.
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

