# =========================================================
# Universidad Americana (UAM)
# Facultad de Ingeniería y Arquitectura (FIA)
# Asignatura: Álgebra Lineal
# Grupo 4
# CHOCO LAB - MENÚ PRINCIPAL Y MÓDULOS COMPLEMENTARIOS (versión integrada)
# =========================================================

import ast
import os
import re
import tkinter as tk
from fractions import Fraction
from tkinter import messagebox, ttk


# =========================================================
# CONFIGURACIÓN COMPARTIDA
# =========================================================

COLOR_FONDO = "#F7F3EE"
COLOR_CHOCOLATE = "#4A2C1A"
COLOR_CHOCOLATE_MEDIO = "#6B4423"
COLOR_BEIGE = "#EADBC8"
COLOR_BLANCO = "#FFFFFF"
COLOR_RESALTADO = "#F3D7A6"
COLOR_ERROR = "#A33A2B"
COLOR_EXITO = "#2E6B3B"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_RECURSOS = os.path.join(BASE_DIR, "recursos")


def configurar_estilos():
    """Configura los estilos generales sin depender de otro archivo."""

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
        "TButton",
        font=("Arial", 10)
    )
    estilo.configure(
        "TNotebook",
        background=COLOR_FONDO,
        borderwidth=0
    )
    estilo.configure(
        "TNotebook.Tab",
        font=("Arial", 10, "bold"),
        padding=(12, 7)
    )


def cargar_logo(lista_imagenes, nombre_archivo, ancho_objetivo=120):
    """Carga un PNG desde la carpeta recursos y conserva su referencia."""

    ruta = os.path.join(RUTA_RECURSOS, nombre_archivo)

    if not os.path.exists(ruta):
        return None

    try:
        imagen_original = tk.PhotoImage(file=ruta)
        ancho_original = imagen_original.width()

        if ancho_original > ancho_objetivo:
            factor = max(1, round(ancho_original / ancho_objetivo))
            imagen = imagen_original.subsample(factor, factor)
        else:
            imagen = imagen_original

        lista_imagenes.extend([imagen_original, imagen])
        return imagen

    except tk.TclError:
        return None


def _obtener_ram_proceso():
    """Devuelve la memoria residente del proceso sin dependencias externas."""

    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class ContadoresMemoria(ctypes.Structure):
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
                    ("PeakPagefileUsage", ctypes.c_size_t)
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            proceso = kernel32.GetCurrentProcess()
            funcion = getattr(kernel32, "K32GetProcessMemoryInfo", None)
            if funcion is None:
                funcion = ctypes.WinDLL("psapi").GetProcessMemoryInfo
            funcion.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(ContadoresMemoria),
                wintypes.DWORD
            ]
            contadores = ContadoresMemoria()
            contadores.cb = ctypes.sizeof(ContadoresMemoria)
            if funcion(proceso, ctypes.byref(contadores), contadores.cb):
                return int(contadores.WorkingSetSize)
        except (AttributeError, OSError, TypeError, ValueError):
            pass

    try:
        if os.path.exists("/proc/self/statm"):
            with open("/proc/self/statm", "r", encoding="utf-8") as archivo:
                partes = archivo.read().split()
            return int(partes[1]) * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError, AttributeError):
        pass

    try:
        import resource
        import sys
        memoria = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(memoria if sys.platform == "darwin" else memoria * 1024)
    except (ImportError, OSError, ValueError):
        return None


def _activar_pantalla_completa(ventana):
    """Abre una ventana en pantalla completa con F11 y Escape disponibles."""

    estado = {"activo": True}

    def aplicar(activo):
        estado["activo"] = activo
        try:
            ventana.attributes("-fullscreen", activo)
        except tk.TclError:
            if activo:
                try:
                    ventana.state("zoomed")
                except tk.TclError:
                    pass

    def alternar(event=None):
        aplicar(not estado["activo"])

    ventana.bind("<F11>", alternar, add="+")
    ventana.bind("<Escape>", lambda event: aplicar(False), add="+")
    ventana.after_idle(lambda: aplicar(True))


class BarraInferiorChoco:
    """Barra café común: RAM, créditos y navegación."""

    CREDITOS = (
        "© 2026 Grupo 4  •  Julio Javier Sevilla Gallegos  •  "
        "Álgebra Lineal  •  Universidad Americana (UAM)"
    )

    def __init__(self, ventana, fila, volver=None, texto_derecha="Volver al menú"):
        self.ventana = ventana
        self.ram_inicial = _obtener_ram_proceso()
        self.after_id = None

        self.marco = tk.Frame(ventana, bg=COLOR_CHOCOLATE, height=48)
        self.marco.grid(row=fila, column=0, sticky="ew")
        self.marco.grid_propagate(False)
        self.marco.columnconfigure(0, weight=1)
        self.marco.columnconfigure(1, weight=3)
        self.marco.columnconfigure(2, weight=1)

        self.texto_ram = tk.StringVar(value="RAM: calculando...")
        tk.Label(
            self.marco,
            textvariable=self.texto_ram,
            font=("Consolas", 8, "bold"),
            fg=COLOR_BLANCO,
            bg=COLOR_CHOCOLATE,
            anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=16)

        tk.Label(
            self.marco,
            text=self.CREDITOS,
            font=("Arial", 8),
            fg=COLOR_BLANCO,
            bg=COLOR_CHOCOLATE,
            anchor="center"
        ).grid(row=0, column=1, sticky="ew", padx=10)

        if volver is not None:
            tk.Button(
                self.marco,
                text=texto_derecha,
                command=volver,
                bg=COLOR_RESALTADO,
                fg=COLOR_CHOCOLATE,
                activebackground=COLOR_BEIGE,
                activeforeground=COLOR_CHOCOLATE,
                relief="flat",
                font=("Arial", 9, "bold"),
                cursor="hand2",
                padx=13,
                pady=5
            ).grid(row=0, column=2, sticky="e", padx=16, pady=7)

        self.actualizar()

    def actualizar(self):
        memoria = _obtener_ram_proceso()
        if memoria is None:
            texto = "RAM: no disponible"
        else:
            diferencia = 0 if self.ram_inicial is None else memoria - self.ram_inicial
            texto = (
                f"RAM: {memoria / 1048576:.2f} MB "
                f"({diferencia / 1048576:+.2f} MB)"
            )
        self.texto_ram.set(texto)
        try:
            self.after_id = self.ventana.after(800, self.actualizar)
        except tk.TclError:
            self.after_id = None


class PieChoco(BarraInferiorChoco):
    """Compatibilidad con el nombre usado por el menú."""

    def __init__(self, ventana, fila):
        super().__init__(ventana, fila)


# =========================================================
# FUNCIONES DE ÁLGEBRA EXACTA
# =========================================================

def _leer_numero(texto):
    """Convierte enteros, decimales o fracciones a Fraction."""

    limpio = texto.strip().replace("−", "-")

    if not limpio:
        raise ValueError("Se encontró un valor vacío.")

    try:
        return Fraction(limpio)
    except (ValueError, ZeroDivisionError):
        raise ValueError(
            f"El valor «{texto}» no es un número válido. "
            "Usa enteros, decimales o fracciones como 3/4."
        ) from None


def _leer_matriz(texto, nombre="matriz"):
    """Lee una matriz escrita por filas, con espacios o comas."""

    texto = texto.strip().replace(";", "\n")

    if not texto:
        raise ValueError(f"Debes ingresar la {nombre}.")

    matriz = []

    for numero_fila, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea:
            continue

        elementos = [
            elemento
            for elemento in re.split(r"[\s,]+", linea)
            if elemento
        ]

        if not elementos:
            continue

        fila = [_leer_numero(elemento) for elemento in elementos]

        if matriz and len(fila) != len(matriz[0]):
            raise ValueError(
                f"La fila {numero_fila} de la {nombre} tiene "
                f"{len(fila)} elementos, pero debe tener {len(matriz[0])}."
            )

        matriz.append(fila)

    if not matriz:
        raise ValueError(f"Debes ingresar la {nombre}.")

    return matriz


def _leer_vector(texto, nombre="vector"):
    """Lee un vector escrito en una fila o en una columna."""

    matriz = _leer_matriz(texto, nombre)

    if len(matriz) == 1:
        return matriz[0]

    if all(len(fila) == 1 for fila in matriz):
        return [fila[0] for fila in matriz]

    raise ValueError(
        f"El {nombre} debe escribirse en una sola fila o columna."
    )


def _texto_numero(numero):
    numero = Fraction(numero)

    if numero.denominator == 1:
        return str(numero.numerator)

    return f"{numero.numerator}/{numero.denominator}"


def _texto_matriz(matriz):
    if not matriz:
        return "[ ]"

    textos = [[_texto_numero(valor) for valor in fila] for fila in matriz]
    anchos = [
        max(len(fila[columna]) for fila in textos)
        for columna in range(len(textos[0]))
    ]

    lineas = []
    for fila in textos:
        contenido = "  ".join(
            valor.rjust(anchos[indice])
            for indice, valor in enumerate(fila)
        )
        lineas.append(f"[ {contenido} ]")

    return "\n".join(lineas)


def _dimensiones(matriz):
    return len(matriz), len(matriz[0])


def _sumar_matrices(a, b, signo=1):
    if _dimensiones(a) != _dimensiones(b):
        raise ValueError(
            "Para sumar o restar, A y B deben tener las mismas dimensiones."
        )

    return [
        [a[i][j] + signo * b[i][j] for j in range(len(a[0]))]
        for i in range(len(a))
    ]


def _multiplicar_matrices(a, b):
    filas_a, columnas_a = _dimensiones(a)
    filas_b, columnas_b = _dimensiones(b)

    if columnas_a != filas_b:
        raise ValueError(
            "No se puede calcular A × B: el número de columnas de A "
            "debe coincidir con el número de filas de B."
        )

    return [
        [
            sum(
                (a[i][k] * b[k][j] for k in range(columnas_a)),
                Fraction(0)
            )
            for j in range(columnas_b)
        ]
        for i in range(filas_a)
    ]


def _transponer(matriz):
    return [list(fila) for fila in zip(*matriz)]


def _determinante_con_pasos(matriz):
    filas, columnas = _dimensiones(matriz)

    if filas != columnas:
        raise ValueError("El determinante solo existe para matrices cuadradas.")

    trabajo = [fila[:] for fila in matriz]
    signo = 1
    determinante = Fraction(1)
    pasos = []

    for columna in range(columnas):
        fila_pivote = None

        for fila in range(columna, filas):
            if trabajo[fila][columna] != 0:
                fila_pivote = fila
                break

        if fila_pivote is None:
            pasos.append(
                f"La columna {columna + 1} no tiene pivote; por eso det(A)=0."
            )
            return Fraction(0), pasos

        if fila_pivote != columna:
            trabajo[columna], trabajo[fila_pivote] = (
                trabajo[fila_pivote],
                trabajo[columna]
            )
            signo *= -1
            pasos.append(
                f"F{columna + 1} ↔ F{fila_pivote + 1}; "
                "el intercambio cambia el signo."
            )

        pivote = trabajo[columna][columna]
        determinante *= pivote
        pasos.append(
            f"Pivote {columna + 1}: {_texto_numero(pivote)}."
        )

        for fila in range(columna + 1, filas):
            if trabajo[fila][columna] == 0:
                continue

            factor = trabajo[fila][columna] / pivote
            trabajo[fila] = [
                trabajo[fila][j] - factor * trabajo[columna][j]
                for j in range(columnas)
            ]
            pasos.append(
                f"F{fila + 1} ← F{fila + 1} − "
                f"({_texto_numero(factor)})F{columna + 1}."
            )

    return signo * determinante, pasos


# =========================================================
# MÓDULO 1: CONVERSIÓN DE SISTEMAS NUMÉRICOS
# =========================================================

