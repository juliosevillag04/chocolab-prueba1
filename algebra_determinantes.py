# =========================================================
# UNIVERSIDAD AMERICANA - ÁLGEBRA LINEAL - GRUPO 4
# CHOCO LAB: DETERMINANTES POR COFACTORES Y FACTORIZACIÓN LU
# =========================================================

from functools import lru_cache #guarda resultados de cálculos anteriores y evitar repetir operaciones
from fractions import Fraction #trabajar con fracciones exactas en lugar de depender de números decimales aproximados.
from statistics import median #obtener la mediana de un conjunto de valores numéricos.
from time import perf_counter_ns #medir intervalos de tiempo con alta resolución, expresados en nanosegundos.

# Se aprovechan los procedimientos exactos que ya utiliza el cuarto módulo.
from algebra_lu import (
    RequiereIntercambioFilas,
    copiar_matriz,
    factorizar_lu,
    identidad,
    multiplicar_matrices,
    validar_matriz_cuadrada,
)


# =========================================================
# BLOQUE 1. VALIDACIÓN Y REPRESENTACIÓN EXACTA
# =========================================================

def normalizar_matriz(matriz):
    """Valida una matriz cuadrada y convierte sus valores a fracciones exactas."""
    return validar_matriz_cuadrada(matriz, "A")


def texto_numero(valor):
    """Representa un valor racional sin redondearlo."""
    valor = Fraction(valor)
    return str(valor.numerator) if valor.denominator == 1 else f"{valor.numerator}/{valor.denominator}"


def texto_matriz(matriz):
    """Representa una matriz con columnas alineadas para el panel de resultados."""
    if not matriz:
        return "[ ]"
    textos = [[texto_numero(valor) for valor in fila] for fila in matriz]
    anchos = [max(len(fila[j]) for fila in textos) for j in range(len(textos[0]))]
    return "\n".join(
        "[ " + "  ".join(valor.rjust(anchos[j]) for j, valor in enumerate(fila)) + " ]"
        for fila in textos
    )



def patron_signos_cofactores(orden):
    """Tablero (+/-) de (-1)^(i+j), tal como en la diapositiva del curso."""
    ancho = max(3, len(str(orden)) + 1)
    encabezado = " " * 6 + " ".join(f"C{j + 1}".center(ancho) for j in range(orden))
    filas = [encabezado]
    for i in range(orden):
        signos = ["+" if (i + j) % 2 == 0 else "-" for j in range(orden)]
        filas.append(f"F{i + 1:<3} [ " + " ".join(signo.center(ancho) for signo in signos) + " ]")
    return "\n".join(filas)


def matriz_con_signos_cofactores(matriz, tipo=None, indice=None):
    """Une signo de cofactor y entrada, resaltando la fila/columna de expansión."""
    if not matriz:
        return "[ ]"
    n = len(matriz)
    entradas = [
        [("+" if (i + j) % 2 == 0 else "-") + "(" + texto_numero(matriz[i][j]) + ")"
         for j in range(n)]
        for i in range(n)
    ]
    anchos = [max(len(fila[j]) for fila in entradas) for j in range(n)]
    encabezado = " " * 7 + "  ".join(f"C{j+1}".center(anchos[j]) for j in range(n))
    filas = [encabezado]
    for i, fila in enumerate(entradas):
        seleccionado = tipo == "fila" and i == indice
        aviso = "  <-- fila elegida" if seleccionado else ""
        filas.append(("> " if seleccionado else "  ") + f"F{i+1} [ " +
                     "  ".join(valor.rjust(anchos[j]) for j, valor in enumerate(fila)) +
                     " ]" + aviso)
    if tipo == "columna":
        filas.append(f"La columna C{indice+1} es la elegida (lee los términos de arriba hacia abajo).")
    return "\n".join(filas)


