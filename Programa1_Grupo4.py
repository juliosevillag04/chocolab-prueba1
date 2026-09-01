# =========================================================
# Universidad Americana (UAM)
# Facultad de Ingeniería y Arquitectura (FIA)
# Carrera: Ingeniería de Sistemas
# Asignatura: Álgebra Lineal
# Grupo 4 - Integrantes:
# Julio Javier Sevilla Gallegos
# Docente: Carlos Iván Argüello Martínez
# =========================================================
# CHOCO LAB - CALCULADORA DE ÁLGEBRA LINEAL
# =========================================================
# Interfaz gráfica para resolver sistemas de ecuaciones
# lineales mediante eliminación por filas.
# =========================================================


import os
import tkinter as tk
from tkinter import ttk

from logica import (
    TOLERANCIA,
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

        self.entradas_matriz = []
        self.etiquetas_filas = []
        self.etiquetas_columnas = []

        self.fila_seleccionada = None
        self.columna_seleccionada = None

        self.pantalla_completa = False

        self.imagenes = []

        self.configurar_ventana()
        self.configurar_estilos()
        self.crear_interfaz()
        self.crear_matriz_interfaz()

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

        frame_info = ttk.LabelFrame(
            frame_izquierdo,
            text="Información de la celda"
        )

        frame_info.grid(
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
            frame_info,
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

        frame_matriz = ttk.LabelFrame(
            frame_izquierdo,
            text="Matriz aumentada"
        )

        frame_matriz.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        frame_matriz.rowconfigure(
            0,
            weight=1
        )

        frame_matriz.columnconfigure(
            0,
            weight=1
        )

        self.canvas_matriz = tk.Canvas(
            frame_matriz,
            bg=COLOR_FONDO,
            highlightthickness=0,
            confine=True
        )

        self.scroll_y_matriz = ttk.Scrollbar(
            frame_matriz,
            orient="vertical",
            command=self.canvas_matriz.yview
        )

        self.scroll_x_matriz = ttk.Scrollbar(
            frame_matriz,
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

        tk.Label(
            frame_derecho,
            text="3. Procedimiento, clasificación y verificación",
            font=("Arial", 11, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_FONDO,
            justify="left",
            anchor="w"
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 6)
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
            "Completa la matriz aumentada y presiona "
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
            value="Listo. Completa la matriz para comenzar."
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

        self.label_creditos = tk.Label(
            self.ventana,
            text=texto_creditos,
            font=("Arial", 8),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO,
            justify="center",
            anchor="center",
            wraplength=1100,
            padx=12,
            pady=4
        )

        self.label_creditos.grid(
            row=4,
            column=0,
            sticky="ew"
        )

        self.label_creditos.bind(
            "<Configure>",
            lambda event:
            self.label_creditos.config(
                wraplength=max(
                    300,
                    event.width - 30
                )
            )
        )

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

        self.crear_matriz_interfaz()

        self.limpiar_salida()

        self.escribir_salida(
            (
                f"Se creó una matriz aumentada para "
                f"{ecuaciones} ecuación(es) y "
                f"{variables} variable(s).\n"
            )
        )

        self.mostrar_mensaje(
            (
                "Choco dice: matriz preparada. "
                "Completa todos los valores."
            )
        )

    def crear_matriz_interfaz(self):

        for widget in self.frame_cuadricula.winfo_children():
            widget.destroy()

        self.entradas_matriz = []
        self.etiquetas_filas = []
        self.etiquetas_columnas = []

        self.fila_seleccionada = None
        self.columna_seleccionada = None

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

    def obtener_base_visible(self):

        if self.modo_indices.get() == "programador":
            return 0

        return 1

    def actualizar_modo(self):

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

    # =====================================================
    # RESOLVER
    # =====================================================

    def resolver(self):

        matriz = self.leer_matriz()

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

        return f"{numero:.6g}"

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

        if len(pasos) == 0:

            self.escribir_salida(
                (
                    "La matriz ya estaba suficientemente reducida; "
                    "no fue necesario realizar operaciones por filas.\n\n"
                )
            )

        else:

            fase_actual = None

            numero_paso = 1

            for paso in pasos:

                if paso["fase"] != fase_actual:

                    fase_actual = paso["fase"]

                    if fase_actual == "escalonamiento":

                        self.escribir_salida(
                            "FASE 1 - FORMA ESCALONADA\n",
                            "titulo"
                        )

                    else:

                        self.escribir_salida(
                            "FASE 2 - FORMA ESCALONADA REDUCIDA\n",
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

        self.escribir_salida(
            "\nMATRIZ ESCALONADA\n",
            "titulo"
        )

        self.escribir_salida(
            self.formatear_matriz(
                resultado["matriz_escalonada"]
            )
            + "\n\n"
        )

        clasificacion = resultado["clasificacion"]

        if clasificacion == "inconsistente":

            self.mostrar_resultado_inconsistente(
                resultado
            )

            return

        self.escribir_salida(
            "MATRIZ ESCALONADA REDUCIDA\n",
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
                    f"x{indice + 1} = "
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
                f"x{columna + 1}"
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
                    f"x{columna + 1} = "
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
                    f"x{columna_pivote + 1} = "
                    + " ".join(partes)
                )
            )

        # Ordenar por número de variable.
        def numero_variable(linea):

            parte = linea.split("=")[0].strip()

            return int(
                parte.replace("x", "")
            )

        lineas.sort(
            key=numero_variable
        )

        return lineas

    # =====================================================
    # EJEMPLOS PARA LOS TRES CASOS DE PRUEBA
    # =====================================================

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

        self.variable_ecuaciones.set(
            "3"
        )

        self.variable_variables.set(
            "3"
        )

        self.crear_matriz_interfaz()

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
                "Matriz limpia.\n"
                "Ingresa un nuevo sistema y presiona "
                "«Resolver sistema».\n"
            )
        )

        self.texto_celda.set(
            (
                "Selecciona una celda para ver su coordenada, "
                "función y si pertenece a la diagonal."
            )
        )

        self.mostrar_mensaje(
            "Choco dice: matriz limpia."
        )

        if self.entradas_matriz:

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
