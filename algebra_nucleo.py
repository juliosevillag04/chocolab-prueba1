"""Motor de conversiones de bases y expresiones matriciales, extraído de Choco Lab Tkinter."""

import ast

import re

from fractions import Fraction

from algebra_determinantes import resolver_determinante

from algebra_eliminacion import invertir_matriz_gauss_jordan, resolver_sistema, convertir_sistema_ecuaciones

from algebra_lu import factorizar_lu, resolver_axb_lu, generar_matriz_lu_aleatoria, generar_sistema_lu_aleatorio

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

def _determinante_con_pasos(matriz, transformaciones=None):
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
            if transformaciones is not None:
                transformaciones.append({"operacion": pasos[-1], "matriz": [r[:] for r in trabajo]})

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
            if transformaciones is not None:
                transformaciones.append({"operacion": pasos[-1], "matriz": [r[:] for r in trabajo]})

    return signo * determinante, pasos

class EvaluadorOriginal:

    """Evaluación AST segura y aritmética de Fraction tomadas del código de escritorio."""

    FUNCIONES={"T","det"}

    def __init__(self,objetos):

        self.objetos=objetos

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
                transformaciones = []
                resultado, pasos_det = _determinante_con_pasos(valor, transformaciones)
                pasos.append({
                    "tipo": "determinante", "a": valor, "r": resultado,
                    "ea": etiqueta, "detalle": pasos_det, "transformaciones": transformaciones
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


class ConversorBases:

    DIGITOS='0123456789ABCDEF'

    BASES={'Decimal (base 10)':10,'Binario (base 2)':2,'Octal (base 8)':8,'Hexadecimal (base 16)':16}

    def _normalizar(self, texto, base): #Conversión de sistemas numéricos
        limpio = (
            texto.strip()
            .upper()
            .replace("_", "")
            .replace(" ", "")
            .replace(",", ".")
        )

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

        if limpio.count(".") > 1:
            raise ValueError("Solo se permite un punto fraccionario.")

        permitidos = set(self.DIGITOS[:base]) | {"."}
        invalidos = sorted(set(limpio) - permitidos)

        if invalidos:
            raise ValueError(
                f"El dígito «{invalidos[0]}» no pertenece a la base {base}."
            )

        parte_entera, separador, parte_fraccionaria = limpio.partition(".")

        if parte_entera == "" and parte_fraccionaria == "":
            raise ValueError("Debes escribir al menos un dígito.")

        if parte_entera == "":
            parte_entera = "0"

        if separador and parte_fraccionaria == "":
            limpio = parte_entera
        elif separador:
            limpio = parte_entera + "." + parte_fraccionaria
        else:
            limpio = parte_entera

        return signo + limpio

    def _a_decimal(self, numero_limpio, base):
        negativo = numero_limpio.startswith("-")
        sin_signo = numero_limpio.lstrip("+-")
        parte_entera, separador, parte_fraccionaria = sin_signo.partition(".")

        valor = Fraction(0)

        for caracter in parte_entera:
            valor = valor * base + self.DIGITOS.index(caracter)

        if separador:
            potencia = base
            for caracter in parte_fraccionaria:
                valor += Fraction(self.DIGITOS.index(caracter), potencia)
                potencia *= base

        return -valor if negativo else valor

    def _representar(self, numero_decimal, base, max_decimales=24):
        numero = Fraction(numero_decimal)
        signo = "-" if numero < 0 else ""
        numero = abs(numero)

        if numero == 0:
            return "0"

        parte_entera = numero.numerator // numero.denominator
        parte_fraccionaria = numero - parte_entera

        if parte_entera == 0:
            texto_entero = "0"
        else:
            digitos_enteros = []
            actual = parte_entera

            while actual > 0:
                actual, residuo = divmod(actual, base)
                digitos_enteros.append(self.DIGITOS[residuo])

            texto_entero = "".join(reversed(digitos_enteros))

        if parte_fraccionaria == 0:
            return signo + texto_entero

        digitos_fraccionarios = []
        actual = parte_fraccionaria

        for _ in range(max_decimales):
            if actual == 0:
                break

            actual *= base
            digito = actual.numerator // actual.denominator
            digitos_fraccionarios.append(self.DIGITOS[digito])
            actual -= digito

        sufijo = "…" if actual != 0 else ""

        return (
            signo
            + texto_entero
            + "."
            + "".join(digitos_fraccionarios)
            + sufijo
        )

    def _expansion_posicional(self, numero_limpio, base):
        negativo = numero_limpio.startswith("-")
        sin_signo = numero_limpio.lstrip("+-")
        parte_entera, separador, parte_fraccionaria = sin_signo.partition(".")
        terminos = []

        for posicion, caracter in enumerate(parte_entera):
            exponente = len(parte_entera) - posicion - 1
            valor = self.DIGITOS.index(caracter)
            terminos.append(f"{valor}×{base}^{exponente}")

        if separador:
            for posicion, caracter in enumerate(parte_fraccionaria, start=1):
                valor = self.DIGITOS.index(caracter)
                terminos.append(f"{valor}×{base}^-{posicion}")

        expresion = " + ".join(terminos) if terminos else "0"

        if negativo:
            return f"−({expresion})"

        return expresion

    def _pasos_division(self, numero_decimal, base, max_decimales=24):
        numero = abs(Fraction(numero_decimal))

        if numero == 0:
            return ["0 ya se representa como 0."]

        pasos = []
        parte_entera = numero.numerator // numero.denominator
        parte_fraccionaria = numero - parte_entera

        pasos.append("Parte entera: divisiones sucesivas.")

        if parte_entera == 0:
            pasos.append("La parte entera es 0.")
        else:
            actual = parte_entera

            while actual > 0:
                cociente, residuo = divmod(actual, base)
                pasos.append(
                    f"{actual} ÷ {base} = {cociente}, "
                    f"residuo {self.DIGITOS[residuo]}"
                )
                actual = cociente

            pasos.append(
                "Los residuos de la parte entera se leen desde el último "
                "hasta el primero."
            )

        if parte_fraccionaria != 0:
            pasos.append("Parte fraccionaria: multiplicaciones sucesivas.")
            actual = parte_fraccionaria

            for _ in range(max_decimales):
                if actual == 0:
                    break

                producto = actual * base
                digito = producto.numerator // producto.denominator
                resto = producto - digito

                pasos.append(
                    f"{actual} × {base} = {producto} → "
                    f"dígito {self.DIGITOS[digito]}, "
                    f"fracción restante {resto}"
                )

                actual = resto

            if actual != 0:
                pasos.append(
                    f"Se muestran los primeros {max_decimales} dígitos "
                    "fraccionarios; la expansión continúa."
                )

            pasos.append(
                "Los dígitos fraccionarios se leen en el mismo orden "
                "en que fueron obtenidos."
            )

        return pasos