def medir_tiempos_metodos(matriz, repeticiones=3, max_orden=7):
    """Cronometra los métodos válidos; mediana de cálculos sin salida visual."""
    a = normalizar_matriz(matriz)
    if len(a) > max_orden:
        return None
    funciones = {
        "cofactores": calcular_cofactores,
        "lu": calcular_lu,
        "gauss": calcular_gauss,
    }
    if len(a) == 3:
        funciones["sarrus"] = calcular_sarrus
    mediciones = {}
    for nombre, funcion in funciones.items():
        duraciones = []
        for _ in range(repeticiones):
            inicio = perf_counter_ns()
            funcion(a, detalle=False)
            duraciones.append((perf_counter_ns() - inicio) / 1_000_000_000)
        mediciones[nombre] = median(duraciones)
    rapido = min(mediciones, key=mediciones.get)
    lento = max(mediciones, key=mediciones.get)
    return {"tiempos": mediciones, "rapido": rapido, "lento": lento,
            "ahorro_segundos": max(0., mediciones[lento] - mediciones[rapido]),
            "repeticiones": repeticiones}


def _transponer(matriz):
    """Intercambia filas y columnas sin modificar el determinante."""
    return [list(fila) for fila in zip(*matriz)]


def _elegir_linea(matriz):
    """Elige la fila o columna que deja menos términos no nulos al expandir."""
    n = len(matriz)
    opciones = []
    for i in range(n):
        opciones.append((sum(matriz[i][j] != 0 for j in range(n)), 0, i, "fila"))
        opciones.append((sum(matriz[j][i] != 0 for j in range(n)), 1, i, "columna"))
    cantidad, _, indice, tipo = min(opciones)
    return tipo, indice, cantidad


# =========================================================
# BLOQUE 2. LOS CINCO CRITERIOS DE RECOMENDACIÓN PREVIA
# =========================================================

def _contar_terminos_teoricos(matriz, orden_filas, limite=10**15):
    """Estima expansiones recursivas SIN almacenar menores repetidos.

    Solo se examina qué coeficientes son cero: NO se calcula el determinante.
    Esta estimación teórica no representa segundos ni operaciones exactas de LU.
    """
    n = len(matriz)

    @lru_cache(maxsize=None)
    def contar(profundidad, mascara):
        if profundidad == n:
            return 0
        total = 0
        posicion = 0
        disponibles = mascara
        while disponibles:
            bit = disponibles & -disponibles
            j = bit.bit_length() - 1
            if matriz[orden_filas[profundidad]][j] != 0:
                total += 1 + contar(profundidad + 1, mascara ^ bit)
                if total > limite:
                    return limite
            posicion += 1
            disponibles ^= bit
        return total

    return contar(0, (1 << n) - 1)


def analizar_eficiencia(matriz):
    """Recomendación breve; el usuario siempre conserva la elección."""
    a = normalizar_matriz(matriz)
    n = len(a)
    superior = all(a[i][j] == 0 for i in range(n) for j in range(i))
    inferior = all(a[i][j] == 0 for i in range(n) for j in range(i + 1, n))
    diagonal = superior and inferior
    ceros = sum(v == 0 for fila in a for v in fila)
    tipo, indice, terminos = _elegir_linea(a)
    trabajo = _transponer(a) if tipo == "columna" else a
    orden_filas = [indice] + [i for i in range(n) if i != indice]
    costo = _contar_terminos_teoricos(trabajo, orden_filas)
    referencia = n ** 3
    if n <= 2:
        metodo, razon = "cofactores", "Orden pequeño; expansión directa."
    elif n == 3:
        if terminos <= 1:
            metodo, razon = "cofactores", "Una línea tiene como máximo un término no nulo."
        else:
            metodo, razon = "sarrus", "Orden 3×3: seis productos diagonales."
    elif superior or inferior:
        metodo, razon = "cofactores", "Matriz triangular: basta el producto diagonal."
    elif costo <= referencia // 2:
        metodo, razon = "cofactores", "Los ceros simplifican el desarrollo."
    else:
        metodo, razon = "lu", "Orden elevado y pocos ceros: eliminación cúbica."
    forma = ("diagonal" if diagonal else "triangular superior" if superior
             else "triangular inferior" if inferior else "general")
    criterios = [
        f"Orden: {n}×{n} · matriz cuadrada válida.",
        f"Estructura: {forma} · ceros: {ceros}/{n*n}.",
        f"Mejor línea de cofactores: {tipo} {indice+1} ({terminos} términos).",
        f"Costo orientativo: cofactores {costo} términos; LU ≈ n³ = {referencia}.",
        "Profe Iván: cofactores ≤3; LU ≥4 (preferencia inicial).",
        "Sarrus: solo 3×3 · Gauss: cualquier orden cuadrado.",
    ]
    return {
        "orden": n, "metodo": metodo, "motivo": razon,
        "criterios": criterios, "tipo_linea": tipo, "indice_linea": indice,
        "forma": forma, "ceros": ceros, "costo_cofactores": costo,
        "referencia_lu": referencia,
    }


