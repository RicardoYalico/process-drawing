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
        self.connection_style = "diagonal" # "diagonal" or "orthogonal"

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
                "font_size": self.font_size,
                "connection_style": self.connection_style
            }
        return None

    def set_properties(self, data, items_by_id):
        self.line_color = QColor(data.get("line_color", self.line_color.name()))
        self.line_width = float(data.get("line_width", self.line_width))
        self.text = data.get("text", "")
        self.font_size = data.get("font_size", 9)
        self.connection_style = data.get("connection_style", "diagonal")

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
            # Corrected call to intersects: it returns a tuple (IntersectType, QPointF_or_None)
            intersect_type, intersection_point_result = line_to_center.intersects(side)

            # Check if there's a bounded intersection and the point is valid
            if intersect_type == QLineF.BoundedIntersection and intersection_point_result is not None:
                current_dist_line = QLineF(line_to_center.p1(), intersection_point_result)
                current_dist_sq = current_dist_line.length() * current_dist_line.length()
                if current_dist_sq < min_dist_sq:
                    line_vec = line_to_center.unitVector()
                    p1_to_intersect_vec = intersection_point_result - line_to_center.p1()
                    dot_product = QPointF.dotProduct(QPointF(line_vec.dx(), line_vec.dy()), p1_to_intersect_vec)

                    if dot_product >= -1e-6 : # Ensure intersection is in the direction of the line or very close
                        min_dist_sq = current_dist_sq
                        closest_intersection = intersection_point_result
        
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

    def _get_orthogonal_path_points_local(self):
        """Calculates the points for an orthogonal path in local coordinates."""
        p1_scene, p2_scene = self._calculate_adjusted_endpoints()
        if p1_scene is None or p2_scene is None:
            return []

        points_scene = []
        points_scene.append(p1_scene)
        # Simple H-V routing: horizontal from p1, then vertical to p2
        intermediate_point = QPointF(p2_scene.x(), p1_scene.y())
        points_scene.append(intermediate_point)
        points_scene.append(p2_scene)

        # Remove duplicate consecutive points (can happen for straight lines)
        final_points_scene = []
        if points_scene:
            final_points_scene.append(points_scene[0])
            for i in range(1, len(points_scene)):
                if QLineF(points_scene[i-1], points_scene[i]).length() > 0.1: # Threshold to avoid floating point issues
                    final_points_scene.append(points_scene[i])

        return [self.mapFromScene(pt) for pt in final_points_scene]


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
        if self.connection_style == "orthogonal":
            local_points = self._get_orthogonal_path_points_local()
            if not local_points or len(local_points) < 2:
                return path
            path.moveTo(local_points[0])
            for point in local_points[1:]:
                path.lineTo(point)
        else: # Diagonal
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
            # Get the actual start and end points for handles
            adj_p1_scene, adj_p2_scene = self._calculate_adjusted_endpoints()
            if adj_p1_scene and adj_p2_scene:
                p1_local_handle = self.mapFromScene(adj_p1_scene)
                p2_local_handle = self.mapFromScene(adj_p2_scene)
                stroked_path.addEllipse(p1_local_handle, self.end_point_handle_radius, self.end_point_handle_radius)
                stroked_path.addEllipse(p2_local_handle, self.end_point_handle_radius, self.end_point_handle_radius)
        return stroked_path

    def boundingRect(self):
        path = QPainterPath()
        text_bound_rect_local = QRectF()
        p1_local_handle = QPointF()
        p2_local_handle = QPointF()

        if self.connection_style == "orthogonal":
            local_points = self._get_orthogonal_path_points_local()
            if not local_points or len(local_points) < 2:
                return QRectF()
            path.moveTo(local_points[0])
            for point in local_points[1:]:
                path.lineTo(point)
            
            # Handles are at the actual adjusted endpoints
            adj_p1_scene, adj_p2_scene = self._calculate_adjusted_endpoints()
            if adj_p1_scene and adj_p2_scene:
                p1_local_handle = self.mapFromScene(adj_p1_scene)
                p2_local_handle = self.mapFromScene(adj_p2_scene)

            if self.text and local_points:
                # For orthogonal, place text near the middle of the path's bounding box
                path_bbox = path.boundingRect()
                mid_point = path_bbox.center()
                font = QFont()
                font.setPointSize(self.font_size)
                fm = QFontMetrics(font)
                text_rect_size = fm.boundingRect(self.text)
                text_bound_rect_local = QRectF(mid_point - QPointF(text_rect_size.width()/2, text_rect_size.height()/2),
                                         QSizeF(text_rect_size.width(), text_rect_size.height()))
        else: # Diagonal
            p1_scene, p2_scene = self._calculate_adjusted_endpoints()
            if p1_scene is None or p2_scene is None:
                return QRectF()
            p1_local_handle = self.mapFromScene(p1_scene) # For diagonal, path points are handle points
            p2_local_handle = self.mapFromScene(p2_scene)
            path.moveTo(p1_local_handle)
            path.lineTo(p2_local_handle)

            if self.text:
                font = QFont()
                font.setPointSize(self.font_size)
                fm = QFontMetrics(font)
                text_rect_size = fm.boundingRect(self.text)
                mid_point = (p1_local_handle + p2_local_handle) / 2.0
                text_bound_rect_local = QRectF(mid_point - QPointF(text_rect_size.width()/2, text_rect_size.height()/2),
                                         QSizeF(text_rect_size.width(), text_rect_size.height()))

        # Combine path bounding rect with text bounding rect
        combined_rect = path.boundingRect().united(text_bound_rect_local)

        # Ensure handles are included in bounding rect if they are outside the path/text
        if p1_local_handle != QPointF() and p2_local_handle != QPointF(): # Check if handles are initialized
             handle_rect = QRectF(p1_local_handle, p2_local_handle).normalized()
             handle_rect = handle_rect.adjusted(-self.end_point_handle_radius, -self.end_point_handle_radius,
                                                self.end_point_handle_radius, self.end_point_handle_radius)
             combined_rect = combined_rect.united(handle_rect)


        margin = self.arrow_size + self.line_width # end_point_handle_radius already considered for handles
        return combined_rect.adjusted(-margin, -margin, margin, margin)


    def paint(self, painter, option, widget=None):
        pen = QPen(self.line_color, self.line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Get actual adjusted endpoints for handles and general reference
        adj_p1_scene, adj_p2_scene = self._calculate_adjusted_endpoints()
        if not (adj_p1_scene and adj_p2_scene):
            return

        p1_local_handle = self.mapFromScene(adj_p1_scene)
        p2_local_handle = self.mapFromScene(adj_p2_scene)

        last_segment_for_arrow = QLineF()
        text_mid_point_local = QPointF()

        if self.connection_style == "orthogonal":
            local_points = self._get_orthogonal_path_points_local()
            if not local_points or len(local_points) < 2:
                return

            line_path = QPainterPath()
            line_path.moveTo(local_points[0])
            for point in local_points[1:]:
                line_path.lineTo(point)
            painter.drawPath(line_path)

            if len(local_points) >= 2:
                last_segment_for_arrow = QLineF(local_points[-2], local_points[-1])
            
            # Text midpoint for orthogonal
            path_bbox_local = line_path.boundingRect()
            text_mid_point_local = path_bbox_local.center()

        else: # Diagonal
            line_local = QLineF(p1_local_handle, p2_local_handle)
            painter.drawLine(line_local)
            last_segment_for_arrow = line_local
            text_mid_point_local = line_local.pointAt(0.5)


        if self.text:
            font = QFont()
            font.setPointSize(self.font_size)
            painter.setFont(font)
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(self.text)
            text_height = fm.height()

            text_bg_rect = QRectF(text_mid_point_local.x() - text_width / 2 - 2,
                                  text_mid_point_local.y() - text_height / 2 - 2,
                                  text_width + 4, text_height + 4)
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(text_bg_rect, 3, 3)

            painter.setPen(Qt.black) # Ensure text color is black
            painter.drawText(text_bg_rect, Qt.AlignCenter, self.text)


        if not (self._dragging_end == 'end' and self._current_drag_pos):
            if last_segment_for_arrow.length() > self.arrow_size / 2.0 : # Check length of the segment for arrow
                angle_rad = math.atan2(-last_segment_for_arrow.dy(), last_segment_for_arrow.dx())
                arrow_tip_point = last_segment_for_arrow.p2()

                arrow_p1 = arrow_tip_point - QPointF(math.cos(angle_rad + math.pi / 6.0) * self.arrow_size,
                                            -math.sin(angle_rad + math.pi / 6.0) * self.arrow_size)
                arrow_p2_actual = arrow_tip_point - QPointF(math.cos(angle_rad - math.pi / 6.0) * self.arrow_size,
                                            -math.sin(angle_rad - math.pi / 6.0) * self.arrow_size)
                arrow_head = QPolygonF([arrow_tip_point, arrow_p1, arrow_p2_actual])
                painter.setBrush(QBrush(self.line_color))
                painter.setPen(self.line_color) # Ensure arrow border is also line_color
                painter.drawPolygon(arrow_head)

        if self.isSelected():
            painter.setBrush(Qt.white)
            painter.setPen(Qt.black)
            painter.drawEllipse(p1_local_handle, self.end_point_handle_radius, self.end_point_handle_radius)
            painter.drawEllipse(p2_local_handle, self.end_point_handle_radius, self.end_point_handle_radius)

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