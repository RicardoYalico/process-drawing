

#  ProzessDiagramm: Tu Herramienta de Diagramación Intuitiva ✨

ProzessDiagramm (Process Drawing Diagramador) es una aplicación de escritorio desarrollada en Python con PyQt5, diseñada para facilitar la creación, personalización y gestión de diagramas de flujo, C4, y otros diagramas visuales. Su interfaz intuitiva y conjunto de herramientas la convierten en una excelente opción para plasmar ideas, procesos y arquitecturas de software.

## ✨ Funcionalidades Destacadas

* **Paleta de Elementos Intuitiva**:
    * **Arrastrar y Soltar**: Añade elementos al lienzo fácilmente desde la paleta.
    * **Previsualización de Íconos**: Cada elemento en la paleta muestra una vista previa de su apariencia.
    * **Búsqueda Integrada**: Filtra elementos en la paleta para encontrar rápidamente lo que necesitas.
    * **Imágenes de Usuario en Paleta**: Importa tus propias imágenes, las cuales se añaden a la paleta para su reutilización.
* **Elementos de Diagrama Diversos y Personalizables**:
    * **Variedad de Tipos**: Incluye Rectángulo, Elipse, Diamante (Decisión), Texto, Imagen, Persona (genérica y estilo C4).
    * **Ítems Contenedores**: Permiten agrupar elementos y crear diagramas con estructura jerárquica o anidada. Ver "Guía Avanzada" para más detalles sobre navegación.
    * **Ítems Scriptables**: Dibuja formas completamente personalizadas utilizando código Python y `QPainter` directamente en el editor de propiedades del ítem.
    * **Edición de Propiedades**: Modifica fácilmente atributos como texto, color de relleno, color de borde y tamaño de fuente para cada elemento a través de un diálogo de propiedades.
* **Conectores Flexibles**:
    * **Creación Intuitiva**: Conecta elementos arrastrando con el clic derecho del ratón desde un ítem de origen a uno de destino.
    * **Estilos de Conexión**: Elige entre un trazado **Diagonal** o **Ortogonal** para los conectores.
    * **Indicadores de Dirección**: Los conectores muestran una flecha en el extremo final para indicar la dirección del flujo.
    * **Etiquetas de Texto**: Añade descripciones o etiquetas a los conectores, editables mediante doble clic o el diálogo de propiedades.
    * **Propiedades Editables**: Personaliza el color de la línea, grosor, texto y tamaño de fuente.
* **Gestión de Lienzo y Vista**:
    * **Zoom Dinámico**: Ajusta el nivel de zoom usando la rueda del ratón (+Ctrl), botones en la barra de herramientas o atajos de teclado.
    * **Desplazamiento (Panning)**: Navega por diagramas grandes arrastrando el lienzo.
    * **Cuadrícula de Fondo (Grid)**: Activa una cuadrícula visual para ayudar en la alineación de los elementos; su visibilidad es conmutable.
    * **Manejo de Capas (Orden Z)**: Controla la superposición de elementos enviándolos al frente, al fondo, o moviéndolos un nivel adelante/atrás.
* **Paneles de Herramientas Avanzadas**:
    * **Explorador de Elementos (Jerarquía)**:
        * Visualiza una estructura de árbol de todos los ítems en la escena, mostrando las relaciones de anidamiento dentro de los contenedores.
        * Selección sincronizada: Al seleccionar un ítem en el árbol se selecciona en la escena y viceversa.
        * Renombra ítems y cambia su orden de capa directamente desde el menú contextual del árbol.
    * **Historial de Cambios Detallado**:
        * Registra una lista cronológica de las acciones realizadas en el diagrama.
        * Previsualiza estados pasados del diagrama en modo de solo lectura haciendo clic en una entrada del historial.
        * Restaura el diagrama a un estado anterior haciendo doble clic en una entrada del historial (esto se convierte en el nuevo estado actual, permitiendo ramificar el historial).
        * Opción para limpiar el historial anterior al estado actual ("Limpiar Historial Anterior").
* **Gestión de Archivos y Exportación**:
    * **Guardado y Carga**: Guarda tus diagramas en formato JSON y vuelve a cargarlos para continuar trabajando.
    * **Exportación de Imágenes**: Exporta la vista actual de tu diagrama (solo elementos visibles) a formatos de imagen populares como PNG, JPG y BMP.