# =========================================================
# BLOQUE 3. CÁLCULO RECURSIVO EXACTO POR COFACTORES
# =========================================================

def _desarrollo_cofactores_completo(matriz_original, valor_esperado):
    """Árbol de Laplace íntegro: matrices y cuentas, sin frases repetidas."""
    recorrido = []
    lineas = ["COFACTORES · DESARROLLO COMPLETO", "-" * 58]

    @lru_cache(maxsize=None)
    def valor_menor(datos):
        n = len(datos)
        if n == 1:
            return datos[0][0]
        if n == 2:
            return datos[0][0]*datos[1][1] - datos[0][1]*datos[1][0]
        tipo, indice, _ = _elegir_linea(datos)
        total = Fraction(0)
        for k in range(n):
            i, j = (indice, k) if tipo == 'fila' else (k, indice)
            if datos[i][j] == 0:
                continue
            menor = tuple(tuple(datos[r][c] for c in range(n) if c != j)
                          for r in range(n) if r != i)
            signo = 1 if (i+j)%2 == 0 else -1
            total += signo*datos[i][j]*valor_menor(menor)
        return total

    def elegir(matriz, nivel):
        if nivel == 1:
            return _elegir_linea(matriz)
        n = len(matriz)
        opciones = []
        for k in range(n):
            opciones.append((sum(matriz[i][k] != 0 for i in range(n)), 0, k, 'columna'))
            opciones.append((sum(matriz[k][j] != 0 for j in range(n)), 1, k, 'fila'))
        cantidad, _, indice, tipo = min(opciones)
        return tipo, indice, cantidad

    def desarrollar(datos, ruta, nivel):
        n = len(datos)
        margen = '  '*(nivel-1)
        interior = margen+'  '
        tabla = [list(fila) for fila in datos]
        lineas.extend([f"{margen}{ruta} · {n}×{n}",
                       *(margen+fila for fila in texto_matriz(tabla).splitlines())])
        if n == 1:
            valor = datos[0][0]
            recorrido.append(dict(tipo="base", nombre=ruta, matriz=tabla, valor=valor))
            lineas.extend([f"{margen}det({ruta}) = {texto_numero(valor)}", ""])
            return valor
        if n == 2:
            a,b = datos[0]; c,d = datos[1]
            valor = a*d-b*c
            recorrido.append(dict(tipo="base", nombre=ruta, matriz=tabla, valor=valor))
            lineas.extend([
                f"{margen}ad - bc = ({texto_numero(a)})({texto_numero(d)})"
                f" - ({texto_numero(b)})({texto_numero(c)}) = {texto_numero(valor)}", ""])
            return valor
        tipo, indice, _ = elegir(datos, nivel)
        recorrido.append(dict(tipo="expandir", nombre=ruta, matriz=tabla, linea=tipo, indice=indice))
        lineas.extend([f"{margen}Signos (−1)^(i+j); expansión por {tipo} {indice+1}:",
                       *(margen+fila for fila in matriz_con_signos_cofactores(tabla, tipo, indice).splitlines())])
        total = Fraction(0)
        aportes = []
        for k in range(n):
            i,j = (indice,k) if tipo == 'fila' else (k,indice)
            coef = datos[i][j]
            if coef == 0:
                continue
            signo = 1 if (i+j)%2 == 0 else -1
            menor = tuple(tuple(datos[r][c] for c in range(n) if c != j)
                          for r in range(n) if r != i)
            ruta_hijo = f"M{i+1}{j+1}" if nivel == 1 else f"{ruta}/M{i+1}{j+1}"
            lineas.extend([f"{margen}a({i+1},{j+1})={texto_numero(coef)}; "
                           f"signo={'+' if signo>0 else '-'}; quitar F{i+1}, C{j+1}:"])
            recorrido.append(dict(tipo="menor", nombre=ruta_hijo, matriz=tabla, menor=menor, fila=i,
                                  columna=j, signo=signo, coeficiente=coef))
            valor = desarrollar(menor, ruta_hijo, nivel+1)
            if valor != valor_menor(menor):
                raise ArithmeticError("El menor recursivo no coincide.")
            aporte = signo*coef*valor
            total += aporte
            aportes.append((signo,coef,valor,aporte))
            lineas.append(f"{interior}({signo})({texto_numero(coef)})"
                          f"({texto_numero(valor)}) = {texto_numero(aporte)}")
        recorrido.append(dict(tipo="suma", nombre=ruta, matriz=tabla, aportes=aportes, valor=total))
        if aportes:
            lineas.append(f"{margen}det({ruta}) = " + " + ".join(
                f"({texto_numero(p)})" for _,_,_,p in aportes) +
                f" = {texto_numero(total)}")
        else:
            lineas.append(f"{margen}Línea nula → det({ruta}) = 0")
        if total != valor_menor(datos):
            raise ArithmeticError("El desarrollo no coincide con el cálculo exacto.")
        lineas.append("")
        return total

    datos = tuple(tuple(valor for valor in fila) for fila in matriz_original)
    total = desarrollar(datos, "A", 1)
    if total != valor_esperado:
        raise ArithmeticError("El desarrollo completo no coincide con el resultado.")
    lineas.append(f"RESULTADO POR COFACTORES: det(A) = {texto_numero(total)}")
    return lineas, recorrido


