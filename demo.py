# demo.py
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import QRectF, Qt

# Asumimos que DiagramItem y AVAILABLE_ITEM_TYPES serían importados
# desde tu archivo principal si esto fuera un módulo separado en un proyecto más grande.
# Por ahora, para que este archivo sea ejecutable por sí mismo (para pruebas),
# podríamos necesitar una definición mínima de DiagramItem aquí o manejar la importación.
# Sin embargo, para la integración que solicitas, main.py importará esto.

# Si DiagramItem no está disponible globalmente al importar demo.py,
# necesitarías una estructura de importación como:
# from main_module import DiagramItem, AVAILABLE_ITEM_TYPES 
# (suponiendo que tu archivo principal se llame main_module.py)
# O, para este ejemplo, definiremos una clase base mínima si es necesario para pruebas aisladas,
# pero el objetivo es que se use la de main.py.

# Para la integración directa, main.py conocerá DiagramItem.
# Solo necesitamos definir la nueva clase y su tipo.

ITEM_RED_CIRCLE = "red_circle"

class RedCircleItem(QGraphicsItem): # Idealmente heredaría de tu DiagramItem
    def __init__(self, parent=None):
        # Si DiagramItem no se puede importar directamente, y solo para este ejemplo aislado:
        # super().__init__(parent) # Si QGraphicsItem es el padre directo
        # Si DiagramItem SÍ se puede importar (como se espera para la integración):
        # super().__init__(ITEM_RED_CIRCLE, parent) # Llamar al __init__ de DiagramItem
        
        # Para este ejemplo de archivo separado que luego se integra,
        # vamos a asumir que el __init__ de la clase base (DiagramItem de main.py)
        # se encargará de `item_type`. Aquí solo definimos las propiedades específicas.
        
        # --- Inicio de Bloque para que sea funcional si DiagramItem no está disponible ---
        # Este bloque es para que el archivo sea "independiente" si se prueba solo.
        # En la integración real, DiagramItem vendrá de main.py.
        super().__init__(parent)
        self.item_type = ITEM_RED_CIRCLE
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.properties = {
            "fill_color": "#FF0000", # Rojo
            "border_color": "#A00000", # Rojo oscuro
            "text": "Círculo",
            "font_size": 10 
        }
        self.width = 60.0
        self.height = 60.0
        # --- Fin de Bloque ---


    def boundingRect(self):
        # Asumiendo que width y height son atributos de la instancia
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QPen(QColor(self.properties.get("border_color", "#A00000")), 2))
        painter.setBrush(QBrush(QColor(self.properties.get("fill_color", "#FF0000"))))
        painter.drawEllipse(QRectF(0, 0, self.width, self.height))
        
        # Dibujar texto (opcional, como en otros ítems)
        font = QFont()
        font.setPointSize(self.properties.get("font_size", 10))
        painter.setFont(font)
        painter.setPen(Qt.white) # Texto blanco para contraste con el rojo
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.properties.get("text", "Círculo"))

        # Si se hereda de DiagramItem, se llamaría a super().paint() para los handles, etc.
        # if hasattr(super(), 'paint'):
        #     super().paint(painter, option, widget)


# Función para registrar este nuevo tipo de ítem (si se usa un sistema de plugins)
# Esto es conceptual para mostrar cómo se podría añadir a AVAILABLE_ITEM_TYPES
def register_item_type():
    """
    Esta función es conceptual. En la práctica, la forma de registrar
    dependerá de cómo esté estructurado tu sistema de plugins o módulos.
    """
    return {
        ITEM_RED_CIRCLE: {"class": RedCircleItem, "icon_char": "🔴", "name": "Círculo Rojo"}
    }

if __name__ == '__main__':
    # Código de prueba simple si ejecutas demo.py directamente
    # Esto requeriría una QApplication, QGraphicsView, QGraphicsScene, etc.
    # Por ahora, este bloque se deja vacío ya que la intención es importarlo.
    print("demo.py ejecutado directamente. Contiene RedCircleItem.")
    # item_info = register_item_type()
    # print(f"Información del ítem a registrar: {item_info}")