* **Operaciones de Edición Esenciales**:
    * **Copiar y Pegar**: Copia (Ctrl+C) los elementos seleccionados y pégalos (Ctrl+V) en una nueva ubicación. Si se copia un contenedor, también se copian sus elementos hijos.
    * **Eliminar**: Borra los elementos seleccionados usando la tecla Supr o la opción del menú/barra de herramientas.
    * **Selección Múltiple**: Selecciona varios elementos arrastrando un rectángulo de selección (RubberBandDrag).

## 🛠️ Tecnologías Utilizadas

* **Python 3:** Lenguaje de programación principal.
* **PyQt5:** Biblioteca para la interfaz gráfica de usuario.

## 📂 Estructura del Proyecto (Simplificada)
```
process-drawing/
├── core/                   # Lógica central de la aplicación
│   ├── init.py
│   ├── scene.py            # Gestión de la escena gráfica (lienzo)
│   ├── diagram_item_base.py # Clase base para todos los elementos del diagrama
│   ├── connector.py        # Lógica para los conectores entre elementos
│   └── constants.py        # Constantes globales
├── items/                  # Definición de los diferentes tipos de elementos gráficos
│   ├── init.py         # Agrupa y expone los tipos de ítems
│   ├── rectangle_item.py   #
│   ├── ellipse_item.py     #
│   ├── container_item.py   #
│   └── ...                 # Otros elementos (diamond, text, image, script, persona, c4persona)
├── ui/                     # Componentes de la interfaz de usuario
│   ├── init.py
│   ├── view.py             # Vista principal del diagrama (QGraphicsView)
│   ├── palette.py          # Paleta de elementos arrastrables
│   └── hierarchy_panel.py  # Panel para mostrar la jerarquía de ítems
└── main.py                 # Punto de entrada de la aplicación, ventana principal
```

## 🏁 Primeros Pasos

1.  **Requisitos Previos:**
    * Asegúrate de tener Python 3 instalado en tu sistema.

2.  **Clona el Repositorio (si aún no lo has hecho):**
    ```bash
    # Ejemplo:
    # git clone [https://github.com/tu_usuario/process-drawing.git](https://github.com/tu_usuario/process-drawing.git)
    # cd process-drawing
    ```
    (Reemplaza la URL con la de tu repositorio si lo subes a una plataforma como GitHub).

3.  **Crea un Entorno Virtual (Recomendado):**
    Esto ayuda a manejar las dependencias de forma aislada.
    ```bash
    python -m venv venv
    ```

4.  **Activa el Entorno Virtual:**
    * En Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * En macOS y Linux:
        ```bash
        source venv/bin/activate
        ```
    Verás `(venv)` al principio de la línea de comandos si se activó correctamente.

5.  **Instala las Dependencias:**
    La dependencia principal es PyQt5.
    ```bash
    pip install PyQt5
    ```
    *Nota: Es una buena práctica crear un archivo `requirements.txt` (ejecutando `pip freeze > requirements.txt` después de instalar PyQt5) para que otros puedan instalar las dependencias fácilmente con `pip install -r requirements.txt`.*

6.  **Ejecuta la Aplicación:**
    Desde el directorio raíz del proyecto (donde se encuentra `main.py`):
    ```bash
    python main.py
    ```

## 💡 Guía de Uso Rápida

1.  **Inicia `ProzessDiagramm`** ejecutando `python main.py`.
2.  **Arrastra elementos** desde la "Paleta de Ítems" (izquierda) al lienzo principal.
3.  **Conecta elementos:** Haz clic derecho sobre un elemento de inicio y arrastra hasta un elemento de destino.
4.  **Edita propiedades:**
    * Selecciona un elemento y haz clic en "Propiedades" en la barra de herramientas o en el menú "Editar".
    * Para elementos con texto (excepto contenedores, scripts, imágenes), haz doble clic para editar el texto directamente.
    * Los conectores también permiten editar su texto mediante doble clic.
5.  **Navega con Contenedores:** Haz doble clic sobre un `ContainerItem` para "entrar" en él y enfocar el diagrama. Usa el botón "⬆️ Subir Nivel" para salir.
6.  **Explora la Jerarquía:** El panel "Explorador de Elementos" (derecha) te permite ver la estructura anidada. Puedes seleccionar, renombrar y cambiar el orden de las capas.
7.  **Revisa el Historial:** El panel "Historial de Cambios" (derecha) te permite ver acciones pasadas, previsualizar estados y revertir a un punto anterior.
8.  **Guarda tu trabajo** usando las opciones del menú "Archivo" (`Ctrl+S`, `Ctrl+Shift+S`).

## 📖 Guía Avanzada

