"""Lógica pura de romanos y arábigos conservada de la aplicación original; sin interfaz Tkinter."""

import sys

from decimal import Decimal, InvalidOperation

from fractions import Fraction

try:
    sys.set_int_max_str_digits(100000)
except (AttributeError,ValueError):
    pass

COMBINING_OVERLINE = "\u0305"

COMBINING_DOUBLE_OVERLINE = "\u033F"

ROMAN_VALUES = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}

ROMAN_PAIRS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)

UNICODE_ROMAN_COMPAT = {
    "Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV",
    "Ⅴ": "V", "Ⅵ": "VI", "Ⅶ": "VII", "Ⅷ": "VIII",
    "Ⅸ": "IX", "Ⅹ": "X", "Ⅺ": "XI", "Ⅻ": "XII",
    "Ⅼ": "L", "Ⅽ": "C", "Ⅾ": "D", "Ⅿ": "M",
    "ⅰ": "I", "ⅱ": "II", "ⅲ": "III", "ⅳ": "IV",
    "ⅴ": "V", "ⅵ": "VI", "ⅶ": "VII", "ⅷ": "VIII",
    "ⅸ": "IX", "ⅹ": "X", "ⅺ": "XI", "ⅻ": "XII",
    "ⅼ": "L", "ⅽ": "C", "ⅾ": "D", "ⅿ": "M",
}

HISTORICAL_ALIASES = {
    "ↀ": "M",     # 1000
    "ↁ": "(V)",   # 5000
    "ↂ": "(X)",   # 10000
}

MAX_DECIMAL_DIGITS = 5000

MAX_VINCULUM_LEVEL = 1700

def classic_arabic_to_roman(number: int) -> str:
    """Convierte un entero de 1 a 3999 a romano moderno habitual."""
    if not isinstance(number, int):
        raise ValueError("El número debe ser entero.")
    if number < 1 or number > 3999:
        raise ValueError("La notación clásica de esta función admite de 1 a 3999.")

    result = []
    remaining = number

    for value, symbol in ROMAN_PAIRS:
        while remaining >= value:
            result.append(symbol)
            remaining -= value

    return "".join(result)

def classic_roman_to_int_strict(roman: str) -> int:
    """Convierte y valida un bloque romano clásico canónico."""
    roman = roman.strip().upper()

    if not roman:
        raise ValueError("Se encontró un bloque romano vacío.")

    if any(ch not in ROMAN_VALUES for ch in roman):
        raise ValueError(
            "Un bloque romano clásico solo puede contener I, V, X, L, C, D y M."
        )

    total = 0
    i = 0

    while i < len(roman):
        current = ROMAN_VALUES[roman[i]]

        if i + 1 < len(roman):
            nxt = ROMAN_VALUES[roman[i + 1]]
            if current < nxt:
                total += nxt - current
                i += 2
                continue

        total += current
        i += 1

    if total < 1 or total > 3999:
        raise ValueError("Cada bloque romano debe representar un valor entre 1 y 3999.")

    canonical = classic_arabic_to_roman(total)
    if roman != canonical:
        raise ValueError(
            f"'{roman}' no sigue la escritura romana canónica. "
            f"Para {total}, la forma habitual es {canonical}."
        )

    return total

def apply_overline(text: str, level: int) -> str:
    """
    Aplica visualmente 'level' barras superiores a cada letra.
    Ejemplo:
      apply_overline("IV", 1) -> I̅V̅
      apply_overline("IV", 2) -> I̅̅V̅̅
    """
    if level <= 0:
        return text
    marks = COMBINING_OVERLINE * level
    return "".join(ch + marks for ch in text)

def wrap_keyboard(text: str, level: int) -> str:
    """Notación fácil de teclado: (IV)=×1000, ((IV))=×1 000 000."""
    if level <= 0:
        return text
    return "(" * level + text + ")" * level

