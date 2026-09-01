# =========================================================
# LÓGICA DEL PROGRAMA
# Calculadora de Álgebra Lineal - Choco Lab
# =========================================================
#
# Este archivo contiene únicamente la lógica matemática.
# =========================================================


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
    Busca una fila con un valor diferente de cero en la columna pivote.

    Se prefiere el valor absoluto más grande para reducir problemas
    numéricos con divisiones por números muy pequeños.
    """

    mejor_fila = None
    mayor_valor = tolerancia

    for fila in range(fila_inicial, len(matriz)):

        valor = abs(matriz[fila][columna])

        if valor > mayor_valor:
            mayor_valor = valor
            mejor_fila = fila

    return mejor_fila


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

    FASE 1:
    Produce forma escalonada creando ceros debajo de cada pivote.

    FASE 2:
    Si el sistema es consistente, continúa hasta forma escalonada
    reducida, convirtiendo los pivotes en 1 y creando ceros arriba.

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
    # FASE 1: FORMA ESCALONADA
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

        # Intercambio de filas si el mejor pivote no está arriba.
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

        pivote = matriz[fila_pivote][columna_pivote]

        # Crear ceros debajo del pivote.
        for fila in range(fila_pivote + 1, numero_filas):

            elemento = matriz[fila][columna_pivote]

            if abs(elemento) < tolerancia:
                continue

            factor = elemento / pivote

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
            "pasos": pasos,
            "pivotes": pivotes,
            "fila_inconsistente": fila_inconsistente,
            "solucion": None,
            "variables_libres": []
        }

    # -----------------------------------------------------
    # FASE 2: FORMA ESCALONADA REDUCIDA
    # -----------------------------------------------------

    for fila_pivote, columna_pivote in reversed(pivotes):

        pivote = matriz[fila_pivote][columna_pivote]

        # Convertir el pivote en 1.
        if abs(pivote - 1.0) >= tolerancia:

            for columna in range(columna_pivote, numero_columnas):

                matriz[fila_pivote][columna] = (
                    matriz[fila_pivote][columna] / pivote
                )

            _limpiar_ceros(matriz, tolerancia)

            _registrar_paso(
                pasos,
                "reduccion",
                (
                    f"F{fila_pivote + 1} → "
                    f"(1/{_numero_corto(pivote)})F{fila_pivote + 1}"
                ),
                matriz
            )

        # Crear ceros arriba del pivote.
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
