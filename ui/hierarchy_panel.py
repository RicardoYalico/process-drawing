# ui/hierarchy_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QInputDialog, QMenu, QAction, QTreeWidgetItemIterator, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal

# Asumimos que DiagramItem e ContainerItem serán accesibles a través de main_app_ref.scene.items_by_id
# ou que se pasarán tipos específicos se é necesario para isinstance.

class ItemHierarchyPanel(QWidget):
    """
    Un panel que mostra unha vista de árbore da xerarquía de elementos na escena.
    """
    item_selected_in_tree = pyqtSignal(str)  # Emite o ID do ítem
    item_renamed_in_tree = pyqtSignal(str, str)  # Emite ID e novo texto
    item_layer_change_requested = pyqtSignal(str, str) # Opcional, para cambiar capas desde aquí

    def __init__(self, main_app_ref, parent=None):
        super().__init__(parent)
        self.main_app = main_app_ref  # Referencia a DiagramApp
        self._block_scene_selection_update = False # Para evitar bucles de sinais

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Eliminar marxes innecesarias

        self.item_tree_widget = QTreeWidget()
        self.item_tree_widget.setHeaderHidden(True)
        self.item_tree_widget.itemClicked.connect(self._on_tree_item_clicked)
        # A edición iniciarase mediante dobre clic ou menú contextual
        self.item_tree_widget.itemDoubleClicked.connect(self._on_tree_item_double_clicked_for_rename)
        self.item_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.item_tree_widget.customContextMenuRequested.connect(self._open_context_menu)
        
        layout.addWidget(self.item_tree_widget)
        self.setLayout(layout)

    def _add_children_to_tree(self, parent_qt_item: QTreeWidgetItem, parent_diagram_item_id: str):
        """Engade recursivamente os fillos dun contedor ao árbore."""
        # Importar ContainerItem aquí para evitar importación circular a nivel de módulo
        from items.container_item import ContainerItem # Asume que está en items/container_item.py
        from core.diagram_item_base import DiagramItem # Para isinstance
        
        container_item = self.main_app.scene.items_by_id.get(parent_diagram_item_id)
        if container_item and isinstance(container_item, ContainerItem) and hasattr(container_item, 'child_item_ids'):
            for child_id in container_item.child_item_ids:
                child_diagram_item = self.main_app.scene.items_by_id.get(child_id)
                if child_diagram_item and isinstance(child_diagram_item, DiagramItem): # Asegurar que é un DiagramItem
                    child_tree_item = QTreeWidgetItem(parent_qt_item)
                    item_text = child_diagram_item.properties.get("text", child_diagram_item.id)
                    if not item_text or item_text == "Item": # Usar ID se o texto é xenérico
                        item_text = f"({child_diagram_item.item_type}) {child_diagram_item.id}"
                    else:
                        item_text = f"{item_text} ({child_diagram_item.item_type})"

                    child_tree_item.setText(0, item_text)
                    child_tree_item.setData(0, Qt.UserRole, child_diagram_item.id)
                    # icon = self.main_app.get_icon_for_item_type(child_diagram_item.item_type) # Necesitaría un método en DiagramApp
                    # if icon: child_tree_item.setIcon(0, icon)
                    if isinstance(child_diagram_item, ContainerItem): # Recursión só para contenedores
                        self._add_children_to_tree(child_tree_item, child_id)

    def update_tree(self):
        """Limpa e repoboa o árbore de xerarquía."""
        from core.diagram_item_base import DiagramItem # Importación local
        from items.container_item import ContainerItem # Importación local

        self._block_scene_selection_update = True  
        
        expanded_items_ids = set()
        iterator = QTreeWidgetItemIterator(self.item_tree_widget, QTreeWidgetItemIterator.All)
        while iterator.value():
            tree_item = iterator.value()
            if tree_item.isExpanded():
                item_id = tree_item.data(0, Qt.UserRole)
                if item_id:
                    expanded_items_ids.add(item_id)
            iterator += 1

        self.item_tree_widget.clear()
        
        root_items = []
        for item_id, diagram_item in self.main_app.scene.items_by_id.items():
            if isinstance(diagram_item, DiagramItem) and not diagram_item.parent_container_id:
                root_items.append(diagram_item)
        
        for diagram_item in root_items:
            tree_item = QTreeWidgetItem(self.item_tree_widget)
            item_text = diagram_item.properties.get("text", diagram_item.id)
            if not item_text or item_text == "Item": 
                item_text = f"({diagram_item.item_type}) {diagram_item.id}"
            else:
                item_text = f"{item_text} ({diagram_item.item_type})"
            
            tree_item.setText(0, item_text)
            tree_item.setData(0, Qt.UserRole, diagram_item.id)

            if isinstance(diagram_item, ContainerItem):
                self._add_children_to_tree(tree_item, diagram_item.id)
            
            if diagram_item.id in expanded_items_ids: 
                tree_item.setExpanded(True)
        
        self._block_scene_selection_update = False

    def update_item_text_in_tree(self, diagram_item_id: str, new_text: str, item_type: str):
        """Actualiza o texto dun ítem específico no árbore."""
        if not diagram_item_id:
            return
        
        iterator = QTreeWidgetItemIterator(self.item_tree_widget, QTreeWidgetItemIterator.All)
        while iterator.value():
            tree_item = iterator.value()
            if tree_item.data(0, Qt.UserRole) == diagram_item_id:
                display_text = new_text if new_text and new_text != "Item" else f"({item_type}) {diagram_item_id}"
                if new_text and new_text != "Item":
                     display_text = f"{new_text} ({item_type})"
                tree_item.setText(0, display_text)
                break
            iterator += 1
            
    def _on_tree_item_clicked(self, tree_item: QTreeWidgetItem, column: int):
        if self._block_scene_selection_update:
            return
        item_id = tree_item.data(0, Qt.UserRole)
        if item_id:
            self.item_selected_in_tree.emit(item_id)

    def _on_tree_item_double_clicked_for_rename(self, tree_item: QTreeWidgetItem, column: int):
        if self.main_app.is_viewing_history: return 
        
        item_id = tree_item.data(0, Qt.UserRole)
        diagram_item = self.main_app.scene.items_by_id.get(item_id)
        if diagram_item:
            current_text = diagram_item.properties.get("text", "")
            new_text, ok = QInputDialog.getText(self, f"Renombrar '{current_text}'", "Nuevo nombre:", text=current_text)
            if ok and new_text != current_text:
                self.item_renamed_in_tree.emit(item_id, new_text) 

    def select_diagram_item_in_tree(self, diagram_item_id):
        """Selecciona e asegura a visibilidade dun ítem no árbore dado o seu ID."""
        if self._block_scene_selection_update: 
            return
            
        self.item_tree_widget.clearSelection()
        if not diagram_item_id:
            return

        iterator = QTreeWidgetItemIterator(self.item_tree_widget, QTreeWidgetItemIterator.All)
        item_to_select = None
        while iterator.value():
            tree_item = iterator.value()
            if tree_item.data(0, Qt.UserRole) == diagram_item_id:
                item_to_select = tree_item
                break
            iterator += 1
        
        if item_to_select:
            original_block_state = self._block_scene_selection_update
            self._block_scene_selection_update = True
            
            self.item_tree_widget.setCurrentItem(item_to_select)
            self.item_tree_widget.scrollToItem(item_to_select, QAbstractItemView.EnsureVisible)
            
            parent = item_to_select.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            
            self._block_scene_selection_update = original_block_state


    def _open_context_menu(self, position):
        if self.main_app.is_viewing_history: return

        selected_items = self.item_tree_widget.selectedItems()
        if not selected_items:
            return
        
        tree_item = selected_items[0]
        item_id = tree_item.data(0, Qt.UserRole)
        if not item_id: return
        
        diagram_item = self.main_app.scene.items_by_id.get(item_id)
        if not diagram_item: return

        menu = QMenu()
        rename_action = menu.addAction("Renombrar")
        menu.addSeparator()
        bring_to_front_action = menu.addAction("Traer al Frente")
        send_to_back_action = menu.addAction("Enviar al Fondo")
        bring_forward_action = menu.addAction("Adelante")
        send_backward_action = menu.addAction("Atrás")
        
        action = menu.exec_(self.item_tree_widget.mapToGlobal(position))
        
        if action == rename_action:
            self._on_tree_item_double_clicked_for_rename(tree_item, 0) 
        elif action == bring_to_front_action:
            self.item_layer_change_requested.emit(item_id, "front")
        elif action == send_to_back_action:
            self.item_layer_change_requested.emit(item_id, "back")
        elif action == bring_forward_action:
            self.item_layer_change_requested.emit(item_id, "forward")
        elif action == send_backward_action:
            self.item_layer_change_requested.emit(item_id, "backward")