def _extended_components(number: int):
    """
    Devuelve componentes (romano_del_bloque, nivel, valor_del_componente).

    Para 1..3999 conserva la notación clásica completa.
    Para valores mayores divide en grupos de 3 cifras (base 1000):
      4 567 890 -> ((IV))(DLXVII)DCCCXC
    """
    if not isinstance(number, int):
        raise ValueError("El número debe ser entero.")
    if number < 1:
        raise ValueError("Los números romanos de esta aplicación representan enteros positivos.")

    if number <= 3999:
        return [(classic_arabic_to_roman(number), 0, number)]

    components = []
    level = 0
    remaining = number

    while remaining > 0:
        chunk = remaining % 1000
        if chunk:
            roman_chunk = classic_arabic_to_roman(chunk)
            components.append(
                (roman_chunk, level, chunk * (1000 ** level))
            )
        remaining //= 1000
        level += 1

        if level > MAX_VINCULUM_LEVEL:
            raise ValueError(
                "El número necesita demasiados niveles de vinculum para mostrarse en la interfaz."
            )

    return list(reversed(components))

def arabic_to_extended_roman(number: int) -> str:
    """Representación visual con barras superiores combinables."""
    return "".join(
        apply_overline(roman, level)
        for roman, level, _ in _extended_components(number)
    )

def arabic_to_extended_keyboard(number: int) -> str:
    """Representación equivalente, fácil de escribir con teclado."""
    return "".join(
        wrap_keyboard(roman, level)
        for roman, level, _ in _extended_components(number)
    )

def normalize_roman_input(text: str) -> str:
    """Normaliza espacios, minúsculas, glifos Unicode y algunos signos históricos."""
    if text is None:
        raise ValueError("Ingrese un número romano.")

    text = text.strip()
    if not text:
        raise ValueError("Ingrese un número romano.")

    # Primero reemplazar caracteres romanos Unicode compatibles.
    for glyph, replacement in UNICODE_ROMAN_COMPAT.items():
        text = text.replace(glyph, replacement)

    # Luego aliases históricos reconocidos.
    for glyph, replacement in HISTORICAL_ALIASES.items():
        text = text.replace(glyph, replacement)

    # Se permiten espacios visuales entre grupos.
    text = "".join(text.split()).upper()

    return text

def tokenize_extended_roman(text: str):
    """
    Convierte una entrada romana en tokens (letra, nivel_vinculum).

    Formas aceptadas:
      XIV
      (IV)
      ((IV))
      I̅V̅
      I̅̅V̅̅
      ↁ  ↂ
    """
    text = normalize_roman_input(text)

    tokens = []
    depth = 0
    i = 0

    while i < len(text):
        ch = text[i]

        if ch == "(":
            depth += 1
            if depth > MAX_VINCULUM_LEVEL:
                raise ValueError("Hay demasiados niveles de paréntesis/vinculum.")
            i += 1
            continue

        if ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("Hay un paréntesis de cierre ')' sin apertura.")
            i += 1
            continue

        if ch in ROMAN_VALUES:
            level = depth
            i += 1

            # Una o más barras combinables también elevan el nivel.
            while i < len(text):
                if text[i] == COMBINING_OVERLINE:
                    level += 1
                    i += 1
                elif text[i] == COMBINING_DOUBLE_OVERLINE:
                    level += 2
                    i += 1
                else:
                    break

            if level > MAX_VINCULUM_LEVEL:
                raise ValueError("El numeral contiene demasiados niveles de vinculum.")

            tokens.append((ch, level))
            continue

        if ch in (COMBINING_OVERLINE, COMBINING_DOUBLE_OVERLINE):
            raise ValueError(
                "Una barra superior debe ir inmediatamente después de una letra romana."
            )

        raise ValueError(
            f"El carácter '{ch}' no es válido. "
            "Use I, V, X, L, C, D, M, paréntesis, barras superiores o ↀ/ↁ/ↂ."
        )

    if depth != 0:
        raise ValueError("Los paréntesis del numeral romano no están equilibrados.")

    if not tokens:
        raise ValueError("Ingrese al menos un símbolo romano.")

    return tokens

def tokens_to_groups(tokens):
    """
    Agrupa letras contiguas que comparten el mismo nivel de vinculum.
    Los niveles deben ir de mayor a menor de izquierda a derecha.
    """
    groups = []
    current_level = None
    letters = []

    for letter, level in tokens:
        if current_level is None:
            current_level = level
            letters = [letter]
            continue

        if level == current_level:
            letters.append(letter)
        else:
            groups.append(("".join(letters), current_level))
            current_level = level
            letters = [letter]

    groups.append(("".join(letters), current_level))

    # La escritura adoptada por el programa ordena primero las magnitudes mayores.
    levels = [level for _, level in groups]
    if any(levels[i] < levels[i + 1] for i in range(len(levels) - 1)):
        raise ValueError(
            "Los niveles de vinculum deben escribirse de mayor a menor. "
            "Ejemplo correcto: (IV)CM = 4900."
        )

    return groups

