# =========================================================
# Universidad Americana (UAM)
# Facultad de Ingeniería y Arquitectura (FIA)
# Carrera: Ingeniería de Sistemas
# Asignatura: Álgebra Lineal
# Grupo 4 - Integrantes:
# Julio Javier Sevilla Gallegos
# Docente: Carlos Iván Argüello Martínez
# =========================================================
# CHOCO LAB - CALCULADORA DE ÁLGEBRA LINEAL (versión integrada)
# =========================================================
# Interfaz gráfica para resolver sistemas de ecuaciones
# lineales mediante eliminación por filas.
# =========================================================

import os
import tkinter as tk
from tkinter import ttk
from fractions import Fraction

from sistemas_eliminacion import (
    TOLERANCIA,
    convertir_ecuacion_a_fila,
    convertir_sistema_ecuaciones,
    copiar_matriz,
    es_elemento_diagonal,
    resolver_sistema,
    verificar_solucion
)

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

COLOR_FONDO = "#F7F3EE"
COLOR_CHOCOLATE = "#4A2C1A"
COLOR_CHOCOLATE_MEDIO = "#6B4423"
COLOR_BEIGE = "#EADBC8"
COLOR_BLANCO = "#FFFFFF"
COLOR_RESALTADO = "#F3D7A6"
COLOR_ERROR = "#A33A2B"
COLOR_ERROR_SUAVE = "#FCE8E6"
COLOR_EXITO = "#2E6B3B"

MAX_DIMENSION = 15

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RECURSOS = os.path.join(BASE_DIR, "recursos")


# =========================================================
# APLICACIÓN
# =========================================================

