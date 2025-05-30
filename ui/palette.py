# ui/palette.py
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QGraphicsItem # QGraphicsItem para setFlags
from PyQt5.QtGui import QPainter, QFont, QIcon, QPixmap, QDrag
from PyQt5.QtCore import Qt, QSize, QPointF, QRectF, QMimeData

from items import AVAILABLE_ITEM_TYPES # Desde items/__init__.py
from core.constants import USER_IMAGE_PREFIX # Desde core/constants.py

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

    # ... (Copiar aquí TODOS los métodos de ItemPalette del archivo main.py original) ...
    # ... (populate_standard_items, add_user_image_to_palette, 
    #      remove_user_image_from_palette, clear_user_images_from_palette,
    #      add_palette_item_entry, startDrag, filter_items) ...
    # Asegúrate de que las importaciones sean correctas dentro de estos métodos si es necesario.
    def populate_standard_items(self):
        from core.constants import ITEM_IMAGE # Importar aquí si es necesario
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
            if not item_bound_rect.isEmpty() and temp_item_instance.width > 0 and temp_item_instance.height > 0 : 
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