def roman_to_arabic_extended(text: str):
    """
    Convierte una entrada romana clásica o extendida a entero.

    Devuelve:
      value,
      canonical_visual,
      canonical_keyboard,
      input_groups
    """
    tokens = tokenize_extended_roman(text)
    groups = tokens_to_groups(tokens)

    total = 0
    interpreted = []

    for letters, level in groups:
        block_value = classic_roman_to_int_strict(letters)
        group_value = block_value * (1000 ** level)
        total += group_value
        interpreted.append((letters, level, block_value, group_value))

    if total < 1:
        raise ValueError("El numeral debe representar un entero positivo.")

    canonical_visual = arabic_to_extended_roman(total)
    canonical_keyboard = arabic_to_extended_keyboard(total)

    return total, canonical_visual, canonical_keyboard, interpreted

def parse_arabic_integer(text: str) -> int:
    """
    Acepta enteros y notación científica exacta:
      4500
      4.5e3
      1e6
    Solo se aceptan valores cuyo resultado sea un entero positivo.
    """
    if text is None:
        raise ValueError("Ingrese un número arábigo.")

    clean = text.strip().replace("_", "").replace(" ", "")
    if not clean:
        raise ValueError("Ingrese un número arábigo.")

    # Evitar una expansión accidental absurda antes de construir el entero.
    lower = clean.lower()
    if "e" in lower:
        try:
            exponent_text = lower.split("e", 1)[1]
            exponent = int(exponent_text)
            if abs(exponent) > MAX_DECIMAL_DIGITS:
                raise ValueError(
                    f"Por seguridad visual, la notación científica admite exponentes "
                    f"de hasta ±{MAX_DECIMAL_DIGITS}."
                )
        except ValueError as exc:
            if "seguridad visual" in str(exc):
                raise
            # Decimal dará después el mensaje principal.

    try:
        value = Decimal(clean)
    except InvalidOperation:
        raise ValueError(
            "Ingrese un entero arábigo válido. También puede usar notación científica, "
            "por ejemplo 4.5e3 o 1e6."
        )

    if not value.is_finite():
        raise ValueError("El valor debe ser finito.")

    if value <= 0:
        raise ValueError("Los números romanos representan enteros positivos.")

    integral = value.to_integral_value()
    if value != integral:
        raise ValueError(
            "La entrada arábiga debe equivaler exactamente a un entero. "
            "Ejemplo válido: 4.5e3 = 4500."
        )

    adjusted = integral.adjusted()
    if adjusted + 1 > MAX_DECIMAL_DIGITS:
        raise ValueError(
            f"El número supera el límite práctico de {MAX_DECIMAL_DIGITS} cifras "
            "adoptado para evitar bloquear la interfaz."
        )

    return int(integral)

def parse_value(text: str, number_type: str) -> int:
    if number_type == "Arábigo":
        return parse_arabic_integer(text)

    if number_type == "Romano":
        value, _, _, _ = roman_to_arabic_extended(text)
        return value

    raise ValueError("Seleccione un tipo de número válido.")

def pretty_number(value):
    """Formato legible para enteros y fracciones exactas."""
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"

    if isinstance(value, int):
        return str(value)

    return str(value)

def roman_if_possible(value):
    if isinstance(value, Fraction):
        if value.denominator != 1:
            return None
        value = value.numerator

    if isinstance(value, int) and value >= 1:
        return arabic_to_extended_roman(value)

    return None

def compact_int(number: int, max_chars=110):
    """
    Muestra completo un entero razonable; para uno gigantesco presenta inicio,
    final y cantidad de cifras para no destruir la interfaz.
    """
    text = str(number)
    if len(text) <= max_chars:
        return text
    return f"{text[:48]}…{text[-24:]}  ({len(text)} cifras)"

def format_with_separators(number: int):
    text = str(number)
    if len(text) > 90:
        return compact_int(number)
    return f"{number:,}"