class ConversionSistemasNumericosApp:

    BASES = {
        "Decimal (base 10)": 10,
        "Binario (base 2)": 2,
        "Octal (base 8)": 8,
        "Hexadecimal (base 16)": 16
    }

    DIGITOS = "0123456789ABCDEF"

    def __init__(self, ventana):
        self.ventana = ventana
        self.imagenes = []

        self.ventana.title("Choco Lab - Conversión de sistemas numéricos")
        self.ventana.geometry("1050x720")
        self.ventana.minsize(850, 600)
        self.ventana.configure(bg=COLOR_FONDO)
        _activar_pantalla_completa(self.ventana)

        configurar_estilos()
        self._crear_interfaz()

    def _crear_interfaz(self):
        self.ventana.rowconfigure(2, weight=1)
        self.ventana.columnconfigure(0, weight=1)

        encabezado = tk.Frame(self.ventana, bg=COLOR_FONDO)
        encabezado.grid(row=0, column=0, sticky="ew", padx=24, pady=(14, 6))
        encabezado.columnconfigure(1, weight=1)

        logo = cargar_logo(self.imagenes, "chocolab.png", 135)
        if logo is not None:
            tk.Label(
                encabezado,
                image=logo,
                bg=COLOR_FONDO
            ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 18))

        tk.Label(
            encabezado,
            text="Conversión de sistemas numéricos",
            font=("Arial", 20, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_FONDO
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            encabezado,
            text="Convierte enteros entre decimal, binario, octal y hexadecimal.",
            font=("Arial", 10),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        entrada = ttk.LabelFrame(self.ventana, text="1. Ingresa el número")
        entrada.grid(row=1, column=0, sticky="ew", padx=24, pady=7)
        entrada.columnconfigure(1, weight=1)

        tk.Label(
            entrada,
            text="Sistema de origen:",
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=12)

        self.base_origen = tk.StringVar(value="Decimal (base 10)")
        selector = ttk.Combobox(
            entrada,
            textvariable=self.base_origen,
            values=list(self.BASES),
            state="readonly",
            width=24
        )
        selector.grid(row=0, column=1, sticky="w", padx=8, pady=12)

        tk.Label(
            entrada,
            text="Número:",
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=2, sticky="e", padx=(18, 8), pady=12)

        self.numero = tk.StringVar()
        campo = tk.Entry(
            entrada,
            textvariable=self.numero,
            font=("Consolas", 12),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_BLANCO,
            relief="solid",
            bd=1
        )
        campo.grid(row=0, column=3, sticky="ew", padx=8, pady=12, ipady=5)
        entrada.columnconfigure(3, weight=1)
        campo.bind("<Return>", lambda event: self.convertir())
        campo.focus_set()

        tk.Button(
            entrada,
            text="Convertir",
            command=self.convertir,
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=16,
            pady=7
        ).grid(row=0, column=4, padx=(10, 6), pady=10)

        tk.Button(
            entrada,
            text="Limpiar",
            command=self.limpiar,
            bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=14,
            pady=7
        ).grid(row=0, column=5, padx=(4, 12), pady=10)

        resultado = ttk.LabelFrame(
            self.ventana,
            text="2. Equivalencias y procedimiento"
        )
        resultado.grid(row=2, column=0, sticky="nsew", padx=24, pady=7)
        resultado.rowconfigure(0, weight=1)
        resultado.columnconfigure(0, weight=1)

        self.salida = tk.Text(
            resultado,
            wrap="word",
            font=("Consolas", 10),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            relief="solid",
            bd=1,
            padx=14,
            pady=12,
            state="disabled"
        )
        self.salida.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        barra = ttk.Scrollbar(
            resultado,
            orient="vertical",
            command=self.salida.yview
        )
        barra.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        self.salida.configure(yscrollcommand=barra.set)

        self.pie = BarraInferiorChoco(
            self.ventana,
            fila=3,
            volver=lambda: self.ventana.event_generate("<<CerrarModulo>>")
        )

        self._mostrar(
            "Selecciona el sistema de origen, escribe un número entero y "
            "presiona «Convertir»."
        )

    def _normalizar(self, texto, base): #Conversión de sistemas numéricos
        limpio = texto.strip().upper().replace("_", "").replace(" ", "")

        if not limpio:
            raise ValueError("Debes escribir un número.")

        signo = ""
        if limpio[0] in "+-":
            signo = limpio[0]
            limpio = limpio[1:]

        prefijos = {2: "0B", 8: "0O", 16: "0X"}
        prefijo = prefijos.get(base)
        if prefijo and limpio.startswith(prefijo):
            limpio = limpio[2:]

        if not limpio:
            raise ValueError("Debes escribir dígitos después del signo o prefijo.")

        permitidos = set(self.DIGITOS[:base])
        invalidos = sorted(set(limpio) - permitidos)

        if invalidos:
            raise ValueError(
                f"El dígito «{invalidos[0]}» no pertenece a la base {base}."
            )

        return signo + limpio

    def _representar(self, numero_decimal, base):
        signo = "-" if numero_decimal < 0 else ""
        numero = abs(numero_decimal)

        if numero == 0:
            return "0"

        digitos = []
        while numero > 0:
            numero, residuo = divmod(numero, base)
            digitos.append(self.DIGITOS[residuo])

        return signo + "".join(reversed(digitos))

    def _expansion_posicional(self, numero_limpio, base):
        negativo = numero_limpio.startswith("-")
        digitos = numero_limpio.lstrip("+-")
        terminos = []

        for posicion, caracter in enumerate(digitos):
            exponente = len(digitos) - posicion - 1
            valor = self.DIGITOS.index(caracter)
            terminos.append(f"{valor}×{base}^{exponente}")

        expresion = " + ".join(terminos)
        if negativo:
            return f"−({expresion})"
        return expresion

    def _pasos_division(self, numero_decimal, base):
        numero = abs(numero_decimal)

        if numero == 0:
            return ["0 ya se representa como 0."]

        pasos = []
        actual = numero

        while actual > 0:
            cociente, residuo = divmod(actual, base)
            pasos.append(
                f"{actual} ÷ {base} = {cociente}, "
                f"residuo {self.DIGITOS[residuo]}"
            )
            actual = cociente

        pasos.append("Se leen los residuos desde el último hasta el primero.")
        return pasos

    def convertir(self):
        nombre_base = self.base_origen.get()
        base = self.BASES[nombre_base]

        try:
            limpio = self._normalizar(self.numero.get(), base)
            decimal = int(limpio, base)
        except ValueError as error:
            messagebox.showerror(
                "Dato no válido",
                f"Choco dice: {error}",
                parent=self.ventana
            )
            return

        binario = self._representar(decimal, 2)
        octal = self._representar(decimal, 8)
        hexadecimal = self._representar(decimal, 16)

        lineas = [
            "EQUIVALENCIAS",
            "=" * 58,
            f"Decimal      : {decimal}",
            f"Binario      : {binario}",
            f"Octal        : {octal}",
            f"Hexadecimal  : {hexadecimal}",
            "",
            "PROCEDIMIENTO",
            "=" * 58,
            f"1. Número de origen: {limpio} en base {base}.",
            "2. Expansión posicional:",
            f"   {self._expansion_posicional(limpio, base)} = {decimal}",
            "",
            "3. Conversión del valor decimal por divisiones sucesivas:"
        ]

        for nombre, base_destino, resultado in (
            ("BINARIO", 2, binario),
            ("OCTAL", 8, octal),
            ("HEXADECIMAL", 16, hexadecimal)
        ):
            lineas.extend(["", f"A {nombre} (base {base_destino}):"])
            lineas.extend(
                f"   {paso}"
                for paso in self._pasos_division(decimal, base_destino)
            )
            lineas.append(f"   Resultado: {resultado}")

        if decimal < 0:
            lineas.append(
                "\nNota: se convirtió el valor absoluto y luego se conservó el signo negativo."
            )

        self._mostrar("\n".join(lineas))

    def _mostrar(self, texto):
        self.salida.configure(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.insert("1.0", texto)
        self.salida.configure(state="disabled")

    def limpiar(self):
        self.numero.set("")
        self._mostrar(
            "Selecciona el sistema de origen, escribe un número entero y "
            "presiona «Convertir»."
        )


# =========================================================
# MÓDULO 3: ÁLGEBRA MATRICIAL Y VECTORIAL
# =========================================================

class _AlgebraMatricialVectorialAppAnterior:

    OPERACIONES = (
        "A + B",
        "A − B",
        "A × B",
        "Transpuesta de A",
        "Determinante de A",
        "k · A",
        "A · x (B como vector)"
    )

    def __init__(self, ventana):
        self.ventana = ventana
        self.imagenes = []

        self.ventana.title("Choco Lab - Álgebra matricial y vectorial")
        self.ventana.geometry("1180x760")
        self.ventana.minsize(930, 640)
        self.ventana.configure(bg=COLOR_FONDO)

        configurar_estilos()
        self._crear_interfaz()

    def _crear_interfaz(self):
        self.ventana.rowconfigure(1, weight=1)
        self.ventana.columnconfigure(0, weight=1)

        encabezado = tk.Frame(self.ventana, bg=COLOR_FONDO)
        encabezado.grid(row=0, column=0, sticky="ew", padx=24, pady=(12, 4))
        encabezado.columnconfigure(1, weight=1)

        logo = cargar_logo(self.imagenes, "chocolab.png", 125)
        if logo is not None:
            tk.Label(
                encabezado,
                image=logo,
                bg=COLOR_FONDO
            ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 18))

        tk.Label(
            encabezado,
            text="Álgebra matricial y vectorial",
            font=("Arial", 20, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_FONDO
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            encabezado,
            text=(
                "Opera matrices y observa Ax como producto, combinación "
                "lineal y producto fila-vector."
            ),
            font=("Arial", 10),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).grid(row=1, column=1, sticky="w", pady=(4, 0))

        cuaderno = ttk.Notebook(self.ventana)
        cuaderno.grid(row=1, column=0, sticky="nsew", padx=24, pady=8)

        pestana_operaciones = tk.Frame(cuaderno, bg=COLOR_FONDO)
        pestana_ecuacion = tk.Frame(cuaderno, bg=COLOR_FONDO)

        cuaderno.add(pestana_operaciones, text="Operaciones con matrices")
        cuaderno.add(pestana_ecuacion, text="Ecuación matricial y vectorial")

        self._crear_pestana_operaciones(pestana_operaciones)
        self._crear_pestana_ecuacion(pestana_ecuacion)

        pie = tk.Frame(self.ventana, bg=COLOR_CHOCOLATE)
        pie.grid(row=2, column=0, sticky="ew")
        pie.columnconfigure(0, weight=1)

        tk.Label(
            pie,
            text=(
                "Choco dice: separa columnas con espacios o comas y "
                "usa una línea por cada fila."
            ),
            font=("Arial", 9, "italic"),
            fg=COLOR_BLANCO,
            bg=COLOR_CHOCOLATE
        ).grid(row=0, column=0, sticky="w", padx=18, pady=10)

        tk.Button(
            pie,
            text="Volver al menú",
            command=lambda: self.ventana.event_generate("<<CerrarModulo>>"),
            bg=COLOR_RESALTADO,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=12,
            pady=5
        ).grid(row=0, column=1, sticky="e", padx=18, pady=6)

    def _crear_editor(self, padre, titulo, columna, ejemplo):
        marco = ttk.LabelFrame(padre, text=titulo)
        marco.grid(
            row=0,
            column=columna,
            sticky="nsew",
            padx=(0 if columna == 0 else 6, 6 if columna == 0 else 0),
            pady=5
        )
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        editor = tk.Text(
            marco,
            height=9,
            width=28,
            font=("Consolas", 11),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            relief="solid",
            bd=1,
            padx=10,
            pady=8,
            undo=True
        )
        editor.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        editor.insert("1.0", ejemplo)
        return editor

    def _crear_salida(self, padre, fila):
        marco = ttk.LabelFrame(padre, text="Resultado y procedimiento")
        marco.grid(row=fila, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        salida = tk.Text(
            marco,
            wrap="none",
            font=("Consolas", 10),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            relief="solid",
            bd=1,
            padx=12,
            pady=10,
            state="disabled"
        )
        salida.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))

        barra_y = ttk.Scrollbar(marco, orient="vertical", command=salida.yview)
        barra_y.grid(row=0, column=1, sticky="ns", pady=(8, 0), padx=(0, 8))

        barra_x = ttk.Scrollbar(marco, orient="horizontal", command=salida.xview)
        barra_x.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))

        salida.configure(
            yscrollcommand=barra_y.set,
            xscrollcommand=barra_x.set
        )
        return salida

    def _crear_pestana_operaciones(self, pestana):
        pestana.rowconfigure(2, weight=1)
        pestana.columnconfigure(0, weight=1)
        pestana.columnconfigure(1, weight=1)

        self.editor_a = self._crear_editor(
            pestana,
            "Matriz A",
            0,
            "1  2\n3  4"
        )
        self.editor_b = self._crear_editor(
            pestana,
            "Matriz B o vector x",
            1,
            "5  6\n7  8"
        )

        controles = tk.Frame(pestana, bg=COLOR_FONDO)
        controles.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        controles.columnconfigure(1, weight=1)

        tk.Label(
            controles,
            text="Operación:",
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=0, padx=(2, 7), pady=5)

        self.operacion = tk.StringVar(value=self.OPERACIONES[0])
        ttk.Combobox(
            controles,
            textvariable=self.operacion,
            values=self.OPERACIONES,
            state="readonly",
            width=31
        ).grid(row=0, column=1, sticky="w", padx=7, pady=5)

        tk.Label(
            controles,
            text="Escalar k:",
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=2, padx=(18, 6), pady=5)

        self.escalar = tk.StringVar(value="2")
        tk.Entry(
            controles,
            textvariable=self.escalar,
            width=10,
            font=("Consolas", 10),
            relief="solid",
            bd=1
        ).grid(row=0, column=3, padx=6, pady=5, ipady=3)

        tk.Button(
            controles,
            text="Calcular",
            command=self.calcular_operacion,
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=18,
            pady=6
        ).grid(row=0, column=4, padx=(14, 6), pady=5)

        tk.Button(
            controles,
            text="Limpiar",
            command=self.limpiar_operaciones,
            bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=14,
            pady=6
        ).grid(row=0, column=5, padx=6, pady=5)

        self.salida_operaciones = self._crear_salida(pestana, 2)
        self._poner_texto(
            self.salida_operaciones,
            "Selecciona una operación y presiona «Calcular»."
        )

    def _crear_pestana_ecuacion(self, pestana):
        pestana.rowconfigure(2, weight=1)
        pestana.columnconfigure(0, weight=1)
        pestana.columnconfigure(1, weight=1)

        self.editor_coeficientes = self._crear_editor(
            pestana,
            "Matriz de coeficientes A",
            0,
            "1  2  3\n0  1  4\n2  0  1"
        )

        marco_vector = ttk.LabelFrame(pestana, text="Vector x")
        marco_vector.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=5)
        marco_vector.rowconfigure(0, weight=1)
        marco_vector.columnconfigure(0, weight=1)

        self.editor_vector = tk.Text(
            marco_vector,
            height=9,
            width=28,
            font=("Consolas", 11),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            relief="solid",
            bd=1,
            padx=10,
            pady=8,
            undo=True
        )
        self.editor_vector.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.editor_vector.insert("1.0", "2\n-1\n3")

        controles = tk.Frame(pestana, bg=COLOR_FONDO)
        controles.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        controles.columnconfigure(0, weight=1)

        tk.Label(
            controles,
            text=(
                "Se mostrará Ax en sus tres representaciones equivalentes."
            ),
            font=("Arial", 9, "italic"),
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE_MEDIO
        ).grid(row=0, column=0, sticky="w", padx=2)

        tk.Button(
            controles,
            text="Calcular Ax",
            command=self.calcular_ax,
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=18,
            pady=6
        ).grid(row=0, column=1, padx=6)

        tk.Button(
            controles,
            text="Limpiar",
            command=self.limpiar_ax,
            bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=14,
            pady=6
        ).grid(row=0, column=2, padx=6)

        self.salida_ax = self._crear_salida(pestana, 2)
        self._poner_texto(
            self.salida_ax,
            "Ingresa A y x para obtener el producto Ax."
        )

    def _poner_texto(self, widget, texto):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", texto)
        widget.configure(state="disabled")

    def calcular_operacion(self):
        operacion = self.operacion.get()

        try:
            a = _leer_matriz(self.editor_a.get("1.0", "end"), "matriz A")
            filas_a, columnas_a = _dimensiones(a)
            lineas = [
                f"Dimensión de A: {filas_a}×{columnas_a}",
                "",
                "A =",
                _texto_matriz(a),
                ""
            ]

            if operacion == "A + B":
                b = _leer_matriz(self.editor_b.get("1.0", "end"), "matriz B")
                resultado = _sumar_matrices(a, b)
                lineas.extend([
                    "B =",
                    _texto_matriz(b),
                    "",
                    "Se suman los elementos que ocupan la misma posición.",
                    "",
                    "A + B =",
                    _texto_matriz(resultado)
                ])

            elif operacion == "A − B":
                b = _leer_matriz(self.editor_b.get("1.0", "end"), "matriz B")
                resultado = _sumar_matrices(a, b, signo=-1)
                lineas.extend([
                    "B =",
                    _texto_matriz(b),
                    "",
                    "Se restan los elementos que ocupan la misma posición.",
                    "",
                    "A − B =",
                    _texto_matriz(resultado)
                ])

            elif operacion == "A × B":
                b = _leer_matriz(self.editor_b.get("1.0", "end"), "matriz B")
                resultado = _multiplicar_matrices(a, b)
                lineas.extend([
                    f"Dimensión de B: {len(b)}×{len(b[0])}",
                    "B =",
                    _texto_matriz(b),
                    "",
                    "Cada entrada se obtiene con fila de A por columna de B.",
                    "",
                    "A × B =",
                    _texto_matriz(resultado)
                ])

            elif operacion == "Transpuesta de A":
                resultado = _transponer(a)
                lineas.extend([
                    "Las filas de A pasan a ser las columnas de Aᵀ.",
                    "",
                    "Aᵀ =",
                    _texto_matriz(resultado)
                ])

            elif operacion == "Determinante de A":
                determinante, pasos = _determinante_con_pasos(a)
                lineas.extend([
                    "Se triangulariza A sin multiplicar filas por escalares.",
                    "",
                    *[f"• {paso}" for paso in pasos],
                    "",
                    f"det(A) = {_texto_numero(determinante)}"
                ])

            elif operacion == "k · A":
                k = _leer_numero(self.escalar.get())
                resultado = [[k * valor for valor in fila] for fila in a]
                lineas.extend([
                    f"k = {_texto_numero(k)}",
                    "Cada elemento de A se multiplica por k.",
                    "",
                    "k · A =",
                    _texto_matriz(resultado)
                ])

            elif operacion == "A · x (B como vector)":
                x = _leer_vector(
                    self.editor_b.get("1.0", "end"),
                    "vector x"
                )

                if columnas_a != len(x):
                    raise ValueError(
                        f"A tiene {columnas_a} columnas, pero x tiene "
                        f"{len(x)} componentes."
                    )

                resultado = _multiplicar_matrices(
                    a,
                    [[valor] for valor in x]
                )
                lineas.extend([
                    "x =",
                    _texto_matriz([[valor] for valor in x]),
                    "",
                    "Cada componente de Ax es el producto punto "
                    "de una fila de A con x.",
                    "",
                    "Ax =",
                    _texto_matriz(resultado)
                ])

            else:
                raise ValueError("Selecciona una operación válida.")

        except ValueError as error:
            messagebox.showerror(
                "No se puede calcular",
                f"Choco dice: {error}",
                parent=self.ventana
            )
            return

        self._poner_texto(self.salida_operaciones, "\n".join(lineas))

    def calcular_ax(self):
        try:
            a = _leer_matriz(
                self.editor_coeficientes.get("1.0", "end"),
                "matriz A"
            )
            x = _leer_vector(
                self.editor_vector.get("1.0", "end"),
                "vector x"
            )

            filas, columnas = _dimensiones(a)

            if columnas != len(x):
                raise ValueError(
                    f"A tiene {columnas} columnas, pero x tiene "
                    f"{len(x)} componentes. Para calcular Ax deben coincidir."
                )

            b_matriz = _multiplicar_matrices(a, [[valor] for valor in x])
            b = [fila[0] for fila in b_matriz]

            columnas_a = [
                [a[fila][columna] for fila in range(filas)]
                for columna in range(columnas)
            ]

            combinacion = " + ".join(
                f"({_texto_numero(x[indice])})a{indice + 1}"
                for indice in range(columnas)
            )

            lineas = [
                "1. ECUACIÓN MATRICIAL",
                "=" * 58,
                "A =",
                _texto_matriz(a),
                "",
                "x =",
                _texto_matriz([[valor] for valor in x]),
                "",
                "Ax = b =",
                _texto_matriz(b_matriz),
                "",
                "2. ECUACIÓN VECTORIAL / COMBINACIÓN LINEAL",
                "=" * 58,
                f"{combinacion} = b",
                ""
            ]

            for indice, columna in enumerate(columnas_a, start=1):
                lineas.append(
                    f"a{indice} = "
                    f"({', '.join(_texto_numero(v) for v in columna)})"
                )

            lineas.extend([
                "",
                "Resultado de la combinación = "
                f"({', '.join(_texto_numero(v) for v in b)})",
                "",
                "3. REPRESENTACIÓN FILA-VECTOR",
                "=" * 58
            ])

            for indice, fila in enumerate(a):
                productos = " + ".join(
                    f"({_texto_numero(fila[j])})({_texto_numero(x[j])})"
                    for j in range(columnas)
                )
                lineas.append(
                    f"Fila {indice + 1} · x: {productos} "
                    f"= {_texto_numero(b[indice])}"
                )

            lineas.extend([
                "",
                "Las tres representaciones producen exactamente el mismo vector b."
            ])

        except ValueError as error:
            messagebox.showerror(
                "No se puede calcular Ax",
                f"Choco dice: {error}",
                parent=self.ventana
            )
            return

        self._poner_texto(self.salida_ax, "\n".join(lineas))

    def limpiar_operaciones(self):
        self.editor_a.delete("1.0", "end")
        self.editor_b.delete("1.0", "end")
        self._poner_texto(
            self.salida_operaciones,
            "Selecciona una operación y presiona «Calcular»."
        )

    def limpiar_ax(self):
        self.editor_coeficientes.delete("1.0", "end")
        self.editor_vector.delete("1.0", "end")
        self._poner_texto(
            self.salida_ax,
            "Ingresa A y x para obtener el producto Ax."
        )