def _resolver_cofactores_normalizada(a, detalle=True):
    """Calcula el determinante exacto; opcionalmente describe TODOS los menores."""
    n = len(a)
    tipo, indice, _ = _elegir_linea(a)
    trabajo = _transponer(a) if tipo == "columna" else a
    orden_filas = [indice] + [i for i in range(n) if i != indice]
    mascara_completa = (1 << n) - 1
    signo_filas = -1 if indice % 2 else 1

    @lru_cache(maxsize=None)
    def recursivo(profundidad, mascara):
        if profundidad == n:
            return Fraction(1)
        total = Fraction(0)
        posicion = 0
        disponibles = mascara
        while disponibles:
            bit = disponibles & -disponibles
            j = bit.bit_length() - 1
            coeficiente = trabajo[orden_filas[profundidad]][j]
            if coeficiente != 0:
                signo = -1 if posicion % 2 else 1
                total += signo * coeficiente * recursivo(profundidad+1, mascara ^ bit)
            posicion += 1
            disponibles ^= bit
        return total

    valor = signo_filas * recursivo(0, mascara_completa)
    pasos, recorrido = _desarrollo_cofactores_completo(a, valor) if detalle else ([], [])
    return {"valor": valor, "pasos": pasos, "recorrido": recorrido, "linea": (tipo, indice)}


def calcular_cofactores(matriz, detalle=True):
    """Devuelve el determinante exacto y el procedimiento de Laplace."""
    return _resolver_cofactores_normalizada(normalizar_matriz(matriz), detalle)


# =========================================================
# BLOQUE 4. FACTORIZACIÓN LU REUTILIZADA Y PA=LU CON PIVOTEO
# =========================================================

