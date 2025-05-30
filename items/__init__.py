# Importar todas as constantes de tipo desde core.constants
from core.constants import ( # CORREXIDO: Importación absoluta
    ITEM_RECTANGLE, ITEM_ELLIPSE, ITEM_DIAMOND, ITEM_TEXT,
    ITEM_CONTAINER, ITEM_IMAGE, ITEM_SCRIPT, ITEM_PERSONA
)

# Importar todas as clases de ítems específicos
from .rectangle_item import RectangleItem # Importación relativa dentro do paquete items
from .ellipse_item import EllipseItem
from .diamond_item import DiamondItem
from .text_item import TextItem
from .container_item import ContainerItem
from .image_item import ImageItem
from .script_item import ScriptItem
from .persona_item import PersonaItem
# from demo import RedCircleItem # Exemplo se demo.py está no nivel superior

AVAILABLE_ITEM_TYPES = {
    ITEM_RECTANGLE: {"class": RectangleItem, "icon_char": "📦", "name": "Rectángulo"},
    ITEM_ELLIPSE:   {"class": EllipseItem,   "icon_char": "🔵", "name": "Elipse"},
    ITEM_DIAMOND:   {"class": DiamondItem,   "icon_char": "💠", "name": "Decisión"},
    ITEM_TEXT:      {"class": TextItem,      "icon_char": "✍️", "name": "Texto"},
    ITEM_CONTAINER: {"class": ContainerItem, "icon_char": "🗳️", "name": "Contenedor"},
    ITEM_IMAGE:     {"class": ImageItem,     "icon_char": "🖼️", "name": "Imagen (Importar)"}, 
    ITEM_SCRIPT:    {"class": ScriptItem,    "icon_char": "📜", "name": "Script"},
    ITEM_PERSONA:   {"class": PersonaItem,   "icon_char": "👤", "name": "Persona"}, 
    # Se se integra demo.py:
    # from demo import ITEM_RED_CIRCLE, RedCircleItem 
    # ITEM_RED_CIRCLE: {"class": RedCircleItem, "icon_char": "🔴", "name": "Círculo Vermello Demo"},
}

__all__ = [
    "RectangleItem", "EllipseItem", "DiamondItem", "TextItem", 
    "ContainerItem", "ImageItem", "ScriptItem", "PersonaItem",
    "AVAILABLE_ITEM_TYPES"
]
