# diagramador_app/core/connector.py
import math
from PyQt5.QtWidgets import QGraphicsItem, QInputDialog, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPolygonF, QPainterPath, QPainterPathStroker, QFontMetrics, QTransform
from PyQt5.QtCore import Qt, QPointF, QLineF, QRectF, QSizeF

# Importar DiagramItem para isinstance y type hinting
from .diagram_item_base import DiagramItem 

class Connector(QGraphicsItem): 
    def __init__(self, start_item: DiagramItem, end_item: DiagramItem, parent=None):
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
        self.item_type = "connector" # Para identificación en historial y otros lugares

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
            intersection_point = QPointF() 
            intersect_type = line_to_center.intersect(side, intersection_point) 
            
            if intersect_type == QLineF.BoundedIntersection:
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
        elif self._dragging_end == 'end' and self._current_drag_pos:
            p2 = self._current_drag_pos
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
            # Necesitamos DiagramItem para la comprobación de tipo
            from .diagram_item_base import DiagramItem 

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