* **Ítems Scriptables (`ScriptItem`):**
    * Al editar las propiedades de un `ScriptItem`, puedes escribir código Python en el campo "Script de Pintura".
    * Este script utiliza un objeto `painter` (una instancia de `QPainter`) y `self` (referencia al propio `ScriptItem`) para dibujar. También tienes acceso a `Qt`, `QColor`, `QRectF`, etc..
    * Ejemplo: `painter.setBrush(QColor("red")); painter.drawRect(0, 0, self.width, self.height)`

* **Navegación y Jerarquía con Contenedores:**
    * Al hacer doble clic en un `ContainerItem`, la vista se actualiza para mostrar solo los elementos hijos de ese contenedor y el contenedor mismo se oculta.
    * Los elementos nuevos creados o pegados mientras se está "dentro" de un contenedor se convierten automáticamente en hijos de ese contenedor activo.
    * Utiliza el botón "⬆️ Subir Nivel" (visible cuando estás dentro de un contenedor) para regresar al nivel padre.
    * La ruta de navegación actual dentro de los contenedores se muestra en la barra de título de la ventana.

* **Uso Avanzado del Panel de Historial:**
    * **Previsualización**: Un clic en una entrada del historial carga ese estado en el lienzo en modo de solo lectura. El panel de historial resaltará la entrada seleccionada.
    * **Restauración**: Un doble clic en una entrada del historial la restaura como el estado actual del diagrama. Esto permite "ramificar" el historial si haces cambios después de restaurar un estado anterior.
    * **Volver al Presente**: Si estás previsualizando un estado histórico, el botón "Volver al Presente" te devuelve al último estado de trabajo activo.
    * **Limpiar Historial Anterior**: Esta opción elimina todas las entradas del historial *anteriores* al estado actual, convirtiendo el estado actual en el punto de partida del nuevo historial. Útil para consolidar cambios después de mucha experimentación.

* **Interacciones con el Explorador de Elementos (Jerarquía):**
    * Además de la selección, puedes hacer doble clic en un ítem del árbol para renombrarlo (si es editable).
    * El menú contextual (clic derecho) sobre un ítem en el árbol permite acceder rápidamente a acciones como "Renombrar" y las opciones de cambio de capa ("Traer al Frente", "Enviar al Fondo", etc.).

* **Estilos de Conectores (Diagonal vs. Ortogonal):**
    * Selecciona un conector y abre el diálogo de "Propiedades".
    * Utiliza el `QComboBox` "Estilo de Conexión" para cambiar entre "Diagonal" y "Ortogonal". El conector se actualizará visualmente en el lienzo.

* **Importación de Imágenes a la Paleta:**
    * Usa "Archivo" -> "Importar Imagen..." para seleccionar un archivo de imagen de tu sistema.
    * La imagen se añadirá como un nuevo ítem al lienzo y también aparecerá en la "Paleta de Ítems" bajo su nombre de archivo para que puedas arrastrar y soltar nuevas instancias de esa imagen.
    * Las imágenes importadas se guardan como referencias de ruta en el archivo JSON del diagrama.

## ⌨️ Atajos de Teclado Comunes

* **Archivo:**
    * `Ctrl+N`: Nuevo diagrama
    * `Ctrl+O`: Abrir diagrama
    * `Ctrl+S`: Guardar diagrama
    * `Ctrl+Shift+S`: Guardar diagrama como...
    * `Ctrl+Q`: Salir
* **Edición:**
    * `Ctrl+C`: Copiar selección
    * `Ctrl+V`: Pegar
    * `Supr` (Delete): Eliminar selección
* **Vista:**
    * `Ctrl++` / `Ctrl+=`: Acercar Zoom
    * `Ctrl+-`: Alejar Zoom
    * `Ctrl+0`: Restablecer Zoom al original
* **Navegación:**
    * `Esc`: Salir del contexto de un contenedor (si estás dentro de uno). Si estás en modo de vista de historial, también puede usarse para volver al presente.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar ProzessDiagramm, por favor considera:

* Reportar bugs y sugerir nuevas características a través de los Issues del repositorio (si aplica).
* Realizar un Fork del proyecto y enviar Pull Requests con tus mejoras.

## 📜 Licencia

Este proyecto se distribuye bajo la Licencia MIT (o la que prefieras). Por favor, revisa el archivo `LICENSE` para más detalles (deberías añadir uno si aún no existe).

---

¡Esperamos que disfrutes usando ProzessDiagramm para dar vida a tus ideas!