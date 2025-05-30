import sys
import json
import math 
import base64 
import time 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsItem, QInputDialog, QLabel, 
    QListWidget, QHBoxLayout, QWidget, QVBoxLayout,
    QPushButton, QDialog, 
    QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QTextEdit, 
    QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, QSizePolicy, QDockWidget,
    QTreeWidget, QTreeWidgetItem, QMenu, QAbstractItemView, QAction, QToolBar,
    QMessageBox, QColorDialog, QFileDialog, QListWidgetItem
)
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QPolygonF, 
                         QTransform, QDrag, QIcon, QPixmap, QFontMetrics, 
                         QPainterPath, QPainterPathStroker, QKeySequence, QImage) 
from PyQt5.QtCore import (Qt, QPointF, QRectF, QSizeF, QMimeData, 
                          pyqtSignal, QSize, QLineF, QFileInfo, QBuffer, QIODevice) 

# Importaciones de los módulos de la aplicación
from core.constants import * 
from core.diagram_item_base import DiagramItem 
from core.connector import Connector 
from core.scene import DiagramScene
from items import AVAILABLE_ITEM_TYPES, ScriptItem, TextItem, ContainerItem
from ui.view import DiagramView
from ui.palette import ItemPalette
from ui.hierarchy_panel import ItemHierarchyPanel # <--- IMPORTACIÓN DEL NUEVO PANEL

# Ventana Principal de la Aplicación
import sys
import json
import math 
import base64 
import time 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsItem, QInputDialog, QLabel, 
    QListWidget, QHBoxLayout, QWidget, QVBoxLayout,
    QPushButton, QDialog, 
    QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox, QTextEdit, 
    QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, QSizePolicy, QDockWidget,
    QTreeWidget, QTreeWidgetItem, QMenu, QAbstractItemView, QAction, QToolBar,
    QMessageBox, QColorDialog 
)
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QPolygonF, 
                         QTransform, QDrag, QIcon, QPixmap, QFontMetrics, 
                         QPainterPath, QPainterPathStroker, QKeySequence, QImage) 
from PyQt5.QtCore import (Qt, QPointF, QRectF, QSizeF, QMimeData, 
                          pyqtSignal, QSize, QLineF, QFileInfo, QBuffer, QIODevice) 

# Importaciones de los módulos de la aplicación
from core.constants import * 
from core.diagram_item_base import DiagramItem 
from core.connector import Connector 
from core.scene import DiagramScene
from items import AVAILABLE_ITEM_TYPES 
from ui.view import DiagramView
from ui.palette import ItemPalette
from ui.hierarchy_panel import ItemHierarchyPanel # <--- IMPORTACIÓN DEL PANEL DE JERARQUÍA

class DiagramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagramador Básico con PyQt5") 
        self.setGeometry(100, 100, 1400, 900) # Aumentar tamaño para nuevos paneles
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

        # Layout principal y widget central
        main_v_layout = QVBoxLayout()
        central_widget_main_area = QWidget() 
        central_widget_main_area.setLayout(main_v_layout)
        self.setCentralWidget(central_widget_main_area) # El widget central ahora es este

        # Layout superior para la vista principal y la paleta
        top_h_layout = QHBoxLayout()
        
        self.scene = DiagramScene(self) 
        self.view = DiagramView(self.scene, self)
        
        # --- Paleta de Ítems (Izquierda) ---
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

        self.palette_dock = QDockWidget("Paleta de Ítems", self)
        palette_widget = QWidget()
        palette_widget.setLayout(palette_v_layout)
        self.palette_dock.setWidget(palette_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.palette_dock)
        self.palette_dock.setObjectName("PaletteDock") # Para guardar/restaurar estado

        # La vista principal se añade al layout horizontal superior
        top_h_layout.addWidget(self.view, 1) 
        main_v_layout.addLayout(top_h_layout) 

        # --- Panel de Historial de Cambios (Derecha) ---
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
        self.history_dock.setObjectName("HistoryDock")

        # --- Panel de Jerarquía de Elementos (Derecha, en pestaña con Historial) ---
        self.hierarchy_panel = ItemHierarchyPanel(main_app_ref=self) # Pasar referencia de DiagramApp
        self.hierarchy_dock = QDockWidget("Explorador de Elementos", self)
        self.hierarchy_dock.setWidget(self.hierarchy_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.hierarchy_dock) 
        self.hierarchy_dock.setObjectName("HierarchyDock")
        
        # Tabular los docks de la derecha
        self.tabifyDockWidget(self.history_dock, self.hierarchy_dock)
        self.history_dock.raise_() # Mostrar el historial por defecto al inicio


        self._create_actions()
        self._create_toolbars()
        self._create_menus()
        self._connect_signals() 

        self.current_file_path = None
        self.set_modified(False) 
        self.new_file() 
        self.hierarchy_panel.update_tree() # Poblar árbol de jerarquía inicialmente


    def _create_actions(self):
        self.new_action = QAction(QIcon.fromTheme("document-new", QIcon()), "Nuevo", self)
        self.new_action.setShortcut("Ctrl+N")
        self.open_action = QAction(QIcon.fromTheme("document-open", QIcon()), "Abrir...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.save_action = QAction(QIcon.fromTheme("document-save", QIcon()), "Guardar", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_as_action = QAction(QIcon.fromTheme("document-save-as", QIcon()), "Guardar Como...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.export_image_action = QAction(QIcon.fromTheme("document-export", QIcon()), "Exportar como Imagen...", self) 
        self.exit_action = QAction(QIcon.fromTheme("application-exit", QIcon()), "Salir", self)
        self.exit_action.setShortcut("Ctrl+Q")
        
        self.copy_action = QAction(QIcon.fromTheme("edit-copy", QIcon()), "Copiar", self)
        self.copy_action.setShortcut(QKeySequence.Copy)
        self.paste_action = QAction(QIcon.fromTheme("edit-paste", QIcon()), "Pegar", self)
        self.paste_action.setShortcut(QKeySequence.Paste)

        self.delete_action = QAction(QIcon.fromTheme("edit-delete", QIcon()), "Eliminar", self)
        self.delete_action.setShortcut(Qt.Key_Delete) 
        self.properties_action = QAction(QIcon.fromTheme("document-properties", QIcon()), "Propiedades...", self)
        
        self.import_image_action = QAction(QIcon.fromTheme("insert-image", QIcon()), "Importar Imagen...", self)

        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon()), "Acercar", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon()), "Alejar", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_reset_action = QAction(QIcon.fromTheme("zoom-original", QIcon()), "Zoom Original", self)
        self.zoom_reset_action.setShortcut("Ctrl+0")

        # Acciones de Capas
        self.bring_to_front_action = QAction(QIcon.fromTheme("go-top", QIcon()), "Traer al Frente", self)
        self.send_to_back_action = QAction(QIcon.fromTheme("go-bottom", QIcon()), "Enviar al Fondo", self)
        self.bring_forward_action = QAction(QIcon.fromTheme("go-up", QIcon()), "Adelante", self)
        self.send_backward_action = QAction(QIcon.fromTheme("go-down", QIcon()), "Atrás", self)


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
        
        layer_toolbar = self.addToolBar("Capas") 
        layer_toolbar.addAction(self.bring_to_front_action)
        layer_toolbar.addAction(self.send_to_back_action)
        layer_toolbar.addAction(self.bring_forward_action)
        layer_toolbar.addAction(self.send_backward_action)


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
        edit_menu.addSeparator()
        layer_menu = edit_menu.addMenu("Capas")
        layer_menu.addAction(self.bring_to_front_action)
        layer_menu.addAction(self.send_to_back_action)
        layer_menu.addAction(self.bring_forward_action)
        layer_menu.addAction(self.send_backward_action)

        
        view_menu = menu_bar.addMenu("&Ver")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.zoom_reset_action)
        view_menu.addSeparator()
        self.toggle_grid_action = QAction("Mostrar Cuadrícula", self, checkable=True) 
        self.toggle_grid_action.setChecked(self.scene.draw_grid)
        view_menu.addAction(self.toggle_grid_action)
        view_menu.addSeparator()
        toggle_palette_action = self.palette_dock.toggleViewAction() 
        toggle_palette_action.setText("Mostrar/Ocultar Paleta")
        view_menu.addAction(toggle_palette_action)
        toggle_history_action = self.history_dock.toggleViewAction() 
        toggle_history_action.setText("Mostrar/Ocultar Historial")
        view_menu.addAction(toggle_history_action)
        if hasattr(self, 'hierarchy_dock'): 
            toggle_hierarchy_action = self.hierarchy_dock.toggleViewAction()
            toggle_hierarchy_action.setText("Mostrar/Ocultar Explorador")
            view_menu.addAction(toggle_hierarchy_action)


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

        self.scene.item_added.connect(self.handle_item_added_or_removed_for_ui)
        self.scene.item_removed.connect(self.handle_item_added_or_removed_for_ui) 
        self.scene.items_visibility_changed.connect(self.update_navigation_buttons)
        self.scene.item_selected.connect(self._on_tree_item_selected_in_hierarchy) # CORRECCIÓN

        if hasattr(self, 'hierarchy_panel') and self.hierarchy_panel:
            self.hierarchy_panel.item_selected_in_tree.connect(self._on_tree_item_selected_in_hierarchy)
            self.hierarchy_panel.item_renamed_in_tree.connect(self._on_tree_item_renamed_in_hierarchy)
            self.hierarchy_panel.item_layer_change_requested.connect(self._on_tree_item_layer_change_requested)
            self.scene.items_visibility_changed.connect(self.hierarchy_panel.update_tree)
        
        self.bring_to_front_action.triggered.connect(self.bring_selected_to_front)
        self.send_to_back_action.triggered.connect(self.send_selected_to_back)
        self.bring_forward_action.triggered.connect(self.bring_selected_forward)
        self.send_backward_action.triggered.connect(self.send_selected_backward)


    def handle_item_removed_for_history(self, item):
        """Manejador para la señal item_removed, para construir una descripción segura."""
        if self.is_viewing_history: return 
        if isinstance(item, (DiagramItem, Connector)):
            item_type_desc = getattr(item, 'item_type', type(item).__name__)
            item_id_desc = getattr(item, 'id', 'N/A')
            text_desc = ""
            if hasattr(item, 'properties') and 'text' in item.properties:
                text_desc = item.properties['text']
            elif hasattr(item, 'text') and item.text: 
                 text_desc = item.text
            
            description = f"Eliminar {item_type_desc}"
            if text_desc:
                description += f" '{text_desc}'"
            description += f" (ID:{item_id_desc})"
            self.on_diagram_modified(action_description=description)
        if hasattr(self, 'hierarchy_panel') and self.hierarchy_panel: 
            self.hierarchy_panel.update_tree()


    def handle_item_added_or_removed_for_ui(self, item):
        """Llamado cuando un ítem se añade o elimina, para actualizar UI como el árbol."""
        if hasattr(self, 'hierarchy_panel') and self.hierarchy_panel:
            self.hierarchy_panel.update_tree()
        
        if isinstance(item, DiagramItem):
            desc_action = "Añadir" if item.scene() else "Eliminar" 
            self.on_diagram_modified(action_description=f"{desc_action} {getattr(item, 'item_type', 'elemento')}")
        elif isinstance(item, Connector):
            desc_action = "Añadir" if item.scene() else "Eliminar"
            self.on_diagram_modified(action_description=f"{desc_action} Conector")


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
        if hasattr(self, 'hierarchy_panel'): self.hierarchy_panel.update_tree()


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
                if hasattr(self, 'hierarchy_panel'): self.hierarchy_panel.update_tree()
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
            # self.update_preview_panel_if_container(None, False) # Eliminado

        if hasattr(self, 'hierarchy_panel') and self.hierarchy_panel: 
            self.hierarchy_panel.update_tree()


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
        
        if hasattr(item_to_edit, "properties"):
            item_text = item_to_edit.properties.get('text', getattr(item_to_edit, 'item_type', type(item_to_edit).__name__))
        else:
            item_text = getattr(item_to_edit, 'text', type(item_to_edit).__name__)
        self._capture_history_state(f"Inicio edición props de {item_text}")

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
        if hasattr(self, 'hierarchy_panel'): 
            self.hierarchy_panel.update_tree()
    
    def update_navigation_buttons(self):
        if self.scene.active_container_id:
            self.up_level_button.setEnabled(True)
            self.up_level_button.setToolTip(f"Volver del contexto actual")
        else:
            self.up_level_button.setEnabled(False)
            self.up_level_button.setToolTip("")
        self.update_title() 
        if hasattr(self, 'hierarchy_panel'): 
            self.hierarchy_panel.update_tree()

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
        
        self.bring_to_front_action.setEnabled(not read_only)
        self.send_to_back_action.setEnabled(not read_only)
        self.bring_forward_action.setEnabled(not read_only)
        self.send_backward_action.setEnabled(not read_only)

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

    def _on_scene_selection_changed_custom_signal(self, selected_item, is_selected): # CORRECCIÓN: Cambiar nombre e argumentos
        """Cuando la selección cambia en la escena (vía sinal personalizado), actualiza el árbol de jerarquía."""
        if hasattr(self, 'hierarchy_panel') and self.hierarchy_panel and not self.hierarchy_panel._block_scene_selection_update:
            if is_selected and selected_item:
                self.hierarchy_panel.select_diagram_item_in_tree(getattr(selected_item, 'id', None))
            else:
                self.hierarchy_panel.select_diagram_item_in_tree(None)
    
    def _on_tree_item_selected_in_hierarchy(self, item_id: str):
        """Cuando se selecciona un ítem en el árbol, selecciónalo en la escena."""
        if self.is_viewing_history: return 
        
        item = self.scene.items_by_id.get(item_id)
        if item:
            self.scene.clearSelection()
            item.setSelected(True)
            self.view.ensureVisible(item, 50, 50) 
            
    def _on_tree_item_renamed_in_hierarchy(self, item_id: str, new_text: str):
        """Cuando un ítem se renombra en el árbol, actualiza el DiagramItem."""
        if self.is_viewing_history: return

        diagram_item = self.scene.items_by_id.get(item_id)
        if diagram_item and isinstance(diagram_item, DiagramItem):
            if diagram_item.properties.get("text") != new_text:
                self._capture_history_state(f"Renombrar '{diagram_item.properties.get('text')}' a '{new_text}' desde árbol")
                diagram_item.properties["text"] = new_text
                diagram_item.update_appearance() 
                self.on_diagram_modified(capture_state=False)

    def _on_tree_item_layer_change_requested(self, item_id: str, change_type: str):
        if self.is_viewing_history: return
        item = self.scene.items_by_id.get(item_id)
        if item and isinstance(item, DiagramItem):
            self.scene.clearSelection()
            item.setSelected(True) 
            if change_type == "front": self.bring_selected_to_front()
            elif change_type == "back": self.send_selected_to_back()
            elif change_type == "forward": self.bring_selected_forward()
            elif change_type == "backward": self.send_selected_backward()


    # --- Métodos de Capas ---
    def _change_z_value(self, direction: str):
        if self.is_viewing_history: return
        selected_items = self.scene.selectedItems()
        if not selected_items: return

        self._capture_history_state(f"Cambio de capa: {direction}")
        
        z_values = [item.zValue() for item_id, item in self.scene.items_by_id.items() if isinstance(item, DiagramItem)]
        if not z_values: 
            min_z = 0.0
            max_z = 0.0
        else:
            min_z = min(z_values) 
            max_z = max(z_values) 

        for item in selected_items:
            if isinstance(item, DiagramItem): 
                if direction == "front":
                    item.setZValue(max_z + 1)
                elif direction == "back":
                    item.setZValue(min_z - 1)
                elif direction == "forward":
                    item.setZValue(item.zValue() + 1)
                elif direction == "backward":
                    item.setZValue(item.zValue() - 1)
        self.on_diagram_modified(capture_state=False, action_description=f"Capa {direction}") 

    def bring_selected_to_front(self): self._change_z_value("front")
    def send_selected_to_back(self): self._change_z_value("back")
    def bring_selected_forward(self): self._change_z_value("forward")
    def send_selected_backward(self): self._change_z_value("backward")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = DiagramApp() 
    main_win.show()
    sys.exit(app.exec_())

