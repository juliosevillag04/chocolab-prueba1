# =========================================================
# Universidad Americana (UAM)
# Facultad de Ingeniería y Arquitectura (FIA)
# Carrera: Ingeniería de Sistemas
# Asignatura: Álgebra Lineal
# Grupo 4 - Integrantes:
# Julio Javier Sevilla Gallegos
# Docente: Carlos Iván Argüello Martínez
# =========================================================
# LÓGICA DEL PROGRAMA
# Calculadora de Álgebra Lineal - Choco Lab
# =========================================================
#
# Este archivo contiene únicamente la lógica matemática.
# =========================================================
import re


TOLERANCIA = 1e-10


# =========================================================
# MATRICES Y VALIDACIONES BÁSICAS
# =========================================================

def crear_matriz(filas=3, columnas=3, valor_inicial=0.0): #valor_inicial=0.0 incia todos los valores en cero
    """
    Crea una matriz de tamaño filas x columnas.

    Ejemplo:
    crear_matriz(2, 3)
    [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0]
    ]
    """

    if not isinstance(filas, int) or not isinstance(columnas, int): #confirma que la fila y columna sean enteros
        raise TypeError("Las dimensiones de la matriz deben ser números enteros.")

    if filas <= 0 or columnas <= 0:
        raise ValueError("La matriz debe tener al menos una fila y una columna.")

    matriz = []

    for _ in range(filas):
        fila = []

        for _ in range(columnas):
            fila.append(valor_inicial)

        matriz.append(fila)

    return matriz


def copiar_matriz(matriz):
    """Devuelve una copia independiente de una matriz."""

    copia = []

    for fila in matriz:
        copia.append(fila[:])

    return copia


def validar_dimensiones(numero_ecuaciones, numero_variables):
    """Verifica que el sistema tenga dimensiones positivas."""

    if not isinstance(numero_ecuaciones, int):
        return False

    if not isinstance(numero_variables, int):
        return False

    if numero_ecuaciones <= 0:
        return False

    if numero_variables <= 0:
        return False

    return True


def validar_posicion(matriz, fila, columna, base=0):
    """
    Valida una coordenada dentro de una matriz.

    base=0 -> modo programador:
        primera posición = (0, 0)

    base=1 -> modo matemático:
        primera posición = (1, 1)
    """

    if base not in (0, 1):
        return False

    if not isinstance(fila, int) or not isinstance(columna, int):
        return False

    fila_interna = fila - base
    columna_interna = columna - base

    if fila_interna < 0 or fila_interna >= len(matriz):
        return False

    if len(matriz) == 0:
        return False

    if columna_interna < 0 or columna_interna >= len(matriz[0]):
        return False

    return True


def buscar_elemento(matriz, fila, columna, base=0):
    """
    Busca un elemento usando base 0 o base 1.
    Retorna None si la posición no existe.
    """

    if not validar_posicion(matriz, fila, columna, base):
        return None

    fila_interna = fila - base
    columna_interna = columna - base

    return matriz[fila_interna][columna_interna]


def modificar_elemento(matriz, fila, columna, nuevo_valor, base=0):
    """
    Modifica un elemento usando base 0 o base 1.
    Retorna True si se realizó la modificación.
    """

    if not validar_posicion(matriz, fila, columna, base):
        return False

    fila_interna = fila - base
    columna_interna = columna - base

    matriz[fila_interna][columna_interna] = nuevo_valor

    return True


def es_elemento_diagonal(fila, columna):
    """
    Un elemento pertenece a la diagonal principal cuando
    su índice de fila es igual a su índice de columna.

    Esto funciona tanto con índices 0,0 como con 1,1,
    porque en ambos casos se cumple fila == columna.
    """

    return fila == columna


def numero_finito(numero):
    """
    Evita aceptar NaN o infinito.
    """

    try:
        numero = float(numero)
    except (TypeError, ValueError):
        return False

    # NaN es el único número que no es igual a sí mismo.
    if numero != numero:
        return False

    if numero == float("inf"):
        return False

    if numero == float("-inf"):
        return False

    return True


def validar_matriz_aumentada(matriz, numero_variables):
    """
    Comprueba que:
    - exista al menos una ecuación;
    - cada fila tenga numero_variables + 1 columnas;
    - todos los elementos sean números finitos.
    """

    if not isinstance(matriz, list) or len(matriz) == 0:
        return False

    columnas_esperadas = numero_variables + 1

    for fila in matriz:

        if not isinstance(fila, list):
            return False

        if len(fila) != columnas_esperadas:
            return False

        for valor in fila:

            if not numero_finito(valor):
                return False

    return True


