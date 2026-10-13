"""Interfaz de escritorio del compilador GENESIS."""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from genesis.analizador_lexico import Token, analizar_codigo
from genesis.afd_numeros import motivo_numero_invalido
from genesis.lenguaje import recorrer_palabras_reservadas
from genesis.tabla_simbolos import (
    ErrorTablaSimbolos,
    consultar_registro,
    leer_registros,
    reconstruir_tabla,
)


class GenesisApp(tk.Tk):
    """Ventana principal, editor y operaciones de archivo."""

    TITULO = "GENESIS | Lexical Analysis Studio"
    CATEGORIAS_RESALTADO = (
        ("estructura", "lila"),
        ("evolucion", "rosa"),
        ("operaciones", "acento"),
    )
    COLOR = {
        "fondo": "#0C1314", "panel": "#142022", "editor": "#0F191B",
        "texto": "#EAF3F2", "secundario": "#95A9A6", "borde": "#2C3F42",
        "acento": "#57C7B6", "acento_activo": "#7DDFC8",
        "exito": "#79DFA7", "lila": "#C28AE8", "rosa": "#EC8CAC",
        "azul": "#7B9BEE", "dorado": "#E3C97C", "error": "#F36C78",
        "margen": "#101C1D", "seleccion": "#285149",
        "scroll_control": "#36534F",
    }

    def __init__(self) -> None:
        super().__init__()
        self.ruta_actual: Path | None = None
        self.tokens: list[Token] = []
        self.analisis_realizado = False
        self.hay_cambios = False
        self._actualizacion_editor_pendiente = False
        self._trabajo_resaltado = None
        self._version_resaltado = 0
        self.menu_archivo_abierto = False
        self._reparto_automatico = True
        self._ajuste_horizontal_pendiente = False

        self.title(self.TITULO)
        ancho = min(1366, max(1120, self.winfo_screenwidth() - 80))
        alto = min(768, max(640, self.winfo_screenheight() - 80))
        izquierda = max(0, (self.winfo_screenwidth() - ancho) // 2)
        arriba = max(0, (self.winfo_screenheight() - alto) // 2)
        self.geometry(f"{ancho}x{alto}+{izquierda}+{arriba}")
        self.minsize(1120, 640)
        self.configure(bg=self.COLOR["fondo"])
        self.protocol("WM_DELETE_WINDOW", self.salir)

        self._configurar_estilos()
        self._crear_menu()
        self._crear_cabecera()
        self._crear_area_central()
        self._crear_barra_estado()
        self._configurar_atajos()
        self._actualizar_archivo()
        self._actualizar_cursor()
        self._dibujar_marca()
        registros_iniciales, _ = self._reconstruir_y_mostrar_tabla([])
        if registros_iniciales is not None:
            self.resumen_resultados.configure(
                text=f"Sin análisis  ·  {registros_iniciales} símbolos precargados"
            )
        self.after(60, self._ajustar_paneles)

    def _configurar_estilos(self) -> None:
        self.fuente_editor = tkfont.Font(family="Consolas", size=12)
        self.fuente_interfaz = "Segoe UI"
        self.fuente_cabecera_tabla = tkfont.Font(
            family=self.fuente_interfaz, size=10, weight="bold"
        )
        self.estilo = ttk.Style(self)
        self.estilo.theme_use("clam")
        estilo = self.estilo
        estilo.configure(
            "Genesis.Treeview",
            background=self.COLOR["panel"],
            fieldbackground=self.COLOR["panel"],
            foreground=self.COLOR["texto"],
            borderwidth=0,
            bordercolor=self.COLOR["borde"],
            lightcolor=self.COLOR["borde"],
            darkcolor=self.COLOR["borde"],
            relief="flat",
            rowheight=28,
            font=(self.fuente_interfaz, 10),
        )
        estilo.configure(
            "Genesis.Treeview.Heading",
            background=self.COLOR["margen"],
            foreground=self.COLOR["texto"],
            borderwidth=0,
            relief="flat",
            padding=(8, 8),
            font=self.fuente_cabecera_tabla,
        )
        estilo.map(
            "Genesis.Treeview",
            background=[("selected", self.COLOR["seleccion"])],
            foreground=[("selected", self.COLOR["texto"])],
        )
        estilo.map(
            "Genesis.Treeview.Heading",
            background=[("active", self.COLOR["borde"])],
        )
        estilo.configure(
            "Genesis.Results.Treeview",
            background=self.COLOR["editor"],
            fieldbackground=self.COLOR["editor"],
            foreground=self.COLOR["texto"],
            borderwidth=0,
            bordercolor=self.COLOR["borde"],
            lightcolor=self.COLOR["borde"],
            darkcolor=self.COLOR["borde"],
            relief="flat",
            rowheight=27,
            font=(self.fuente_interfaz, 10),
        )
        estilo.configure(
            "Genesis.Results.Treeview.Heading",
            background=self.COLOR["margen"],
            foreground=self.COLOR["texto"],
            borderwidth=0,
            relief="flat",
            padding=(8, 7),
            font=self.fuente_cabecera_tabla,
        )
        estilo.map(
            "Genesis.Results.Treeview",
            background=[("selected", self.COLOR["seleccion"])],
            foreground=[("selected", self.COLOR["texto"])],
        )
        estilo.map(
            "Genesis.Results.Treeview.Heading",
            background=[("active", self.COLOR["borde"])],
        )
        for orientacion in ("Vertical", "Horizontal"):
            nombre = f"Genesis.{orientacion}.TScrollbar"
            estilo.configure(
                nombre,
                background=self.COLOR["scroll_control"],
                troughcolor=self.COLOR["editor"],
                arrowcolor=self.COLOR["secundario"],
                bordercolor=self.COLOR["borde"],
                lightcolor=self.COLOR["scroll_control"],
                darkcolor=self.COLOR["scroll_control"],
                borderwidth=1,
                width=16,
                arrowsize=16,
                relief="flat",
            )
            estilo.map(
                nombre,
                background=[("active", self.COLOR["acento"])],
                lightcolor=[("active", self.COLOR["acento"])],
                darkcolor=[("active", self.COLOR["acento"])],
            )

    def _dibujar_marca(self) -> None:
        """Dibuja una doble hélice geométrica con los colores del ADN."""
        self.marca.delete("all")
        self.marca.create_line(
            14, 7, 35, 19, 14, 31, 35, 43,
            fill=self.COLOR["acento"], width=2, smooth=True,
        )
        self.marca.create_line(
            35, 7, 14, 19, 35, 31, 14, 43,
            fill=self.COLOR["lila"], width=2, smooth=True,
        )
        for desplazamiento in range(4):
            y = 7 + desplazamiento * 12
            izquierdo = 14 if desplazamiento % 2 == 0 else 35
            derecho = 35 if desplazamiento % 2 == 0 else 14
            self.marca.create_line(
                izquierdo, y, derecho, y,
                fill=self.COLOR["azul"], width=2,
            )
            self.marca.create_oval(
                izquierdo - 3, y - 3, izquierdo + 3, y + 3,
                fill=self.COLOR["acento"], outline="",
            )
            self.marca.create_oval(
                derecho - 3, y - 3, derecho + 3, y + 3,
                fill=self.COLOR["rosa"], outline="",
            )

    def _crear_menu(self) -> None:
        self.barra_navegacion = tk.Frame(
            self, bg=self.COLOR["panel"], height=64
        )
        self.barra_navegacion.grid(row=0, column=0, sticky="ew")
        self.barra_navegacion.grid_propagate(False)
        self.barra_navegacion.columnconfigure(6, weight=1)

        self.boton_archivo = tk.Button(
            self.barra_navegacion,
            text="Archivo  ▾",
            command=self._alternar_menu_archivo,
            bg=self.COLOR["panel"],
            fg=self.COLOR["secundario"],
            activebackground=self.COLOR["seleccion"],
            activeforeground=self.COLOR["acento_activo"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=7,
            cursor="hand2",
            font=(self.fuente_interfaz, 10, "bold"),
        )
        self.boton_archivo.grid(row=0, column=5, padx=(12, 0), sticky="w")
        self.boton_archivo.bind("<Enter>", self._al_entrar_archivo)
        self.boton_archivo.bind("<Leave>", self._al_salir_archivo)

        self.desplegable_archivo = tk.Frame(
            self,
            bg=self.COLOR["panel"],
            highlightbackground=self.COLOR["borde"],
            highlightthickness=1,
            bd=0,
        )
        opciones = (
            ("Nuevo", "Ctrl+N", self.nuevo),
            ("Abrir archivo", "Ctrl+O", self.abrir),
            None,
            ("Guardar", "Ctrl+S", self.guardar),
            ("Guardar como", "", self.guardar_como),
            None,
            ("Salir", "", self.salir),
        )
        self.filas_archivo = {}
        for opcion in opciones:
            if opcion is None:
                tk.Frame(
                    self.desplegable_archivo,
                    bg=self.COLOR["borde"],
                    height=1,
                ).pack(fill="x", padx=12, pady=4)
            else:
                nombre, atajo, accion = opcion
                self._crear_fila_archivo(nombre, atajo, accion)

        self.bind_all("<ButtonPress-1>", self._al_click_fuera_menu, add="+")
        self.bind_all("<Escape>", self._al_escape_menu, add="+")
        self.bind_all("<FocusOut>", self._al_perder_foco_menu, add="+")
        self.bind("<Configure>", self._al_configurar_ventana, add="+")

    def _crear_fila_archivo(self, nombre: str, atajo: str, accion) -> None:
        fila = tk.Frame(self.desplegable_archivo, bg=self.COLOR["panel"], height=34)
        fila.pack(fill="x")
        fila.pack_propagate(False)
        texto = tk.Label(
            fila,
            text=nombre,
            bg=self.COLOR["panel"],
            fg=self.COLOR["texto"],
            font=(self.fuente_interfaz, 10),
            cursor="hand2",
        )
        texto.pack(side="left", padx=(14, 0), pady=7)
        atajo_texto = tk.Label(
            fila,
            text=atajo,
            bg=self.COLOR["panel"],
            fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 9),
            cursor="hand2",
        )
        atajo_texto.pack(side="right", padx=(10, 14))
        for widget in (fila, texto, atajo_texto):
            widget.bind(
                "<Enter>",
                lambda evento, componentes=(fila, texto, atajo_texto):
                    self._resaltar_fila_archivo(componentes, True),
            )
            widget.bind(
                "<Leave>",
                lambda evento, componentes=(fila, texto, atajo_texto):
                    self._resaltar_fila_archivo(componentes, False),
            )
            widget.bind(
                "<Button-1>",
                lambda evento, comando=accion: self._seleccionar_opcion_archivo(
                    comando
                ),
            )
        self.filas_archivo[nombre] = fila

    def _resaltar_fila_archivo(self, componentes, activo: bool) -> None:
        fondo = self.COLOR["seleccion"] if activo else self.COLOR["panel"]
        for widget in componentes:
            widget.configure(bg=fondo)
        componentes[1].configure(
            fg=self.COLOR["acento_activo"] if activo else self.COLOR["texto"]
        )
        componentes[2].configure(
            fg=self.COLOR["acento_activo"] if activo else self.COLOR["secundario"]
        )

    def _al_entrar_archivo(self, evento=None) -> None:
        self.boton_archivo.configure(
            bg=self.COLOR["seleccion"], fg=self.COLOR["acento_activo"]
        )

    def _al_salir_archivo(self, evento=None) -> None:
        if not self.menu_archivo_abierto:
            self.boton_archivo.configure(
                bg=self.COLOR["panel"], fg=self.COLOR["secundario"]
            )

    def _alternar_menu_archivo(self) -> None:
        if self.menu_archivo_abierto:
            self._cerrar_menu_archivo()
        else:
            self.menu_archivo_abierto = True
            self._al_entrar_archivo()
            self._posicionar_menu_archivo()

    def _posicionar_menu_archivo(self) -> None:
        x = self.boton_archivo.winfo_rootx() - self.winfo_rootx()
        y = (
            self.barra_navegacion.winfo_rooty()
            + self.barra_navegacion.winfo_height()
            - self.winfo_rooty()
        )
        self.desplegable_archivo.place(x=x, y=y, width=276)
        self.desplegable_archivo.lift()

    def _cerrar_menu_archivo(self) -> None:
        self.desplegable_archivo.place_forget()
        self.menu_archivo_abierto = False
        self.boton_archivo.configure(
            bg=self.COLOR["panel"], fg=self.COLOR["secundario"]
        )

    def _seleccionar_opcion_archivo(self, accion) -> None:
        self._cerrar_menu_archivo()
        accion()

    @staticmethod
    def _pertenece_a(widget, contenedor) -> bool:
        while widget is not None:
            if widget is contenedor:
                return True
            widget = widget.master
        return False

    def _al_click_fuera_menu(self, evento) -> None:
        if self.menu_archivo_abierto and not (
            self._pertenece_a(evento.widget, self.desplegable_archivo)
            or self._pertenece_a(evento.widget, self.boton_archivo)
        ):
            self._cerrar_menu_archivo()

    def _al_escape_menu(self, evento) -> str | None:
        if self.menu_archivo_abierto:
            self._cerrar_menu_archivo()
            return "break"
        return None

    def _al_perder_foco_menu(self, evento) -> None:
        if self.menu_archivo_abierto:
            self.after_idle(self._cerrar_menu_si_inactivo)

    def _cerrar_menu_si_inactivo(self) -> None:
        if self.menu_archivo_abierto and self.focus_displayof() is None:
            self._cerrar_menu_archivo()

    def _al_configurar_ventana(self, evento) -> None:
        if evento.widget is self and self.menu_archivo_abierto:
            self._posicionar_menu_archivo()

    def _crear_cabecera(self) -> None:
        cabecera = self.barra_navegacion

        self.marca = tk.Canvas(
            cabecera,
            width=50,
            height=50,
            bg=self.COLOR["panel"],
            bd=0,
            highlightthickness=0,
        )
        self.marca.grid(row=0, column=0, padx=(12, 6), pady=7)

        identidad = tk.Frame(cabecera, bg=self.COLOR["panel"])
        identidad.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=7)
        tk.Label(
            identidad,
            text="GENESIS",
            bg=self.COLOR["panel"],
            fg=self.COLOR["texto"],
            font=(self.fuente_interfaz, 17, "bold"),
        ).pack(anchor="w")
        tk.Frame(
            cabecera, bg=self.COLOR["borde"], width=1, height=26
        ).grid(row=0, column=2, padx=(0, 16))
        tk.Label(
            cabecera,
            text="Lexical Analysis Studio",
            bg=self.COLOR["panel"],
            fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 10),
        ).grid(row=0, column=3, sticky="w")
        tk.Frame(
            cabecera, bg=self.COLOR["borde"], width=1, height=26
        ).grid(row=0, column=4, padx=(18, 0))

        self.boton_compilar = tk.Button(
            cabecera,
            text="▶  Compilar",
            command=self.compilar,
            bg=self.COLOR["acento"],
            fg=self.COLOR["fondo"],
            activebackground=self.COLOR["acento_activo"],
            activeforeground=self.COLOR["fondo"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=22,
            pady=10,
            cursor="hand2",
            font=(self.fuente_interfaz, 10, "bold"),
        )
        self.boton_compilar.grid(row=0, column=7, padx=(0, 16))

        tk.Frame(self, bg=self.COLOR["borde"], height=1).grid(
            row=1, column=0, sticky="ew"
        )

    def _crear_area_central(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.divisor_vertical = tk.PanedWindow(
            self,
            orient=tk.VERTICAL,
            bg=self.COLOR["fondo"],
            sashwidth=8,
            sashrelief="flat",
            bd=0,
            showhandle=False,
        )
        self.divisor_vertical.grid(
            row=2, column=0, sticky="nsew", padx=16, pady=(12, 10)
        )

        self.divisor_horizontal = tk.PanedWindow(
            self.divisor_vertical,
            orient=tk.HORIZONTAL,
            bg=self.COLOR["fondo"],
            sashwidth=8,
            sashrelief="flat",
            bd=0,
            showhandle=False,
        )
        self.divisor_horizontal.bind("<Configure>", self._programar_reparto_horizontal)
        self.divisor_horizontal.bind(
            "<ButtonPress-1>", self._desactivar_reparto_automatico
        )
        self._crear_editor()
        self._crear_panel_simbolos()
        self._crear_resultados()

        self.divisor_horizontal.add(self.panel_editor, minsize=520, stretch="always")
        self.divisor_horizontal.add(self.panel_simbolos, minsize=520, stretch="never")
        self.divisor_vertical.add(
            self.divisor_horizontal, minsize=270, stretch="always"
        )
        self.divisor_vertical.add(self.panel_resultados, minsize=200, stretch="never")

    def _crear_editor(self) -> None:
        self.panel_editor = tk.Frame(
            self.divisor_horizontal,
            bg=self.COLOR["panel"],
            highlightbackground=self.COLOR["borde"],
            highlightthickness=1,
        )
        self.panel_editor.grid_rowconfigure(2, weight=1)
        self.panel_editor.grid_columnconfigure(0, weight=1)
        tk.Frame(self.panel_editor, bg=self.COLOR["acento"], height=2).grid(
            row=0, column=0, sticky="ew"
        )

        encabezado = tk.Frame(self.panel_editor, bg=self.COLOR["margen"], height=42)
        encabezado.grid(row=1, column=0, sticky="ew")
        encabezado.grid_propagate(False)
        pestana = tk.Frame(encabezado, bg=self.COLOR["panel"], height=39)
        pestana.grid(row=0, column=0, sticky="ns", padx=(1, 0), pady=(1, 0))
        pestana.columnconfigure(1, weight=1)
        icono = tk.Canvas(
            pestana, width=18, height=20, bg=self.COLOR["panel"],
            bd=0, highlightthickness=0,
        )
        icono.grid(row=0, column=0, padx=(12, 8), pady=9)
        icono.create_polygon(
            3, 2, 11, 2, 15, 6, 15, 18, 3, 18,
            outline=self.COLOR["acento"], fill="", width=1,
        )
        icono.create_line(11, 2, 11, 6, 15, 6, fill=self.COLOR["acento"])
        icono.create_line(6, 10, 12, 10, fill=self.COLOR["secundario"])
        icono.create_line(6, 13, 12, 13, fill=self.COLOR["secundario"])
        self.etiqueta_archivo = tk.Label(
            pestana,
            bg=self.COLOR["panel"],
            fg=self.COLOR["texto"],
            font=(self.fuente_interfaz, 10, "bold"),
            anchor="w",
        )
        self.etiqueta_archivo.grid(row=0, column=1, sticky="w", pady=9)
        self.etiqueta_cambios = tk.Label(
            pestana,
            bg=self.COLOR["panel"],
            fg=self.COLOR["acento"],
            font=(self.fuente_interfaz, 10, "bold"),
            width=2,
        )
        self.etiqueta_cambios.grid(row=0, column=2, padx=(6, 12))

        cuerpo = tk.Frame(self.panel_editor, bg=self.COLOR["editor"])
        cuerpo.grid(row=2, column=0, sticky="nsew")
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        self.numeros_linea = tk.Canvas(
            cuerpo, width=56, bg=self.COLOR["margen"], bd=0, highlightthickness=0
        )
        self.numeros_linea.grid(row=0, column=0, sticky="ns")

        self.editor = tk.Text(
            cuerpo,
            wrap="none",
            undo=True,
            maxundo=-1,
            bg=self.COLOR["editor"],
            fg=self.COLOR["texto"],
            insertbackground=self.COLOR["acento"],
            selectbackground=self.COLOR["seleccion"],
            selectforeground=self.COLOR["texto"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=self.fuente_editor,
            padx=13,
            pady=12,
            spacing1=1,
            spacing3=1,
            insertwidth=2,
            tabs=(self.fuente_editor.measure("    "),),
        )
        for categoria, color in self.CATEGORIAS_RESALTADO:
            self.editor.tag_configure(
                f"reservada_{categoria}", foreground=self.COLOR[color]
            )
        self.editor.tag_raise("sel")
        self.editor.grid(row=0, column=1, sticky="nsew")
        barra_vertical = ttk.Scrollbar(
            cuerpo,
            orient="vertical",
            command=self._desplazar_editor,
            style="Genesis.Vertical.TScrollbar",
        )
        barra_vertical.grid(row=0, column=2, sticky="ns")
        barra_horizontal = ttk.Scrollbar(
            cuerpo,
            orient="horizontal",
            command=self.editor.xview,
            style="Genesis.Horizontal.TScrollbar",
        )
        barra_horizontal.grid(row=1, column=1, sticky="ew")
        self.editor.configure(
            yscrollcommand=lambda primero, ultimo: self._sincronizar_desplazamiento(
                barra_vertical, primero, ultimo
            ),
            xscrollcommand=barra_horizontal.set,
        )
        self.editor.bind("<<Modified>>", self._al_modificar_editor)
        self.editor.bind("<KeyRelease>", self._programar_actualizacion_editor)
        self.editor.bind("<ButtonRelease-1>", self._programar_actualizacion_editor)
        self.editor.bind("<MouseWheel>", self._programar_actualizacion_editor)
        self.editor.bind("<Configure>", self._programar_actualizacion_editor)
        self.editor.bind("<Tab>", self._insertar_tabulacion)
        self.editor.bind("<Return>", self._insertar_nueva_linea)
        self.editor.edit_modified(False)

    def _crear_panel_simbolos(self) -> None:
        self.panel_simbolos = tk.Frame(
            self.divisor_horizontal,
            bg=self.COLOR["panel"],
            highlightbackground=self.COLOR["borde"],
            highlightthickness=1,
        )
        self.panel_simbolos.grid_rowconfigure(2, weight=1)
        self.panel_simbolos.grid_columnconfigure(0, weight=1)
        tk.Frame(self.panel_simbolos, bg=self.COLOR["lila"], height=2).grid(
            row=0, column=0, sticky="ew"
        )

        encabezado = tk.Frame(self.panel_simbolos, bg=self.COLOR["panel"], height=48)
        encabezado.grid(row=1, column=0, sticky="ew")
        encabezado.grid_propagate(False)
        encabezado.columnconfigure(0, weight=1)
        tk.Label(
            encabezado,
            text="TABLA DE SÍMBOLOS",
            bg=self.COLOR["panel"],
            fg=self.COLOR["lila"],
            font=(self.fuente_interfaz, 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=13)
        self.etiqueta_total_simbolos = tk.Label(
            encabezado,
            text="0 registros",
            bg=self.COLOR["margen"],
            fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 9, "bold"),
            padx=9,
            pady=4,
        )
        self.etiqueta_total_simbolos.grid(row=0, column=1, padx=14)

        contenedor = tk.Frame(self.panel_simbolos, bg=self.COLOR["panel"])
        contenedor.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 4))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("registro", "lexema", "tipo", "linea", "columna")
        self.tabla_simbolos = ttk.Treeview(
            contenedor,
            columns=columnas,
            show="headings",
            selectmode="browse",
            style="Genesis.Treeview",
        )
        configuracion = (
            ("registro", "Número de registro", 138),
            ("lexema", "Lexema", 76),
            ("tipo", "Tipo de token", 143),
            ("linea", "Línea", 50),
            ("columna", "Columna", 71),
        )
        for identificador, titulo, ancho in configuracion:
            ancho = max(ancho, self.fuente_cabecera_tabla.measure(titulo) + 16)
            anclaje = (
                "center" if identificador in {"registro", "linea", "columna"}
                else "w"
            )
            self.tabla_simbolos.heading(identificador, text=titulo, anchor=anclaje)
            self.tabla_simbolos.column(
                identificador,
                width=ancho,
                minwidth=ancho,
                anchor=anclaje,
                stretch=identificador in {"lexema", "tipo"},
            )
        self._configurar_etiquetas_tokens(self.tabla_simbolos)
        self.tabla_simbolos.grid(row=0, column=0, sticky="nsew")
        desplazamiento = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=self.tabla_simbolos.yview,
            style="Genesis.Vertical.TScrollbar",
        )
        desplazamiento.grid(row=0, column=1, sticky="ns")
        desplazamiento_horizontal = ttk.Scrollbar(
            contenedor,
            orient="horizontal",
            command=self.tabla_simbolos.xview,
            style="Genesis.Horizontal.TScrollbar",
        )
        desplazamiento_horizontal.grid(row=1, column=0, sticky="ew")
        self.tabla_simbolos.configure(
            yscrollcommand=desplazamiento.set,
            xscrollcommand=desplazamiento_horizontal.set,
        )

        consulta = tk.Frame(
            self.panel_simbolos, bg=self.COLOR["panel"],
            highlightbackground=self.COLOR["borde"], highlightthickness=1,
        )
        consulta.grid(row=3, column=0, sticky="ew")
        tk.Label(
            consulta,
            text="Ir al registro:",
            bg=self.COLOR["panel"],
            fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 9),
        ).pack(side="left", padx=(14, 0), pady=9)
        self.entrada_consulta = tk.Entry(
            consulta,
            width=6,
            bg=self.COLOR["editor"],
            fg=self.COLOR["texto"],
            insertbackground=self.COLOR["acento"],
            relief="flat",
            font=(self.fuente_interfaz, 9),
        )
        self.entrada_consulta.pack(side="left", padx=(10, 8), ipady=4)
        self.entrada_consulta.bind("<Return>", self._consultar_simbolo)
        self.boton_consultar = tk.Button(
            consulta,
            text="Consultar",
            command=self._consultar_simbolo,
            bg=self.COLOR["borde"],
            fg=self.COLOR["texto"],
            activebackground=self.COLOR["seleccion"],
            activeforeground=self.COLOR["acento_activo"],
            relief="flat",
            bd=0,
            padx=11,
            pady=4,
            cursor="hand2",
            font=(self.fuente_interfaz, 9),
        )
        self.boton_consultar.pack(side="left", padx=(0, 10))

    def _configurar_etiquetas_tokens(self, tabla: ttk.Treeview) -> None:
        tabla.tag_configure(
            "reservada", foreground=self.COLOR["texto"], background="#1B2730"
        )
        tabla.tag_configure("identificador", foreground=self.COLOR["texto"])
        tabla.tag_configure(
            "numero", foreground=self.COLOR["azul"], background="#14272A"
        )
        tabla.tag_configure("error", foreground=self.COLOR["error"])

    @staticmethod
    def _etiqueta_token(clasificacion: str) -> str:
        if clasificacion == "PALABRA_RESERVADA":
            return "reservada"
        if clasificacion == "IDENTIFICADOR":
            return "identificador"
        if clasificacion in {"ENTERO", "DECIMAL"}:
            return "numero"
        if clasificacion in {
            "IDENTIFICADOR_INVALIDO", "NUMERO_INVALIDO", "TOKEN_DESCONOCIDO"
        }:
            return "error"
        return ""

    def _crear_resultados(self) -> None:
        self.panel_resultados = tk.Frame(
            self.divisor_vertical,
            bg=self.COLOR["panel"],
            highlightbackground=self.COLOR["borde"],
            highlightthickness=1,
        )
        self.panel_resultados.grid_rowconfigure(2, weight=1)
        self.panel_resultados.grid_columnconfigure(0, weight=1)
        tk.Frame(self.panel_resultados, bg=self.COLOR["lila"], height=2).grid(
            row=0, column=0, sticky="ew"
        )

        encabezado = tk.Frame(self.panel_resultados, bg=self.COLOR["margen"], height=46)
        encabezado.grid(row=1, column=0, sticky="ew")
        encabezado.grid_propagate(False)
        encabezado.columnconfigure(1, weight=1)
        barra_pestanas = tk.Frame(encabezado, bg=self.COLOR["margen"])
        barra_pestanas.grid(row=0, column=0, sticky="w", padx=(2, 0))
        self.botones_resultados = {}
        self.rayas_resultados = {}
        for clave, texto in (
            ("tokens", "TOKENS"),
            ("errores", "ERRORES"),
        ):
            contenedor = tk.Frame(barra_pestanas, bg=self.COLOR["margen"])
            contenedor.pack(side="left", fill="y")
            boton = tk.Button(
                contenedor, text=texto,
                command=lambda nombre=clave: self._seleccionar_resultado(nombre),
                bg=self.COLOR["margen"], fg=self.COLOR["secundario"],
                activebackground=self.COLOR["panel"],
                activeforeground=self.COLOR["texto"],
                relief="flat", bd=0, highlightthickness=0,
                padx=18, pady=11, cursor="hand2",
                font=(self.fuente_interfaz, 9, "bold"),
            )
            boton.pack(fill="x")
            raya = tk.Frame(contenedor, bg=self.COLOR["margen"], height=2)
            raya.pack(fill="x")
            self.botones_resultados[clave] = boton
            self.rayas_resultados[clave] = raya

        self.resumen_resultados = tk.Label(
            encabezado, text="Sin análisis",
            bg=self.COLOR["margen"], fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 9), anchor="e",
        )
        self.resumen_resultados.grid(row=0, column=1, sticky="e", padx=16)

        superficie = tk.Frame(self.panel_resultados, bg=self.COLOR["editor"])
        superficie.grid(row=2, column=0, sticky="nsew", padx=7, pady=(0, 7))
        superficie.grid_rowconfigure(0, weight=1)
        superficie.grid_columnconfigure(0, weight=1)
        self.vistas_resultados = {}
        for clave in ("tokens", "errores"):
            vista = tk.Frame(superficie, bg=self.COLOR["editor"])
            vista.grid(row=0, column=0, sticky="nsew")
            vista.grid_rowconfigure(0, weight=1)
            vista.grid_columnconfigure(0, weight=1)
            self.vistas_resultados[clave] = vista
        self._crear_vista_tokens()
        self._crear_vista_errores()
        self._seleccionar_resultado("tokens")

    def _crear_tabla_resultados(
        self, vista: tk.Frame, columnas: tuple[tuple[str, str, int], ...]
    ) -> ttk.Treeview:
        tabla = ttk.Treeview(
            vista, columns=tuple(columna[0] for columna in columnas),
            show="headings", selectmode="browse",
            style="Genesis.Results.Treeview",
        )
        for clave, titulo, ancho in columnas:
            centrado = clave in {"numero", "linea", "columna"}
            anclaje = "center" if centrado else "w"
            tabla.heading(clave, text=titulo, anchor=anclaje)
            tabla.column(
                clave, width=ancho, minwidth=ancho,
                anchor=anclaje, stretch=not centrado,
            )
        tabla.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(
            vista, orient="vertical", command=tabla.yview,
            style="Genesis.Vertical.TScrollbar",
        )
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(
            vista, orient="horizontal", command=tabla.xview,
            style="Genesis.Horizontal.TScrollbar",
        )
        horizontal.grid(row=1, column=0, sticky="ew")
        tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        return tabla

    def _crear_vista_tokens(self) -> None:
        self.tabla_tokens = self._crear_tabla_resultados(
            self.vistas_resultados["tokens"],
            (
                ("numero", "#", 70),
                ("lexema", "Lexema", 280),
                ("tipo", "Tipo de token", 330),
                ("linea", "Línea", 90),
                ("columna", "Columna", 100),
            ),
        )
        self._configurar_etiquetas_tokens(self.tabla_tokens)

    def _crear_vista_errores(self) -> None:
        vista = self.vistas_resultados["errores"]
        self.tabla_errores = self._crear_tabla_resultados(
            vista,
            (
                ("linea", "Línea", 90),
                ("columna", "Columna", 100),
                ("lexema", "Lexema rechazado", 220),
                ("descripcion", "Descripción del error", 520),
            ),
        )
        self.tabla_errores.tag_configure("error", foreground=self.COLOR["error"])
        self.tabla_errores.tag_configure("sistema", foreground=self.COLOR["dorado"])
        self.aviso_errores = tk.Label(
            vista, text="Ejecuta Compilar para ver errores léxicos.",
            bg=self.COLOR["editor"], fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 10),
        )
        self.aviso_errores.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.aviso_errores.lift()

    def _seleccionar_resultado(self, nombre: str) -> None:
        self.pestana_activa = nombre
        self.vistas_resultados[nombre].tkraise()
        for clave, boton in self.botones_resultados.items():
            activo = clave == nombre
            boton.configure(
                bg=self.COLOR["panel"] if activo else self.COLOR["margen"],
                fg=self.COLOR["texto"] if activo else self.COLOR["secundario"],
            )
            self.rayas_resultados[clave].configure(
                bg=self.COLOR["lila"] if activo else self.COLOR["margen"]
            )

    def _crear_barra_estado(self) -> None:
        barra = tk.Frame(
            self, bg=self.COLOR["panel"], height=34,
            highlightbackground=self.COLOR["borde"], highlightthickness=1,
        )
        barra.grid(row=3, column=0, sticky="ew")
        barra.grid_propagate(False)
        barra.columnconfigure(1, weight=1)
        self.estado = tk.Label(
            barra,
            text="●  Listo para analizar",
            bg=self.COLOR["panel"],
            fg=self.COLOR["exito"],
            font=(self.fuente_interfaz, 9, "bold"),
        )
        self.estado.grid(row=0, column=0, padx=(16, 20), pady=7)

        self.cursor_estado = tk.Label(
            barra,
            bg=self.COLOR["panel"],
            fg=self.COLOR["secundario"],
            font=(self.fuente_interfaz, 9),
        )
        self.cursor_estado.grid(row=0, column=2, padx=(8, 16))

    def _configurar_atajos(self) -> None:
        self.bind_all("<Control-n>", lambda evento: self._ejecutar_atajo(self.nuevo))
        self.bind_all("<Control-o>", lambda evento: self._ejecutar_atajo(self.abrir))
        self.bind_all("<Control-s>", lambda evento: self._ejecutar_atajo(self.guardar))
        self.bind_all("<F5>", lambda evento: self._ejecutar_atajo(self.compilar))

    def _ejecutar_atajo(self, accion) -> str:
        if self.menu_archivo_abierto:
            self._cerrar_menu_archivo()
        accion()
        return "break"

    def _programar_reparto_horizontal(self, evento=None) -> None:
        if self._reparto_automatico and not self._ajuste_horizontal_pendiente:
            self._ajuste_horizontal_pendiente = True
            self.after_idle(self._aplicar_reparto_horizontal)

    def _aplicar_reparto_horizontal(self) -> None:
        self._ajuste_horizontal_pendiente = False
        if self._reparto_automatico:
            ancho = self.divisor_horizontal.winfo_width()
            if ancho > 0:
                self.divisor_horizontal.sash_place(0, round(ancho * 0.60), 0)

    def _desactivar_reparto_automatico(self, evento) -> None:
        self._reparto_automatico = False

    def _ajustar_paneles(self) -> None:
        self.update_idletasks()
        alto = self.divisor_vertical.winfo_height()
        self._aplicar_reparto_horizontal()
        if alto > 440:
            altura_resultados = max(225, min(305, round(alto * 0.44)))
            self.divisor_vertical.sash_place(0, 0, alto - altura_resultados)
        self._programar_actualizacion_editor()

    def _sincronizar_desplazamiento(
        self, barra: ttk.Scrollbar, primero: str, ultimo: str
    ) -> None:
        barra.set(primero, ultimo)
        self._programar_actualizacion_editor()

    def _desplazar_editor(self, *argumentos: str) -> None:
        self.editor.yview(*argumentos)
        self._programar_actualizacion_editor()

    def _programar_actualizacion_editor(self, evento=None) -> None:
        if not self._actualizacion_editor_pendiente:
            self._actualizacion_editor_pendiente = True
            self.after_idle(self._actualizar_editor)

    def _actualizar_editor(self) -> None:
        self._actualizacion_editor_pendiente = False
        self._actualizar_cursor()
        self._actualizar_numeros_linea()

    def _actualizar_numeros_linea(self) -> None:
        self.numeros_linea.delete("all")
        indice = self.editor.index("@0,0")
        limite = self.editor.winfo_height()
        while True:
            posicion = self.editor.dlineinfo(indice)
            if posicion is None or posicion[1] >= limite:
                break
            numero = indice.split(".")[0]
            self.numeros_linea.create_text(
                45,
                posicion[1] + posicion[3] / 2,
                text=numero,
                anchor="e",
                fill=self.COLOR["secundario"],
                font=self.fuente_editor,
            )
            siguiente = self.editor.index(f"{indice} +1line")
            if siguiente == indice:
                break
            indice = siguiente

    def _actualizar_cursor(self) -> None:
        linea, columna = self.editor.index("insert").split(".")
        self.cursor_estado.configure(
            text=f"Línea {linea}  ·  Columna {int(columna) + 1}"
        )

    def _al_modificar_editor(self, evento=None) -> None:
        if not self.editor.edit_modified():
            return
        self.editor.edit_modified(False)
        self.hay_cambios = True
        self.estado.configure(text="●  Cambios sin analizar", fg=self.COLOR["dorado"])
        self._actualizar_archivo()
        self._programar_actualizacion_editor()
        self._programar_resaltado()

    def _programar_resaltado(self) -> None:
        if self._trabajo_resaltado is not None:
            self.after_cancel(self._trabajo_resaltado)
        self._version_resaltado += 1
        version = self._version_resaltado
        self._trabajo_resaltado = self.after(
            60, lambda: self._iniciar_resaltado(version)
        )

    def _iniciar_resaltado(self, version: int) -> None:
        if version != self._version_resaltado:
            return
        self._trabajo_resaltado = None
        for categoria, _ in self.CATEGORIAS_RESALTADO:
            self.editor.tag_remove(f"reservada_{categoria}", "1.0", "end")
        self._resaltar_bloque(1, version)

    def _resaltar_bloque(self, primera_linea: int, version: int) -> None:
        if version != self._version_resaltado:
            return
        ultima_linea = int(self.editor.index("end-1c").split(".")[0])
        siguiente_linea = min(primera_linea + 120, ultima_linea + 1)
        for numero in range(primera_linea, siguiente_linea):
            contenido = self.editor.get(f"{numero}.0", f"{numero}.end")
            for inicio, fin, categoria in recorrer_palabras_reservadas(contenido):
                self.editor.tag_add(
                    f"reservada_{categoria}",
                    f"{numero}.{inicio}",
                    f"{numero}.{fin}",
                )
        if siguiente_linea <= ultima_linea:
            self._trabajo_resaltado = self.after(
                1, lambda: self._resaltar_bloque(siguiente_linea, version)
            )
        else:
            self._trabajo_resaltado = None

    def _insertar_tabulacion(self, evento) -> str:
        self.editor.insert("insert", "\t")
        return "break"

    def _insertar_nueva_linea(self, evento) -> str:
        inicio = self.editor.index("insert linestart")
        contenido = self.editor.get(inicio, "insert")
        sangria = contenido[: len(contenido) - len(contenido.lstrip(" \t"))]
        self.editor.insert("insert", "\n" + sangria)
        return "break"

    def _actualizar_archivo(self) -> None:
        nombre = self.ruta_actual.name if self.ruta_actual else "Sin título.gen"
        self.etiqueta_archivo.configure(text=self._abreviar_nombre(nombre, 32))
        self.etiqueta_cambios.configure(text="●" if self.hay_cambios else "")
        self.title(self.TITULO)

    @staticmethod
    def _abreviar_nombre(nombre: str, limite: int) -> str:
        if len(nombre) <= limite:
            return nombre
        return f"{nombre[:limite - 13]}…{nombre[-12:]}"

    def _confirmar_descartar(self) -> bool:
        if not self.hay_cambios:
            return True
        nombre = self.ruta_actual.name if self.ruta_actual else "Sin título.gen"
        return messagebox.askyesno(
            "Cambios sin guardar",
            f"Hay cambios sin guardar en {nombre}.\n¿Deseas descartarlos?",
            parent=self,
            icon="warning",
        )

    def _reemplazar_editor(self, contenido: str) -> None:
        self.editor.delete("1.0", "end")
        if contenido:
            self.editor.insert("1.0", contenido)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.editor.mark_set("insert", "1.0")
        self.editor.yview_moveto(0)
        self.editor.xview_moveto(0)
        self.hay_cambios = False
        self.estado.configure(text="●  Listo para analizar", fg=self.COLOR["exito"])
        self._actualizar_archivo()
        self._programar_actualizacion_editor()
        self._programar_resaltado()
        self.editor.focus_set()

    def nuevo(self) -> None:
        if not self._confirmar_descartar():
            return
        self.ruta_actual = None
        self._reemplazar_editor("")

    def abrir(self) -> None:
        if not self._confirmar_descartar():
            return
        nombre = filedialog.askopenfilename(
            parent=self,
            title="Abrir programa GENESIS",
            filetypes=[
                ("Programas GENESIS y texto", "*.gen *.txt"),
                ("Programas GENESIS", "*.gen"),
                ("Archivos de texto", "*.txt"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not nombre:
            return
        ruta = Path(nombre)
        try:
            contenido = ruta.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            self._registrar_error_sistema(f"No se pudo abrir el archivo: {error}")
            messagebox.showerror(
                "No se pudo abrir el archivo", str(error), parent=self
            )
            return
        self.ruta_actual = ruta
        self._reemplazar_editor(contenido)

    def guardar(self) -> bool:
        if self.ruta_actual is None:
            return self.guardar_como()
        try:
            self.ruta_actual.write_text(
                self.editor.get("1.0", "end-1c"), encoding="utf-8"
            )
        except (OSError, UnicodeError) as error:
            self._registrar_error_sistema(f"No se pudo guardar el archivo: {error}")
            messagebox.showerror(
                "No se pudo guardar el archivo", str(error), parent=self
            )
            return False
        self.hay_cambios = False
        self.editor.edit_modified(False)
        self._actualizar_archivo()
        return True

    def guardar_como(self) -> bool:
        nombre = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar programa GENESIS",
            defaultextension=".gen",
            initialfile=self.ruta_actual.name if self.ruta_actual else "Sin título.gen",
            filetypes=[
                ("Programas GENESIS", "*.gen"),
                ("Archivos de texto", "*.txt"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not nombre:
            return False
        ruta_anterior = self.ruta_actual
        self.ruta_actual = Path(nombre)
        if self.guardar():
            return True
        self.ruta_actual = ruta_anterior
        self._actualizar_archivo()
        return False

    def salir(self) -> None:
        if self._confirmar_descartar():
            self.destroy()

    def _actualizar_aviso_errores(self) -> None:
        if self.tabla_errores.get_children():
            self.aviso_errores.grid_remove()
            return
        mensaje = (
            "No se detectaron errores léxicos" if self.analisis_realizado
            else "Ejecuta Compilar para ver errores léxicos."
        )
        self.aviso_errores.configure(text=mensaje)
        self.aviso_errores.grid()
        self.aviso_errores.lift()

    def _registrar_error_sistema(
        self, descripcion: str, linea: int | None = None,
        columna: int | None = None, lexema: str = "",
    ) -> None:
        self.tabla_errores.insert(
            "", "end",
            values=(
                linea if linea is not None else "—",
                columna if columna is not None else "—",
                lexema,
                f"ERROR DEL SISTEMA · {descripcion}",
            ),
            tags=("sistema",),
        )
        self._actualizar_aviso_errores()
        self._seleccionar_resultado("errores")
        self.estado.configure(text="●  Error del sistema", fg=self.COLOR["error"])

    def _reconstruir_y_mostrar_tabla(
        self, tokens: list[Token]
    ) -> tuple[int | None, int]:
        try:
            omitidos = reconstruir_tabla(tokens)
            registros = leer_registros()
        except (OSError, UnicodeError, ErrorTablaSimbolos) as error:
            for fila in self.tabla_simbolos.get_children():
                self.tabla_simbolos.delete(fila)
            self.etiqueta_total_simbolos.configure(text="No disponible")
            self._registrar_error_sistema(
                f"No se pudo actualizar la Tabla de símbolos: {error}"
            )
            return None, 1

        for fila in self.tabla_simbolos.get_children():
            self.tabla_simbolos.delete(fila)
        for registro in registros:
            self.tabla_simbolos.insert(
                "", "end", iid=str(registro.numero),
                values=(
                    registro.numero,
                    registro.lexema,
                    registro.tipo,
                    registro.linea if registro.linea else "-",
                    registro.columna if registro.columna else "-",
                ),
                tags=(self._etiqueta_token(registro.tipo),),
            )
        self.etiqueta_total_simbolos.configure(text=f"{len(registros)} registros")
        for omitido in omitidos:
            self._registrar_error_sistema(
                f"No se pudo almacenar el símbolo. {omitido.motivo}",
                omitido.linea, omitido.columna, omitido.lexema,
            )
        return len(registros), len(omitidos)

    def _actualizar_resumen_analisis(
        self, total_tokens: int, total_simbolos: int | None,
        errores_lexicos: int, errores_tabla: int,
    ) -> None:
        simbolos = str(total_simbolos) if total_simbolos is not None else "—"
        self.resumen_resultados.configure(
            text=f"{total_tokens} tokens  ·  {simbolos} símbolos  ·  "
            f"{errores_lexicos} errores"
        )
        if errores_lexicos or errores_tabla:
            self.estado.configure(text="●  Revisar errores", fg=self.COLOR["error"])
        elif total_tokens == 0:
            self.estado.configure(
                text="●  Código vacío · análisis completado",
                fg=self.COLOR["exito"],
            )
        else:
            self.estado.configure(text="●  Análisis completado", fg=self.COLOR["exito"])

    def _actualizar_vistas_resultados(
        self, errores_detectados: list[tuple[Token, str]]
    ) -> None:
        for fila in self.tabla_tokens.get_children():
            self.tabla_tokens.delete(fila)
        for numero, token in enumerate(self.tokens, start=1):
            self.tabla_tokens.insert(
                "", "end", iid=str(numero),
                values=(
                    numero, token.lexema, token.clasificacion,
                    token.linea, token.columna,
                ),
                tags=(self._etiqueta_token(token.clasificacion),),
            )

        for fila in self.tabla_errores.get_children():
            self.tabla_errores.delete(fila)
        for token, descripcion in errores_detectados:
            self.tabla_errores.insert(
                "", "end",
                values=(token.linea, token.columna, token.lexema, descripcion),
                tags=("error",),
            )
        self._actualizar_aviso_errores()

    def _consultar_simbolo(self, evento=None) -> None:
        texto = self.entrada_consulta.get().strip()
        if not texto or any(not "0" <= caracter <= "9" for caracter in texto):
            self.estado.configure(
                text="●  Introduce un número de registro válido",
                fg=self.COLOR["dorado"],
            )
            return
        try:
            registro = consultar_registro(int(texto))
        except (ValueError, IndexError) as error:
            self.estado.configure(text=f"●  {error}", fg=self.COLOR["dorado"])
            return
        except (OSError, ErrorTablaSimbolos) as error:
            self._registrar_error_sistema(
                f"No se pudo consultar el registro: {error}"
            )
            return

        self.tabla_simbolos.selection_set(str(registro.numero))
        self.tabla_simbolos.focus(str(registro.numero))
        self.tabla_simbolos.see(str(registro.numero))
        linea = registro.linea if registro.linea else "-"
        columna = registro.columna if registro.columna else "-"
        self.estado.configure(
            text=f"●  Registro {registro.numero}: {registro.lexema} · "
            f"{registro.tipo} · L{linea}:C{columna}",
            fg=self.COLOR["acento"],
        )

    def compilar(self) -> None:
        self._ejecutar_compilacion()

    def _ejecutar_compilacion(self) -> None:
        if self.editor.edit_modified():
            self._al_modificar_editor()
        self.tokens = analizar_codigo(self.editor.get("1.0", "end-1c"))
        errores_detectados: list[tuple[Token, str]] = []
        for token in self.tokens:
            if token.clasificacion == "IDENTIFICADOR_INVALIDO":
                errores_detectados.append((
                    token, "Identificador inválido. Debe comenzar con una letra."
                ))
            elif token.clasificacion == "NUMERO_INVALIDO":
                errores_detectados.append((
                    token, f"Número inválido. {motivo_numero_invalido(token.lexema)}"
                ))
            elif token.clasificacion == "TOKEN_DESCONOCIDO":
                errores_detectados.append((token, "Símbolo desconocido."))

        self.analisis_realizado = True
        self._actualizar_vistas_resultados(errores_detectados)
        total_simbolos, errores_tabla = self._reconstruir_y_mostrar_tabla(self.tokens)
        self._actualizar_resumen_analisis(
            len(self.tokens), total_simbolos, len(errores_detectados), errores_tabla
        )
        if errores_detectados or errores_tabla:
            self._seleccionar_resultado("errores")
        else:
            self._seleccionar_resultado("tokens")
