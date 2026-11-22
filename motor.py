"""Núcleo matemático independiente de la interfaz.

No utiliza rutinas de bibliotecas para resolver raíces; Bisección, Regla
Falsa, Newton-Raphson y la detección de intervalos están programados aquí.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import sympy as sp

X = sp.Symbol('x', real=True)
ALLOWED_FUNCTIONS = {
    'sin': sp.sin, 'sen': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'tg': sp.tan, 'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    'sqrt': sp.sqrt, 'raiz': sp.sqrt, 'abs': sp.Abs,
    'ln': sp.log, 'log': sp.log, 'log10': lambda v: sp.log(v, 10),
    'exp': sp.exp,
}
CONSTANTS = {'x': X, 'pi': sp.pi, 'e': sp.E}
TOKEN_RE = re.compile(r'\s*(?:(\d+(?:\.\d*)?|\.\d+)(?:([eE][+-]?\d+))?|([A-Za-z_]+)|([+\-*/^(),]))')

class EntradaInvalida(ValueError):
    """Error claro para el usuario, sin mostrar trazas internas."""


def latex_a_texto(raw: str) -> str:
    """Convierte el subconjunto de LaTeX necesario para el teclado MathLive."""
    raw = str(raw or '').strip()
    if len(raw) > 320:
        raise EntradaInvalida('La ecuación es demasiado larga (máximo 320 caracteres).')
    raw = re.sub(r'^\s*f\s*\(\s*x\s*\)\s*=\s*', '', raw, flags=re.I)
    raw = raw.replace('−', '-').replace('×', '*').replace('÷', '/')
    raw = raw.replace('π', 'pi').replace('√', 'sqrt')
    raw = raw.replace('\\left', '').replace('\\right', '')
    raw = raw.replace('\\cdot', '*').replace('\\times', '*')
    raw = raw.replace('\\pi', 'pi').replace('\\mathrm{e}', 'e')
    raw = raw.replace('\\operatorname{', '\\fn{')
    # El lector reconoce grupos anidados, sin ejecutar texto de la expresión.
    def group(s: str, start: int, opener='{', closer='}'):
        if start >= len(s) or s[start] != opener:
            raise EntradaInvalida('Faltan llaves o paréntesis en la fórmula.')
        depth = 1
        for i in range(start + 1, len(s)):
            if s[i] == opener: depth += 1
            if s[i] == closer: depth -= 1
            if depth == 0: return s[start+1:i], i+1
        raise EntradaInvalida('Hay llaves o paréntesis sin cerrar.')
    def convert(s: str, depth=0) -> str:
        if depth > 14: raise EntradaInvalida('La ecuación tiene demasiados niveles de anidamiento.')
        out, i = [], 0
        while i < len(s):
            if s.startswith('\\frac', i) or s.startswith('\\dfrac', i):
                i += 6 if s.startswith('\\dfrac', i) else 5
                a,i = group(s,i)
                b,i = group(s,i)
                out.append(f'(({convert(a, depth+1)})/({convert(b, depth+1)}))')
            elif s.startswith('\\sqrt',i):
                i += 5
                degree = None
                if i < len(s) and s[i] == '[':
                    degree,i = group(s,i,'[',']')
                b,i = group(s,i)
                if degree is not None:
                    out.append(f'(({convert(b,depth+1)})^(1/({convert(degree,depth+1)})))')
                else: out.append(f'sqrt({convert(b,depth+1)})')
            elif s.startswith('\\fn',i):
                i += 3
                fun,i=group(s,i)
                out.append(fun)
            elif s[i] == '\\':
                match = re.match(r'\\([a-zA-Z]+)',s[i:])
                if not match: raise EntradaInvalida('Símbolo matemático no admitido.')
                name=match.group(1)
                names={'sin':'sin','cos':'cos','tan':'tan','ln':'ln','log':'log','arcsin':'asin','arccos':'acos','arctan':'atan','exp':'exp','operatorname':'', 'cdot':'*','times':'*'}
                if name not in names: raise EntradaInvalida(f'El comando \\{name} no está admitido en Choco Lab.')
                out.append(names[name]);i+=len(match.group(0))
            elif s[i]=='{':
                inner,i=group(s,i)
                out.append('('+convert(inner,depth+1)+')')
            else:
                out.append(s[i]);i+=1
        return ''.join(out)
    return convert(raw)


class SafeParser:
    def __init__(self,text):
        if not text.strip(): raise EntradaInvalida('Escribe primero una función de x.')
        self.tokens=[]; idx=0
        while idx<len(text):
            if text[idx:].isspace(): break
            m=TOKEN_RE.match(text,idx)
            if not m: raise EntradaInvalida(f'Símbolo no admitido cerca de: {text[idx:idx+10]!r}.')
            num, exponent, name, op = m.groups()
            if num is not None:
                v = float(num + (exponent or ''))
                if not math.isfinite(v): raise EntradaInvalida('Constante numérica demasiado grande.')
                self.tokens.append(('number',sp.Float(v) if '.' in num or exponent else sp.Integer(num)))
            elif name: self.tokens.append(('name',name.lower()))
            else: self.tokens.append((op,op))
            idx=m.end()
            if len(self.tokens)>170: raise EntradaInvalida('La fórmula supera el límite de complejidad.')
        self.tokens.append(('EOF',''))
        self.i=0
        self.steps=0
    def at(self,t): return self.tokens[self.i][0]==t
    def pop(self,t=None):
        value=self.tokens[self.i]
        if t and value[0]!=t: raise EntradaInvalida(f'Se esperaba {t} en la ecuación.')
        self.i+=1
        self.steps+=1
        if self.steps>600: raise EntradaInvalida('La fórmula es demasiado compleja.')
        return value[1]
    def parse(self):
        result=self.sum()
        if not self.at('EOF'): raise EntradaInvalida('Hay elementos sin interpretar en la ecuación.')
        return result
    def sum(self):
        v=self.product()
        while self.at('+') or self.at('-'):
            op=self.pop(); w=self.product()
            v=v+w if op=='+' else v-w
        return v
    def product(self):
        v=self.unary()
        while True:
            if self.at('*') or self.at('/'):
                op=self.pop()
                w=self.unary()
                v=v*w if op=='*' else v/w
            elif self.at('number') or self.at('name') or self.at('('):
                v=v*self.unary()  # multiplicación implícita: 2x y 2(x+1)
            else: break
        return v
    def unary(self):
        if self.at('+'): self.pop();return self.unary()
        if self.at('-'): self.pop();return -self.unary()
        return self.power()
    def power(self):
        base=self.atom()
        if self.at('^'):
            self.pop()
            exponent=self.unary()
            if exponent.is_number and exponent.is_real:
                try:
                    ev=float(exponent)
                    if abs(ev)>30: raise EntradaInvalida('Los exponentes deben tener magnitud menor o igual que 30.')
                except (ValueError,TypeError,OverflowError):
                    raise EntradaInvalida('Exponente inválido.')
            base=base**exponent
        return base
    def atom(self):
        if self.at('number'): return self.pop()
        if self.at('('):
            self.pop();out=self.sum();self.pop(')');return out
        if self.at('name'):
            name=self.pop()
            if name in ALLOWED_FUNCTIONS:
                if not self.at('('):raise EntradaInvalida(f'Escribe {name}(...) con paréntesis.')
                self.pop('(');arg=self.sum();self.pop(')')
                return ALLOWED_FUNCTIONS[name](arg)
            if name not in CONSTANTS:
                raise EntradaInvalida(f'Variable o función desconocida: «{name}». Solo se admite x.')
            return CONSTANTS[name]
        raise EntradaInvalida('La ecuación contiene un operador o paréntesis fuera de lugar.')


@dataclass
class Funcion:
    texto: str
    expr: sp.Expr
    evaluador: object
    def en(self, xx: float):
        try:
            with np.errstate(all='ignore'):
                v=self.evaluador(float(xx))
            if isinstance(v,complex):
                if abs(v.imag)>1e-10: return None
                v=v.real
            v=float(v)
            if not math.isfinite(v) or abs(v)>1e100: return None
            return v
        except (ValueError,OverflowError,ZeroDivisionError,TypeError, FloatingPointError):
            return None
    def continuidad(self,a,b):
        # Comprobación simbólica de continuidad, conservadora cuando SymPy no determina el dominio.
        try:
            domain=sp.calculus.util.continuous_domain(self.expr,X,sp.S.Reals)
            is_continuous=sp.Interval(float(a),float(b)).is_subset(domain)
            return bool(is_continuous)
        except Exception:
            return False


@lru_cache(maxsize=256)
def crear_funcion(texto: str) -> Funcion:
    normal=latex_a_texto(texto)
    expression=SafeParser(normal).parse()
    if not expression.free_symbols.issubset({X}):
        raise EntradaInvalida('Solo puedes utilizar la variable x.')
    if expression.has(sp.zoo,sp.nan,sp.oo,-sp.oo,sp.I):
        raise EntradaInvalida('La función contiene valores no reales o indefinidos.')
    try:
        fn=sp.lambdify(X,expression,modules=[{'Abs':abs},'numpy'])
    except Exception:
        raise EntradaInvalida('No se puede evaluar esa expresión.')
    return Funcion(normal,expression,fn)


def numero(v,nombre, lo=-1e5,hi=1e5):
    try: x=float(v)
    except (TypeError,ValueError):raise EntradaInvalida(f'«{nombre}» debe ser un número.')
    if not math.isfinite(x) or not lo<=x<=hi:
        raise EntradaInvalida(f'«{nombre}» debe estar entre {lo:g} y {hi:g}.')
    return x


def biseccion(f:Funcion,a,b,tol=0.0001,max_it=100):
    a=numero(a,'a');b=numero(b,'b')
    tol=numero(tol,'Precisión',1e-12,1.0)
    if a>=b: raise EntradaInvalida('El límite a debe ser menor que b.')
    fa=f.en(a);fb=f.en(b)
    if fa is None or fb is None:raise EntradaInvalida('La función no está definida en uno de los extremos.')
    if not f.continuidad(a,b):
        raise EntradaInvalida('La función no es continua en todo [a, b] o no se puede demostrar su continuidad. Selecciona otro intervalo.')
    rows=[]
    if abs(fa)<1e-13: return {'raiz':a,'filas':rows,'iteraciones':0,'residuo':abs(fa),'cota':0.,'motivo':'El extremo a ya es una raíz.','a_inicial':a,'b_inicial':b}
    if abs(fb)<1e-13: return {'raiz':b,'filas':rows,'iteraciones':0,'residuo':abs(fb),'cota':0.,'motivo':'El extremo b ya es una raíz.','a_inicial':a,'b_inicial':b}
    if fa*fb>=0:
        raise EntradaInvalida('El intervalo no encierra un cambio de signo: f(a) y f(b) deben tener signos contrarios.')
    initial_a,initial_b=a,b
    for i in range(1,max_it+1):
        c=a+(b-a)/2
        fc=f.en(c)
        if fc is None: raise EntradaInvalida('La función dejó de estar definida dentro del intervalo.')
        # Igual que en el Excel del profesor: Error = |f(c)|.
        # La cota (b-a)/2 se conserva en la respuesta solo como dato auxiliar,
        # pero no determina cuándo finaliza el método.
        error=abs(fc)
        cota=(b-a)/2
        rows.append({'it':i,'a':a,'b':b,'c':c,'fa':fa,'fb':fb,'fc':fc,'error':error,
                     'decision':'Raíz encontrada' if abs(fc)<1e-13 else 'Precisión alcanzada' if error<=tol else 'b ← c' if fa*fc<0 else 'a ← c'})
        if abs(fc)<1e-13: motivo='Raíz exacta detectada (precisión numérica).';break
        if error<=tol:motivo='Residuo absoluto |f(c)| ≤ tolerancia.';break
        if fa*fc<0: b,fb=c,fc
        else: a,fa=c,fc
    else: motivo='Límite de iteraciones alcanzado.'
    return {'raiz':c,'filas':rows,'iteraciones':len(rows),'residuo':abs(fc),'cota':cota,
            'motivo':motivo,'a_inicial':initial_a,'b_inicial':initial_b}


def regla_falsa(f: Funcion, a, b, tol=0.0001, max_it=200):
    """Regula Falsi clásico: interpolación lineal con intervalo acotado.

    La tolerancia se aplica al residuo absoluto |f(Xr)|, igual que en
    bisección. Se conservan valores completos durante las iteraciones.
    """
    a = numero(a, 'a')
    b = numero(b, 'b')
    tol = numero(tol, 'Precisión', 1e-12, 1.0)
    if a >= b:
        raise EntradaInvalida('El límite a debe ser menor que b.')

    fa, fb = f.en(a), f.en(b)
    if fa is None or fb is None:
        raise EntradaInvalida('La función no está definida en uno de los extremos.')
    if not f.continuidad(a, b):
        raise EntradaInvalida('La función no es continua en todo [a, b] o no se puede demostrar su continuidad. Selecciona otro intervalo.')

    inicio_a, inicio_b = a, b
    filas = []
    if abs(fa) < 1e-13:
        return {'raiz': a, 'filas': filas, 'iteraciones': 0, 'residuo': abs(fa),
                'motivo': 'El extremo a ya es una raíz.', 'a_inicial': a,
                'b_inicial': b, 'convergencia': True}
    if abs(fb) < 1e-13:
        return {'raiz': b, 'filas': filas, 'iteraciones': 0, 'residuo': abs(fb),
                'motivo': 'El extremo b ya es una raíz.', 'a_inicial': a,
                'b_inicial': b, 'convergencia': True}
    if (fa > 0) == (fb > 0):
        raise EntradaInvalida('El intervalo no encierra un cambio de signo: f(a) y f(b) deben tener signos contrarios.')

    converge = False
    xr, fxr = a, fa
    for i in range(1, max_it + 1):
        denominador = fb - fa
        if denominador == 0 or not math.isfinite(denominador):
            motivo = 'No se puede calcular la secante: diferencia entre f(a) y f(b) inválida.'
            break
        # Equivalente a Xr = b - f(b)*(a-b)/(f(a)-f(b)).
        xr = a - fa * ((b - a) / denominador)
        if not math.isfinite(xr) or not a <= xr <= b:
            motivo = 'La interpolación produjo un valor fuera del intervalo.'
            break
        # Con aritmética finita un extremo puede dejar de moverse.
        if xr == a or xr == b:
            fxr = f.en(xr)
            if fxr is None:
                motivo = 'La función no está definida en la nueva aproximación.'
            else:
                motivo = ('Precisión alcanzada.' if abs(fxr) <= tol else
                          'Estancamiento numérico: la aproximación coincide con un extremo y no se reduce el residuo.')
                converge = abs(fxr) <= tol
            break
        fxr = f.en(xr)
        if fxr is None:
            raise EntradaInvalida('La función dejó de estar definida dentro del intervalo.')

        error = abs(fxr)
        es_raiz = error < 1e-13
        converge = error <= tol
        decision = ('Raíz encontrada' if es_raiz else
                    'Precisión alcanzada' if converge else
                    'b ← Xr' if (fa > 0) != (fxr > 0) else 'a ← Xr')
        filas.append({'it': i, 'a': a, 'b': b, 'xr': xr,
                      'fa': fa, 'fb': fb, 'fxr': fxr,
                      'error': error, 'decision': decision})
        if es_raiz:
            motivo = 'Raíz exacta detectada (precisión numérica).'
            break
        if converge:
            motivo = 'Residuo absoluto |f(Xr)| ≤ tolerancia.'
            break
        if (fa > 0) != (fxr > 0):
            b, fb = xr, fxr
        else:
            a, fa = xr, fxr
    else:
        motivo = 'Límite de iteraciones alcanzado sin cumplir la tolerancia.'

    return {'raiz': xr, 'filas': filas, 'iteraciones': len(filas),
            'residuo': abs(fxr) if fxr is not None else None,
            'motivo': motivo, 'a_inicial': inicio_a, 'b_inicial': inicio_b,
            'convergencia': converge}




def _residuo_newton_preciso(f: Funcion, punto: float, valor_f: float) -> float:
    """Calcula el residuo sin ocultar cancelaciones de los float ordinarios.

    El paso de Newton continúa usando los mismos valores de doble precisión.
    Solo cuando |f(x)| es muy pequeño reevaluamos la expresión simbólica
    con 50 dígitos, tomando el valor binario REAL de x (sin inventar cifras
    ni redondear la aproximación que llegó al motor).

    Si la función es exactamente cero en ese punto, el resultado correcto
    sigue siendo 0. La interfaz presenta ese caso con texto descriptivo.
    """
    residuo = abs(valor_f)
    if residuo >= 1e-6:
        return residuo
    try:
        expresion_en_punto = f.expr.subs(X, sp.Rational(punto))
        # SymPy puede representar un cero exacto como 0.e-159 al usar
        # evalf; detectarlo ANTES evita fabricar un residuo positivo.
        if expresion_en_punto.is_zero is True:
            return 0.0
        evaluacion = expresion_en_punto.evalf(50)
        if evaluacion.is_real is True and evaluacion.is_finite is True:
            preciso = abs(float(evaluacion))
            if math.isfinite(preciso):
                return preciso
    except (ArithmeticError, TypeError, ValueError, OverflowError):
        pass
    return residuo


def validar_max_iteraciones(valor, limite=1000):
    """Máximo configurable para los métodos abiertos: entero entre 1 y 1000."""
    if isinstance(valor, bool):
        raise EntradaInvalida('El máximo de iteraciones debe ser un número entero.')
    try:
        n = int(str(valor).strip())
    except (ValueError, TypeError, OverflowError):
        raise EntradaInvalida('El máximo de iteraciones debe ser un número entero.')
    if n < 1 or n > limite:
        raise EntradaInvalida(f'El máximo de iteraciones debe estar entre 1 y {limite}.')
    return n


def newton_raphson(f: Funcion, x0, tol=0.0001, max_it=100):
    """Newton-Raphson clásico con criterios dobles de parada.

    El algoritmo está implementado directamente aquí; SymPy solo obtiene la
    derivada analítica. No se exige un intervalo ni se fuerza una raíz elegida.
    Se evalúan |f(x_{n+1})| y |x_{n+1}-x_n| sin redondear los cálculos.
    """
    x = numero(x0, 'Valor inicial x₀')
    tol = numero(tol, 'Precisión', 1e-12, 1.0)
    max_it = validar_max_iteraciones(max_it)
    expresion_derivada = sp.diff(f.expr, X)
    try:
        evaluador_derivada = sp.lambdify(X, expresion_derivada,
                                         modules=[{'Abs': abs}, 'numpy'])
    except Exception as exc:
        raise EntradaInvalida('No fue posible calcular la derivada de esta función.') from exc
    derivada = Funcion(str(expresion_derivada), expresion_derivada, evaluador_derivada)
    filas = []
    fx = f.en(x)
    if fx is None:
        raise EntradaInvalida('La función no está definida en el punto inicial x₀.')
    residuo = _residuo_newton_preciso(f, x, fx)
    if residuo <= 1e-13:
        return {'raiz': x, 'filas': [], 'iteraciones': 0, 'residuo': residuo,
                'cambio': 0.0, 'motivo': 'El punto inicial ya es una raíz (precisión numérica).',
                'convergencia': True, 'x0_inicial': x,
                'derivada': str(expresion_derivada),
                'derivada_latex': sp.latex(expresion_derivada)}

    convergencia = False
    cambio = None
    motivo = 'Límite de iteraciones alcanzado sin cumplir ambos criterios.'
    for i in range(1, max_it + 1):
        dfx = derivada.en(x)
        if dfx is None or abs(dfx) <= 1e-12:
            motivo = ('Derivada nula, muy pequeña o indefinida: Newton-Raphson '
                      'no puede continuar desde esta aproximación.')
            if not filas:
                raise EntradaInvalida(motivo + ' Prueba otro valor inicial x₀.')
            break
        siguiente = x - fx / dfx
        if not math.isfinite(siguiente) or abs(siguiente) > 1e5:
            motivo = 'Las iteraciones se alejaron del rango numérico permitido. Prueba otro x₀.'
            if not filas:
                raise EntradaInvalida(motivo)
            break
        fsiguiente = f.en(siguiente)
        if fsiguiente is None:
            motivo = 'La siguiente aproximación está fuera del dominio de la función.'
            if not filas:
                raise EntradaInvalida(motivo)
            break
        cambio = abs(siguiente - x)
        residuo = _residuo_newton_preciso(f, siguiente, fsiguiente)
        filas.append({'it': i, 'xn': x, 'fxn': fx, 'dfxn': dfx,
                      'xnext': siguiente, 'fxnext': fsiguiente,
                      'residuo': residuo, 'cambio': cambio})
        x, fx = siguiente, fsiguiente
        if residuo <= tol and cambio <= tol:
            convergencia = True
            motivo = 'Residuo |f(xₙ₊₁)| y cambio |xₙ₊₁ − xₙ| ≤ tolerancia.'
            break
        if cambio == 0:
            motivo = ('Estancamiento numérico: la aproximación no cambia, '
                      'pero el residuo todavía supera la precisión solicitada.')
            break
    return {'raiz': x, 'filas': filas, 'iteraciones': len(filas),
            'residuo': residuo, 'cambio': cambio,
            'motivo': motivo, 'convergencia': convergencia,
            'x0_inicial': numero(x0, 'Valor inicial x₀'),
            'derivada': str(expresion_derivada),
            'derivada_latex': sp.latex(expresion_derivada)}


def secante(f: Funcion, x0, x1, tol=0.0001, max_it=100):
    """Método abierto de la secante (sin intervalo obligatorio ni derivadas).

    Cada fila aplica una vez la fórmula usando x_(n-1), x_n y produce x_(n+1).
    Al igual que en Newton, converge solo cuando el residuo EN EL NUEVO PUNTO
    y el cambio entre las últimas aproximaciones cumplen la tolerancia.
    """
    anterior = numero(x0, 'Valor inicial x₀')
    actual = numero(x1, 'Valor inicial x₁')
    tol = numero(tol, 'Precisión', 1e-12, 1.0)
    max_it = validar_max_iteraciones(max_it)
    if anterior == actual:
        raise EntradaInvalida('Los dos valores iniciales deben ser distintos: x₀ ≠ x₁.')
    f_anterior, f_actual = f.en(anterior), f.en(actual)
    if f_anterior is None or f_actual is None:
        raise EntradaInvalida('La función no está definida en uno de los puntos iniciales.')

    # Si uno de los valores ingresados ya es una raíz, no se inventan pasos.
    for punto,valor in ((actual, f_actual), (anterior, f_anterior)):
        residuo_inicial = _residuo_newton_preciso(f, punto, valor)
        if residuo_inicial <= 1e-13:
            return {'raiz': punto, 'filas': [], 'iteraciones': 0,
                    'residuo': residuo_inicial, 'cambio': None,
                    'motivo': 'Uno de los puntos iniciales ya es una raíz (precisión numérica).',
                    'convergencia': True, 'x0_inicial': anterior, 'x1_inicial': actual}

    filas = []
    convergencia = False
    residuo = _residuo_newton_preciso(f, actual, f_actual)
    cambio = None
    motivo = 'Límite de iteraciones alcanzado sin cumplir ambos criterios.'
    for i in range(1, max_it + 1):
        denominador = f_actual - f_anterior
        if denominador == 0 or not math.isfinite(denominador):
            motivo = ('No se puede continuar: f(xₙ) y f(xₙ₋₁) son iguales '
                      'y la fórmula de la secante dividiría entre cero.')
            if not filas:
                raise EntradaInvalida(motivo + ' Prueba otros valores iniciales.')
            break
        # x_(n+1) = x_n - f(x_n)*(x_n-x_(n-1))/(f(x_n)-f(x_(n-1)))
        siguiente = actual - f_actual * ((actual - anterior) / denominador)
        if not math.isfinite(siguiente) or abs(siguiente) > 1e5:
            motivo = 'Las aproximaciones salieron del rango numérico permitido. Prueba otros puntos iniciales.'
            if not filas:
                raise EntradaInvalida(motivo)
            break
        f_siguiente = f.en(siguiente)
        if f_siguiente is None:
            motivo = 'La siguiente aproximación está fuera del dominio de la función.'
            if not filas:
                raise EntradaInvalida(motivo)
            break

        cambio = abs(siguiente - actual)
        residuo = _residuo_newton_preciso(f, siguiente, f_siguiente)
        filas.append({'it': i, 'xprev': anterior, 'xn': actual,
                      'fxprev': f_anterior, 'fxn': f_actual, 'xnext': siguiente,
                      'fxnext': f_siguiente, 'residuo': residuo, 'cambio': cambio})
        anterior, f_anterior = actual, f_actual
        actual, f_actual = siguiente, f_siguiente
        if residuo <= tol and cambio <= tol:
            convergencia = True
            motivo = 'Residuo |f(xₙ₊₁)| y cambio |xₙ₊₁ − xₙ| ≤ tolerancia.'
            break
        if cambio == 0:
            motivo = ('Estancamiento numérico: la aproximación no cambia, '
                      'pero el residuo todavía supera la precisión solicitada.')
            break
    return {'raiz': actual, 'filas': filas, 'iteraciones': len(filas),
            'residuo': residuo, 'cambio': cambio, 'motivo': motivo,
            'convergencia': convergencia, 'x0_inicial': numero(x0, 'x₀'),
            'x1_inicial': numero(x1, 'x₁')}


def datos_grafico(f:Funcion, minimo=-10,maximo=10,puntos=1400):
    minimo=numero(minimo,'Mínimo de X',-1e5,1e5)
    maximo=numero(maximo,'Máximo de X',-1e5,1e5)
    if minimo>=maximo:raise EntradaInvalida('El mínimo del rango debe ser menor que el máximo.')
    xs=np.linspace(minimo,maximo,puntos)
    ys=[]
    for x in xs:
        val=f.en(float(x));ys.append(val)
    # Ignoramos valores no finitos o enormemente grandes: no unir saltos por polos.
    finite=[abs(y) for y in ys if y is not None]
    if finite:
        scale=float(np.percentile(finite,90))
        cap=max(20.,scale*12)
    else: cap=20.
    ys=[None if y is None or abs(y)>cap else y for y in ys]
    return {'x':xs.tolist(),'y':ys,'min':minimo,'max':maximo}


def candidatos(f:Funcion, minimo=-10, maximo=10, muestras=2401, limite=70):
    inicio=numero(minimo,'Mínimo de X');final=numero(maximo,'Máximo de X')
    if inicio>=final:raise EntradaInvalida('El rango de búsqueda no es válido.')
    xs=np.linspace(inicio,final,muestras)
    ys=[f.en(float(v)) for v in xs]
    cand=[]
    def push(a,b,aprox,exact=False):
        if cand and abs(aprox-cand[-1]['estimado'])<abs(xs[1]-xs[0])*1.25:
            if exact: cand[-1]={'a':a,'b':b,'estimado':aprox,'exacta':True}
            return
        if len(cand)<limite:cand.append({'a':a,'b':b,'estimado':aprox,'exacta':exact})
    for i in range(len(xs)-1):
        x1,x2=float(xs[i]),float(xs[i+1]);y1,y2=ys[i],ys[i+1]
        if y1 is None or y2 is None:continue
        if abs(y1)<1e-10:
            push(x1,x1,x1,True)
            continue
        if y1*y2<0:
            # Prevenir falsos positivos por discontinuidades.
            if not f.continuidad(x1,x2): continue
            push(x1,x2,(x1+x2)/2)
    if ys[-1] is not None and abs(ys[-1])<1e-10:
        push(float(xs[-1]),float(xs[-1]),float(xs[-1]),True)
    def etiqueta(i):
        s='';i+=1
        while i:i,r=divmod(i-1,26);s=chr(65+r)+s
        return s
    for idx,r in enumerate(cand):
        r['etiqueta']=etiqueta(idx)
        # Proponer intervalos cómodos (~0.4) sin sobrepasar otras raíces vecinas.
        if not r['exacta']:
            nearest = min((abs(r['estimado']-other['estimado']) for j,other in enumerate(cand) if j!=idx),default=math.inf)
            if nearest > 0.48:
                aa=round(r['estimado']-0.2,1)
                bb=round(r['estimado']+0.2,1)
                if inicio<=aa<bb<=final:
                    fa=f.en(aa);fb=f.en(bb)
                    if fa is not None and fb is not None and (fa*fb<0 or abs(fa)<1e-13 or abs(fb)<1e-13) and f.continuidad(aa,bb):
                        r['a'],r['b']=aa,bb
    return cand