def _factorizar_con_intercambios(a):
    """Construye PA=LU cuando el código LU original necesita intercambiar filas."""
    n = len(a)
    p, l, u = identidad(n), identidad(n), copiar_matriz(a)
    pasos = []
    intercambios = 0
    for k in range(n - 1):
        if u[k][k] == 0:
            nueva = next((i for i in range(k + 1, n) if u[i][k] != 0), None)
            if nueva is not None:
                u[k], u[nueva] = u[nueva], u[k]
                p[k], p[nueva] = p[nueva], p[k]
                for j in range(k):
                    l[k][j], l[nueva][j] = l[nueva][j], l[k][j]
                intercambios += 1
                pasos.append({
                    "tipo": "intercambio", "operacion": f"F{k+1} ↔ F{nueva+1}",
                    "P": copiar_matriz(p), "L": copiar_matriz(l), "U": copiar_matriz(u),
                })
        pivote = u[k][k]
        if pivote == 0:
            pasos.append({"tipo": "sin_pivote", "columna": k, "U": copiar_matriz(u)})
            continue
        for i in range(k + 1, n):
            if u[i][k] == 0:
                continue
            valor_original = u[i][k]
            fila_antes = u[i][:]
            fila_pivote = u[k][:]
            factor = valor_original / pivote
            l[i][k] = factor
            for j in range(k, n):
                u[i][j] -= factor * u[k][j]
            pasos.append({
                "tipo": "eliminacion", "columna": k, "fila": i,
                "pivote": pivote, "multiplicador": factor,
                "valor_eliminado": valor_original,
                "fila_antes": fila_antes, "fila_pivote": fila_pivote,
                "operacion": f"F{i+1} ← F{i+1} − ({texto_numero(factor)})F{k+1}",
                "P": copiar_matriz(p), "L": copiar_matriz(l), "U": copiar_matriz(u),
            })
    return p, l, u, pasos, intercambios, "PA = LU (con intercambios)"


def calcular_lu(matriz, detalle=True):
    """Obtiene det(A) con L y U, teniendo en cuenta los intercambios de filas.

    Reutiliza el algoritmo A=LU del módulo existente siempre que sea posible.
    Si necesita pivoteo, construye PA=LU y aplica el factor (-1)^s.
    """
    a = normalizar_matriz(matriz)
    try:
        previo = factorizar_lu(a)
        p, l, u = identidad(len(a)), previo["L"], previo["U"]
        pasos, intercambios = previo["pasos"], 0
        modalidad = "A = LU (sin intercambios; procedimiento del módulo LU existente)"
    except RequiereIntercambioFilas:
        p, l, u, pasos, intercambios, modalidad = _factorizar_con_intercambios(a)

    producto_pa = multiplicar_matrices(p, a)
    producto_lu = multiplicar_matrices(l, u)
    verificada = producto_pa == producto_lu
    if not verificada:
        raise ArithmeticError("Error interno: P·A y L·U no coinciden.")
    producto_diagonal = Fraction(1)
    for i in range(len(a)):
        producto_diagonal *= u[i][i]
    signo = -1 if intercambios % 2 else 1
    determinante = signo * producto_diagonal
    return {
        "valor": determinante, "A": a, "P": p, "L": l, "U": u,
        "pasos": pasos if detalle else [], "intercambios": intercambios,
        "signo": signo, "producto_diagonal": producto_diagonal,
        "producto_pa": producto_pa, "producto_lu": producto_lu,
        "verificacion": verificada, "modalidad": modalidad,
    }


# =========================================================
# BLOQUE 5. GAUSS Y REGLA DE SARRUS
# =========================================================

