# GENESIS — Lexical Analysis Studio

GENESIS es un lenguaje de programación académico orientado a describir ecosistemas, especies y evolución artificial. Este proyecto implementa su **análisis léxico** para la materia Lenguajes y Autómatas I. Actualmente no ejecuta programas ni simulaciones biológicas.

## Funcionalidades

- Editor con resaltado de las 11 palabras reservadas, números de línea y apertura de archivos `.gen` y `.txt`.
- Tokenización manual y autómatas finitos deterministas para identificadores, enteros y decimales.
- Vistas de tokens y errores léxicos con posiciones de línea y columna.
- Tabla de símbolos binaria con eliminación secuencial de duplicados y consulta de registros mediante acceso aleatorio.
- Operaciones de archivo, compilación desde la interfaz y atajo `F5`.

## Requisitos y ejecución

Se necesita **Python 3.14 con Tkinter** en Windows. El proyecto no requiere paquetes externos.

```powershell
git clone https://github.com/nata23-dev/compilador-.git
cd compilador-
py main.py
```

También puedes abrir la carpeta clonada en VS Code y ejecutar `py main.py` desde su terminal.

## Estructura

```text
main.py                    Punto de entrada de la interfaz
genesis/                   Interfaz, reglas del lenguaje, analizador y AFD
ejemplos/                  Programas GENESIS de ejemplo (.gen)
datos/Tabla de símbolos   Archivo binario de la tabla de símbolos
```

Cada registro de la Tabla de símbolos ocupa **300 bytes**. La consulta individual se realiza con `seek()` según el número de registro. El archivo binario se publica con su contenido actual; al iniciar la aplicación, la tabla se reconstruye con las palabras reservadas y, al compilar, con los símbolos del programa analizado.