class ChocoLabApp:

    def __init__(self, ventana):

        self.ventana = ventana

        self.numero_ecuaciones = 3
        self.numero_variables = 3

        self.matriz_original = None
        self.resultado_actual = None
        self.nombres_variables = ["x1", "x2", "x3"]
        self.modo_numeros = tk.StringVar(value="Decimal")

        self.entradas_matriz = []
        self.entradas_ecuaciones = []
        self.etiquetas_filas = []
        self.etiquetas_columnas = []

        self.modo_entrada = "ecuacion"

        self.fila_seleccionada = None
        self.columna_seleccionada = None

        # El módulo se abre ocupando toda la pantalla, igual que el menú.
        # F11 alterna este modo y Escape permite volver a una ventana normal.
        self.pantalla_completa = True

        self.imagenes = []

        # Monitor de memoria RAM del propio proceso.
        # Se mantiene sin librerías externas para conservar el enfoque del curso.
        self.ram_base_bytes = None
        self.ram_after_id = None
        self.ram_metodo = ""

        # Respaldo multiplataforma: si Windows no permite consultar el
        # Working Set por su API, tracemalloc evita que el indicador quede N/D.
        # Este respaldo mide memoria administrada por Python y se rotula como
        # aproximada; normalmente en Windows se usará el Working Set real.
        self.tracemalloc_activo = False
        try:
            import tracemalloc
            tracemalloc.start()
            self.tracemalloc_activo = True
        except (ImportError, RuntimeError):
            pass

        self.configurar_ventana()
        self.configurar_estilos()
        self.crear_interfaz()
        self.crear_entrada_actual()
        self.iniciar_monitor_ram()

    # =====================================================
    # VENTANA
    # =====================================================

    def configurar_ventana(self):

        self.ventana.title(
            "Choco Lab - Sistemas por eliminación de filas"
        )

        self.ventana.geometry(
            "1200x760"
        )

        self.ventana.minsize(
            900,
            620
        )

        self.ventana.resizable(
            True,
            True
        )

        self.ventana.configure(
            bg=COLOR_FONDO
        )

        try:
            self.ventana.attributes(
                "-fullscreen",
                True
            )
        except tk.TclError:
            # Respaldo para gestores de ventanas que no implementan
            # el atributo fullscreen de Tk.
            try:
                self.ventana.state("zoomed")
            except tk.TclError:
                pass

        self.ventana.bind(
            "<F11>",
            lambda event:
            self.alternar_pantalla_completa()
        )

        self.ventana.bind(
            "<Escape>",
            lambda event:
            self.salir_pantalla_completa()
        )

        self.ventana.bind(
            "<Control-r>",
            lambda event:
            self.resolver()
        )

        self.ventana.bind(
            "<Control-n>",
            lambda event:
            self.limpiar_matriz()
        )

    def configurar_estilos(self):

        estilo = ttk.Style()

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "TFrame",
            background=COLOR_FONDO
        )

        estilo.configure(
            "TLabel",
            background=COLOR_FONDO,
            foreground=COLOR_CHOCOLATE
        )

        estilo.configure(
            "TLabelframe",
            background=COLOR_FONDO
        )

        estilo.configure(
            "TLabelframe.Label",
            background=COLOR_FONDO,
            foreground=COLOR_CHOCOLATE,
            font=("Arial", 11, "bold")
        )

        estilo.configure(
            "TRadiobutton",
            background=COLOR_FONDO,
            foreground=COLOR_CHOCOLATE
        )

        estilo.configure(
            "TButton",
            font=("Arial", 10)
        )

    # =====================================================
    # LOGOS
    # =====================================================

    def cargar_logo(self, nombre_archivo, ancho_objetivo=120):

        ruta = os.path.join(
            RUTA_RECURSOS,
            nombre_archivo
        )

        if not os.path.exists(ruta):
            return None

        try:
            imagen_original = tk.PhotoImage(
                file=ruta
            )

            ancho_original = imagen_original.width()

            if ancho_original > ancho_objetivo:

                factor = max(
                    1,
                    round(ancho_original / ancho_objetivo)
                )

                imagen = imagen_original.subsample(
                    factor,
                    factor
                )

            else:
                imagen = imagen_original

            self.imagenes.append(
                imagen_original
            )

            self.imagenes.append(
                imagen
            )

            return imagen

        except tk.TclError:
            return None

    # =====================================================
    # INTERFAZ GENERAL
    # =====================================================

    def crear_interfaz(self):

        self.ventana.rowconfigure(
            2,
            weight=1
        )

        self.ventana.columnconfigure(
            0,
            weight=1
        )

        self.crear_encabezado()
        self.crear_panel_configuracion()
        self.crear_zona_principal()
        self.crear_barra_estado()
        self.crear_pie_creditos()

    def crear_encabezado(self):

        encabezado = tk.Frame(
            self.ventana,
            bg=COLOR_FONDO,
            height=82
        )

        encabezado.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=24,
            pady=(6, 3)
        )

        encabezado.grid_propagate(
            False
        )

        encabezado.columnconfigure(
            1,
            weight=1
        )

        # -------------------------------------------------
        # LOGO CHOCO LAB
        # -------------------------------------------------

        frame_choco = tk.Frame(
            encabezado,
            bg=COLOR_FONDO
        )

        frame_choco.grid(
            row=0,
            column=0,
            sticky="w"
        )

        logo_choco = self.cargar_logo(
            "chocolab.png",
            145
        )

        if logo_choco is not None:

            tk.Label(
                frame_choco,
                image=logo_choco,
                bg=COLOR_FONDO
            ).pack(
                anchor="w"
            )

        tk.Label(
            frame_choco,
            text="Sistemas por eliminación de filas",
            font=("Arial", 9),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).pack(
            anchor="w",
            pady=(1, 0)
        )

        # -------------------------------------------------
        # LOGO FIA
        # -------------------------------------------------

        logo_fia = self.cargar_logo(
            "logofia.png",
            145
        )

        if logo_fia is not None:

            tk.Label(
                encabezado,
                image=logo_fia,
                bg=COLOR_FONDO
            ).grid(
                row=0,
                column=2,
                sticky="e"
            )

    def crear_panel_configuracion(self):

        panel = ttk.LabelFrame(
            self.ventana,
            text="1. Configura el sistema"
        )

        panel.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(2, 6)
        )

        panel.columnconfigure(
            0,
            weight=1
        )

        fila = tk.Frame(
            panel,
            bg=COLOR_FONDO
        )

        fila.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=10,
            pady=7
        )

        tk.Label(
            fila,
            text="Ecuaciones:",
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).pack(
            side="left"
        )

        self.variable_ecuaciones = tk.StringVar(
            value="3"
        )

        self.spin_ecuaciones = tk.Spinbox(
            fila,
            from_=1,
            to=MAX_DIMENSION,
            width=6,
            justify="center",
            textvariable=self.variable_ecuaciones
        )

        self.spin_ecuaciones.pack(
            side="left",
            padx=(5, 12)
        )

        tk.Label(
            fila,
            text="Variables:",
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).pack(
            side="left"
        )

        self.variable_variables = tk.StringVar(
            value="3"
        )

        self.spin_variables = tk.Spinbox(
            fila,
            from_=1,
            to=MAX_DIMENSION,
            width=6,
            justify="center",
            textvariable=self.variable_variables
        )

        self.spin_variables.pack(
            side="left",
            padx=(5, 10)
        )

        ttk.Button(
            fila,
            text="Crear / cambiar matriz",
            command=self.cambiar_dimensiones
        ).pack(
            side="left",
            padx=(0, 18)
        )

        tk.Label(
            fila,
            text="Coordenadas:",
            font=("Arial", 9, "bold"),
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).pack(
            side="left",
            padx=(0, 5)
        )

        self.modo_indices = tk.StringVar(
            value="matematico"
        )

        ttk.Radiobutton(
            fila,
            text="Matemático (1,1)",
            variable=self.modo_indices,
            value="matematico",
            command=self.actualizar_modo
        ).pack(
            side="left",
            padx=3
        )

        ttk.Radiobutton(
            fila,
            text="Programador (0,0)",
            variable=self.modo_indices,
            value="programador",
            command=self.actualizar_modo
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            fila,
            text="⛶ Pantalla completa",
            command=self.alternar_pantalla_completa
        ).pack(
            side="right"
        )

    def crear_zona_principal(self):

        self.panel_principal = tk.PanedWindow(
            self.ventana,
            orient="horizontal",
            sashwidth=7,
            sashrelief="raised",
            opaqueresize=True,
            bg=COLOR_BEIGE
        )

        self.panel_principal.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=24,
            pady=(0, 8)
        )

        # =================================================
        # IZQUIERDA: INCISO 2 + MATRIZ
        # =================================================

        frame_izquierdo = tk.Frame(
            self.panel_principal,
            bg=COLOR_FONDO
        )

        frame_izquierdo.rowconfigure(
            3,
            weight=1
        )

        frame_izquierdo.columnconfigure(
            0,
            weight=1
        )

        self.panel_principal.add(
            frame_izquierdo,
            minsize=380
        )

        # -------------------------------------------------
        # 2. INGRESA LOS DATOS
        # -------------------------------------------------

        frame_ayuda = ttk.LabelFrame(
            frame_izquierdo,
            text="2. Ingresa los datos"
        )

        frame_ayuda.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 6)
        )

        self.label_ayuda = tk.Label(
            frame_ayuda,
            text=(
                "Cada fila representa una ecuación. "
                "Ingresa los coeficientes de x₁, x₂, ... "
                "y en la columna b escribe el término independiente."
            ),
            font=("Arial", 9),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO,
            justify="left",
            anchor="w",
            wraplength=540
        )

        self.label_ayuda.pack(
            fill="x",
            padx=12,
            pady=7
        )

        # -------------------------------------------------
        # INFORMACIÓN DE LA CELDA
        # FUERA DEL CUADRO MOVIBLE DE LA MATRIZ
        # -------------------------------------------------

        self.frame_info = ttk.LabelFrame(
            frame_izquierdo,
            text="Información de la celda"
        )

        self.frame_info.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 6)
        )

        self.texto_celda = tk.StringVar(
            value=(
                "Selecciona una celda para ver su coordenada, "
                "función y si pertenece a la diagonal principal."
            )
        )

        self.label_celda = tk.Label(
            self.frame_info,
            textvariable=self.texto_celda,
            font=("Arial", 9),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO,
            justify="left",
            anchor="w",
            wraplength=540
        )

        self.label_celda.pack(
            fill="x",
            padx=12,
            pady=7
        )

        # -------------------------------------------------
        # BOTONES
        # TAMBIÉN FUERA DEL CUADRO MOVIBLE DE LA MATRIZ
        # -------------------------------------------------

        frame_botones = tk.Frame(
            frame_izquierdo,
            bg=COLOR_FONDO
        )

        frame_botones.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 7)
        )

        self.boton_modo_entrada = ttk.Button(
            frame_botones,
            text="Matriz/Ecuación",
            width=17,
            command=self.alternar_modo_entrada
        )

        self.boton_modo_entrada.pack(
            side="left",
            padx=(0, 5)
        )

        self.boton_resolver = tk.Button(
            frame_botones,
            text="Resolver sistema",
            font=("Arial", 9, "bold"),
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            cursor="hand2",
            width=17,
            command=self.resolver
        )

        self.boton_resolver.pack(
            side="left",
            padx=(0, 5),
            ipady=1
        )

        ttk.Button(
            frame_botones,
            text="Limpiar valores",
            width=14,
            command=self.limpiar_matriz
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            frame_botones,
            text="Restaurar tamaño",
            width=15,
            command=self.restaurar_tamano
        ).pack(
            side="left",
            padx=5
        )

        # -------------------------------------------------
        # MATRIZ AUMENTADA
        # ESTE ES EL ÚNICO CUADRO MOVIBLE DEL LADO IZQUIERDO
        # -------------------------------------------------

        self.frame_datos = ttk.LabelFrame(
            frame_izquierdo,
            text="Matriz aumentada"
        )

        self.frame_datos.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        self.frame_datos.rowconfigure(
            0,
            weight=1
        )

        self.frame_datos.columnconfigure(
            0,
            weight=1
        )

        self.canvas_matriz = tk.Canvas(
            self.frame_datos,
            bg=COLOR_FONDO,
            highlightthickness=0,
            confine=True
        )

        self.scroll_y_matriz = ttk.Scrollbar(
            self.frame_datos,
            orient="vertical",
            command=self.canvas_matriz.yview
        )

        self.scroll_x_matriz = ttk.Scrollbar(
            self.frame_datos,
            orient="horizontal",
            command=self.canvas_matriz.xview
        )

        self.canvas_matriz.configure(
            yscrollcommand=self.scroll_y_matriz.set,
            xscrollcommand=self.scroll_x_matriz.set
        )

        self.canvas_matriz.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.scroll_y_matriz.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.scroll_y_matriz.configure(
            takefocus=True
        )

        self.scroll_y_matriz.bind(
            "<ButtonRelease-1>",
            self.enfocar_barra,
            add="+"
        )

        self.scroll_y_matriz.bind(
            "<Up>",
            lambda event:
            self.mover_barra_vertical(-1)
        )

        self.scroll_y_matriz.bind(
            "<Down>",
            lambda event:
            self.mover_barra_vertical(1)
        )        

        self.scroll_x_matriz.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.scroll_x_matriz.configure(
            takefocus=True
        )

        self.scroll_x_matriz.bind(
            "<ButtonRelease-1>",
            self.enfocar_barra,
            add="+"
        )

        self.scroll_x_matriz.bind(
            "<Left>",
            lambda event:
            self.mover_barra_horizontal(-1)
        )

        self.scroll_x_matriz.bind(
            "<Right>",
            lambda event:
            self.mover_barra_horizontal(1)
        )

        self.frame_cuadricula = tk.Frame(
            self.canvas_matriz,
            bg=COLOR_FONDO
        )

        self.id_ventana_canvas = (
            self.canvas_matriz.create_window(
                0,
                0,
                window=self.frame_cuadricula,
                anchor="nw"
            )
        )

        self.frame_cuadricula.bind(
            "<Configure>",
            self.actualizar_region_scroll
        )

        self.canvas_matriz.bind(
            "<Configure>",
            self.actualizar_region_scroll
        )

        # -------------------------------------------------
        # RUEDA DEL MOUSE EN LA MATRIZ
        # -------------------------------------------------

        self.ventana.bind_all(
            "<MouseWheel>",
            self.controlar_rueda_matriz,
            add="+"
        )

        # =================================================
        # DERECHA: INCISO 3 PROCEDIMIENTO
        # =================================================

        frame_derecho = tk.Frame(
            self.panel_principal,
            bg=COLOR_FONDO
        )

        frame_derecho.rowconfigure(
            1,
            weight=1
        )

        frame_derecho.columnconfigure(
            0,
            weight=1
        )

        self.panel_principal.add(
            frame_derecho,
            minsize=380
        )

        frame_encabezado_resultado = tk.Frame(
            frame_derecho,
            bg=COLOR_FONDO
        )
        frame_encabezado_resultado.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6)
        )

        tk.Label(
            frame_encabezado_resultado,
            text="3. Procedimiento, clasificación y verificación",
            font=("Arial", 11, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_FONDO,
            justify="left",
            anchor="w"
        ).pack(
            side="left"
        )

        # -------------------------------------------------
        # VISTA DEL PROCEDIMIENTO
        # Dos fases / Gauss / Gauss-Jordan
        # -------------------------------------------------

        self.modo_vista_procedimiento = tk.StringVar(
            value="Dos fases"
        )

        self.boton_vista_procedimiento = tk.Menubutton(
            frame_encabezado_resultado,
            text="Vista: Dos fases ▾",
            font=("Arial", 9),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_BEIGE,
            activeforeground=COLOR_CHOCOLATE,
            activebackground=COLOR_RESALTADO,
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=2
        )

        self.menu_vista_procedimiento = tk.Menu(
            self.boton_vista_procedimiento,
            tearoff=0
        )

        for opcion in (
            "Dos fases",
            "Gauss",
            "Gauss-Jordan"
        ):

            self.menu_vista_procedimiento.add_radiobutton(
                label=opcion,
                variable=self.modo_vista_procedimiento,
                value=opcion,
                command=self.actualizar_vista_procedimiento
            )

        self.boton_vista_procedimiento.config(
            menu=self.menu_vista_procedimiento
        )

        self.boton_vista_procedimiento.pack(
            side="left",
            padx=(8, 0),
            pady=0
        )

        self.boton_modo_numeros = tk.Button(
            frame_encabezado_resultado,
            text="Números: Decimal",
            font=("Arial", 9),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_BEIGE,
            activeforeground=COLOR_CHOCOLATE,
            activebackground=COLOR_RESALTADO,
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=2,
            command=self.alternar_modo_numeros
        )
        self.boton_modo_numeros.pack(
            side="left",
            padx=(6, 0)
        )

        frame_texto = tk.Frame(
            frame_derecho,
            bg=COLOR_FONDO
        )

        frame_texto.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        frame_texto.rowconfigure(
            0,
            weight=1
        )

        frame_texto.columnconfigure(
            0,
            weight=1
        )

        self.salida = tk.Text(
            frame_texto,
            wrap="none",
            font=("Consolas", 10),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            padx=12,
            pady=12
        )

        scroll_y = ttk.Scrollbar(
            frame_texto,
            orient="vertical",
            command=self.salida.yview
        )

        scroll_x = ttk.Scrollbar(
            frame_texto,
            orient="horizontal",
            command=self.salida.xview
        )

        self.salida.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.salida.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scroll_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scroll_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.salida.tag_configure(
            "titulo",
            font=("Consolas", 11, "bold"),
            foreground=COLOR_CHOCOLATE
        )

        self.salida.tag_configure(
            "exito",
            font=("Consolas", 10, "bold"),
            foreground=COLOR_EXITO
        )

        self.salida.tag_configure(
            "error",
            font=("Consolas", 10, "bold"),
            foreground=COLOR_ERROR
        )

        self.escribir_salida(
            "Escribe las ecuaciones del sistema y presiona "
            "«Resolver sistema».\n\n"
            "Atajos:\n"
            "  F11       Pantalla completa\n"
            "  Esc       Salir de pantalla completa\n"
            "  Ctrl + R  Resolver\n"
            "  Ctrl + N  Limpiar\n"
        )

        self.ventana.after(
            150,
            self.posicionar_divisor_inicial
        )

    def posicionar_divisor_inicial(self):

        self.ventana.update_idletasks()

        ancho = self.panel_principal.winfo_width()

        if ancho > 10:

            self.panel_principal.sash_place(
                0,
                ancho // 2,
                1
            )

    def crear_barra_estado(self):

        self.mensaje = tk.StringVar(
            value="Listo. Escribe las ecuaciones para comenzar."
        )

        self.label_estado = tk.Label(
            self.ventana,
            textvariable=self.mensaje,
            font=("Arial", 9, "italic"),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_BEIGE,
            anchor="w",
            padx=12,
            pady=5
        )

        self.label_estado.grid(
            row=3,
            column=0,
            sticky="ew"
        )

    def crear_pie_creditos(self):

        texto_creditos = (
            "© 2026 Grupo 4  •  Julio Javier Sevilla Gallegos  •  "
            "Álgebra Lineal (MTM0120)  •  "
            "Facultad de Ingeniería y Arquitectura (FIA)  •  "
            "Universidad Americana (UAM)"
        )

        # Barra común de Choco Lab: RAM a la izquierda, créditos al centro
        # y regreso al menú en la esquina derecha.
        self.frame_pie = tk.Frame(
            self.ventana,
            bg=COLOR_CHOCOLATE,
            height=46
        )

        self.frame_pie.grid(
            row=4,
            column=0,
            sticky="ew"
        )

        self.frame_pie.grid_propagate(False)
        self.frame_pie.columnconfigure(0, weight=1)
        self.frame_pie.columnconfigure(1, weight=3)
        self.frame_pie.columnconfigure(2, weight=1)

        self.texto_ram = tk.StringVar(
            value="RAM: calculando..."
        )

        self.label_ram = tk.Label(
            self.frame_pie,
            textvariable=self.texto_ram,
            font=("Consolas", 8, "bold"),
            fg=COLOR_BLANCO,
            bg=COLOR_CHOCOLATE,
            justify="left",
            anchor="w",
            padx=14,
            pady=4
        )

        self.label_ram.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.label_creditos = tk.Label(
            self.frame_pie,
            text=texto_creditos,
            font=("Arial", 8),
            fg=COLOR_BLANCO,
            bg=COLOR_CHOCOLATE,
            justify="center",
            anchor="center",
            wraplength=760,
            padx=12,
            pady=4
        )

        self.label_creditos.grid(
            row=0,
            column=1,
            sticky="ew"
        )

        self.boton_volver_menu = tk.Button(
            self.frame_pie,
            text="Volver al menú",
            command=self.volver_al_menu,
            font=("Arial", 9, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_RESALTADO,
            activeforeground=COLOR_CHOCOLATE,
            activebackground=COLOR_BEIGE,
            relief="flat",
            cursor="hand2",
            padx=13,
            pady=5
        )

        self.boton_volver_menu.grid(
            row=0,
            column=2,
            sticky="e",
            padx=14,
            pady=7
        )

        self.frame_pie.bind(
            "<Configure>",
            self.ajustar_pie_creditos
        )

    def ajustar_pie_creditos(self, event):
        """Ajusta el ancho de los créditos sin tapar el indicador de RAM."""

        ancho_laterales = 430

        try:
            ancho_laterales = max(
                400,
                self.label_ram.winfo_reqwidth()
                + self.boton_volver_menu.winfo_reqwidth()
                + 55
            )
        except tk.TclError:
            pass

        self.label_creditos.config(
            wraplength=max(
                300,
                event.width - ancho_laterales
            )
        )

    def volver_al_menu(self):
        """Cierra el módulo integrado o la ventana si se ejecutó solo."""

        if isinstance(self.ventana, tk.Toplevel):
            self.ventana.event_generate("<<CerrarModulo>>")
        else:
            self.ventana.destroy()

    def obtener_uso_ram_bytes(self):
        """
        Devuelve la memoria usada actualmente por este proceso en bytes.

        Prioridad:
        1. Windows: Working Set real mediante la API de Windows.
        2. Windows: ``tasklist`` como respaldo del Working Set.
        3. Linux: RSS desde /proc/self/statm.
        4. Unix/macOS: ru_maxrss.
        5. Último respaldo: memoria administrada por Python (tracemalloc).

        No requiere instalar psutil ni ninguna librería externa.
        """

        self.ram_metodo = ""

        # -------------------------------------------------
        # WINDOWS: WORKING SET REAL MEDIANTE API NATIVA
        # -------------------------------------------------
        if os.name == "nt":

            try:
                import ctypes
                from ctypes import wintypes

                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ("cb", wintypes.DWORD),
                        ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]

                kernel32 = ctypes.WinDLL(
                    "kernel32",
                    use_last_error=True
                )

                kernel32.GetCurrentProcess.argtypes = []
                kernel32.GetCurrentProcess.restype = wintypes.HANDLE
                proceso = kernel32.GetCurrentProcess()

                funcion_memoria = getattr(
                    kernel32,
                    "K32GetProcessMemoryInfo",
                    None
                )

                if funcion_memoria is None:
                    psapi = ctypes.WinDLL(
                        "psapi",
                        use_last_error=True
                    )
                    funcion_memoria = psapi.GetProcessMemoryInfo

                funcion_memoria.argtypes = [
                    wintypes.HANDLE,
                    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                    wintypes.DWORD
                ]
                funcion_memoria.restype = wintypes.BOOL

                contadores = PROCESS_MEMORY_COUNTERS()
                contadores.cb = ctypes.sizeof(
                    PROCESS_MEMORY_COUNTERS
                )

                correcto = funcion_memoria(
                    proceso,
                    ctypes.byref(contadores),
                    contadores.cb
                )

                if correcto and contadores.WorkingSetSize > 0:
                    self.ram_metodo = "working_set"
                    return int(contadores.WorkingSetSize)

            except (
                AttributeError,
                OSError,
                ValueError,
                TypeError
            ):
                pass

            # ---------------------------------------------
            # RESPALDO WINDOWS: TASKLIST
            # ---------------------------------------------
            # tasklist también informa el Working Set del proceso.
            # Se usa solamente si la consulta nativa anterior falla.
            try:
                import csv
                import io
                import re
                import subprocess

                pid = os.getpid()
                flags = getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                )

                salida = subprocess.run(
                    [
                        "tasklist",
                        "/FI",
                        f"PID eq {pid}",
                        "/FO",
                        "CSV",
                        "/NH"
                    ],
                    capture_output=True,
                    text=True,
                    errors="ignore",
                    creationflags=flags,
                    timeout=2,
                    check=False
                ).stdout

                for fila in csv.reader(
                    io.StringIO(salida)
                ):
                    if len(fila) < 5:
                        continue

                    if fila[1].strip() != str(pid):
                        continue

                    # Funciona tanto con "45,812 K" como con
                    # formatos regionales del tipo "45.812 KB".
                    digitos = re.sub(
                        r"[^0-9]",
                        "",
                        fila[-1]
                    )

                    if digitos:
                        self.ram_metodo = "tasklist"
                        return int(digitos) * 1024

            except (
                OSError,
                ValueError,
                IndexError,
                subprocess.SubprocessError
                if 'subprocess' in locals()
                else OSError
            ):
                pass

        # -------------------------------------------------
        # LINUX: RSS ACTUAL
        # -------------------------------------------------
        try:
            if os.path.exists("/proc/self/statm"):

                with open(
                    "/proc/self/statm",
                    "r",
                    encoding="utf-8"
                ) as archivo:
                    partes = archivo.read().split()

                if len(partes) >= 2:
                    paginas_residentes = int(partes[1])
                    tamano_pagina = os.sysconf("SC_PAGE_SIZE")
                    self.ram_metodo = "rss_proc"
                    return paginas_residentes * tamano_pagina

        except (OSError, ValueError, AttributeError):
            pass

        # -------------------------------------------------
        # UNIX / MACOS: PICO DE RSS COMO RESPALDO
        # -------------------------------------------------
        try:
            import resource
            import sys

            memoria = resource.getrusage(
                resource.RUSAGE_SELF
            ).ru_maxrss

            self.ram_metodo = "ru_maxrss"

            if sys.platform == "darwin":
                return int(memoria)

            return int(memoria * 1024)

        except (ImportError, OSError, ValueError):
            pass

        # -------------------------------------------------
        # ÚLTIMO RESPALDO: MEMORIA ADMINISTRADA POR PYTHON
        # -------------------------------------------------
        if self.tracemalloc_activo:
            try:
                import tracemalloc
                memoria_actual, _ = tracemalloc.get_traced_memory()

                if memoria_actual >= 0:
                    self.ram_metodo = "tracemalloc"
                    return int(memoria_actual)

            except (RuntimeError, ImportError):
                pass

        return None

    def iniciar_monitor_ram(self):
        """Inicia el indicador periódico de memoria en el pie."""

        self.ram_base_bytes = self.obtener_uso_ram_bytes()
        self.actualizar_indicador_ram()

    def actualizar_indicador_ram(self):
        """Actualiza RAM, variación desde el inicio y tamaño del sistema."""

        memoria_bytes = self.obtener_uso_ram_bytes()

        if memoria_bytes is None:
            texto_memoria = "RAM: no disponible"

        else:
            memoria_mb = memoria_bytes / (1024 ** 2)

            if self.ram_base_bytes is None:
                self.ram_base_bytes = memoria_bytes

            diferencia_mb = (
                memoria_bytes - self.ram_base_bytes
            ) / (1024 ** 2)

            # Si se llegó al último respaldo, se aclara que no es el
            # Working Set total del proceso sino memoria de Python.
            if self.ram_metodo == "tracemalloc":
                nombre_memoria = "Mem. Python aprox."
            else:
                nombre_memoria = "RAM"

            texto_memoria = (
                f"{nombre_memoria}: {memoria_mb:.2f} MB "
                f"({diferencia_mb:+.2f} MB)"
            )

        filas = self.numero_ecuaciones
        columnas = self.numero_variables + 1

        self.texto_ram.set(
            f"{texto_memoria}  •  Matriz: {filas}×{columnas}"
        )

        try:
            intervalo = (
                1200
                if self.ram_metodo == "tasklist"
                else 750
            )

            self.ram_after_id = self.ventana.after(
                intervalo,
                self.actualizar_indicador_ram
            )
        except tk.TclError:
            self.ram_after_id = None

    def mostrar_mensaje(self, texto, error=False):

        self.mensaje.set(texto)

        if error:

            self.label_estado.config(
                fg=COLOR_ERROR
            )

        else:

            self.label_estado.config(
                fg=COLOR_CHOCOLATE_MEDIO
            )

    # =====================================================
    # MATRIZ DINÁMICA
    # =====================================================

    def cursor_esta_sobre_matriz(self, widget):

        actual = widget

        while actual is not None:

            if actual == self.canvas_matriz:
                return True

            if actual == self.frame_cuadricula:
                return True

            try:

                actual = actual.master

            except AttributeError:

                break

        return False


    def controlar_rueda_matriz(self, event):

        # Identificar el elemento que está debajo del cursor
        widget = self.ventana.winfo_containing(
            event.x_root,
            event.y_root
        )

        # Si el cursor no está sobre la matriz,
        # no hacemos nada
        if not self.cursor_esta_sobre_matriz(
            widget
        ):

            return

        # -------------------------------------------------
        # SHIFT + RUEDA = IZQUIERDA / DERECHA
        # -------------------------------------------------

        shift_presionado = bool(
            event.state & 0x0001
        )

        if shift_presionado:

            if event.delta > 0:
                direccion = -1
            else:
                direccion = 1

            self.canvas_matriz.xview_scroll(
                direccion,
                "units"
            )

        # -------------------------------------------------
        # RUEDA NORMAL = ARRIBA / ABAJO
        # -------------------------------------------------

        else:

            if event.delta > 0:
                direccion = -1
            else:
                direccion = 1

            self.canvas_matriz.yview_scroll(
                direccion,
                "units"
            )

        return "break"

    def enfocar_barra(self, event):

        event.widget.focus_set()


    def mover_barra_vertical(self, direccion):

        self.canvas_matriz.yview_scroll(
            direccion,
            "units"
        )

        return "break"


    def mover_barra_horizontal(self, direccion):

        self.canvas_matriz.xview_scroll(
            direccion,
            "units"
        )

        return "break"

    def actualizar_region_scroll(self, event=None):

        self.ventana.after_idle(
            self.aplicar_region_scroll
        )


    def aplicar_region_scroll(self):

        if not hasattr(
            self,
            "canvas_matriz"
        ):
            return

        self.frame_cuadricula.update_idletasks()

        ancho_contenido = max(
            1,
            self.frame_cuadricula.winfo_reqwidth()
        )

        alto_contenido = max(
            1,
            self.frame_cuadricula.winfo_reqheight()
        )

        ancho_visible = max(
            1,
            self.canvas_matriz.winfo_width()
        )

        alto_visible = max(
            1,
            self.canvas_matriz.winfo_height()
        )

        ancho_region = max(
            ancho_contenido,
            ancho_visible
        )

        alto_region = max(
            alto_contenido,
            alto_visible
        )

        self.canvas_matriz.configure(
            scrollregion=(
                0,
                0,
                ancho_region,
                alto_region
            )
        )

        if ancho_contenido <= ancho_visible:

            self.canvas_matriz.xview_moveto(
                0
            )

        if alto_contenido <= alto_visible:

            self.canvas_matriz.yview_moveto(
                0
            )



    def leer_entero_dimension(self, texto, nombre):

        texto = texto.strip()

        try:
            valor = int(texto)
        except ValueError:
            raise ValueError(
                f"{nombre} debe ser un número entero."
            )

        if valor < 1:
            raise ValueError(
                f"{nombre} debe ser mayor o igual que 1."
            )

        if valor > MAX_DIMENSION:
            raise ValueError(
                (
                    f"{nombre} no puede ser mayor que "
                    f"{MAX_DIMENSION} en esta interfaz."
                )
            )

        return valor

    def cambiar_dimensiones(self):

        try:

            ecuaciones = self.leer_entero_dimension(
                self.variable_ecuaciones.get(),
                "El número de ecuaciones"
            )

            variables = self.leer_entero_dimension(
                self.variable_variables.get(),
                "El número de variables"
            )

        except ValueError as error:

            self.mostrar_mensaje(
                f"Choco dice: {error}",
                True
            )

            return

        self.numero_ecuaciones = ecuaciones
        self.numero_variables = variables
        self.nombres_variables = [
            f"x{indice + 1}"
            for indice in range(variables)
        ]

        self.crear_entrada_actual()

        self.limpiar_salida()

        self.escribir_salida(
            (
                f"Se preparó el sistema para "
                f"{ecuaciones} ecuación(es) y "
                f"{variables} variable(s).\n"
            )
        )

        self.mostrar_mensaje(
            (
                "Choco dice: sistema preparado. "
                "Completa todos los valores."
            )
        )

    def crear_entrada_actual(self):

        if self.modo_entrada == "ecuacion":
            self.crear_ecuaciones_interfaz()
        else:
            self.crear_matriz_interfaz()

    def alternar_modo_entrada(self):

        if self.modo_entrada == "matriz":
            self.modo_entrada = "ecuacion"
            self.crear_ecuaciones_interfaz()

            self.mostrar_mensaje(
                (
                    "Choco dice: modo ecuación activado. "
                    "Escribe una ecuación completa en cada fila."
                )
            )

        else:
            self.modo_entrada = "matriz"
            self.crear_matriz_interfaz()

            self.mostrar_mensaje(
                (
                    "Choco dice: modo matriz activado. "
                    "Completa la matriz aumentada."
                )
            )

        self.matriz_original = None
        self.resultado_actual = None

        self.limpiar_salida()

        if self.modo_entrada == "ecuacion":
            self.escribir_salida(
                (
                    "Modo ecuación activado.\n"
                    "Ejemplos: x + 2y + 3z = 9, f = 7 o 67g12 - 2h = 10\n\n"
                    "Completa todas las ecuaciones y presiona "
                    "«Resolver sistema».\n"
                )
            )
        else:
            self.escribir_salida(
                (
                    "Modo matriz activado.\n"
                    "Completa la matriz aumentada y presiona "
                    "«Resolver sistema».\n"
                )
            )

    def crear_matriz_interfaz(self):

        for widget in self.frame_cuadricula.winfo_children():
            widget.destroy()

        self.entradas_matriz = []
        self.entradas_ecuaciones = []
        self.etiquetas_filas = []
        self.etiquetas_columnas = []

        self.fila_seleccionada = None
        self.columna_seleccionada = None

        self.frame_datos.config(
            text="Matriz aumentada"
        )

        self.frame_info.config(
            text="Información de la celda"
        )

        self.label_ayuda.config(
            text=(
                "Cada fila representa una ecuación. "
                "Ingresa los coeficientes de x₁, x₂, ... "
                "y en la columna b escribe el término independiente."
            )
        )

        tk.Label(
            self.frame_cuadricula,
            text="Ecuación",
            font=("Arial", 9, "bold"),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=6
        )

        for columna in range(
            self.numero_variables
        ):

            etiqueta = tk.Label(
                self.frame_cuadricula,
                font=("Arial", 9, "bold"),
                fg=COLOR_CHOCOLATE,
                bg=COLOR_FONDO,
                justify="center"
            )

            etiqueta.grid(
                row=0,
                column=columna + 1,
                padx=5,
                pady=6
            )

            self.etiquetas_columnas.append(
                etiqueta
            )

        etiqueta_b = tk.Label(
            self.frame_cuadricula,
            font=("Arial", 9, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_BEIGE,
            justify="center"
        )

        etiqueta_b.grid(
            row=0,
            column=self.numero_variables + 1,
            padx=(14, 5),
            pady=6
        )

        self.etiquetas_columnas.append(
            etiqueta_b
        )

        for fila in range(
            self.numero_ecuaciones
        ):

            etiqueta_fila = tk.Label(
                self.frame_cuadricula,
                font=("Arial", 9, "bold"),
                fg=COLOR_CHOCOLATE,
                bg=COLOR_FONDO
            )

            etiqueta_fila.grid(
                row=fila + 1,
                column=0,
                padx=8,
                pady=5
            )

            self.etiquetas_filas.append(
                etiqueta_fila
            )

            fila_entradas = []

            for columna in range(
                self.numero_variables + 1
            ):

                color_celda = (
                    "#FFF9ED"
                    if columna == self.numero_variables
                    else COLOR_BLANCO
                )

                entrada = tk.Entry(
                    self.frame_cuadricula,
                    width=9,
                    font=("Arial", 11),
                    justify="center",
                    bg=color_celda,
                    fg=COLOR_CHOCOLATE,
                    relief="solid",
                    bd=1
                )

                padx = (
                    (14, 5)
                    if columna == self.numero_variables
                    else 5
                )

                entrada.grid(
                    row=fila + 1,
                    column=columna + 1,
                    padx=padx,
                    pady=5,
                    ipady=5
                )

                entrada.bind(
                    "<FocusIn>",
                    lambda event,
                    f=fila,
                    c=columna:
                    self.seleccionar_celda(
                        f,
                        c
                    )
                )

                entrada.bind(
                    "<FocusOut>",
                    lambda event,
                    f=fila,
                    c=columna:
                    self.validar_celda_visual(
                        f,
                        c
                    )
                )

                entrada.bind(
                    "<Return>",
                    lambda event:
                    self.mover_foco_siguiente(
                        event
                    )
                )

                fila_entradas.append(
                    entrada
                )

            self.entradas_matriz.append(
                fila_entradas
            )

        self.actualizar_modo()

        self.texto_celda.set(
            (
                "Selecciona una celda para ver su coordenada, "
                "función y si pertenece a la diagonal principal."
            )
        )

        self.canvas_matriz.xview_moveto(
            0
        )

        self.canvas_matriz.yview_moveto(
            0
        )

        self.actualizar_region_scroll()

        if self.entradas_matriz:

            self.ventana.after(
                100,
                lambda:
                self.entradas_matriz[0][0].focus_set()
            )

    def crear_ecuaciones_interfaz(self):

        for widget in self.frame_cuadricula.winfo_children():
            widget.destroy()

        self.entradas_matriz = []
        self.entradas_ecuaciones = []
        self.etiquetas_filas = []
        self.etiquetas_columnas = []

        self.fila_seleccionada = None
        self.columna_seleccionada = None

        self.frame_datos.config(
            text="Sistema en forma de ecuaciones"
        )

        self.frame_info.config(
            text="Información de la ecuación"
        )

        self.label_ayuda.config(
            text=(
                "Escribe una ecuación completa en cada fila. Puedes elegir "
                "cualquier variable que comience con una letra; usa los mismos "
                "nombres en todo el sistema. Ejemplos: f = 7 o 67g12 - 2h = 10"
            )
        )

        tk.Label(
            self.frame_cuadricula,
            text="Ecuaciones del sistema",
            font=("Arial", 9, "bold"),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            padx=8,
            pady=6,
            sticky="w"
        )

        for fila in range(self.numero_ecuaciones):

            tk.Label(
                self.frame_cuadricula,
                text=f"Ecuación {fila + 1}",
                font=("Arial", 9, "bold"),
                fg=COLOR_CHOCOLATE,
                bg=COLOR_FONDO
            ).grid(
                row=fila + 1,
                column=0,
                padx=(8, 10),
                pady=6,
                sticky="e"
            )

            entrada = tk.Entry(
                self.frame_cuadricula,
                width=48,
                font=("Arial", 11),
                justify="left",
                bg=COLOR_BLANCO,
                fg=COLOR_CHOCOLATE,
                relief="solid",
                bd=1
            )

            entrada.grid(
                row=fila + 1,
                column=1,
                padx=(0, 10),
                pady=6,
                ipady=5,
                sticky="ew"
            )

            entrada.bind(
                "<FocusIn>",
                lambda event,
                f=fila:
                self.seleccionar_ecuacion(f)
            )

            entrada.bind(
                "<FocusOut>",
                lambda event,
                f=fila:
                self.validar_ecuacion_visual(f)
            )

            entrada.bind(
                "<Return>",
                lambda event:
                self.mover_foco_siguiente(event)
            )

            self.entradas_ecuaciones.append(
                entrada
            )

        self.frame_cuadricula.columnconfigure(
            1,
            weight=1
        )

        self.texto_celda.set(
            (
                "Selecciona una ecuación para escribirla. "
                "Ejemplos: x + 2y + 3z = 9, f = 7 o 67g12 - 2h = 10"
            )
        )

        self.canvas_matriz.xview_moveto(0)
        self.canvas_matriz.yview_moveto(0)
        self.actualizar_region_scroll()

        if self.entradas_ecuaciones:
            self.ventana.after(
                100,
                lambda:
                self.entradas_ecuaciones[0].focus_set()
            )

    def obtener_base_visible(self):

        if self.modo_indices.get() == "programador":
            return 0

        return 1

    def actualizar_modo(self):

        if self.modo_entrada == "ecuacion":
            return

        base = self.obtener_base_visible()

        for fila in range(self.numero_ecuaciones):

            self.etiquetas_filas[fila].config(
                text=f"Fila {fila + base}"
            )

        for columna in range(self.numero_variables):

            self.etiquetas_columnas[columna].config(
                text=(
                    f"x{columna + 1}\n"
                    f"Col. {columna + base}"
                )
            )

        self.etiquetas_columnas[
            self.numero_variables
        ].config(
            text=(
                "b (=)\n"
                f"Col. {self.numero_variables + base}"
            )
        )

        if (
            self.fila_seleccionada is not None
            and self.columna_seleccionada is not None
        ):

            self.actualizar_informacion_celda(
                self.fila_seleccionada,
                self.columna_seleccionada
            )

    # =====================================================
    # CELDAS Y VALIDACIÓN VISUAL
    # =====================================================

    def color_normal_celda(self, columna):

        if columna == self.numero_variables:
            return "#FFF9ED"

        return COLOR_BLANCO

    def limpiar_resaltado(self):

        for fila in range(self.numero_ecuaciones):

            for columna in range(self.numero_variables + 1):

                entrada = self.entradas_matriz[fila][columna]

                texto = entrada.get().strip()

                if texto != "":

                    try:
                        self.convertir_numero(texto)

                    except ValueError:

                        entrada.config(
                            bg=COLOR_ERROR_SUAVE
                        )

                        continue

                entrada.config(
                    bg=self.color_normal_celda(columna)
                )

    def asegurar_celda_visible(self, fila, columna):

        entrada = self.entradas_matriz[
            fila
        ][
            columna
        ]

        # Actualizar dimensiones reales
        self.ventana.update_idletasks()

        # Posición de la celda dentro de la cuadrícula
        x = entrada.winfo_x()
        y = entrada.winfo_y()

        ancho_celda = entrada.winfo_width()
        alto_celda = entrada.winfo_height()

        # Tamaño visible del Canvas
        ancho_visible = self.canvas_matriz.winfo_width()
        alto_visible = self.canvas_matriz.winfo_height()

        # Tamaño total de la matriz
        ancho_total = max(
            self.frame_cuadricula.winfo_reqwidth(),
            ancho_visible
        )

        alto_total = max(
            self.frame_cuadricula.winfo_reqheight(),
            alto_visible
        )

        # Posición actual visible
        izquierda = self.canvas_matriz.canvasx(
            0
        )

        arriba = self.canvas_matriz.canvasy(
            0
        )

        margen = 15

        # -------------------------------------------------
        # DESPLAZAMIENTO HORIZONTAL
        # -------------------------------------------------

        if x < izquierda + margen:

            nueva_posicion = max(
                0,
                x - margen
            )

            self.canvas_matriz.xview_moveto(
                nueva_posicion / ancho_total
            )

        elif (
            x + ancho_celda
            >
            izquierda + ancho_visible - margen
        ):

            nueva_posicion = (
                x
                + ancho_celda
                - ancho_visible
                + margen
            )

            maximo = max(
                0,
                ancho_total - ancho_visible
            )

            nueva_posicion = min(
                nueva_posicion,
                maximo
            )

            self.canvas_matriz.xview_moveto(
                nueva_posicion / ancho_total
            )

        # -------------------------------------------------
        # DESPLAZAMIENTO VERTICAL
        # -------------------------------------------------

        if y < arriba + margen:

            nueva_posicion = max(
                0,
                y - margen
            )

            self.canvas_matriz.yview_moveto(
                nueva_posicion / alto_total
            )

        elif (
            y + alto_celda
            >
            arriba + alto_visible - margen
        ):

            nueva_posicion = (
                y
                + alto_celda
                - alto_visible
                + margen
            )

            maximo = max(
                0,
                alto_total - alto_visible
            )

            nueva_posicion = min(
                nueva_posicion,
                maximo
            )

            self.canvas_matriz.yview_moveto(
                nueva_posicion / alto_total
            )

    def seleccionar_celda(self, fila, columna):

        self.fila_seleccionada = fila
        self.columna_seleccionada = columna

        self.limpiar_resaltado()

        self.entradas_matriz[
            fila
        ][
            columna
        ].config(
            bg=COLOR_RESALTADO
        )

        self.actualizar_informacion_celda(
            fila,
            columna
        )

        self.ventana.after_idle(
            lambda:
            self.asegurar_celda_visible(
                fila,
                columna
            )
        )

    def actualizar_informacion_celda(self, fila, columna):

        base = self.obtener_base_visible()

        fila_visible = fila + base
        columna_visible = columna + base

        if columna < self.numero_variables:

            variable = f"x{columna + 1}"

            if es_elemento_diagonal(
                fila,
                columna
            ):

                diagonal = (
                    "Sí. Está en la diagonal principal "
                    "porque fila = columna."
                )

            else:

                diagonal = (
                    "No. No pertenece a la diagonal principal "
                    "porque fila ≠ columna."
                )

            funcion = (
                f"Coeficiente de {variable}"
            )

        else:

            funcion = (
                "Término independiente b "
                "(valor ubicado a la derecha del signo =)"
            )

            diagonal = (
                "No se considera parte de la diagonal "
                "de la matriz de coeficientes."
            )

        self.texto_celda.set(
            (
                f"Coordenada: ({fila_visible}, {columna_visible})\n"
                f"Función: {funcion}\n"
                f"Diagonal: {diagonal}"
            )
        )

    def convertir_numero(self, texto):

        texto = texto.strip()

        if texto == "":
            raise ValueError("La celda está vacía.")

        # Facilita al usuario escribir 2,5 o 2.5.
        texto = texto.replace(",", ".")

        try:
            numero = float(texto)

        except ValueError:
            raise ValueError(
                f"«{texto}» no es un número válido."
            )

        if numero != numero:
            raise ValueError(
                "NaN no es un valor válido."
            )

        if numero == float("inf") or numero == float("-inf"):
            raise ValueError(
                "No se permiten valores infinitos."
            )

        return numero

    def validar_celda_visual(self, fila, columna):

        entrada = self.entradas_matriz[fila][columna]

        texto = entrada.get().strip()

        if texto == "":
            entrada.config(
                bg=self.color_normal_celda(columna)
            )

            return

        try:

            numero = self.convertir_numero(
                texto
            )

        except ValueError:

            entrada.config(
                bg=COLOR_ERROR_SUAVE
            )

            return

        entrada.delete(
            0,
            tk.END
        )

        entrada.insert(
            0,
            self.formatear_numero(numero)
        )

        entrada.config(
            bg=self.color_normal_celda(columna)
        )

    def seleccionar_ecuacion(self, fila):

        for entrada in self.entradas_ecuaciones:

            if entrada.get().strip() == "":
                entrada.config(bg=COLOR_BLANCO)
                continue

            try:
                convertir_ecuacion_a_fila(
                    entrada.get(),
                    self.numero_variables
                )
                entrada.config(bg=COLOR_BLANCO)
            except (TypeError, ValueError):
                entrada.config(bg=COLOR_ERROR_SUAVE)

        self.entradas_ecuaciones[fila].config(
            bg=COLOR_RESALTADO
        )

        self.texto_celda.set(
            (
                f"Ecuación {fila + 1}\n"
                "Puedes elegir cualquier nombre de variable que comience "
                "con una letra y mantenerlo en todo el sistema.\n"
                "Ejemplos: x + 2y = 9, f = 7 o 67g12 - 2h = 10"
            )
        )

    def validar_ecuacion_visual(self, fila):

        entrada = self.entradas_ecuaciones[fila]
        texto = entrada.get().strip()

        if texto == "":
            entrada.config(bg=COLOR_BLANCO)
            return

        try:
            convertir_ecuacion_a_fila(
                texto,
                self.numero_variables
            )
            entrada.config(bg=COLOR_BLANCO)
        except (TypeError, ValueError):
            entrada.config(bg=COLOR_ERROR_SUAVE)

    def mover_foco_siguiente(self, event):

        event.widget.tk_focusNext().focus()

        return "break"

    # =====================================================
    # LECTURA PROFESIONAL DE LA MATRIZ
    # =====================================================

    def leer_matriz(self):

        matriz = []

        primera_celda_invalida = None
        primer_error = None

        for fila in range(self.numero_ecuaciones):

            fila_valores = []

            for columna in range(self.numero_variables + 1):

                entrada = self.entradas_matriz[fila][columna]

                texto = entrada.get().strip()

                try:

                    valor = self.convertir_numero(
                        texto
                    )

                    fila_valores.append(
                        valor
                    )

                    entrada.config(
                        bg=self.color_normal_celda(columna)
                    )

                except ValueError as error:

                    entrada.config(
                        bg=COLOR_ERROR_SUAVE
                    )

                    if primera_celda_invalida is None:

                        primera_celda_invalida = (
                            fila,
                            columna
                        )

                        primer_error = str(error)

            matriz.append(
                fila_valores
            )

        if primera_celda_invalida is not None:

            fila, columna = primera_celda_invalida

            self.entradas_matriz[fila][columna].focus_set()

            base = self.obtener_base_visible()

            self.mostrar_mensaje(
                (
                    "Choco dice: revisa la celda "
                    f"({fila + base}, {columna + base}). "
                    f"{primer_error}"
                ),
                True
            )

            return None

        return matriz

    def leer_ecuaciones(self):

        ecuaciones = []
        primera_ecuacion_invalida = None
        primer_error = None

        for fila in range(self.numero_ecuaciones):

            entrada = self.entradas_ecuaciones[fila]
            texto = entrada.get().strip()

            if texto == "":
                entrada.config(bg=COLOR_ERROR_SUAVE)

                if primera_ecuacion_invalida is None:
                    primera_ecuacion_invalida = fila
                    primer_error = "La ecuación está vacía."

                continue

            try:
                convertir_ecuacion_a_fila(
                    texto,
                    self.numero_variables
                )
                ecuaciones.append(texto)
                entrada.config(bg=COLOR_BLANCO)

            except (TypeError, ValueError) as error:
                entrada.config(bg=COLOR_ERROR_SUAVE)

                if primera_ecuacion_invalida is None:
                    primera_ecuacion_invalida = fila
                    primer_error = str(error)

        if primera_ecuacion_invalida is not None:

            self.entradas_ecuaciones[
                primera_ecuacion_invalida
            ].focus_set()

            self.mostrar_mensaje(
                (
                    "Choco dice: revisa la ecuación "
                    f"{primera_ecuacion_invalida + 1}. "
                    f"{primer_error}"
                ),
                True
            )

            return None

        try:
            matriz, nombres = convertir_sistema_ecuaciones(
                ecuaciones,
                self.numero_variables
            )
            self.nombres_variables = nombres
            return matriz
        except (TypeError, ValueError) as error:
            self.mostrar_mensaje(f"Choco dice: {error}", True)
            return None

    # =====================================================
    # RESOLVER
    # =====================================================

    def resolver(self):

        if self.modo_entrada == "ecuacion":
            matriz = self.leer_ecuaciones()
        else:
            matriz = self.leer_matriz()
            self.nombres_variables = [
                f"x{indice + 1}"
                for indice in range(self.numero_variables)
            ]

        if matriz is None:
            return

        self.matriz_original = copiar_matriz(
            matriz
        )

        try:

            resultado = resolver_sistema(
                matriz,
                self.numero_variables
            )

        except ValueError as error:

            self.mostrar_mensaje(
                f"Choco dice: {error}",
                True
            )

            return

        self.resultado_actual = resultado

        self.mostrar_resultado(
            resultado
        )

        self.mostrar_mensaje(
            (
                "Choco dice: sistema procesado correctamente. "
                "Revisa el procedimiento y la clasificación."
            )
        )

    # =====================================================
    # VISTA DEL PROCEDIMIENTO
    # =====================================================

    def actualizar_vista_procedimiento(self):

        modo = self.modo_vista_procedimiento.get()

        self.boton_vista_procedimiento.config(
            text=f"Vista: {modo} ▾"
        )

        # Si ya existe una resolución, refrescar únicamente la vista.
        # No se vuelve a calcular el sistema.
        if self.resultado_actual is not None:
            self.mostrar_resultado(
                self.resultado_actual
            )

    def alternar_modo_numeros(self):

        nuevo_modo = (
            "Fracción"
            if self.modo_numeros.get() == "Decimal"
            else "Decimal"
        )
        self.modo_numeros.set(nuevo_modo)
        self.boton_modo_numeros.config(
            text=f"Números: {nuevo_modo}"
        )

        if self.resultado_actual is not None:
            self.mostrar_resultado(self.resultado_actual)

    # =====================================================
    # RESULTADOS
    # =====================================================

    def limpiar_salida(self):

        self.salida.config(
            state="normal"
        )

        self.salida.delete(
            "1.0",
            tk.END
        )

        self.salida.config(
            state="disabled"
        )

    def escribir_salida(self, texto, etiqueta=None):

        self.salida.config(
            state="normal"
        )

        if etiqueta is None:

            self.salida.insert(
                tk.END,
                texto
            )

        else:

            self.salida.insert(
                tk.END,
                texto,
                etiqueta
            )

        self.salida.config(
            state="disabled"
        )

        self.salida.see(
            tk.END
        )

    def formatear_numero(self, numero):

        if abs(numero) < TOLERANCIA:
            numero = 0.0

        if float(numero).is_integer():
            return str(int(numero))

        if self.modo_numeros.get() == "Fracción":
            return str(Fraction(float(numero)).limit_denominator(10000))

        texto = f"{numero:.3f}"
        return texto.rstrip("0").rstrip(".")

    def formatear_matriz(self, matriz):

        lineas = []

        for fila in matriz:

            coeficientes = []

            for valor in fila[:-1]:

                coeficientes.append(
                    f"{self.formatear_numero(valor):>10}"
                )

            termino = (
                f"{self.formatear_numero(fila[-1]):>10}"
            )

            lineas.append(
                "[ "
                + " ".join(coeficientes)
                + "  | "
                + termino
                + " ]"
            )

        return "\n".join(lineas)

    def mostrar_resultado(self, resultado):

        self.limpiar_salida()

        modo_vista = self.modo_vista_procedimiento.get()

        self.escribir_salida(
            "MATRIZ AUMENTADA INICIAL\n",
            "titulo"
        )

        self.escribir_salida(
            self.formatear_matriz(
                self.matriz_original
            )
            + "\n\n"
        )

        pasos = resultado["pasos"]

        if modo_vista == "Dos fases":
            fases_visibles = (
                "escalonamiento",
                "reduccion"
            )
        elif modo_vista == "Gauss":
            fases_visibles = (
                "escalonamiento",
            )
        elif modo_vista == "Gauss-Jordan":
            fases_visibles = (
                "escalonamiento",
                "reduccion",
            )

        pasos_visibles = []

        for paso in pasos:

            if paso["fase"] in fases_visibles:
                pasos_visibles.append(paso)

        if len(pasos_visibles) == 0:

            if modo_vista == "Gauss":
                mensaje_fase = (
                    "La fase Gauss no requirió operaciones por filas.\n\n"
                )
            elif modo_vista == "Gauss-Jordan":

                if resultado["clasificacion"] == "inconsistente":
                    mensaje_fase = (
                        "Gauss-Jordan no se ejecutó porque durante Gauss "
                        "se detectó que el sistema es inconsistente.\n\n"
                    )
                else:
                    mensaje_fase = (
                        "La fase Gauss-Jordan no requirió operaciones "
                        "adicionales.\n\n"
                    )
            else:
                mensaje_fase = (
                    "La matriz ya estaba suficientemente reducida; "
                    "no fue necesario realizar operaciones por filas.\n\n"
                )

            self.escribir_salida(
                mensaje_fase
            )

        else:

            fase_actual = None
            numero_paso = 1
            encabezado_jordan_mostrado = False

            for paso in pasos_visibles:

                if paso["fase"] != fase_actual:

                    fase_actual = paso["fase"]

                    if modo_vista == "Gauss-Jordan":
                        titulo_fase = "GAUSS-JORDAN DESDE LA MATRIZ INICIAL\n"
                        if encabezado_jordan_mostrado:
                            titulo_fase = None
                        encabezado_jordan_mostrado = True
                    elif fase_actual == "escalonamiento":

                        if modo_vista == "Dos fases":
                            titulo_fase = "FASE 1 - GAUSS\n"
                        else:
                            titulo_fase = "GAUSS\n"

                    else:

                        if modo_vista == "Dos fases":
                            titulo_fase = "FASE 2 - GAUSS-JORDAN\n"
                        else:
                            titulo_fase = "GAUSS-JORDAN\n"

                    if titulo_fase is not None:
                        self.escribir_salida(
                            titulo_fase,
                            "titulo"
                        )

                self.escribir_salida(
                    (
                        f"\nPaso {numero_paso}: "
                        f"{paso['operacion']}\n"
                    )
                )

                self.escribir_salida(
                    self.formatear_matriz(
                        paso["matriz"]
                    )
                    + "\n"
                )

                numero_paso += 1

        # -------------------------------------------------
        # MATRICES RESULTANTES SEGÚN LA VISTA ELEGIDA
        # -------------------------------------------------

        if modo_vista in (
            "Dos fases",
            "Gauss"
        ):

            self.escribir_salida(
                "\nMATRIZ GAUSS\n",
                "titulo"
            )

            self.escribir_salida(
                self.formatear_matriz(
                    resultado["matriz_escalonada"]
                )
                + "\n\n"
            )

        clasificacion = resultado["clasificacion"]

        if (
            clasificacion == "unica"
            and modo_vista in ("Dos fases", "Gauss")
        ):
            self.mostrar_sustitucion_regresiva(resultado)

        if clasificacion == "inconsistente":

            self.mostrar_resultado_inconsistente(
                resultado
            )

            return

        if modo_vista in (
            "Dos fases",
            "Gauss-Jordan"
        ):

            self.escribir_salida(
                "MATRIZ GAUSS-JORDAN\n",
                "titulo"
            )

            self.escribir_salida(
                self.formatear_matriz(
                    resultado["matriz_reducida"]
                )
                + "\n\n"
            )

        if clasificacion == "unica":

            self.mostrar_resultado_unico(
                resultado
            )

        else:

            self.mostrar_resultado_infinito(
                resultado
            )

    def mostrar_resultado_inconsistente(self, resultado):

        self.escribir_salida(
            (
                "CLASIFICACIÓN\n"
                "Sistema Inconsistente: Sin Solución.\n"
            ),
            "error"
        )

        fila = resultado["fila_inconsistente"]

        valor_b = resultado[
            "matriz_escalonada"
        ][
            fila
        ][
            self.numero_variables
        ]

        self.escribir_salida(
            (
                "\nSe encontró una contradicción del tipo:\n"
                f"0 = {self.formatear_numero(valor_b)}\n\n"
                "Por lo tanto, no existe ningún conjunto de valores "
                "que satisfaga todas las ecuaciones al mismo tiempo.\n"
            )
        )

    def mostrar_sustitucion_regresiva(self, resultado):

        self.escribir_salida(
            "SUSTITUCIÓN REGRESIVA (DESARROLLO ALGEBRAICO)\n",
            "titulo"
        )

        matriz = resultado["matriz_escalonada"]
        solucion = resultado["solucion"]

        for fila, columna_pivote in reversed(resultado["pivotes"]):
            nombre = self.nombres_variables[columna_pivote]
            termino_independiente = matriz[fila][self.numero_variables]
            ecuacion_simbolica = nombre
            ecuacion_sustituida = nombre
            hay_terminos = False
            suma_conocida = 0.0

            for columna in range(columna_pivote + 1, self.numero_variables):
                coeficiente = matriz[fila][columna]
                if abs(coeficiente) < TOLERANCIA:
                    continue

                valor = solucion[columna]
                suma_conocida += coeficiente * valor
                signo = " + " if coeficiente > 0 else " - "
                magnitud = abs(coeficiente)
                texto_coeficiente = ""
                if abs(magnitud - 1.0) >= TOLERANCIA:
                    texto_coeficiente = self.formatear_numero(magnitud)

                ecuacion_simbolica += (
                    signo
                    + texto_coeficiente
                    + self.nombres_variables[columna]
                )
                ecuacion_sustituida += (
                    signo
                    + (
                        f"({self.formatear_numero(magnitud)})"
                        if texto_coeficiente
                        else ""
                    )
                    + f"({self.formatear_numero(valor)})"
                )
                hay_terminos = True

            if not hay_terminos:
                self.escribir_salida(
                    f"{nombre} = {self.formatear_numero(termino_independiente)}\n\n"
                )
                continue

            self.escribir_salida(
                f"{ecuacion_simbolica} = "
                f"{self.formatear_numero(termino_independiente)}\n"
            )
            self.escribir_salida(
                f"{ecuacion_sustituida} = "
                f"{self.formatear_numero(termino_independiente)}\n"
            )
            self.escribir_salida(
                f"{nombre} = {self.formatear_numero(termino_independiente)} "
                f"- ({self.formatear_numero(suma_conocida)})\n"
            )
            self.escribir_salida(
                f"{nombre} = {self.formatear_numero(solucion[columna_pivote])}\n\n"
            )

    def mostrar_resultado_unico(self, resultado):

        self.escribir_salida(
            (
                "CLASIFICACIÓN\n"
                "Sistema Consistente Determinado: "
                "Presenta Solución Única.\n\n"
            ),
            "exito"
        )

        self.escribir_salida(
            "SOLUCIÓN\n",
            "titulo"
        )

        solucion = resultado["solucion"]

        for indice, valor in enumerate(solucion):

            self.escribir_salida(
                (
                    f"{self.nombres_variables[indice]} = "
                    f"{self.formatear_numero(valor)}\n"
                )
            )

        self.escribir_salida(
            "\nVERIFICACIÓN AUTOMÁTICA\n",
            "titulo"
        )

        verificaciones = verificar_solucion(
            self.matriz_original,
            solucion,
            self.numero_variables
        )

        todas_correctas = True

        for verificacion in verificaciones:

            simbolo = "✓"

            if not verificacion["correcta"]:
                simbolo = "✗"
                todas_correctas = False

            self.escribir_salida(
                (
                    f"{simbolo} Ecuación "
                    f"{verificacion['ecuacion']}: "
                    f"{self.formatear_numero(verificacion['lado_izquierdo'])}"
                    " = "
                    f"{self.formatear_numero(verificacion['lado_derecho'])}\n"
                )
            )

        if todas_correctas:

            self.escribir_salida(
                (
                    "\nVerificación correcta: la solución satisface "
                    "el sistema original.\n"
                ),
                "exito"
            )

        else:

            self.escribir_salida(
                (
                    "\nAdvertencia: alguna ecuación no pasó "
                    "la verificación numérica.\n"
                ),
                "error"
            )

    def mostrar_resultado_infinito(self, resultado):

        self.escribir_salida(
            (
                "CLASIFICACIÓN\n"
                "Sistema Consistente Indeterminado: "
                "Presenta Infinitas Soluciones.\n\n"
            ),
            "exito"
        )

        libres = resultado[
            "variables_libres"
        ]

        nombres_libres = []

        for columna in libres:

            nombres_libres.append(
                self.nombres_variables[columna]
            )

        self.escribir_salida(
            (
                "Variables libres: "
                + ", ".join(nombres_libres)
                + "\n\n"
            )
        )

        self.escribir_salida(
            "SOLUCIÓN GENERAL\n",
            "titulo"
        )

        for linea in self.crear_solucion_parametrica(resultado):

            self.escribir_salida(
                linea + "\n"
            )

        self.escribir_salida(
            (
                "\nAl existir al menos una variable libre, "
                "hay infinitas asignaciones posibles.\n"
            )
        )

    # =====================================================
    # SOLUCIÓN PARAMÉTRICA PARA CASO INFINITO
    # =====================================================

    def crear_solucion_parametrica(self, resultado):

        matriz = resultado[
            "matriz_reducida"
        ]

        pivotes = resultado[
            "pivotes"
        ]

        libres = resultado[
            "variables_libres"
        ]

        parametro_por_columna = {}

        for indice, columna in enumerate(libres):

            parametro_por_columna[columna] = (
                f"t{indice + 1}"
            )

        lineas = []

        # Variables libres.
        for columna in libres:

            lineas.append(
                (
                    f"{self.nombres_variables[columna]} = "
                    f"{parametro_por_columna[columna]}"
                )
            )

        # Variables básicas.
        for fila, columna_pivote in pivotes:

            termino_independiente = matriz[
                fila
            ][
                self.numero_variables
            ]

            partes = []

            if (
                abs(termino_independiente) >= TOLERANCIA
                or len(libres) == 0
            ):

                partes.append(
                    self.formatear_numero(
                        termino_independiente
                    )
                )

            for columna_libre in libres:

                coeficiente = -matriz[
                    fila
                ][
                    columna_libre
                ]

                if abs(coeficiente) < TOLERANCIA:
                    continue

                parametro = parametro_por_columna[
                    columna_libre
                ]

                magnitud = abs(coeficiente)

                if abs(magnitud - 1.0) < TOLERANCIA:
                    termino = parametro
                else:
                    termino = (
                        f"{self.formatear_numero(magnitud)}"
                        f"{parametro}"
                    )

                if len(partes) == 0:

                    if coeficiente < 0:
                        partes.append(
                            "-" + termino
                        )
                    else:
                        partes.append(
                            termino
                        )

                else:

                    if coeficiente < 0:
                        partes.append(
                            "- " + termino
                        )
                    else:
                        partes.append(
                            "+ " + termino
                        )

            if len(partes) == 0:
                partes.append("0")

            lineas.append(
                (
                    f"{self.nombres_variables[columna_pivote]} = "
                    + " ".join(partes)
                )
            )

        # Ordenar por número de variable.
        def numero_variable(linea):

            parte = linea.split("=")[0].strip()

            return self.nombres_variables.index(parte)

        lineas.sort(
            key=numero_variable
        )

        return lineas

    # =====================================================
    # EJEMPLOS PARA LOS TRES CASOS DE PRUEBA
    # =====================================================

    def formatear_ecuacion_desde_fila(self, fila_matriz):

        partes = []

        for columna in range(self.numero_variables):

            coeficiente = fila_matriz[columna]

            if abs(coeficiente) < TOLERANCIA:
                continue

            magnitud = abs(coeficiente)
            variable = f"x{columna + 1}"

            if abs(magnitud - 1.0) < TOLERANCIA:
                termino = variable
            else:
                termino = (
                    f"{self.formatear_numero(magnitud)}"
                    f"{variable}"
                )

            if len(partes) == 0:
                if coeficiente < 0:
                    partes.append("-" + termino)
                else:
                    partes.append(termino)
            else:
                if coeficiente < 0:
                    partes.append("- " + termino)
                else:
                    partes.append("+ " + termino)

        if len(partes) == 0:
            partes.append("0")

        return (
            " ".join(partes)
            + " = "
            + self.formatear_numero(fila_matriz[-1])
        )

    def cargar_ejemplo(self):

        tipo = self.tipo_ejemplo.get()

        ejemplos = {
            "Solución única": [
                [1, 1, 1, 6],
                [2, -1, 1, 3],
                [1, 2, -1, 2]
            ],
            "Infinitas soluciones": [
                [1, 1, 1, 6],
                [2, 2, 2, 12],
                [1, -1, 1, 2]
            ],
            "Sin solución": [
                [1, 1, 1, 6],
                [2, 2, 2, 12],
                [1, 1, 1, 8]
            ]
        }

        matriz = ejemplos[tipo]

        self.numero_ecuaciones = 3
        self.numero_variables = 3
        self.nombres_variables = ["x1", "x2", "x3"]

        self.variable_ecuaciones.set(
            "3"
        )

        self.variable_variables.set(
            "3"
        )

        self.crear_entrada_actual()

        if self.modo_entrada == "ecuacion":

            for fila in range(3):
                self.entradas_ecuaciones[fila].insert(
                    0,
                    self.formatear_ecuacion_desde_fila(
                        matriz[fila]
                    )
                )

        else:

            for fila in range(3):

                for columna in range(4):

                    self.entradas_matriz[
                        fila
                    ][
                        columna
                    ].insert(
                        0,
                        self.formatear_numero(
                            matriz[fila][columna]
                        )
                    )

        self.mostrar_mensaje(
            (
                f"Choco dice: ejemplo «{tipo}» cargado. "
                "Presiona Resolver sistema."
            )
        )

    # =====================================================
    # LIMPIAR
    # =====================================================

    def limpiar_matriz(self):

        if self.modo_entrada == "ecuacion":

            for entrada in self.entradas_ecuaciones:
                entrada.delete(0, tk.END)
                entrada.config(bg=COLOR_BLANCO)

        else:

            for fila in range(self.numero_ecuaciones):

                for columna in range(self.numero_variables + 1):

                    entrada = self.entradas_matriz[
                        fila
                    ][
                        columna
                    ]

                    entrada.delete(
                        0,
                        tk.END
                    )

                    entrada.config(
                        bg=self.color_normal_celda(columna)
                    )

        self.matriz_original = None
        self.resultado_actual = None

        self.limpiar_salida()

        self.escribir_salida(
            (
                "Datos limpiados.\n"
                "Ingresa un nuevo sistema y presiona "
                "«Resolver sistema».\n"
            )
        )

        if self.modo_entrada == "ecuacion":
            self.texto_celda.set(
                (
                    "Selecciona una ecuación para escribirla. "
                    "Ejemplos: x + 2y + 3z = 9, f = 7 o 67g12 - 2h = 10"
                )
            )
        else:
            self.texto_celda.set(
                (
                    "Selecciona una celda para ver su coordenada, "
                    "función y si pertenece a la diagonal."
                )
            )

        self.mostrar_mensaje(
            "Choco dice: datos limpiados."
        )

        if self.modo_entrada == "ecuacion" and self.entradas_ecuaciones:
            self.entradas_ecuaciones[0].focus_set()
        elif self.entradas_matriz:
            self.entradas_matriz[0][0].focus_set()

    # =====================================================
    # PANTALLA COMPLETA Y TAMAÑO
    # =====================================================

    def alternar_pantalla_completa(self):

        self.pantalla_completa = not self.pantalla_completa

        self.ventana.attributes(
            "-fullscreen",
            self.pantalla_completa
        )

        if self.pantalla_completa:

            self.mostrar_mensaje(
                (
                    "Pantalla completa activada. "
                    "Presiona Esc o F11 para salir."
                )
            )

        else:

            self.mostrar_mensaje(
                "Pantalla completa desactivada."
            )

    def salir_pantalla_completa(self):

        if self.pantalla_completa:

            self.pantalla_completa = False

            self.ventana.attributes(
                "-fullscreen",
                False
            )

            self.mostrar_mensaje(
                "Pantalla completa desactivada."
            )

    def restaurar_tamano(self):

        # Salir de pantalla completa
        self.salir_pantalla_completa()

        # Si estaba maximizada, regresar a ventana normal
        self.ventana.state(
            "normal"
        )

        # Regresar al tamaño original
        self.ventana.geometry(
            "1200x760"
        )

        # Esperar a que Tkinter actualice las dimensiones
        self.ventana.update_idletasks()

        # Regresar el divisor al centro
        self.posicionar_divisor_inicial()

        # Regresar la matriz a la esquina superior izquierda
        self.canvas_matriz.xview_moveto(
            0
        )

        self.canvas_matriz.yview_moveto(
            0
        )

        # Regresar también el procedimiento al inicio
        self.salida.xview_moveto(
            0
        )

        self.salida.yview_moveto(
            0
        )

        self.mostrar_mensaje(
            "Choco dice: tamaño y posición de los paneles restaurados."
        )


# =========================================================
# INICIO DEL PROGRAMA
# =========================================================

def main():

    ventana = tk.Tk()

    app = ChocoLabApp(
        ventana
    )

    ventana.mainloop()


if __name__ == "__main__":
    main()