def calcular_gauss(matriz, detalle=True):
    """Determinante por eliminación gaussiana sin escalar filas; signo por permutas."""
    a = normalizar_matriz(matriz)
    n = len(a)
    u = copiar_matriz(a)
    intercambios = 0
    pasos = []
    for k in range(n):
        if u[k][k] == 0:
            pivote_nuevo = next((i for i in range(k+1, n) if u[i][k] != 0), None)
            if pivote_nuevo is None:
                if detalle:
                    pasos.append({"tipo":"sin_pivote", "columna":k, "U":copiar_matriz(u)})
                return {"valor":Fraction(0), "U":u, "intercambios":intercambios,
                        "producto_diagonal":Fraction(0), "pasos":pasos}
            u[k],u[pivote_nuevo] = u[pivote_nuevo],u[k]
            intercambios += 1
            if detalle:
                pasos.append({"tipo":"intercambio", "operacion":f"F{k+1} ↔ F{pivote_nuevo+1}",
                              "U":copiar_matriz(u)})
        pivote = u[k][k]
        for i in range(k+1,n):
            if u[i][k] == 0:
                continue
            original = u[i][:]
            fila_pivote = u[k][:]
            m = u[i][k]/pivote
            for j in range(k,n):
                u[i][j] -= m*u[k][j]
            if detalle:
                pasos.append({"tipo":"eliminacion", "fila":i,"columna":k,
                              "multiplicador":m,"pivote":pivote,
                              "fila_antes":original,"fila_pivote":fila_pivote,
                              "U":copiar_matriz(u)})
    diagonal = Fraction(1)
    for i in range(n):
        diagonal *= u[i][i]
    valor = (-1 if intercambios%2 else 1)*diagonal
    return {"valor":valor,"U":u,"intercambios":intercambios,
            "producto_diagonal":diagonal,"pasos":pasos}


def calcular_sarrus(matriz, detalle=True):
    """Regla de Sarrus exacta; exclusivamente para matrices 3×3."""
    a = normalizar_matriz(matriz)
    if len(a) != 3:
        raise ValueError("La regla de Sarrus solo se aplica a matrices 3×3.")
    positivos = []
    negativos = []
    for j in range(3):
        positivos.append(tuple(a[i][(j+i)%3] for i in range(3)))
        negativos.append(tuple(a[i][(j-i)%3] for i in range(3)))
    sum_pos = sum((x*y*z for x,y,z in positivos), Fraction(0))
    sum_neg = sum((x*y*z for x,y,z in negativos), Fraction(0))
    return {"valor":sum_pos-sum_neg, "positivos":positivos,
            "negativos":negativos,"suma_positiva":sum_pos,
            "suma_negativa":sum_neg,"pasos":[]}


# =========================================================
# BLOQUE 6. VERIFICACIÓN CRUZADA DEL RESULTADO
# =========================================================


def resolver_determinante(matriz, metodo):
    """Calcula el método escogido y comprueba con métodos independientes exactos."""
    a = normalizar_matriz(matriz)
    if metodo not in ("cofactores", "lu", "gauss", "sarrus"):
        raise ValueError("Elige cofactores, LU, Gauss o Sarrus.")
    if metodo == "sarrus" and len(a) != 3:
        raise ValueError("Sarrus se usa exclusivamente con matrices 3×3.")
    analisis = analizar_eficiencia(a)
    # Los desarrollos extensos solo se generan para el método escogido.
    cofactores = calcular_cofactores(a, detalle=(metodo == "cofactores"))
    lu = calcular_lu(a, detalle=(metodo == "lu"))
    gauss = calcular_gauss(a, detalle=(metodo == "gauss"))
    sarrus = calcular_sarrus(a, detalle=(metodo == "sarrus")) if len(a) == 3 else None
    valores = {"cofactores":cofactores["valor"], "lu":lu["valor"],
               "gauss":gauss["valor"]}
    if sarrus is not None:
        valores["sarrus"] = sarrus["valor"]
    if len(set(valores.values())) != 1 or not lu["verificacion"]:
        raise ArithmeticError("La verificación exacta entre métodos no coincide.")
    return {"A":a, "metodo":metodo, "analisis":analisis,
            "resultado":valores[metodo], "cofactores":cofactores,
            "lu":lu,"gauss":gauss,"sarrus":sarrus,"valores":valores,
            "verificacion_cruzada":True,
            "verificacion_factorizacion":lu["verificacion"]}
