# =========================================================
# Universidad Americana (UAM)
# Facultad de Ingeniería y Arquitectura (FIA)
# Asignatura: Álgebra Lineal
# Grupo 4
# =========================================================
# CHOCO LAB - LÓGICA DE FACTORIZACIÓN LU
# =========================================================
# Implementación exacta con Fraction y sin librerías externas.
# Convención del material del curso: A = LU se construye mediante
# operaciones de reemplazo de filas, sin intercambios. Si un pivote
# obliga a intercambiar filas, corresponde trabajar con PA = LU.
# =========================================================

from fractions import Fraction
import random


class ErrorLU(ValueError):
    """Error base del módulo LU."""


class RequiereIntercambioFilas(ErrorLU):
    """La matriz requiere pivoteo/intercambio y no admite esta A=LU directa."""


def leer_numero(texto):
    """Convierte enteros, decimales o fracciones a Fraction."""
    if isinstance(texto, Fraction):
        return texto
    if isinstance(texto, int):
        return Fraction(texto)
    if isinstance(texto, float):
        return Fraction(str(texto))

    limpio = str(texto).strip().replace("−", "-").replace(",", ".")
    if not limpio:
        raise ValueError("Se encontró una celda vacía.")

    try:
        return Fraction(limpio)
    except (ValueError, ZeroDivisionError):
        raise ValueError(
            f"«{texto}» no es un número válido. Usa enteros, decimales "
            "o fracciones como 3/4."
        ) from None


def copiar_matriz(matriz):
    return [fila[:] for fila in matriz]


def identidad(orden):
    return [
        [Fraction(1 if i == j else 0) for j in range(orden)]
        for i in range(orden)
    ]


def validar_matriz_cuadrada(matriz, nombre="A"):
    if not isinstance(matriz, list) or not matriz:
        raise ValueError(f"La matriz {nombre} no puede estar vacía.")

    orden = len(matriz)
    if any(not isinstance(fila, list) or len(fila) != orden for fila in matriz):
        raise ValueError(f"La matriz {nombre} debe ser cuadrada (n×n).")

    exacta = []
    for i, fila in enumerate(matriz, start=1):
        nueva = []
        for j, valor in enumerate(fila, start=1):
            try:
                nueva.append(leer_numero(valor))
            except ValueError as error:
                raise ValueError(
                    f"Valor no válido en {nombre}({i},{j}): {error}"
                ) from None
        exacta.append(nueva)
    return exacta


def validar_vector(vector, orden, nombre="b"):
    if not isinstance(vector, list) or len(vector) != orden:
        raise ValueError(
            f"El vector {nombre} debe tener exactamente {orden} entradas."
        )

    exacto = []
    for i, valor in enumerate(vector, start=1):
        try:
            exacto.append(leer_numero(valor))
        except ValueError as error:
            raise ValueError(
                f"Valor no válido en {nombre}{i}: {error}"
            ) from None
    return exacto


def multiplicar_matrices(a, b):
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("Las dimensiones no permiten multiplicar las matrices.")

    filas_a = len(a)
    columnas_a = len(a[0])
    columnas_b = len(b[0])

    return [
        [
            sum((a[i][k] * b[k][j] for k in range(columnas_a)), Fraction(0))
            for j in range(columnas_b)
        ]
        for i in range(filas_a)
    ]


def multiplicar_matriz_vector(matriz, vector):
    if not matriz or len(matriz[0]) != len(vector):
        raise ValueError("Las dimensiones no permiten calcular A·x.")
    return [
        sum((matriz[i][j] * vector[j] for j in range(len(vector))), Fraction(0))
        for i in range(len(matriz))
    ]


def matrices_iguales(a, b):
    return a == b


def vectores_iguales(a, b):
    return a == b


def factorizar_lu(matriz):
    """Calcula A = LU mediante eliminación sin intercambios de filas.

    L es triangular inferior unitaria y guarda los multiplicadores m_ik.
    U es la matriz triangular superior obtenida por reemplazos de fila.
    """
    a = validar_matriz_cuadrada(matriz, "A")
    n = len(a)
    l = identidad(n)
    u = copiar_matriz(a)
    pasos = []

    for k in range(n - 1):
        pivote = u[k][k]

        if pivote == 0:
            hay_elemento_debajo = any(u[i][k] != 0 for i in range(k + 1, n))
            if hay_elemento_debajo:
                raise RequiereIntercambioFilas(
                    f"El pivote u{k + 1}{k + 1} es 0 y hay un valor no nulo "
                    f"debajo en la columna {k + 1}. Para continuar habría que "
                    "intercambiar filas. Con la convención del curso, en ese caso "
                    "corresponde usar PA = LU, no A = LU directamente."
                )
            # Toda la parte inferior de esa columna ya es cero; no hay nada que eliminar.
            pasos.append({
                "tipo": "columna_sin_eliminacion",
                "columna": k,
                "pivote": pivote,
                "operacion": (
                    f"Columna {k + 1}: el pivote es 0, pero todas las entradas "
                    "debajo ya son 0; no se requiere eliminación en esta columna."
                ),
                "L": copiar_matriz(l),
                "U": copiar_matriz(u),
            })
            continue

        for i in range(k + 1, n):
            if u[i][k] == 0:
                continue

            valor_original = u[i][k]
            multiplicador = valor_original / pivote
            l[i][k] = multiplicador

            fila_antes = u[i][:]
            fila_pivote = u[k][:]
            u[i] = [
                u[i][j] - multiplicador * u[k][j]
                for j in range(n)
            ]

            pasos.append({
                "tipo": "eliminacion",
                "columna": k,
                "fila": i,
                "pivote": pivote,
                "valor_eliminado": valor_original,
                "multiplicador": multiplicador,
                "fila_antes": fila_antes,
                "fila_pivote": fila_pivote,
                "operacion": f"F{i + 1} ← F{i + 1} − ({multiplicador})F{k + 1}",
                "L": copiar_matriz(l),
                "U": copiar_matriz(u),
            })

    producto = multiplicar_matrices(l, u)
    verificacion = matrices_iguales(producto, a)

    return {
        "A": a,
        "L": l,
        "U": u,
        "pasos": pasos,
        "producto_LU": producto,
        "verificacion": verificacion,
    }