# =========================================================
# CONVERSIÓN DE ECUACIONES A MATRIZ AUMENTADA
# =========================================================

_PATRON_NUMERO = (
    r"(?:\d+(?:[.,]\d*)?|[.,]\d+)"
    r"(?:[eE][+-]?\d+)?"
)

# Una variable comienza con una letra y puede continuar con letras,
# números o guion bajo. Ejemplos: f, g12, presion2, variable_a.
_PATRON_VARIABLE = r"(?:[a-zA-Z][a-zA-Z0-9_]*)"

_PATRON_TERMINO = re.compile(
    rf"[+-](?:{_PATRON_NUMERO}(?:\*?{_PATRON_VARIABLE})?|{_PATRON_VARIABLE})"
)


def _leer_expresion_lineal(expresion, nombres_variables):
    """
    Lee uno de los lados de una ecuación lineal.

    Acepta, por ejemplo:
    x + 2y - 3.5z + 4
    x1 + 2x2 - 3.5x3 + 4

    También se pueden mezclar ambas notaciones.
    """

    expresion = expresion.lower()
    expresion = expresion.replace("−", "-")
    expresion = expresion.replace("–", "-")
    expresion = expresion.replace("·", "*")
    expresion = expresion.translate(
        str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    )
    expresion = "".join(expresion.split())

    if expresion == "":
        raise ValueError("Falta un lado de la ecuación.")

    if expresion[0] not in "+-":
        expresion = "+" + expresion

    coeficientes = [0.0] * len(nombres_variables)
    constante = 0.0
    posicion = 0

    while posicion < len(expresion):

        coincidencia = _PATRON_TERMINO.match(
            expresion,
            posicion
        )

        if coincidencia is None:
            raise ValueError(
                "La ecuación contiene un término no válido. "
                "Usa un formato como x + 2y - 3z = 9 o "
                "x1 + 2x2 - 3x3 = 9."
            )

        termino = coincidencia.group()
        posicion = coincidencia.end()

        signo = -1.0 if termino[0] == "-" else 1.0
        contenido = termino[1:]

        variable = re.fullmatch(
            rf"(?:(?P<coeficiente>{_PATRON_NUMERO})\*?)?"
            rf"(?P<variable>{_PATRON_VARIABLE})",
            contenido
        )

        if variable is not None:

            nombre_variable = variable.group("variable").lower()

            if nombre_variable not in nombres_variables:
                raise ValueError(
                    f"La variable «{nombre_variable}» no pertenece a las "
                    "variables definidas para este sistema."
                )

            indice = nombres_variables.index(nombre_variable)

            texto_coeficiente = variable.group("coeficiente")

            if texto_coeficiente is None:
                coeficiente = 1.0
            else:
                coeficiente = float(
                    texto_coeficiente.replace(",", ".")
                )

            coeficientes[indice] += signo * coeficiente

        else:

            constante += signo * float(
                contenido.replace(",", ".")
            )

    return coeficientes, constante


def extraer_variables(ecuacion):
    """Obtiene los nombres de variables en su orden de aparición."""

    if not isinstance(ecuacion, str):
        raise TypeError("La ecuación debe escribirse como texto.")

    texto = ecuacion.translate(
        str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    )
    nombres = []

    for nombre in re.findall(_PATRON_VARIABLE, texto):
        nombre = nombre.lower()
        if nombre not in nombres:
            nombres.append(nombre)

    return nombres


def convertir_ecuacion_a_fila(
    ecuacion,
    numero_variables,
    nombres_variables=None
):
    """
    Convierte una ecuación lineal en una fila de matriz aumentada.

    Ejemplos:
    x + 2y + 3z = 9      ->  [1.0, 2.0, 3.0, 9.0]
    x1 + 2x2 + 3x3 = 9   ->  [1.0, 2.0, 3.0, 9.0]

    También permite constantes o variables en ambos lados. Todos los
    términos se reorganizan automáticamente antes de formar la fila.
    """

    if not isinstance(ecuacion, str):
        raise TypeError("La ecuación debe escribirse como texto.")

    if not isinstance(numero_variables, int) or numero_variables <= 0:
        raise ValueError("El número de variables debe ser positivo.")

    if ecuacion.count("=") != 1:
        raise ValueError(
            "La ecuación debe contener exactamente un signo =."
        )

    if nombres_variables is None:
        nombres_variables = extraer_variables(ecuacion)

        if len(nombres_variables) > numero_variables:
            raise ValueError(
                f"La ecuación usa {len(nombres_variables)} variables, pero "
                f"el sistema está configurado para {numero_variables}."
            )

        while len(nombres_variables) < numero_variables:
            nombres_variables.append(f"__variable_{len(nombres_variables) + 1}")

    if len(nombres_variables) != numero_variables:
        raise ValueError("La cantidad de nombres de variables no coincide con el sistema.")

    lado_izquierdo, lado_derecho = ecuacion.split("=")

    coeficientes_izquierdos, constante_izquierda = (
        _leer_expresion_lineal(
            lado_izquierdo,
            nombres_variables
        )
    )

    coeficientes_derechos, constante_derecha = (
        _leer_expresion_lineal(
            lado_derecho,
            nombres_variables
        )
    )

    fila = []

    for columna in range(numero_variables):
        fila.append(
            coeficientes_izquierdos[columna]
            - coeficientes_derechos[columna]
        )

    fila.append(
        constante_derecha - constante_izquierda
    )

    _limpiar_ceros([fila])

    return fila