# =========================================================
# MÓDULO 3 REVISADO: ESPACIO DE TRABAJO MATRICIAL/VECTORIAL
# =========================================================

class AlgebraMatricialVectorialApp:
    """Calculadora libre de matrices, vectores y expresiones algebraicas."""

    MAX_DIMENSION = 15
    FUNCIONES = {"T", "det"}

    def __init__(self, ventana):
        self.ventana = ventana
        self.imagenes = []
        self.objetos = {}
        self.entradas_celdas = []
        self.estado = tk.StringVar(value="Listo para crear matrices y vectores.")

        self.modo_entrada = tk.StringVar(value="Celdas")
        self.tipo_objeto = tk.StringVar(value="Matriz")
        self.nombre_objeto = tk.StringVar(value="A")
        self.nombre_resultado_ecuaciones = tk.StringVar(value="b")
        self.filas = tk.IntVar(value=2)
        self.columnas = tk.IntVar(value=2)
        self.expresion = tk.StringVar(value="A(u+v)")
        self.formato_salida = tk.StringVar(value="Completa")
        self.nombre_matriz_resolver = tk.StringVar(value="A")
        self.nombre_vector_objetivo = tk.StringVar(value="b")

        self.ventana.title("Choco Lab - Ecuaciones matriciales y vectoriales")
        self.ventana.geometry("1280x800")
        self.ventana.minsize(980, 650)
        self.ventana.configure(bg=COLOR_FONDO)
        _activar_pantalla_completa(self.ventana)

        configurar_estilos()
        self._crear_interfaz()
        self._crear_celdas()
        self._cambiar_modo_entrada()
        self.cargar_ejemplo_distributivo()

    # -----------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # -----------------------------------------------------

    def _crear_interfaz(self):
        self.ventana.rowconfigure(1, weight=1)
        self.ventana.columnconfigure(0, weight=1)

        encabezado = tk.Frame(self.ventana, bg=COLOR_FONDO, height=82)
        encabezado.grid(row=0, column=0, sticky="ew", padx=22, pady=(7, 3))
        encabezado.grid_propagate(False)
        encabezado.columnconfigure(1, weight=1)

        logo = cargar_logo(self.imagenes, "chocolab.png", 135)
        if logo is not None:
            tk.Label(encabezado, image=logo, bg=COLOR_FONDO).grid(
                row=0, column=0, rowspan=2, sticky="w", padx=(0, 18)
            )

        tk.Label(
            encabezado,
            text="Ecuaciones matriciales y vectoriales",
            font=("Arial", 20, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_FONDO
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            encabezado,
            text=(
                "Crea datos por celdas o ecuaciones y escribe expresiones "
                "como A(u+v), Au+Av, Ax=b, AB o 3A."
            ),
            font=("Arial", 10),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).grid(row=1, column=1, sticky="w", pady=(3, 0))

        logo_fia = cargar_logo(self.imagenes, "logofia.png", 125)
        if logo_fia is not None:
            tk.Label(encabezado, image=logo_fia, bg=COLOR_FONDO).grid(
                row=0, column=2, rowspan=2, sticky="e", padx=(15, 0)
            )

        # El divisor horizontal se puede arrastrar para aumentar o reducir
        # el panel de resultados, tal como se solicitó.
        self.divisor = tk.PanedWindow(
            self.ventana,
            orient=tk.VERTICAL,
            bg=COLOR_CHOCOLATE_MEDIO,
            sashwidth=9,
            sashrelief="raised",
            opaqueresize=True,
            bd=0
        )
        self.divisor.grid(row=1, column=0, sticky="nsew", padx=22, pady=6)

        zona_trabajo = tk.Frame(self.divisor, bg=COLOR_FONDO)
        zona_resultado = tk.Frame(self.divisor, bg=COLOR_FONDO)
        self.divisor.add(zona_trabajo, minsize=265, stretch="always")
        self.divisor.add(zona_resultado, minsize=150, stretch="always")
        self.ventana.after(250, self._posicionar_divisor)

        zona_trabajo.rowconfigure(0, weight=1)
        zona_trabajo.columnconfigure(0, weight=3)
        zona_trabajo.columnconfigure(1, weight=2)

        self._crear_panel_datos(zona_trabajo)
        self._crear_panel_operacion(zona_trabajo)
        self._crear_panel_resultado(zona_resultado)

        tk.Label(
            self.ventana,
            textvariable=self.estado,
            font=("Arial", 9, "italic"),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_BEIGE,
            anchor="w",
            padx=14,
            pady=5
        ).grid(row=2, column=0, sticky="ew")

        self.pie = BarraInferiorChoco(
            self.ventana,
            fila=3,
            volver=lambda: self.ventana.event_generate("<<CerrarModulo>>")
        )

    def _posicionar_divisor(self):
        try:
            alto = self.divisor.winfo_height()
            if alto > 300:
                self.divisor.sash_place(0, 0, int(alto * 0.63))
        except tk.TclError:
            pass

    def _crear_panel_datos(self, padre):
        panel = ttk.LabelFrame(padre, text="1. Crear o editar datos")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        panel.rowconfigure(3, weight=1)
        panel.columnconfigure(0, weight=1)

        modos = tk.Frame(panel, bg=COLOR_FONDO)
        modos.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 3))

        tk.Label(
            modos, text="Entrada:", bg=COLOR_FONDO, fg=COLOR_CHOCOLATE,
            font=("Arial", 9, "bold")
        ).pack(side="left", padx=(0, 6))

        for texto in ("Celdas", "Ecuaciones"):
            ttk.Radiobutton(
                modos,
                text=texto,
                value=texto,
                variable=self.modo_entrada,
                command=self._cambiar_modo_entrada
            ).pack(side="left", padx=6)

        self.controles_celdas = tk.Frame(panel, bg=COLOR_FONDO)
        self.controles_celdas.grid(row=1, column=0, sticky="ew", padx=10, pady=3)

        tk.Label(
            self.controles_celdas, text="Tipo:", bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=0, padx=(0, 4), pady=3)
        selector_tipo = ttk.Combobox(
            self.controles_celdas,
            textvariable=self.tipo_objeto,
            values=("Matriz", "Vector"),
            state="readonly",
            width=9
        )
        selector_tipo.grid(row=0, column=1, padx=4, pady=3)
        selector_tipo.bind("<<ComboboxSelected>>", self._cambio_tipo)

        tk.Label(
            self.controles_celdas, text="Nombre:", bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=2, padx=(10, 4), pady=3)
        tk.Entry(
            self.controles_celdas,
            textvariable=self.nombre_objeto,
            width=8,
            font=("Consolas", 10),
            relief="solid",
            bd=1
        ).grid(row=0, column=3, padx=4, pady=3, ipady=2)

        tk.Label(
            self.controles_celdas, text="Filas:", bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=4, padx=(10, 3), pady=3)
        tk.Spinbox(
            self.controles_celdas,
            from_=1,
            to=self.MAX_DIMENSION,
            textvariable=self.filas,
            width=4,
            command=self._crear_celdas
        ).grid(row=0, column=5, padx=3, pady=3)

        tk.Label(
            self.controles_celdas, text="Columnas:", bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).grid(row=0, column=6, padx=(10, 3), pady=3)
        self.spin_columnas = tk.Spinbox(
            self.controles_celdas,
            from_=1,
            to=self.MAX_DIMENSION,
            textvariable=self.columnas,
            width=4,
            command=self._crear_celdas
        )
        self.spin_columnas.grid(row=0, column=7, padx=3, pady=3)

        tk.Button(
            self.controles_celdas,
            text="Aplicar tamaño",
            command=self._crear_celdas,
            bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=9,
            pady=4
        ).grid(row=0, column=8, padx=(10, 0), pady=3)

        self.marco_celdas = tk.Frame(panel, bg=COLOR_FONDO)
        self.marco_celdas.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.marco_celdas.rowconfigure(0, weight=1)
        self.marco_celdas.columnconfigure(0, weight=1)

        self.canvas_celdas = tk.Canvas(
            self.marco_celdas,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BEIGE,
            highlightthickness=1
        )
        self.canvas_celdas.grid(row=0, column=0, sticky="nsew")
        barra_y = ttk.Scrollbar(
            self.marco_celdas, orient="vertical", command=self.canvas_celdas.yview
        )
        barra_y.grid(row=0, column=1, sticky="ns")
        barra_x = ttk.Scrollbar(
            self.marco_celdas, orient="horizontal", command=self.canvas_celdas.xview
        )
        barra_x.grid(row=1, column=0, sticky="ew")
        self.canvas_celdas.configure(
            yscrollcommand=barra_y.set,
            xscrollcommand=barra_x.set
        )
        self.rejilla_celdas = tk.Frame(self.canvas_celdas, bg=COLOR_BLANCO)
        self.ventana_rejilla = self.canvas_celdas.create_window(
            (0, 0), window=self.rejilla_celdas, anchor="nw"
        )
        self.rejilla_celdas.bind(
            "<Configure>",
            lambda event: self.canvas_celdas.configure(
                scrollregion=self.canvas_celdas.bbox("all")
            )
        )

        self.marco_ecuaciones = ttk.LabelFrame(
            panel, text="Sistema lineal que se convertirá en A y b"
        )
        self.marco_ecuaciones.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.marco_ecuaciones.rowconfigure(1, weight=1)
        self.marco_ecuaciones.columnconfigure(0, weight=1)

        nombres = tk.Frame(self.marco_ecuaciones, bg=COLOR_FONDO)
        nombres.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        tk.Label(
            nombres, text="Matriz:", bg=COLOR_FONDO, fg=COLOR_CHOCOLATE
        ).pack(side="left")
        tk.Entry(
            nombres, textvariable=self.nombre_objeto, width=7,
            font=("Consolas", 10), relief="solid", bd=1
        ).pack(side="left", padx=(4, 12))
        tk.Label(
            nombres, text="Vector independiente:", bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE
        ).pack(side="left")
        tk.Entry(
            nombres, textvariable=self.nombre_resultado_ecuaciones, width=7,
            font=("Consolas", 10), relief="solid", bd=1
        ).pack(side="left", padx=4)

        self.editor_ecuaciones = tk.Text(
            self.marco_ecuaciones,
            height=8,
            wrap="none",
            font=("Consolas", 10),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            relief="solid",
            bd=1,
            padx=8,
            pady=7,
            undo=True
        )
        self.editor_ecuaciones.grid(
            row=1, column=0, sticky="nsew", padx=8, pady=(3, 4)
        )
        self.editor_ecuaciones.insert(
            "1.0",
            "1x + 2y - 3z = 9\n2x - y + 4z = 7\n-x + 3y + z = 2"
        )
        tk.Label(
            self.marco_ecuaciones,
            text=(
                "Una ecuación por línea. Se aceptan x, y, z; x1, x2, x3; "
                "o nombres como f y g12."
            ),
            font=("Arial", 8, "italic"),
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE_MEDIO,
            anchor="w"
        ).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))

        botones = tk.Frame(panel, bg=COLOR_FONDO)
        botones.grid(row=4, column=0, sticky="ew", padx=10, pady=(4, 9))
        tk.Button(
            botones,
            text="Guardar datos",
            command=self.guardar_desde_entrada,
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=6
        ).pack(side="left")
        tk.Button(
            botones,
            text="Vaciar entrada",
            command=self.vaciar_entrada,
            bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=12,
            pady=6
        ).pack(side="left", padx=7)

    def _crear_panel_operacion(self, padre):
        panel = ttk.LabelFrame(padre, text="2. Datos guardados y operación")
        panel.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        # Las pestañas dejan la evaluación libre y la resolución del sistema
        # accesibles sin reducir el espacio para ingresar los datos.
        self.cuaderno_operacion = ttk.Notebook(panel)
        self.cuaderno_operacion.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        expresiones = tk.Frame(self.cuaderno_operacion, bg=COLOR_FONDO)
        self.pestana_resolver = tk.Frame(self.cuaderno_operacion, bg=COLOR_FONDO)
        self.cuaderno_operacion.add(expresiones, text="Operaciones libres")
        self.cuaderno_operacion.add(self.pestana_resolver, text="Resolver Ax=b")
        expresiones.rowconfigure(0, weight=1)
        expresiones.columnconfigure(0, weight=1)
        self._crear_panel_resolver(self.pestana_resolver)

        self.arbol = ttk.Treeview(
            expresiones,
            columns=("tipo", "dimension"),
            show="tree headings",
            height=6,
            selectmode="browse"
        )
        self.arbol.heading("#0", text="Nombre")
        self.arbol.heading("tipo", text="Tipo")
        self.arbol.heading("dimension", text="Dimensión")
        self.arbol.column("#0", width=90, stretch=True)
        self.arbol.column("tipo", width=80, anchor="center")
        self.arbol.column("dimension", width=90, anchor="center")
        self.arbol.grid(row=0, column=0, sticky="nsew", padx=10, pady=(9, 2))
        self.arbol.bind("<Double-1>", lambda event: self.cargar_seleccion())

        acciones_objetos = tk.Frame(expresiones, bg=COLOR_FONDO)
        acciones_objetos.grid(row=1, column=0, sticky="ew", padx=10, pady=3)
        tk.Button(
            acciones_objetos, text="Editar seleccionado",
            command=self.cargar_seleccion, bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE, relief="flat", padx=9, pady=4
        ).pack(side="left")
        tk.Button(
            acciones_objetos, text="Eliminar",
            command=self.eliminar_seleccion, bg=COLOR_BEIGE,
            fg=COLOR_ERROR, relief="flat", padx=9, pady=4
        ).pack(side="left", padx=6)
        tk.Button(
            acciones_objetos, text="Ejemplo A(u+v)",
            command=self.cargar_ejemplo_distributivo, bg=COLOR_RESALTADO,
            fg=COLOR_CHOCOLATE, relief="flat", padx=9, pady=4
        ).pack(side="right")

        expresion_marco = ttk.LabelFrame(expresiones, text="Expresión libre")
        expresion_marco.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 4))
        expresion_marco.columnconfigure(0, weight=1)

        entrada_expresion = tk.Entry(
            expresion_marco,
            textvariable=self.expresion,
            font=("Consolas", 13, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_BLANCO,
            relief="solid",
            bd=1
        )
        entrada_expresion.grid(row=0, column=0, sticky="ew", padx=8, pady=8, ipady=5)
        entrada_expresion.bind("<Return>", lambda event: self.calcular())

        ejemplos = tk.Frame(expresion_marco, bg=COLOR_FONDO)
        ejemplos.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 5))
        for texto in ("A(u+v)", "Au+Av", "Ax=b", "A+B", "AB", "3A", "T(A)", "det(A)"):
            tk.Button(
                ejemplos,
                text=texto,
                command=lambda valor=texto: self.expresion.set(valor),
                bg=COLOR_BLANCO,
                fg=COLOR_CHOCOLATE,
                relief="groove",
                font=("Consolas", 8),
                padx=5,
                pady=2
            ).pack(side="left", padx=2, pady=2)

        formato = tk.Frame(expresiones, bg=COLOR_FONDO)
        formato.grid(row=3, column=0, sticky="ew", padx=10, pady=4)
        tk.Label(
            formato, text="Mostrar:", bg=COLOR_FONDO, fg=COLOR_CHOCOLATE,
            font=("Arial", 9, "bold")
        ).pack(side="left")
        for texto in ("Completa", "Matrices", "Ecuaciones"):
            ttk.Radiobutton(
                formato,
                text=texto,
                value=texto,
                variable=self.formato_salida
            ).pack(side="left", padx=5)

        botones = tk.Frame(expresiones, bg=COLOR_FONDO)
        botones.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 9))
        tk.Button(
            botones,
            text="Calcular y explicar",
            command=self.calcular,
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=16,
            pady=7
        ).pack(side="left")
        tk.Button(
            botones,
            text="Limpiar resultado",
            command=lambda: self._mostrar_resultado(self._ayuda_inicial()),
            bg=COLOR_BEIGE,
            fg=COLOR_CHOCOLATE,
            relief="flat",
            padx=12,
            pady=7
        ).pack(side="left", padx=7)

        tk.Label(
            expresiones,
            text=(
                "Multiplicación implícita: A(u+v), Au, AB y 3A. "
                "También puedes escribir * o ×."
            ),
            font=("Arial", 8, "italic"),
            bg=COLOR_FONDO,
            fg=COLOR_CHOCOLATE_MEDIO,
            justify="left",
            wraplength=430
        ).grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 8))

    def _crear_panel_resolver(self, panel):
        """Presenta Ax=b y pertenencia al espacio generado como dos tareas claras."""

        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        ecuacion = ttk.LabelFrame(panel, text="Resolver la ecuación matricial Ax = b")
        ecuacion.grid(row=0, column=0, sticky="ew", padx=10, pady=(9, 6))
        ecuacion.columnconfigure(1, weight=1)

        tk.Label(
            ecuacion, text="Matriz A:", bg=COLOR_FONDO, fg=COLOR_CHOCOLATE
        ).grid(row=0, column=0, sticky="w", padx=9, pady=6)
        self.selector_matriz = ttk.Combobox(
            ecuacion, textvariable=self.nombre_matriz_resolver, state="readonly"
        )
        self.selector_matriz.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(
            ecuacion, text="Vector b:", bg=COLOR_FONDO, fg=COLOR_CHOCOLATE
        ).grid(row=1, column=0, sticky="w", padx=9, pady=6)
        self.selector_objetivo = ttk.Combobox(
            ecuacion, textvariable=self.nombre_vector_objetivo, state="readonly"
        )
        self.selector_objetivo.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        tk.Button(
            ecuacion, text="Encontrar x",
            command=self.resolver_axb,
            bg=COLOR_CHOCOLATE, fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat", font=("Arial", 10, "bold"), padx=14, pady=6
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=9, pady=(6, 9))

        combinacion = ttk.LabelFrame(
            panel, text="¿Se puede escribir b como combinación lineal?"
        )
        combinacion.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 9))
        combinacion.columnconfigure(0, weight=1)
        combinacion.rowconfigure(1, weight=1)

        tk.Label(
            combinacion,
            text="Selecciona los vectores que generarán b (Ctrl+clic para elegir varios):",
            bg=COLOR_FONDO, fg=COLOR_CHOCOLATE,
            font=("Arial", 9), anchor="w", wraplength=430
        ).grid(row=0, column=0, sticky="ew", padx=9, pady=(7, 2))

        lista = tk.Frame(combinacion, bg=COLOR_FONDO)
        lista.grid(row=1, column=0, sticky="nsew", padx=9, pady=3)
        lista.rowconfigure(0, weight=1)
        lista.columnconfigure(0, weight=1)
        self.lista_vectores = tk.Listbox(
            lista, selectmode="extended", exportselection=False,
            height=5, font=("Consolas", 10),
            bg=COLOR_BLANCO, fg=COLOR_CHOCOLATE
        )
        self.lista_vectores.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(lista, orient="vertical", command=self.lista_vectores.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self.lista_vectores.configure(yscrollcommand=barra.set)

        tk.Button(
            combinacion, text="Encontrar los pesos",
            command=self.resolver_combinacion,
            bg=COLOR_CHOCOLATE, fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat", font=("Arial", 10, "bold"), padx=14, pady=6
        ).grid(row=2, column=0, sticky="w", padx=9, pady=(5, 9))
        tk.Button(
            combinacion, text="Cargar ejemplo",
            command=self.cargar_ejemplo_combinacion,
            bg=COLOR_RESALTADO, fg=COLOR_CHOCOLATE,
            relief="flat", padx=9, pady=5
        ).grid(row=2, column=0, sticky="e", padx=9, pady=(5, 9))

    def _crear_panel_resultado(self, padre):
        padre.rowconfigure(0, weight=1)
        padre.columnconfigure(0, weight=1)
        marco = ttk.LabelFrame(
            padre,
            text="3. Resultado, desarrollo e interpretación (arrastra la barra café para cambiar el tamaño)"
        )
        marco.grid(row=0, column=0, sticky="nsew")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        self.salida = tk.Text(
            marco,
            wrap="none",
            font=("Consolas", 10),
            bg=COLOR_BLANCO,
            fg=COLOR_CHOCOLATE,
            relief="solid",
            bd=1,
            padx=14,
            pady=10,
            state="disabled"
        )
        self.salida.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        barra_y = ttk.Scrollbar(marco, orient="vertical", command=self.salida.yview)
        barra_y.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=(8, 0))
        barra_x = ttk.Scrollbar(marco, orient="horizontal", command=self.salida.xview)
        barra_x.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))
        self.salida.configure(
            yscrollcommand=barra_y.set,
            xscrollcommand=barra_x.set
        )
        self._mostrar_resultado(self._ayuda_inicial())

    # -----------------------------------------------------
    # EDICIÓN Y ALMACENAMIENTO DE DATOS
    # -----------------------------------------------------

    def _cambio_tipo(self, event=None):
        if self.tipo_objeto.get() == "Vector":
            if self.nombre_objeto.get() == "A":
                siguiente = next(
                    (nombre for nombre in ("u", "v", "w", "x", "b")
                     if nombre not in self.objetos),
                    f"v{len(self.objetos) + 1}"
                )
                self.nombre_objeto.set(siguiente)
            self.columnas.set(1)
            self.spin_columnas.configure(state="disabled")
        else:
            if self.nombre_objeto.get() in ("u", "v", "w"):
                self.nombre_objeto.set(
                    next(
                        (nombre for nombre in ("A", "B", "C")
                         if nombre not in self.objetos),
                        f"M{len(self.objetos) + 1}"
                    )
                )
            self.spin_columnas.configure(state="normal")
        self._crear_celdas()

    def _cambiar_modo_entrada(self):
        if self.modo_entrada.get() == "Celdas":
            self.controles_celdas.grid()
            self.marco_celdas.grid()
            self.marco_ecuaciones.grid_remove()
        else:
            self.controles_celdas.grid_remove()
            self.marco_celdas.grid_remove()
            self.marco_ecuaciones.grid()

    def _crear_celdas(self, valores=None):
        try:
            filas = int(self.filas.get())
            columnas = int(self.columnas.get())
        except (ValueError, tk.TclError):
            return

        filas = max(1, min(self.MAX_DIMENSION, filas))
        columnas = max(1, min(self.MAX_DIMENSION, columnas))
        if self.tipo_objeto.get() == "Vector":
            columnas = 1
            self.columnas.set(1)

        anteriores = []
        for fila in self.entradas_celdas:
            anteriores.append([entrada.get() for entrada in fila])

        for widget in self.rejilla_celdas.winfo_children():
            widget.destroy()
        self.entradas_celdas = []

        for j in range(columnas):
            tk.Label(
                self.rejilla_celdas,
                text=f"C{j + 1}",
                font=("Arial", 8, "bold"),
                fg=COLOR_CHOCOLATE_MEDIO,
                bg=COLOR_BLANCO
            ).grid(row=0, column=j + 1, padx=3, pady=3)

        fuente = valores if valores is not None else anteriores
        for i in range(filas):
            tk.Label(
                self.rejilla_celdas,
                text=f"F{i + 1}",
                font=("Arial", 8, "bold"),
                fg=COLOR_CHOCOLATE_MEDIO,
                bg=COLOR_BLANCO
            ).grid(row=i + 1, column=0, padx=5, pady=3)
            fila_entradas = []
            for j in range(columnas):
                entrada = tk.Entry(
                    self.rejilla_celdas,
                    width=9,
                    justify="center",
                    font=("Consolas", 10),
                    fg=COLOR_CHOCOLATE,
                    bg=COLOR_BLANCO,
                    relief="solid",
                    bd=1
                )
                entrada.grid(row=i + 1, column=j + 1, padx=3, pady=3, ipady=3)
                valor = "0"
                if i < len(fuente) and j < len(fuente[i]):
                    valor_fuente = fuente[i][j]
                    valor = (
                        _texto_numero(valor_fuente)
                        if isinstance(valor_fuente, Fraction)
                        else str(valor_fuente)
                    )
                entrada.insert(0, valor)
                fila_entradas.append(entrada)
            self.entradas_celdas.append(fila_entradas)

    def _validar_nombre(self, nombre):
        nombre = nombre.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", nombre):
            raise ValueError(
                "El nombre debe comenzar con una letra y continuar solo con letras, números o _."
            )
        if nombre in self.FUNCIONES:
            raise ValueError(f"«{nombre}» está reservado como función.")
        return nombre

    def guardar_desde_entrada(self):
        try:
            if self.modo_entrada.get() == "Ecuaciones":
                self._guardar_sistema_ecuaciones()
            else:
                self._guardar_celdas()
        except (ValueError, TypeError) as error:
            messagebox.showerror(
                "No se pudieron guardar los datos",
                f"Choco dice: {error}",
                parent=self.ventana
            )

    def _guardar_celdas(self):
        nombre = self._validar_nombre(self.nombre_objeto.get())
        matriz = []
        for i, fila in enumerate(self.entradas_celdas, start=1):
            nueva_fila = []
            for j, entrada in enumerate(fila, start=1):
                try:
                    nueva_fila.append(_leer_numero(entrada.get()))
                except ValueError as error:
                    raise ValueError(f"Celda F{i}, C{j}: {error}") from None
            matriz.append(nueva_fila)

        tipo = "Vector" if len(matriz[0]) == 1 else "Matriz"
        self._guardar_objeto(nombre, matriz, tipo)
        self.estado.set(
            f"Choco dice: {nombre} se guardó como {tipo.lower()} de dimensión "
            f"{len(matriz)}×{len(matriz[0])}."
        )

    def _guardar_sistema_ecuaciones(self):
        nombre_a = self._validar_nombre(self.nombre_objeto.get())
        nombre_b = self._validar_nombre(self.nombre_resultado_ecuaciones.get())
        if nombre_a == nombre_b:
            raise ValueError("La matriz y el vector independiente necesitan nombres distintos.")

        ecuaciones = [
            linea.strip()
            for linea in self.editor_ecuaciones.get("1.0", "end").splitlines()
            if linea.strip()
        ]
        if not ecuaciones:
            raise ValueError("Escribe al menos una ecuación.")

        try:
            from sistemas_eliminacion import extraer_variables, convertir_sistema_ecuaciones
        except ImportError as error:
            raise ValueError(
                "No se encontró sistemas_eliminacion.py en la misma carpeta."
            ) from error

        variables = []
        for ecuacion in ecuaciones:
            for variable in extraer_variables(ecuacion):
                if variable not in variables:
                    variables.append(variable)
        if not variables:
            raise ValueError("No se encontraron variables en las ecuaciones.")

        aumentada, orden = convertir_sistema_ecuaciones(ecuaciones, len(variables))
        matriz_a = [
            [Fraction(str(valor)).limit_denominator(1000000) for valor in fila[:-1]]
            for fila in aumentada
        ]
        vector_b = [
            [Fraction(str(fila[-1])).limit_denominator(1000000)]
            for fila in aumentada
        ]
        self._guardar_objeto(nombre_a, matriz_a, "Matriz", variables=orden)
        self._guardar_objeto(nombre_b, vector_b, "Vector")
        self.expresion.set(f"{nombre_a}x={nombre_b}")
        self.nombre_matriz_resolver.set(nombre_a)
        self.nombre_vector_objetivo.set(nombre_b)
        self.cuaderno_operacion.select(self.pestana_resolver)
        self.estado.set(
            f"Choco dice: el sistema creó {nombre_a} y {nombre_b}. "
            f"Orden de variables: {', '.join(orden)}. Presiona «Encontrar x»."
        )

    def _guardar_objeto(self, nombre, valor, tipo, variables=None):
        self.objetos[nombre] = {
            "valor": [fila[:] for fila in valor],
            "tipo": tipo,
            "variables": list(variables or [])
        }
        self._actualizar_arbol()

    def _actualizar_arbol(self):
        """Sincroniza el inventario de datos con los selectores de solución."""

        for item in self.arbol.get_children():
            self.arbol.delete(item)
        for nombre, datos in self.objetos.items():
            valor = datos["valor"]
            self.arbol.insert(
                "",
                "end",
                iid=nombre,
                text=nombre,
                values=(datos["tipo"], f"{len(valor)}×{len(valor[0])}")
            )

        # Un vector columna es también una matriz m×1, así que puede ser A
        # en un sistema con una sola incógnita.
        matrices = list(self.objetos)
        vectores = [
            nombre for nombre, datos in self.objetos.items()
            if datos["tipo"] == "Vector"
        ]
        self.selector_matriz.configure(values=matrices)
        self.selector_objetivo.configure(values=vectores)
        if self.nombre_matriz_resolver.get() not in matrices:
            self.nombre_matriz_resolver.set(matrices[0] if matrices else "")
        if self.nombre_vector_objetivo.get() not in vectores:
            self.nombre_vector_objetivo.set(vectores[0] if vectores else "")

        seleccionados = {
            self.lista_vectores.get(indice)
            for indice in self.lista_vectores.curselection()
        }
        self.lista_vectores.delete(0, "end")
        for indice, nombre in enumerate(vectores):
            self.lista_vectores.insert("end", nombre)
            if nombre in seleccionados:
                self.lista_vectores.selection_set(indice)

    def cargar_seleccion(self):
        seleccion = self.arbol.selection()
        if not seleccion:
            messagebox.showinfo(
                "Selecciona un dato",
                "Elige una matriz o vector de la lista para editarlo.",
                parent=self.ventana
            )
            return
        nombre = seleccion[0]
        datos = self.objetos[nombre]
        valor = datos["valor"]
        self.modo_entrada.set("Celdas")
        self._cambiar_modo_entrada()
        self.nombre_objeto.set(nombre)
        self.tipo_objeto.set(datos["tipo"])
        self.filas.set(len(valor))
        self.columnas.set(len(valor[0]))
        self.spin_columnas.configure(
            state="disabled" if datos["tipo"] == "Vector" else "normal"
        )
        self._crear_celdas(valor)
        self.estado.set(f"Editando {nombre}. Guarda los datos para aplicar los cambios.")

    def eliminar_seleccion(self):
        seleccion = self.arbol.selection()
        if not seleccion:
            return
        nombre = seleccion[0]
        del self.objetos[nombre]
        self._actualizar_arbol()
        self.estado.set(f"Choco dice: se eliminó {nombre}.")

    def vaciar_entrada(self):
        if self.modo_entrada.get() == "Ecuaciones":
            self.editor_ecuaciones.delete("1.0", "end")
        else:
            for fila in self.entradas_celdas:
                for entrada in fila:
                    entrada.delete(0, "end")
                    entrada.insert(0, "0")

    def cargar_ejemplo_distributivo(self):
        # Ejercicio de la presentación Ecuación Matricial:
        # A=[[2,5],[3,1]], u=[4,-1] y v=[-3,5].
        self._guardar_objeto(
            "A",
            [[Fraction(2), Fraction(5)], [Fraction(3), Fraction(1)]],
            "Matriz"
        )
        self._guardar_objeto("u", [[Fraction(4)], [Fraction(-1)]], "Vector")
        self._guardar_objeto("v", [[Fraction(-3)], [Fraction(5)]], "Vector")
        self.expresion.set("A(u+v)")
        self.estado.set(
            "Ejemplo cargado. Presiona «Calcular y explicar» para comparar A(u+v) con Au+Av."
        )

    def cargar_ejemplo_combinacion(self):
        """Prepara el ejercicio de combinación lineal de la presentación."""

        a1 = [[Fraction(1)], [Fraction(-2)], [Fraction(-5)]]
        a2 = [[Fraction(2)], [Fraction(5)], [Fraction(6)]]
        b = [[Fraction(7)], [Fraction(4)], [Fraction(-3)]]
        self._guardar_objeto("a1", a1, "Vector")
        self._guardar_objeto("a2", a2, "Vector")
        self._guardar_objeto("b", b, "Vector")
        self._guardar_objeto("M", [[a1[i][0], a2[i][0]] for i in range(3)], "Matriz")
        self.nombre_matriz_resolver.set("M")
        self.nombre_vector_objetivo.set("b")
        self.lista_vectores.selection_clear(0, "end")
        for indice in range(self.lista_vectores.size()):
            if self.lista_vectores.get(indice) in ("a1", "a2"):
                self.lista_vectores.selection_set(indice)
        self.cuaderno_operacion.select(self.pestana_resolver)
        self.estado.set(
            "Ejemplo listo: b = 3a1 + 2a2. Pulsa «Encontrar los pesos» "
            "o resuelve Mx=b."
        )

    # -----------------------------------------------------
    # ANALIZADOR SEGURO DE EXPRESIONES
    # -----------------------------------------------------

    def _segmentar_nombre(self, token):
        if token in self.objetos or token in self.FUNCIONES:
            return [token]
        nombres = sorted(self.objetos, key=len, reverse=True)
        memoria = {}

        def buscar(posicion):
            if posicion == len(token):
                return []
            if posicion in memoria:
                return memoria[posicion]
            for nombre in nombres:
                if token.startswith(nombre, posicion):
                    resto = buscar(posicion + len(nombre))
                    if resto is not None:
                        memoria[posicion] = [nombre] + resto
                        return memoria[posicion]
            memoria[posicion] = None
            return None

        partes = buscar(0)
        return partes if partes and len(partes) > 1 else [token]

    def _normalizar_expresion(self, texto):
        texto = texto.strip()
        if not texto:
            raise ValueError("Escribe una expresión, por ejemplo A(u+v).")
        texto = (
            texto.replace("−", "-")
            .replace("–", "-")
            .replace("×", "*")
            .replace("·", "*")
        )
        texto = re.sub(
            r"\b([A-Za-z][A-Za-z0-9_]*)\s*(?:\^T|ᵀ)",
            r"T(\1)",
            texto
        )

        patron = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)|[A-Za-z_][A-Za-z0-9_]*|[()+\-*/=]")
        tokens = patron.findall(texto)
        resto = patron.sub("", texto)
        if resto.strip():
            raise ValueError(f"La expresión contiene símbolos no admitidos: {resto.strip()}")

        expandidos = []
        for token in tokens:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
                expandidos.extend(self._segmentar_nombre(token))
            else:
                expandidos.append(token)

        resultado = []
        for token in expandidos:
            if resultado:
                anterior = resultado[-1]
                termina = (
                    anterior == ")"
                    or re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)", anterior)
                    or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", anterior)
                )
                comienza = (
                    token == "("
                    or re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)", token)
                    or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token)
                )
                es_funcion = anterior in self.FUNCIONES and token == "("
                if termina and comienza and not es_funcion:
                    resultado.append("*")
            resultado.append(token)
        return "".join(resultado)

    def _analizar_lado(self, texto):
        normalizada = self._normalizar_expresion(texto)
        if "=" in normalizada:
            raise ValueError("Cada lado de la igualdad debe ser una expresión independiente.")
        try:
            return ast.parse(normalizada, mode="eval").body, normalizada
        except SyntaxError:
            raise ValueError(
                "La expresión no está completa. Revisa operadores y paréntesis."
            ) from None

    @staticmethod
    def _es_matriz(valor):
        return isinstance(valor, list)

    @staticmethod
    def _copiar_valor(valor):
        if isinstance(valor, list):
            return [fila[:] for fila in valor]
        return Fraction(valor)

    def _etiqueta_nodo(self, nodo):
        if isinstance(nodo, ast.Name):
            return nodo.id
        if isinstance(nodo, ast.Constant):
            return str(nodo.value)
        if isinstance(nodo, ast.UnaryOp):
            signo = "−" if isinstance(nodo.op, ast.USub) else "+"
            return signo + self._etiqueta_nodo(nodo.operand)
        if isinstance(nodo, ast.BinOp):
            simbolo = {
                ast.Add: "+", ast.Sub: "−", ast.Mult: "·", ast.Div: "÷"
            }.get(type(nodo.op), "?")
            return f"({self._etiqueta_nodo(nodo.left)} {simbolo} {self._etiqueta_nodo(nodo.right)})"
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            return f"{nodo.func.id}({self._etiqueta_nodo(nodo.args[0])})"
        return "resultado"

    def _evaluar(self, nodo, pasos):
        if isinstance(nodo, ast.Name):
            if nodo.id not in self.objetos:
                disponibles = ", ".join(self.objetos) or "ninguno"
                raise ValueError(
                    f"No existe un dato llamado «{nodo.id}». Datos guardados: {disponibles}."
                )
            return self._copiar_valor(self.objetos[nodo.id]["valor"])

        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
            return Fraction(str(nodo.value))

        if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
            valor = self._evaluar(nodo.operand, pasos)
            if isinstance(nodo.op, ast.UAdd):
                return valor
            return self._multiplicar_valores(
                Fraction(-1), valor, pasos, "−1", self._etiqueta_nodo(nodo.operand)
            )

        if isinstance(nodo, ast.BinOp):
            izquierdo = self._evaluar(nodo.left, pasos)
            derecho = self._evaluar(nodo.right, pasos)
            ei = self._etiqueta_nodo(nodo.left)
            ed = self._etiqueta_nodo(nodo.right)
            if isinstance(nodo.op, ast.Add):
                return self._sumar_valores(izquierdo, derecho, pasos, ei, ed, 1)
            if isinstance(nodo.op, ast.Sub):
                return self._sumar_valores(izquierdo, derecho, pasos, ei, ed, -1)
            if isinstance(nodo.op, ast.Mult):
                return self._multiplicar_valores(izquierdo, derecho, pasos, ei, ed)
            if isinstance(nodo.op, ast.Div):
                return self._dividir_valores(izquierdo, derecho, pasos, ei, ed)
            raise ValueError("Ese operador no está permitido.")

        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            if len(nodo.args) != 1 or nodo.keywords:
                raise ValueError("T(...) y det(...) reciben exactamente un dato.")
            nombre = nodo.func.id
            valor = self._evaluar(nodo.args[0], pasos)
            etiqueta = self._etiqueta_nodo(nodo.args[0])
            if not self._es_matriz(valor):
                raise ValueError(f"{nombre}(...) requiere una matriz o vector.")
            if nombre == "T":
                resultado = _transponer(valor)
                pasos.append({
                    "tipo": "transpuesta", "a": valor, "r": resultado,
                    "ea": etiqueta
                })
                return resultado
            if nombre == "det":
                resultado, pasos_det = _determinante_con_pasos(valor)
                pasos.append({
                    "tipo": "determinante", "a": valor, "r": resultado,
                    "ea": etiqueta, "detalle": pasos_det
                })
                return resultado
            raise ValueError("Solo se admiten las funciones T(...) y det(...).")

        raise ValueError("La expresión contiene una construcción no permitida.")

    def _sumar_valores(self, a, b, pasos, ea, eb, signo):
        simbolo = "+" if signo == 1 else "−"
        if self._es_matriz(a) and self._es_matriz(b):
            resultado = _sumar_matrices(a, b, signo=signo)
            pasos.append({
                "tipo": "suma", "a": a, "b": b, "r": resultado,
                "ea": ea, "eb": eb, "simbolo": simbolo
            })
            return resultado
        if not self._es_matriz(a) and not self._es_matriz(b):
            resultado = a + signo * b
            pasos.append({
                "tipo": "escalar_suma", "a": a, "b": b, "r": resultado,
                "ea": ea, "eb": eb, "simbolo": simbolo
            })
            return resultado
        raise ValueError("No se puede sumar o restar un escalar con una matriz o vector.")

    def _multiplicar_valores(self, a, b, pasos, ea, eb):
        if self._es_matriz(a) and self._es_matriz(b):
            fa, ca = _dimensiones(a)
            fb, cb = _dimensiones(b)
            if ca != fb:
                raise ValueError(
                    f"No se puede multiplicar {ea} ({fa}×{ca}) por {eb} ({fb}×{cb}). "
                    f"Deben coincidir las dimensiones internas: {ca} = {fb}."
                )
            resultado = _multiplicar_matrices(a, b)
            pasos.append({
                "tipo": "producto", "a": a, "b": b, "r": resultado,
                "ea": ea, "eb": eb
            })
            return resultado
        if self._es_matriz(a) and not self._es_matriz(b):
            resultado = [[b * valor for valor in fila] for fila in a]
            pasos.append({
                "tipo": "escalar", "a": b, "b": a, "r": resultado,
                "ea": eb, "eb": ea
            })
            return resultado
        if not self._es_matriz(a) and self._es_matriz(b):
            resultado = [[a * valor for valor in fila] for fila in b]
            pasos.append({
                "tipo": "escalar", "a": a, "b": b, "r": resultado,
                "ea": ea, "eb": eb
            })
            return resultado
        resultado = a * b
        pasos.append({
            "tipo": "escalar_producto", "a": a, "b": b, "r": resultado,
            "ea": ea, "eb": eb
        })
        return resultado

    def _dividir_valores(self, a, b, pasos, ea, eb):
        if self._es_matriz(b):
            raise ValueError("La división entre matrices o vectores no está definida aquí.")
        if b == 0:
            raise ValueError("No se puede dividir entre cero.")
        if self._es_matriz(a):
            resultado = [[valor / b for valor in fila] for fila in a]
        else:
            resultado = a / b
        pasos.append({
            "tipo": "division", "a": a, "b": b, "r": resultado,
            "ea": ea, "eb": eb
        })
        return resultado

    # -----------------------------------------------------
    # ECUACIONES MATRICIALES Y COMBINACIONES LINEALES
    # -----------------------------------------------------

    @staticmethod
    def _numero_de_eliminacion(valor):
        """Presenta el resultado numérico de Gauss como fracción legible."""

        if abs(valor) < 1e-10:
            return "0"
        candidato = Fraction(float(valor)).limit_denominator(100000)
        if abs(float(candidato) - valor) <= 1e-9 * max(1, abs(valor)):
            return _texto_numero(candidato)
        return f"{valor:.8g}"

    def _texto_matriz_eliminacion(self, matriz):
        """Da formato a las matrices calculadas por el eliminador anterior."""

        return "\n".join(
            "[ " + "  ".join(self._numero_de_eliminacion(valor) for valor in fila) + " ]"
            for fila in matriz
        )

    def _texto_aumentada(self, a, b):
        """Coloca la columna b tras A para ver el sistema [A|b]."""

        filas = []
        for fila_a, fila_b in zip(a, b):
            numeros = "  ".join(_texto_numero(valor) for valor in fila_a)
            filas.append(f"[ {numeros}  |  {_texto_numero(fila_b[0])} ]")
        return "\n".join(filas)

    def _datos_sistema(self, nombre_a, nombre_b):
        """Obtiene y valida A de m×n y b de m×1."""

        if nombre_a not in self.objetos:
            raise ValueError("Primero guarda una matriz A por celdas o ecuaciones.")
        if nombre_b not in self.objetos:
            raise ValueError("Primero guarda el vector b como una matriz de una columna.")
        a = self.objetos[nombre_a]["valor"]
        b = self.objetos[nombre_b]["valor"]
        if len(b[0]) != 1:
            raise ValueError(f"{nombre_b} debe ser un vector columna (m×1).")
        if len(a) != len(b):
            raise ValueError(
                f"{nombre_a} tiene {len(a)} filas y {nombre_b} tiene {len(b)} entradas. "
                "Para Ax=b deben coincidir."
            )
        return a, b

    def _resolver_datos(self, a, b, nombres, titulo, combinacion=False, variable="x"):
        """Usa resolver_sistema([A|b]) para hallar pesos o incógnitas."""

        from sistemas_eliminacion import resolver_sistema

        if not a or not a[0] or len(b) != len(a) or any(len(fila) != 1 for fila in b):
            raise ValueError("A debe tener columnas y b debe tener una entrada por fila de A.")
        columnas = len(a[0])
        if len(nombres) != columnas:
            raise ValueError("Se requiere un nombre por columna de A.")

        # El eliminador existente utiliza tolerancia 1e-10 y números reales.
        # Las entradas originales siguen siendo Fraction para presentarlas sin redondeo.
        aumentada = [
            [float(valor) for valor in fila_a] + [float(fila_b[0])]
            for fila_a, fila_b in zip(a, b)
        ]
        resultado = resolver_sistema(aumentada, columnas)
        clasificacion = resultado["clasificacion"]

        lineas = [
            titulo.upper(),
            "=" * 68,
            f"A tiene {len(a)} filas y {columnas} columnas. "
            f"b tiene {len(b)} entradas.",
            "A =", _texto_matriz(a), "",
            "b =", _texto_matriz(b), "",
            "SISTEMA EQUIVALENTE",
            "=" * 68,
            f"{variable} tiene {columnas} componentes.",
            "[A | b] =", self._texto_aumentada(a, b), ""
        ]

        etiquetas = (
            [f"c{j + 1}" for j in range(columnas)] if combinacion else nombres
        )

        if combinacion:
            lineas.extend([
                "Las columnas elegidas forman A. Los valores de c son sus pesos:",
                " + ".join(f"c{j + 1}·{nombres[j]}" for j in range(columnas))
                + " = b",
                ""
            ])

        lineas.extend([
            "ELIMINACIÓN POR FILAS (PROGRAMA ANTERIOR)",
            "=" * 68
        ])
        if resultado["pasos"]:
            for indice, paso in enumerate(resultado["pasos"], start=1):
                fase = "Gauss" if paso["fase"] == "escalonamiento" else "Gauss-Jordan"
                lineas.extend([
                    f"Paso {indice} · {fase}: {paso['operacion']}",
                    self._texto_matriz_eliminacion(paso["matriz"]),
                    ""
                ])
        else:
            lineas.append("La matriz ya estaba escalonada; no hicieron falta operaciones.")

        lineas.extend([
            "FORMA ESCALONADA:",
            self._texto_matriz_eliminacion(resultado["matriz_escalonada"]),
            "",
            "RESULTADO",
            "=" * 68
        ])

        if clasificacion == "inconsistente":
            fila = resultado["fila_inconsistente"]
            termino = resultado["matriz_escalonada"][fila][-1]
            lineas.extend([
                f"Fila {fila + 1}: 0 = {self._numero_de_eliminacion(termino)}.",
                "El sistema no tiene solución.",
                (
                    "Por tanto, b NO es combinación lineal de los vectores elegidos."
                    if combinacion else "No existe un vector x que cumpla Ax=b."
                )
            ])
            return "\n".join(lineas)

        reducida = resultado["matriz_reducida"]
        lineas.extend([
            "FORMA ESCALONADA REDUCIDA:",
            self._texto_matriz_eliminacion(reducida), ""
        ])

        if clasificacion == "unica":
            pesos = resultado["solucion"]
            lineas.extend([
                "Solución única:",
                *(
                    f"{etiquetas[j]}" + (
                        f" (peso de {nombres[j]})" if combinacion else ""
                    ) + " = "
                    f"{self._numero_de_eliminacion(pesos[j])}"
                    for j in range(columnas)
                )
            ])
        else:
            libres = resultado["variables_libres"]
            pivotes = resultado["pivotes"]
            lineas.extend([
                "Infinitas soluciones:",
                "Variables libres: " + ", ".join(etiquetas[j] for j in libres) + ".",
                "Asigna libremente un valor a cada parámetro:"
            ])
            for numero, j in enumerate(libres, start=1):
                lineas.append(f"{etiquetas[j]} = t{numero}")

            # Cada fila pivote en la RREF indica:
            # x_pivote = b_fila - suma(coeficiente_libre · t).
            for fila, j in pivotes:
                texto = self._numero_de_eliminacion(reducida[fila][-1])
                for numero, libre in enumerate(libres, start=1):
                    coeficiente = reducida[fila][libre]
                    if abs(coeficiente) >= 1e-10:
                        signo = " - " if coeficiente > 0 else " + "
                        magnitud = self._numero_de_eliminacion(abs(coeficiente))
                        texto += f"{signo}{magnitud}·t{numero}"
                lineas.append(f"{etiquetas[j]} = {texto}")

            pesos = [0.0] * columnas
            for fila, j in pivotes:
                pesos[j] = reducida[fila][-1]
            lineas.append("Una solución particular se obtiene tomando todos los t = 0.")

        x_aprox = [[valor] for valor in pesos]
        producto = _multiplicar_matrices(a, x_aprox)
        coincide = all(
            abs(float(producto[i][0] - b[i][0])) <=
            1e-7 * max(1.0, abs(float(b[i][0])))
            for i in range(len(b))
        )
        lineas.extend([
            "",
            f"{variable} =",
            self._texto_matriz_eliminacion(x_aprox),
            "",
            "VERIFICACIÓN",
            "=" * 68,
            f"A{variable} =",
            self._texto_matriz_eliminacion(producto),
            "La sustitución reproduce b." if coincide else
            "La verificación numérica no coincide; revisa los datos."
        ])

        if combinacion:
            combinacion_texto = " + ".join(
                f"({self._numero_de_eliminacion(pesos[j])}){nombres[j]}"
                for j in range(columnas)
            )
            lineas.extend([
                "",
                "CONCLUSIÓN SOBRE COMBINACIÓN LINEAL",
                "=" * 68,
                "Sí, b es combinación lineal de los vectores elegidos.",
                combinacion_texto + " = b.",
                (
                    "Estos pesos son los únicos."
                    if clasificacion == "unica" else
                    "Hay infinitas elecciones de pesos; arriba se muestra una."
                )
            ])
        else:
            lineas.extend([
                "",
                "INTERPRETACIÓN",
                "=" * 68,
                (
                    "b se obtiene combinando las columnas de A con los pesos de x."
                    if coincide else "Revisa el redondeo de los coeficientes."
                )
            ])
        lineas.extend([
            "",
            "El algoritmo de eliminación clasifica valores reales con tolerancia 1e-10."
        ])
        return "\n".join(lineas)

    def resolver_axb(self, nombres=None, incognita="x"):
        """Resuelve la A y b elegidas sin exigir que el usuario ya conozca x."""

        try:
            nombre_a, nombre_b = nombres or (
                self.nombre_matriz_resolver.get(), self.nombre_vector_objetivo.get()
            )
            a, b = self._datos_sistema(nombre_a, nombre_b)
            variables = self.objetos[nombre_a]["variables"]
            if len(variables) != len(a[0]):
                variables = [f"{incognita}{j + 1}" for j in range(len(a[0]))]
            salida = self._resolver_datos(
                a, b, variables, f"Resolver {nombre_a}{incognita} = {nombre_b}",
                variable=incognita
            )
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            self.estado.set(f"No se pudo resolver: {error}")
            messagebox.showerror("No se puede resolver Ax=b", str(error), parent=self.ventana)
            return
        self._mostrar_resultado(salida)
        self.estado.set(f"Choco dice: resolví {nombre_a}{incognita}={nombre_b} por eliminación.")

    def resolver_combinacion(self):
        """Comprueba si b está en el espacio generado por los vectores elegidos."""

        try:
            nombre_b = self.nombre_vector_objetivo.get()
            if nombre_b not in self.objetos or len(self.objetos[nombre_b]["valor"][0]) != 1:
                raise ValueError("Selecciona primero el vector objetivo b.")
            nombres = [
                self.lista_vectores.get(indice)
                for indice in self.lista_vectores.curselection()
            ]
            if not nombres:
                raise ValueError("Selecciona al menos un vector de la lista (Ctrl+clic para varios).")
            if nombre_b in nombres:
                raise ValueError("El vector objetivo b no debe elegirse entre sus generadores.")

            b = self.objetos[nombre_b]["valor"]
            for nombre in nombres:
                if len(self.objetos[nombre]["valor"]) != len(b):
                    raise ValueError(
                        f"{nombre} tiene {len(self.objetos[nombre]['valor'])} entradas "
                        f"y {nombre_b} tiene {len(b)}. Todos deben estar en R^{len(b)}."
                    )
            a = [
                [self.objetos[nombre]["valor"][i][0] for nombre in nombres]
                for i in range(len(b))
            ]
            salida = self._resolver_datos(
                a, b, nombres,
                f"¿{nombre_b} es combinación lineal de {', '.join(nombres)}?",
                combinacion=True, variable="c"
            )
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            self.estado.set(f"No se pudo comprobar: {error}")
            messagebox.showerror("Combinación lineal", str(error), parent=self.ventana)
            return
        self._mostrar_resultado(salida)
        self.estado.set("Choco dice: comprobé la combinación lineal por eliminación.")

    # -----------------------------------------------------
    # PRESENTACIÓN DEL PROCEDIMIENTO
    # -----------------------------------------------------

    def calcular(self):
        texto = self.expresion.get().strip()
        try:
            if texto.count("=") > 1:
                raise ValueError("Usa como máximo un signo = en la expresión.")
            partes = texto.split("=", 1)

            # Cuando x aún no existe, "Ax" es un único token para el
            # analizador de expresiones. En Ax=b identificamos A por su
            # nombre guardado y tratamos el resto como la incógnita.
            if len(partes) == 2:
                unido = partes[0].strip()
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", unido):
                    matrices = sorted(self.objetos, key=len, reverse=True)
                    for nombre_a in matrices:
                        incognita = unido[len(nombre_a):]
                        if (
                            unido.startswith(nombre_a)
                            and incognita
                            and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", incognita)
                            and incognita not in self.objetos
                        ):
                            partes[0] = f"{nombre_a}*{incognita}"
                            break
            nodo_izq, normalizada_izq = self._analizar_lado(partes[0])

            # Ax=b también sirve para ENCONTRAR x cuando todavía no se ha
            # guardado ese vector. Si x sí existe, se evalúa la igualdad.
            if len(partes) == 2:
                nodo_der_previo, _ = self._analizar_lado(partes[1])
                es_ecuacion_por_resolver = (
                    isinstance(nodo_izq, ast.BinOp)
                    and isinstance(nodo_izq.op, ast.Mult)
                    and isinstance(nodo_izq.left, ast.Name)
                    and isinstance(nodo_izq.right, ast.Name)
                    and isinstance(nodo_der_previo, ast.Name)
                    and nodo_izq.right.id not in self.objetos
                    and nodo_izq.left.id in self.objetos
                    and nodo_der_previo.id in self.objetos
                )
                if es_ecuacion_por_resolver:
                    nombre_a = nodo_izq.left.id
                    nombre_b = nodo_der_previo.id
                    self.nombre_matriz_resolver.set(nombre_a)
                    self.nombre_vector_objetivo.set(nombre_b)
                    self.cuaderno_operacion.select(self.pestana_resolver)
                    self.resolver_axb(
                        nombres=(nombre_a, nombre_b),
                        incognita=nodo_izq.right.id
                    )
                    return

            pasos = []
            resultado_izq = self._evaluar(nodo_izq, pasos)

            nodo_der = None
            resultado_der = None
            normalizada_der = None
            if len(partes) == 2:
                nodo_der, normalizada_der = self._analizar_lado(partes[1])
                resultado_der = self._evaluar(nodo_der, pasos)
                self._validar_comparables(resultado_izq, resultado_der)

            salida = self._construir_salida(
                texto,
                nodo_izq,
                resultado_izq,
                pasos,
                nodo_der,
                resultado_der,
                normalizada_izq,
                normalizada_der
            )
        except (ValueError, TypeError, ZeroDivisionError) as error:
            self.estado.set(f"No se pudo calcular: {error}")
            messagebox.showerror(
                "No se puede calcular",
                f"Choco dice: {error}",
                parent=self.ventana
            )
            return

        self._mostrar_resultado(salida)
        self.estado.set(f"Choco dice: expresión «{texto}» calculada correctamente.")

    def _validar_comparables(self, a, b):
        if self._es_matriz(a) != self._es_matriz(b):
            raise ValueError("Los dos lados de la igualdad no son del mismo tipo.")
        if self._es_matriz(a) and _dimensiones(a) != _dimensiones(b):
            raise ValueError(
                f"Los lados tienen dimensiones distintas: "
                f"{_dimensiones(a)[0]}×{_dimensiones(a)[1]} y "
                f"{_dimensiones(b)[0]}×{_dimensiones(b)[1]}."
            )

    def _iguales(self, a, b):
        return a == b

    def _nombres_usados(self, *nodos):
        usados = []
        for nodo in nodos:
            if nodo is None:
                continue
            for elemento in ast.walk(nodo):
                if isinstance(elemento, ast.Name) and elemento.id in self.objetos:
                    if elemento.id not in usados:
                        usados.append(elemento.id)
        return usados

    def _construir_salida(
        self, texto, nodo_izq, resultado_izq, pasos,
        nodo_der, resultado_der, normalizada_izq, normalizada_der
    ):
        formato = self.formato_salida.get()
        lineas = [
            "EXPRESIÓN",
            "=" * 72,
            texto,
            ""
        ]

        usados = self._nombres_usados(nodo_izq, nodo_der)
        if formato in ("Completa", "Matrices"):
            lineas.extend(["DATOS USADOS", "=" * 72])
            for nombre in usados:
                datos = self.objetos[nombre]
                valor = datos["valor"]
                lineas.extend([
                    f"{nombre} ({datos['tipo']}, {len(valor)}×{len(valor[0])}) =",
                    _texto_matriz(valor),
                    ""
                ])

        lineas.extend(["RESULTADO", "=" * 72])
        etiqueta_izq = self._etiqueta_nodo(nodo_izq)
        lineas.append(f"{etiqueta_izq} =")
        lineas.append(self._texto_valor(resultado_izq))

        if nodo_der is not None:
            etiqueta_der = self._etiqueta_nodo(nodo_der)
            lineas.extend([
                "",
                f"{etiqueta_der} =",
                self._texto_valor(resultado_der),
                "",
                (
                    "✓ Los dos lados son iguales entrada por entrada."
                    if self._iguales(resultado_izq, resultado_der)
                    else "✗ Los dos lados no son iguales."
                )
            ])

        if formato in ("Completa", "Ecuaciones"):
            lineas.extend(["", "DESARROLLO PASO A PASO", "=" * 72])
            if pasos:
                for indice, paso in enumerate(pasos, start=1):
                    lineas.extend(self._describir_paso(indice, paso))
            else:
                lineas.append("La expresión corresponde directamente a un dato guardado.")

            distributiva = self._seccion_distributiva(nodo_izq)
            if distributiva:
                lineas.extend(["", *distributiva])

        lineas.extend(["", "INTERPRETACIÓN", "=" * 72])
        lineas.extend(self._interpretar(resultado_izq, pasos, nodo_der, resultado_der))
        lineas.extend([
            "",
            "Nota: el cálculo usa fracciones exactas; no redondea durante las operaciones."
        ])
        return "\n".join(lineas)

    def _texto_valor(self, valor):
        return _texto_matriz(valor) if self._es_matriz(valor) else _texto_numero(valor)

    def _describir_paso(self, indice, paso):
        tipo = paso["tipo"]
        titulo = f"Paso {indice}. "
        lineas = []

        if tipo == "suma":
            titulo += f"{paso['ea']} {paso['simbolo']} {paso['eb']}"
            lineas.extend([titulo, self._texto_valor(paso["r"])])
            a, b, r = paso["a"], paso["b"], paso["r"]
            for i in range(len(a)):
                calculos = []
                for j in range(len(a[0])):
                    calculos.append(
                        f"r{i + 1}{j + 1}=({_texto_numero(a[i][j])})"
                        f"{paso['simbolo']}({_texto_numero(b[i][j])})"
                        f"={_texto_numero(r[i][j])}"
                    )
                lineas.append("   " + "   ".join(calculos))

        elif tipo == "producto":
            a, b, r = paso["a"], paso["b"], paso["r"]
            fa, ca = _dimensiones(a)
            fb, cb = _dimensiones(b)
            lineas.extend([
                titulo + f"{paso['ea']} por {paso['eb']}",
                f"   ({fa}×{ca})({fb}×{cb}) produce una matriz {fa}×{cb}."
            ])
            for i in range(fa):
                for j in range(cb):
                    productos = " + ".join(
                        f"({_texto_numero(a[i][k])})({_texto_numero(b[k][j])})"
                        for k in range(ca)
                    )
                    lineas.append(
                        f"   r{i + 1}{j + 1} = {productos} = {_texto_numero(r[i][j])}"
                    )
            lineas.extend(["   Resultado:", self._texto_valor(r)])
            if cb == 1:
                lineas.extend(self._representacion_vectorial(a, b, r, paso["ea"], paso["eb"]))

        elif tipo == "escalar":
            lineas.extend([
                titulo + f"Multiplicación escalar {paso['ea']}·{paso['eb']}",
                f"   Cada entrada se multiplica por {_texto_numero(paso['a'])}.",
                self._texto_valor(paso["r"])
            ])

        elif tipo == "transpuesta":
            lineas.extend([
                titulo + f"Transpuesta de {paso['ea']}",
                "   Las filas pasan a ser columnas.",
                self._texto_valor(paso["r"])
            ])

        elif tipo == "determinante":
            lineas.append(titulo + f"Determinante de {paso['ea']}")
            lineas.extend(f"   {detalle}" for detalle in paso["detalle"])
            lineas.append(f"   det = {_texto_numero(paso['r'])}")

        elif tipo == "division":
            lineas.extend([
                titulo + f"{paso['ea']} dividido entre {paso['eb']}",
                self._texto_valor(paso["r"])
            ])

        else:
            lineas.append(titulo + self._texto_valor(paso["r"]))

        lineas.append("")
        return lineas

    def _representacion_vectorial(self, a, x, resultado, ea, ex):
        filas, columnas = _dimensiones(a)
        coeficientes = [x[i][0] for i in range(columnas)]
        lineas = [
            "",
            "   ECUACIÓN VECTORIAL / COMBINACIÓN DE COLUMNAS",
            "   " + "-" * 57
        ]
        terminos = []
        for j in range(columnas):
            columna = [[a[i][j]] for i in range(filas)]
            terminos.append(
                f"({_texto_numero(coeficientes[j])})a{j + 1}"
            )
            lineas.append(f"   a{j + 1} = {_texto_matriz(columna).replace(chr(10), ' ')}")
        lineas.append(
            f"   {ea}{ex} = " + " + ".join(terminos)
            + " = " + _texto_matriz(resultado).replace("\n", " ")
        )
        lineas.append("   Regla fila-vector:")
        for i in range(filas):
            productos = " + ".join(
                f"({_texto_numero(a[i][j])})({_texto_numero(coeficientes[j])})"
                for j in range(columnas)
            )
            lineas.append(
                f"   Fila {i + 1}·{ex}: {productos} = {_texto_numero(resultado[i][0])}"
            )
        return lineas

    def _seccion_distributiva(self, nodo):
        if not (
            isinstance(nodo, ast.BinOp)
            and isinstance(nodo.op, ast.Mult)
            and isinstance(nodo.right, ast.BinOp)
            and isinstance(nodo.right.op, (ast.Add, ast.Sub))
        ):
            return []
        try:
            a = self._evaluar(nodo.left, [])
            u = self._evaluar(nodo.right.left, [])
            v = self._evaluar(nodo.right.right, [])
            if not all(self._es_matriz(valor) for valor in (a, u, v)):
                return []
            signo = 1 if isinstance(nodo.right.op, ast.Add) else -1
            suma = _sumar_matrices(u, v, signo=signo)
            izquierda = _multiplicar_matrices(a, suma)
            au = _multiplicar_matrices(a, u)
            av = _multiplicar_matrices(a, v)
            derecha = _sumar_matrices(au, av, signo=signo)
        except (ValueError, IndexError):
            return []

        simbolo = "+" if signo == 1 else "−"
        ea = self._etiqueta_nodo(nodo.left)
        eu = self._etiqueta_nodo(nodo.right.left)
        ev = self._etiqueta_nodo(nodo.right.right)
        return [
            "COMPROBACIÓN DE LA PROPIEDAD DISTRIBUTIVA",
            "=" * 72,
            f"{eu} {simbolo} {ev} =",
            _texto_matriz(suma),
            "",
            f"{ea}({eu} {simbolo} {ev}) =",
            _texto_matriz(izquierda),
            "",
            f"{ea}{eu} =",
            _texto_matriz(au),
            f"{ea}{ev} =",
            _texto_matriz(av),
            f"{ea}{eu} {simbolo} {ea}{ev} =",
            _texto_matriz(derecha),
            "",
            (
                f"✓ Se verifica que {ea}({eu} {simbolo} {ev}) = "
                f"{ea}{eu} {simbolo} {ea}{ev}."
                if izquierda == derecha
                else "✗ Los resultados no coinciden; revisa los datos."
            )
        ]

    def _interpretar(self, resultado, pasos, nodo_der, resultado_der):
        lineas = []
        if self._es_matriz(resultado):
            filas, columnas = _dimensiones(resultado)
            if columnas == 1:
                lineas.append(
                    f"• El resultado es un vector columna de {filas} componentes; pertenece a R^{filas}."
                )
            else:
                lineas.append(f"• El resultado es una matriz de orden {filas}×{columnas}.")
        else:
            lineas.append("• El resultado es un escalar.")

        if any(paso["tipo"] == "producto" for paso in pasos):
            lineas.append(
                "• En cada producto matriz-vector, cada entrada surge del producto punto "
                "entre una fila de la matriz y el vector."
            )
            if any(
                paso["tipo"] == "producto" and len(paso["b"][0]) == 1
                for paso in pasos
            ):
                lineas.append(
                    "• El mismo producto también es una combinación lineal de las columnas "
                    "de la matriz, usando las entradas del vector como pesos."
                )
        if nodo_der is not None:
            lineas.append(
                "• La igualdad es verdadera." if resultado == resultado_der
                else "• La igualdad es falsa para los datos ingresados."
            )
        return lineas

    def _mostrar_resultado(self, texto):
        self.salida.configure(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.insert("1.0", texto)
        self.salida.configure(state="disabled")

    @staticmethod
    def _ayuda_inicial():
        return (
            "CÓMO USAR ESTE MÓDULO\n"
            "=" * 72 + "\n"
            "1. Crea matrices o vectores con nombres como A, B, u, v, x o b.\n"
            "2. También puedes pegar un sistema de ecuaciones para crear A y b.\n"
            "3. En «Operaciones libres» calcula expresiones como A(u+v).\n"
            "4. En «Resolver Ax=b» selecciona A y b, o elige vectores "
            "para comprobar si generan b.\n\n"
            "Ejemplos admitidos:\n"
            "  A(u+v)     Au+Av     Ax=b     A+B     A-B\n"
            "  AB         A*B       3A       (1/2)A\n"
            "  T(A)       A^T       det(A)\n\n"
            "Si x no está guardado, Ax=b encuentra x; si ya existe, comprueba la igualdad.\n"
            "El panel se puede agrandar o reducir arrastrando la barra café horizontal."
        )


# =========================================================
# MENÚ PRINCIPAL
# =========================================================

class ChocoLabMenu:

    def __init__(self, ventana):
        self.ventana = ventana
        self.imagenes = []
        self.modulo_abierto = None

        self.configurar_ventana()
        configurar_estilos()
        self.crear_interfaz()

    def configurar_ventana(self):
        self.ventana.title("Choco Lab - Calculadora de Álgebra Lineal")
        self.ventana.geometry("1100x700")
        self.ventana.minsize(900, 600)
        self.ventana.resizable(True, True)
        self.ventana.configure(bg=COLOR_FONDO)
        _activar_pantalla_completa(self.ventana)

    def crear_interfaz(self):
        self.ventana.rowconfigure(0, weight=1)
        self.ventana.columnconfigure(0, weight=1)

        principal = tk.Frame(self.ventana, bg=COLOR_FONDO)
        principal.grid(row=0, column=0, sticky="nsew", padx=34, pady=(28, 16))
        principal.rowconfigure(0, weight=1)
        principal.columnconfigure(0, weight=1)
        principal.columnconfigure(1, weight=1)

        izquierda = tk.Frame(principal, bg=COLOR_FONDO)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 26))
        izquierda.rowconfigure(0, weight=1)
        izquierda.columnconfigure(0, weight=1)

        contenedor_logo = tk.Frame(izquierda, bg=COLOR_FONDO)
        contenedor_logo.grid(row=0, column=0)

        logo_choco = cargar_logo(self.imagenes, "chocolab.png", 455)

        if logo_choco is not None:
            tk.Label(
                contenedor_logo,
                image=logo_choco,
                bg=COLOR_FONDO
            ).pack(pady=(0, 18))
        else:
            tk.Label(
                contenedor_logo,
                text="🐶",
                font=("Segoe UI Emoji", 90),
                bg=COLOR_FONDO,
                fg=COLOR_CHOCOLATE
            ).pack(pady=(0, 8))

        tk.Label(
            contenedor_logo,
            text="CHOCO LAB",
            font=("Arial", 28, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_FONDO
        ).pack()

        tk.Label(
            contenedor_logo,
            text="Calculadora de Álgebra Lineal",
            font=("Arial", 13),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO
        ).pack(pady=(6, 0))

        derecha = tk.Frame(principal, bg=COLOR_FONDO)
        derecha.grid(row=0, column=1, sticky="nsew", padx=(26, 0))
        derecha.rowconfigure(0, weight=1)
        derecha.columnconfigure(0, weight=1)

        tarjeta = tk.Frame(
            derecha,
            bg=COLOR_BLANCO,
            highlightbackground=COLOR_BEIGE,
            highlightthickness=1
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", pady=24)
        tarjeta.columnconfigure(0, weight=1)

        logo_fia = cargar_logo(self.imagenes, "logofia.png", 155)
        if logo_fia is not None:
            tk.Label(
                tarjeta,
                image=logo_fia,
                bg=COLOR_BLANCO
            ).grid(row=0, column=0, sticky="e", padx=22, pady=(18, 0))

        tk.Label(
            tarjeta,
            text="Selecciona un módulo",
            font=("Arial", 20, "bold"),
            fg=COLOR_CHOCOLATE,
            bg=COLOR_BLANCO
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(12, 5))

        tk.Label(
            tarjeta,
            text=(
                "Los tres módulos funcionan con estos mismos archivos. "
                "Al cerrar un módulo regresarás a este menú."
            ),
            font=("Arial", 10),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_BLANCO,
            justify="left",
            wraplength=400
        ).grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 20))

        self.crear_boton_modulo(
            tarjeta,
            fila=3,
            titulo="Conversión de sistemas numéricos",
            descripcion=(
                "Decimal, binario, octal y hexadecimal con validación, "
                "equivalencias y procedimiento."
            ),
            comando=self.abrir_conversion
        )

        self.crear_boton_modulo(
            tarjeta,
            fila=4,
            titulo="Sistemas de eliminación por filas",
            descripcion=(
                "Módulo de Gauss y Gauss-Jordan con entrada matricial "
                "o mediante ecuaciones."
            ),
            comando=self.abrir_eliminacion
        )

        self.crear_boton_modulo(
            tarjeta,
            fila=5,
            titulo="Álgebra matricial y vectorial",
            descripcion=(
                "Operaciones con matrices, vectores, Ax, combinación "
                "lineal y representación fila-vector."
            ),
            comando=self.abrir_algebra
        )

        tk.Label(
            tarjeta,
            text="Choco dice: elige el tema que necesitas estudiar o resolver.",
            font=("Arial", 9, "italic"),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_BLANCO
        ).grid(row=6, column=0, sticky="w", padx=30, pady=(20, 24))

        self.pie = BarraInferiorChoco(
            self.ventana,
            fila=1,
            volver=self.ventana.destroy,
            texto_derecha="Cerrar programa"
        )

    def crear_boton_modulo(self, padre, fila, titulo, descripcion, comando):
        marco = tk.Frame(
            padre,
            bg=COLOR_FONDO,
            highlightbackground=COLOR_BEIGE,
            highlightthickness=1,
            cursor="hand2"
        )
        marco.grid(row=fila, column=0, sticky="ew", padx=30, pady=7)
        marco.columnconfigure(0, weight=1)

        boton = tk.Button(
            marco,
            text=titulo,
            font=("Arial", 12, "bold"),
            bg=COLOR_CHOCOLATE,
            fg=COLOR_BLANCO,
            activebackground=COLOR_CHOCOLATE_MEDIO,
            activeforeground=COLOR_BLANCO,
            relief="flat",
            cursor="hand2",
            command=comando,
            anchor="w",
            padx=16,
            pady=10
        )
        boton.grid(row=0, column=0, sticky="ew")

        etiqueta = tk.Label(
            marco,
            text=descripcion,
            font=("Arial", 9),
            fg=COLOR_CHOCOLATE_MEDIO,
            bg=COLOR_FONDO,
            justify="left",
            anchor="w",
            wraplength=390,
            padx=16,
            pady=8,
            cursor="hand2"
        )
        etiqueta.grid(row=1, column=0, sticky="ew")
        etiqueta.bind("<Button-1>", lambda event: comando())

    def _abrir_modulo(self, clase_modulo, titulo_error):
        if self.modulo_abierto is not None:
            try:
                self.modulo_abierto.lift()
                self.modulo_abierto.focus_force()
                return
            except tk.TclError:
                self.modulo_abierto = None

        self.ventana.withdraw()
        ventana_modulo = tk.Toplevel(self.ventana)
        self.modulo_abierto = ventana_modulo

        def cerrar(event=None):
            if self.modulo_abierto is None:
                return

            try:
                if ventana_modulo.winfo_exists():
                    ventana_modulo.destroy()
            except tk.TclError:
                pass
            finally:
                self.modulo_abierto = None
                self.ventana.deiconify()
                self.ventana.lift()
                self.ventana.focus_force()

        ventana_modulo.protocol("WM_DELETE_WINDOW", cerrar)
        ventana_modulo.bind("<<CerrarModulo>>", cerrar, add="+")

        try:
            clase_modulo(ventana_modulo)
        except Exception as error:
            cerrar()
            messagebox.showerror(
                f"No se pudo abrir {titulo_error}",
                "Choco encontró un problema al abrir el módulo:\n\n"
                f"{type(error).__name__}: {error}",
                parent=self.ventana
            )

    def abrir_conversion(self):
        self._abrir_modulo(
            ConversionSistemasNumericosApp,
            "Conversión de sistemas numéricos"
        )

    def abrir_eliminacion(self):
        try:
            from interfaz_sistemas_eliminacion import ChocoLabApp
        except Exception as error:
            messagebox.showerror(
                "No se pudo cargar el módulo de eliminación",
                "Verifica que interfaz_sistemas_eliminacion.py y "
                "sistemas_eliminacion.py estén en esta misma carpeta.\n\n"
                f"{type(error).__name__}: {error}",
                parent=self.ventana
            )
            return

        self._abrir_modulo(
            ChocoLabApp,
            "Sistemas de eliminación por filas"
        )

    def abrir_algebra(self):
        self._abrir_modulo(
            AlgebraMatricialVectorialApp,
            "Álgebra matricial y vectorial"
        )


def main():
    ventana = tk.Tk()
    ChocoLabMenu(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