def sustitucion_adelante(l, b):
    """Resuelve Ly=b para L triangular inferior."""
    n = len(l)
    y = [Fraction(0) for _ in range(n)]
    pasos = []

    for i in range(n):
        suma = sum((l[i][j] * y[j] for j in range(i)), Fraction(0))
        diagonal = l[i][i]
        if diagonal == 0:
            raise ErrorLU(
                f"No se puede resolver Ly=b porque L({i + 1},{i + 1}) = 0."
            )
        y[i] = (b[i] - suma) / diagonal
        pasos.append({
            "fila": i,
            "suma": suma,
            "diagonal": diagonal,
            "rhs": b[i],
            "valor": y[i],
        })

    return y, pasos


def sustitucion_atras(u, y):
    """Resuelve Ux=y para U triangular superior."""
    n = len(u)
    x = [Fraction(0) for _ in range(n)]
    pasos = []

    for i in range(n - 1, -1, -1):
        diagonal = u[i][i]
        if diagonal == 0:
            raise ErrorLU(
                "La matriz U tiene un cero en la diagonal. El sistema no puede "
                "tener solución única mediante sustitución hacia atrás con esta "
                "factorización."
            )

        suma = sum((u[i][j] * x[j] for j in range(i + 1, n)), Fraction(0))
        x[i] = (y[i] - suma) / diagonal
        pasos.append({
            "fila": i,
            "suma": suma,
            "diagonal": diagonal,
            "rhs": y[i],
            "valor": x[i],
        })

    return x, pasos


def resolver_axb_lu(matriz, vector_b):
    """Resuelve Ax=b usando A=LU, Ly=b y Ux=y."""
    resultado_lu = factorizar_lu(matriz)
    a = resultado_lu["A"]
    n = len(a)
    b = validar_vector(vector_b, n, "b")

    # Para obtener una solución única por sustitución hacia atrás, U debe tener
    # todos sus elementos diagonales distintos de cero.
    for i in range(n):
        if resultado_lu["U"][i][i] == 0:
            raise ErrorLU(
                f"U({i + 1},{i + 1}) = 0. Por tanto, este sistema no presenta "
                "una solución única resoluble con la sustitución hacia atrás "
                "del método LU mostrado en el curso."
            )

    y, pasos_y = sustitucion_adelante(resultado_lu["L"], b)
    x, pasos_x = sustitucion_atras(resultado_lu["U"], y)

    ly = multiplicar_matriz_vector(resultado_lu["L"], y)
    ux = multiplicar_matriz_vector(resultado_lu["U"], x)
    ax = multiplicar_matriz_vector(a, x)

    return {
        **resultado_lu,
        "b": b,
        "y": y,
        "x": x,
        "pasos_y": pasos_y,
        "pasos_x": pasos_x,
        "Ly": ly,
        "Ux": ux,
        "Ax": ax,
        "verificacion_Ly": vectores_iguales(ly, b),
        "verificacion_Ux": vectores_iguales(ux, y),
        "verificacion_Ax": vectores_iguales(ax, b),
    }


def generar_matriz_lu_aleatoria(orden, minimo=-5, maximo=5, rng=None):
    """Genera A=L·U con una LU válida sin intercambios.

    Se construyen L y U primero para garantizar que el ejercicio generado sea
    compatible con el algoritmo A=LU del curso.
    """
    if not isinstance(orden, int) or orden < 1:
        raise ValueError("El orden debe ser un entero mayor o igual que 1.")
    if orden > 15:
        raise ValueError("El orden máximo admitido por la interfaz es 15.")

    rng = rng or random
    l = identidad(orden)
    u = [[Fraction(0) for _ in range(orden)] for _ in range(orden)]

    for i in range(orden):
        for j in range(i):
            l[i][j] = Fraction(rng.randint(-2, 2))

    for i in range(orden):
        for j in range(i, orden):
            if i == j:
                opciones = [v for v in range(minimo, maximo + 1) if v != 0]
                u[i][j] = Fraction(rng.choice(opciones))
            else:
                u[i][j] = Fraction(rng.randint(minimo, maximo))

    a = multiplicar_matrices(l, u)
    return {
        "A": a,
        "L_generadora": l,
        "U_generadora": u,
    }


def generar_sistema_lu_aleatorio(orden, rng=None):
    """Genera A, b con solución entera conocida para practicar Ax=b por LU."""
    rng = rng or random
    datos = generar_matriz_lu_aleatoria(orden, rng=rng)
    x = [Fraction(rng.randint(-5, 5)) for _ in range(orden)]

    # Evita el vector nulo completo para que el ejercicio sea más ilustrativo.
    if all(valor == 0 for valor in x):
        x[rng.randrange(orden)] = Fraction(rng.choice([-3, -2, -1, 1, 2, 3]))

    b = multiplicar_matriz_vector(datos["A"], x)
    return {
        **datos,
        "b": b,
        "x_generadora": x,
    }