def convertir_sistema_ecuaciones(ecuaciones, numero_variables):
    """
    Convierte todas las ecuaciones usando un único orden de variables.

    El orden se determina por la primera aparición de cada nombre en el
    sistema. Así, nombres como f, g12 o temperatura3 conservan su identidad.
    """

    nombres_variables = []

    for ecuacion in ecuaciones:
        for nombre in extraer_variables(ecuacion):
            if nombre not in nombres_variables:
                nombres_variables.append(nombre)

    if len(nombres_variables) != numero_variables:
        raise ValueError(
            f"Se encontraron {len(nombres_variables)} variable(s) distinta(s) "
            f"({', '.join(nombres_variables) if nombres_variables else 'ninguna'}), "
            f"pero el sistema está configurado para {numero_variables}."
        )

    matriz = []
    for ecuacion in ecuaciones:
        matriz.append(
            convertir_ecuacion_a_fila(
                ecuacion,
                numero_variables,
                nombres_variables
            )
        )

    return matriz, nombres_variables


# =========================================================
# FUNCIONES AUXILIARES PARA LA REDUCCIÓN POR FILAS
# =========================================================

def _limpiar_ceros(matriz, tolerancia=TOLERANCIA):
    """
    Convierte números extremadamente pequeños en 0.0.

    Esto evita resultados como:
    2.220446049250313e-16
    """

    for fila in range(len(matriz)):

        for columna in range(len(matriz[fila])):

            if abs(matriz[fila][columna]) < tolerancia:
                matriz[fila][columna] = 0.0


def _numero_corto(numero):
    """Formato corto para describir operaciones por filas."""

    if abs(numero) < TOLERANCIA:
        numero = 0.0

    if float(numero).is_integer():
        return str(int(numero))

    return f"{numero:.6g}"


def _registrar_paso(pasos, fase, operacion, matriz):
    """Guarda una operación y una copia de la matriz resultante."""

    pasos.append(
        {
            "fase": fase,
            "operacion": operacion,
            "matriz": copiar_matriz(matriz)
        }
    )


def _buscar_mejor_fila_pivote(matriz, fila_inicial, columna, tolerancia):
    """
    Busca la fila que conviene usar para formar el siguiente pivote.

    Prioridad del algoritmo:
    1. Conservar un 1 si ya está en la posición pivote.
    2. Buscar un 1 debajo e intercambiar filas.
    3. Usar un -1, porque se convierte en 1 con un escalamiento simple.
    4. Si no existe ±1, usar una entrada diferente de cero.

    De esta forma se imita el razonamiento de "aprovechar" un 1 existente
    antes de crear uno mediante división.
    """

    # 1. El pivote actual ya es 1.
    if abs(matriz[fila_inicial][columna] - 1.0) < tolerancia:
        return fila_inicial

    # 2. Buscar un 1 en las filas disponibles.
    for fila in range(fila_inicial + 1, len(matriz)):

        if abs(matriz[fila][columna] - 1.0) < tolerancia:
            return fila

    # 3. Aprovechar un -1 si existe.
    if abs(matriz[fila_inicial][columna] + 1.0) < tolerancia:
        return fila_inicial

    for fila in range(fila_inicial + 1, len(matriz)):

        if abs(matriz[fila][columna] + 1.0) < tolerancia:
            return fila

    # 4. En ausencia de ±1, usar la primera entrada no nula.
    for fila in range(fila_inicial, len(matriz)):

        if abs(matriz[fila][columna]) >= tolerancia:
            return fila

    return None


