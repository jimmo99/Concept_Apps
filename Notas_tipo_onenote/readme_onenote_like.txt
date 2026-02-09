Gestor de Notas Personal - Versión Simplificada
===============================================

Descripción
-----------
Esta aplicación es un gestor de notas personales, inspirado en OneNote y Trello.
Permite crear notas con título, contenido, estados configurables y múltiples etiquetas.  
También puedes archivar notas para sacarlas de la vista principal y consultarlas cuando quieras.

Funcionalidades principales
---------------------------
- Crear, editar y eliminar notas.
- Asignar estados (configurables) y múltiples etiquetas a cada nota.
- Archivar notas para mantener organizada solo la información relevante.
- Buscar notas por texto y etiquetas.
- Adjuntar archivos a las notas.
- Exportar todas las notas a un archivo Excel para copia de seguridad o traslado.
- Gestión dinámica de estados con ventana para añadir o eliminar opciones.

Requisitos
----------
- Python 3.7 o superior.
- Librerías requeridas:
  - tkinter (incluido en Python en la mayoría de los casos)
  - openpyxl (instalar con `pip install openpyxl`)

Instalación y uso
-----------------
1. Instala Python si no lo tienes (https://www.python.org/downloads/).
2. Instala la librería openpyxl:
pip install openpyxl
3. Ejecuta el script principal con:
python gestor_notas.py
4. Usa el panel lateral para crear y gestionar notas.
5. El botón "Editar estados" permite añadir nuevos estados personalizados.
6. Usa "Archivar" y "Mostrar Archivadas" para mantener la organización.
7. Exporta a Excel para respaldar tus notas.

Notas complementarias
---------------------
- Todos los datos se guardan localmente en una base de datos SQLite `notas_movil.db`.
- La carpeta `attachments/` guarda los archivos adjuntos.
- Interfaz multi-plataforma para Windows, Linux y macOS.
- Actualmente sin sincronización online, se puede añadir en futuras versiones.

Licencia
--------
Proyecto de código abierto para uso personal y educativo.

---

Disfruta organizando tus notas con facilidad y flexibilidad.