def _buscar_fila_inconsistente(matriz, numero_variables, tolerancia):
    """
    Busca una fila del tipo:

    0  0  0 ... 0 | b

    con b diferente de cero.
    """

    for indice_fila in range(len(matriz)):

        coeficientes_en_cero = True

        for columna in range(numero_variables):

            if abs(matriz[indice_fila][columna]) >= tolerancia:
                coeficientes_en_cero = False
                break

        termino_independiente = matriz[indice_fila][numero_variables]

        if coeficientes_en_cero and abs(termino_independiente) >= tolerancia:
            return indice_fila

    return None


# =========================================================
# ALGORITMO DE ELIMINACIÓN POR FILAS
# =========================================================

def resolver_sistema(matriz_aumentada, numero_variables, tolerancia=TOLERANCIA):
    """
    Resuelve y clasifica un sistema lineal mediante operaciones por filas.

    El algoritmo sigue dos fases:

    FASE 1 - GAUSS:
    En cada columna pivote, primero convierte el pivote en 1 y después
    crea ceros debajo. Si existe un 1 disponible en una fila inferior,
    se prefiere intercambiar filas antes que crear el 1 por división.

    FASE 2 - GAUSS-JORDAN:
    Si el sistema es consistente, recorre los pivotes desde la derecha
    hacia la izquierda y crea ceros arriba de cada pivote.

    Retorna un diccionario con:
    - clasificación;
    - matriz escalonada;
    - matriz escalonada reducida;
    - pasos;
    - posiciones pivote;
    - solución única, si existe;
    - variables libres;
    - fila inconsistente, si existe.
    """

    if not validar_matriz_aumentada(matriz_aumentada, numero_variables):
        raise ValueError("La matriz aumentada no tiene una estructura válida.")

    matriz = copiar_matriz(matriz_aumentada)

    numero_filas = len(matriz)
    numero_columnas = numero_variables + 1

    pasos = []
    pivotes = []

    fila_pivote = 0

    # -----------------------------------------------------
    # FASE 1: GAUSS
    # PIVOTE EN 1 Y CEROS DEBAJO
    # -----------------------------------------------------

    for columna_pivote in range(numero_variables):

        if fila_pivote >= numero_filas:
            break

        mejor_fila = _buscar_mejor_fila_pivote(
            matriz,
            fila_pivote,
            columna_pivote,
            tolerancia
        )

        # Si no existe pivote en esta columna,
        # la variable correspondiente puede ser libre.
        if mejor_fila is None:
            continue

        # Si ya existe un 1 útil debajo, se sube mediante intercambio.
        if mejor_fila != fila_pivote:

            matriz[fila_pivote], matriz[mejor_fila] = (
                matriz[mejor_fila],
                matriz[fila_pivote]
            )

            _limpiar_ceros(matriz, tolerancia)

            _registrar_paso(
                pasos,
                "escalonamiento",
                f"F{fila_pivote + 1} ↔ F{mejor_fila + 1}",
                matriz
            )

        # PRIMERO: convertir el pivote actual en 1.
        pivote = matriz[fila_pivote][columna_pivote]

        if abs(pivote - 1.0) >= tolerancia:

            for columna in range(columna_pivote, numero_columnas):

                matriz[fila_pivote][columna] = (
                    matriz[fila_pivote][columna] / pivote
                )

            _limpiar_ceros(matriz, tolerancia)

            _registrar_paso(
                pasos,
                "escalonamiento",
                (
                    f"F{fila_pivote + 1} → "
                    f"(1/{_numero_corto(pivote)})F{fila_pivote + 1}"
                ),
                matriz
            )

        # DESPUÉS: crear ceros debajo del pivote 1.
        for fila in range(fila_pivote + 1, numero_filas):

            elemento = matriz[fila][columna_pivote]

            if abs(elemento) < tolerancia:
                continue

            factor = elemento

            for columna in range(columna_pivote, numero_columnas):

                matriz[fila][columna] = (
                    matriz[fila][columna]
                    - factor * matriz[fila_pivote][columna]
                )

            _limpiar_ceros(matriz, tolerancia)

            _registrar_paso(
                pasos,
                "escalonamiento",
                (
                    f"F{fila + 1} → F{fila + 1} "
                    f"- ({_numero_corto(factor)})F{fila_pivote + 1}"
                ),
                matriz
            )

        pivotes.append(
            (fila_pivote, columna_pivote)
        )

        # La fila del pivote queda terminada y se ignora en la siguiente vuelta.
        fila_pivote += 1

    matriz_escalonada = copiar_matriz(matriz)

    # -----------------------------------------------------
    # CLASIFICACIÓN PRELIMINAR:
    # ¿APARECIÓ 0 = b?
    # -----------------------------------------------------

    fila_inconsistente = _buscar_fila_inconsistente(
        matriz_escalonada,
        numero_variables,
        tolerancia
    )

    if fila_inconsistente is not None:

        return {
            "clasificacion": "inconsistente",
            "matriz_escalonada": matriz_escalonada,
            "matriz_reducida": matriz_escalonada,
            "matriz_gauss": matriz_escalonada,
            "matriz_gauss_jordan": matriz_escalonada,
            "pasos": pasos,
            "pivotes": pivotes,
            "fila_inconsistente": fila_inconsistente,
            "solucion": None,
            "variables_libres": []
        }

    # -----------------------------------------------------
    # FASE 2: GAUSS-JORDAN
    # CEROS ARRIBA, DE DERECHA A IZQUIERDA
    # -----------------------------------------------------

    for fila_pivote, columna_pivote in reversed(pivotes):

        # En Gauss todos los pivotes ya quedaron convertidos en 1.
        # Ahora se usa cada pivote para crear ceros por encima.
        for fila in range(fila_pivote):

            factor = matriz[fila][columna_pivote]

            if abs(factor) < tolerancia:
                continue

            for columna in range(columna_pivote, numero_columnas):

                matriz[fila][columna] = (
                    matriz[fila][columna]
                    - factor * matriz[fila_pivote][columna]
                )

            _limpiar_ceros(matriz, tolerancia)

            _registrar_paso(
                pasos,
                "reduccion",
                (
                    f"F{fila + 1} → F{fila + 1} "
                    f"- ({_numero_corto(factor)})F{fila_pivote + 1}"
                ),
                matriz
            )

    matriz_reducida = copiar_matriz(matriz)

    # -----------------------------------------------------
    # DETERMINAR VARIABLES PIVOTE Y VARIABLES LIBRES
    # -----------------------------------------------------

    columnas_pivote = []

    for _, columna in pivotes:
        columnas_pivote.append(columna)

    variables_libres = []

    for columna in range(numero_variables):

        if columna not in columnas_pivote:
            variables_libres.append(columna)

    # -----------------------------------------------------
    # SOLUCIÓN ÚNICA O INFINITAS SOLUCIONES
    # -----------------------------------------------------

    if len(columnas_pivote) == numero_variables:

        solucion = [0.0] * numero_variables

        for fila, columna in pivotes:

            solucion[columna] = matriz_reducida[fila][numero_variables]

        return {
            "clasificacion": "unica",
            "matriz_escalonada": matriz_escalonada,
            "matriz_reducida": matriz_reducida,
            "matriz_gauss": matriz_escalonada,
            "matriz_gauss_jordan": matriz_reducida,
            "pasos": pasos,
            "pivotes": pivotes,
            "fila_inconsistente": None,
            "solucion": solucion,
            "variables_libres": []
        }

    return {
        "clasificacion": "infinitas",
        "matriz_escalonada": matriz_escalonada,
        "matriz_reducida": matriz_reducida,
        "matriz_gauss": matriz_escalonada,
        "matriz_gauss_jordan": matriz_reducida,
        "pasos": pasos,
        "pivotes": pivotes,
        "fila_inconsistente": None,
        "solucion": None,
        "variables_libres": variables_libres
    }


# =========================================================
# VERIFICACIÓN AUTOMÁTICA DE LA SOLUCIÓN
# =========================================================

def verificar_solucion(
    matriz_original,
    solucion,
    numero_variables,
    tolerancia=1e-8
):
    """
    Sustituye la solución obtenida en el sistema original.

    Retorna una lista con el lado izquierdo, lado derecho
    y el resultado de la comprobación de cada ecuación.
    """

    if solucion is None:
        return []

    if len(solucion) != numero_variables:
        raise ValueError("La cantidad de soluciones no coincide con las variables.")

    verificaciones = []

    for indice_fila in range(len(matriz_original)):

        lado_izquierdo = 0.0

        for columna in range(numero_variables):

            lado_izquierdo += (
                matriz_original[indice_fila][columna]
                * solucion[columna]
            )

        lado_derecho = matriz_original[indice_fila][numero_variables]

        diferencia = abs(lado_izquierdo - lado_derecho)

        verificaciones.append(
            {
                "ecuacion": indice_fila + 1,
                "lado_izquierdo": lado_izquierdo,
                "lado_derecho": lado_derecho,
                "correcta": diferencia <= tolerancia
            }
        )

    return verificaciones
