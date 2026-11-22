"""Choco Lab · Jacobi y Gauss-Seidel para Ax=b.

Implementación sin bibliotecas de resolución numérica. Conserva los valores de
punto flotante de doble precisión durante las iteraciones (no redondea los
cálculos). Las expresiones de ecuaciones se interpretan sin eval/exec.
"""
from __future__ import annotations

import math
import re
from fractions import Fraction

MAX_N = 15
MAX_IT = 1000
EJEMPLO_A = [
    [10, -1, 2, 0],
    [-1, 11, -1, 3],
    [2, -1, 10, -1],
    [0, 3, -1, 8],
]
EJEMPLO_B = [6, 25, -11, 15]
EJEMPLO_ECUACIONES = [
    '10x1-x2+2x3=6', '-x1+11x2-x3+3x4=25',
    '2x1-x2+10x3-x4=-11', '3x2-x3+8x4=15',
]


class ErrorIterativo(ValueError):
    """Error comprensible para mostrar en la interfaz."""


def _entero(value, nombre, minimum, maximum):
    if isinstance(value, bool):
        raise ErrorIterativo(f'{nombre} debe ser un entero.')
    try:
        num = int(value)
        if str(value).strip() not in (str(num), str(float(num))):
            raise ValueError()
    except (ValueError, TypeError, OverflowError):
        raise ErrorIterativo(f'{nombre} debe ser un entero.') from None
    if not minimum <= num <= maximum:
        raise ErrorIterativo(f'{nombre} debe estar entre {minimum} y {maximum}.')
    return num


def _numero(value, etiqueta):
    if isinstance(value, bool):
        raise ErrorIterativo(f'{etiqueta} no es un número válido.')
    try:
        clean = str(value).strip().replace('−', '-').replace(',', '.')
        number = float(Fraction(clean))
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        raise ErrorIterativo(f'{etiqueta}: escribe un entero, decimal o fracción (por ejemplo 3/4).') from None
    if not math.isfinite(number) or abs(number) > 1e12:
        raise ErrorIterativo(f'{etiqueta} debe ser finito y de magnitud no mayor que 10¹².')
    return number


def validar_matriz(A_raw, b_raw):
    if not isinstance(A_raw, list) or not 2 <= len(A_raw) <= MAX_N:
        raise ErrorIterativo('La matriz A debe tener de 2 a 15 filas.')
    n = len(A_raw)
    if any(not isinstance(row, list) or len(row) != n for row in A_raw):
        raise ErrorIterativo('Jacobi y Gauss-Seidel requieren una matriz cuadrada A de n × n.')
    A = [[_numero(x, f'A({i+1},{j+1})') for j, x in enumerate(row)] for i, row in enumerate(A_raw)]
    if not isinstance(b_raw, list) or len(b_raw) != n:
        raise ErrorIterativo(f'El vector b debe contener {n} términos independientes.')
    b = [_numero((v[0] if isinstance(v,list) and len(v)==1 else v), f'b({i+1})') for i, v in enumerate(b_raw)]
    return A, b


# Acepta enteros, decimales, fracciones, exponentes y coeficientes implícitos;
# NO evalúa funciones ni expresiones Python y rechaza términos no lineales.
_NUM = r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
_RATIO = rf'{_NUM}(?:/{_NUM})?'
_TERM = re.compile(rf'([+-])(?:({_RATIO})(?:\*?([a-z][a-z0-9_]*))?|([a-z][a-z0-9_]*))', re.I)
_VAR = re.compile(r'[a-z][a-z0-9_]*', re.I)
_FRAC_LATEX = re.compile(r'\\(?:dfrac|tfrac|frac)\s*\{([+-]?\d+(?:\.\d+)?)\}\s*\{([+-]?\d+(?:\.\d+)?)\}')


def normalizar_ecuacion(original):
    if not isinstance(original, str) or not original.strip() or len(original) > 1400:
        raise ErrorIterativo('Escribe una ecuación lineal válida y no demasiado extensa.')
    s = original.strip().replace('−','-').replace('–','-').replace('·','*').replace('×','*')
    s = re.sub(r'\\(?:left|right)', '', s)
    s = re.sub(r'\\(?:cdot|times)', '*', s)
    # Reconocer fracciones escritas con el editor matemático MathLive.
    for _ in range(8):
        newer = _FRAC_LATEX.sub(r'\1/\2', s)
        if newer == s:
            break
        s = newer
    s = re.sub(r'_\{(\d+)\}', r'\1', s)
    s = re.sub(r'_(\d+)', r'\1', s)
    s = s.translate(str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789'))
    # Paréntesis permitidos únicamente alrededor de números/fracciones.
    s = re.sub(r'\(\s*([+-]?\d+(?:\.\d+)?/\d+(?:\.\d+)?)\s*\)', r'\1', s)
    s = ''.join(s.split()).replace(',', '.')
    if s.count('=') != 1:
        raise ErrorIterativo('Cada ecuación necesita un único signo igual (=).')
    return s


def _leer_lado(s):
    if not s:
        raise ErrorIterativo('Hay un lado de la ecuación vacío.')
    if s[0] not in '+-':
        s = '+' + s
    result, constant, idx = {}, Fraction(0), 0
    while idx < len(s):
        match = _TERM.match(s, idx)
        if not match:
            raise ErrorIterativo('Ecuación no lineal o sintaxis no admitida. Usa, por ejemplo, 2x1-3x2=5.')
        sign, raw, var, varonly = match.groups()
        if raw is None:
            value, var = Fraction(1), varonly
        else:
            try:
                value = Fraction(raw)
            except (ValueError, ZeroDivisionError):
                raise ErrorIterativo('Hay un coeficiente no válido o una división entre cero.') from None
        if sign == '-': value = -value
        if var:
            result[var] = result.get(var, Fraction(0)) + value
        else:
            constant += value
        idx = match.end()
    return result, constant


def ecuaciones_a_matriz(ecuaciones, n=None, con_texto=False):
    if not isinstance(ecuaciones, list) or not 2 <= len(ecuaciones) <= MAX_N:
        raise ErrorIterativo('Escribe entre 2 y 15 ecuaciones.')
    if n is not None and len(ecuaciones) != _entero(n, 'Cantidad de incógnitas', 2, MAX_N):
        raise ErrorIterativo('La cantidad de ecuaciones debe coincidir con las incógnitas.')
    nombres, datos = [], []
    for i, eq in enumerate(ecuaciones,1):
        try:
            left, right = normalizar_ecuacion(eq).split('=')
            lhs, a = _leer_lado(left)
            rhs, b = _leer_lado(right)
        except ErrorIterativo as exc:
            raise ErrorIterativo(f'Ecuación {i}: {exc}') from None
        merged = {name: lhs.get(name,0)-rhs.get(name,0) for name in set(lhs)|set(rhs)}
        rhs_value = b-a
        for name in list(lhs)+list(rhs):
            if name not in nombres:
                nombres.append(name)
        datos.append((merged,rhs_value))
    if len(nombres) != len(ecuaciones):
        raise ErrorIterativo(f'El sistema contiene {len(nombres)} incógnitas diferentes; se necesitan {len(ecuaciones)}. Incluye todas las variables al menos una vez.')
    if set(nombres) == {f'x{i}' for i in range(1,len(nombres)+1)}:
        nombres = [f'x{i}' for i in range(1,len(nombres)+1)]
    exactA = [[str(coeff.get(name,0)) for name in nombres] for coeff,_ in datos]
    exactB = [str(v) for _,v in datos]
    matriz = [[_numero(value, f'Coeficiente de {nombres[j]} en ecuación {i+1}') for j,value in enumerate(row)] for i,row in enumerate(exactA)]
    b = [_numero(value, f'Término independiente de la ecuación {i+1}') for i,value in enumerate(exactB)]
    if con_texto: return matriz, b, nombres, exactA, exactB
    return matriz, b, nombres


def _diag(A):
    rows=[]
    for i,row in enumerate(A):
        other=sum(abs(v) for j,v in enumerate(row) if i!=j)
        piv=abs(row[i]); strict=piv>other
        rows.append({'fila':i+1, 'diagonal':row[i], 'diagonal_abs':piv,
                     'suma_fuera':other, 'estricta':strict, 'nula':row[i]==0,
                     'debil':piv>=other})
    return {'filas':rows, 'dominancia_estricta':all(r['estricta'] for r in rows),
            'dominancia_debil':all(r['debil'] for r in rows),
            'diagonal_nula':any(r['nula'] for r in rows)}


def _reordenar_pivotes(A, b):
    n=len(A)
    # Matching entre columnas y ecuaciones; prioriza dominancia de cada fila.
    links=[]
    for j in range(n):
        indices=[i for i in range(n) if A[i][j]!=0]
        indices.sort(key=lambda i:(abs(A[i][j])<=sum(abs(v) for k,v in enumerate(A[i]) if k!=j),
                                   -abs(A[i][j]),i))
        links.append(indices)
    row_for_col=[-1]*n
    chosen_row=[-1]*n
    def assign(col, visited):
        for row in links[col]:
            if row in visited:continue
            visited.add(row)
            if chosen_row[row] == -1 or assign(chosen_row[row],visited):
                chosen_row[row]=col;row_for_col[col]=row
                return True
        return False
    for col in range(n):
        if not assign(col,set()):
            raise ErrorIterativo('No es posible obtener una diagonal sin ceros únicamente reordenando ecuaciones.')
    return [A[i][:] for i in row_for_col],[b[i] for i in row_for_col],row_for_col


def _residual(A,b,x):
    Ax=[sum(aij*xj for aij,xj in zip(row,x)) for row in A]
    residual=[bi-yi for bi,yi in zip(b,Ax)]
    return Ax,residual,max(abs(v) for v in residual)


def resolver_iterativo(A_raw,b_raw,metodo='jacobi',x0=None,tolerancia=1e-4,max_it=100,reordenar=True):
    if metodo not in ('jacobi','gauss_seidel'):
        raise ErrorIterativo('Elige Jacobi o Gauss-Seidel.')
    A,b=validar_matriz(A_raw,b_raw)
    n=len(A)
    tol=_numero(tolerancia,'Tolerancia')
    if tol < 1e-12 or tol > 1:
        raise ErrorIterativo('La tolerancia debe estar entre 10⁻¹² y 1.')
    limit=_entero(max_it,'Máximo de iteraciones',1,MAX_IT)
    if x0 is None:
        x=[0.0]*n
    elif not isinstance(x0,list) or len(x0)!=n:
        raise ErrorIterativo(f'El vector inicial X⁽⁰⁾ debe tener {n} componentes.')
    else:
        x=[_numero(v,f'X⁽⁰⁾ componente {i+1}') for i,v in enumerate(x0)]
    originalA=[row[:] for row in A]; originalb=b[:]
    order=list(range(n)); reordered=False
    if any(A[i][i]==0 for i in range(n)) and reordenar:
        A,b,order=_reordenar_pivotes(A,b)
        reordered=order!=list(range(n))
    diagnosis=_diag(A)
    if diagnosis['diagonal_nula']:
        raise ErrorIterativo('La diagonal de A contiene ceros: no se puede despejar una incógnita. Reordena las ecuaciones o activa el reordenamiento automático.')
    ax, residual, residual_norm = _residual(A,b,x)
    filas=[{'k':0,'x':x[:],'residuo':residual_norm,'cambio':None,'Ax':ax,'vector_residual':residual}]
    converged=residual_norm<=tol
    reason='La aproximación inicial satisface el residuo solicitado.' if converged else ''
    if not converged:
        for k in range(1,limit+1):
            old=x[:]
            new=old[:] if metodo=='gauss_seidel' else [0.0]*n
            for i in range(n):
                # Jacobi siempre consulta old; Seidel consulta new para j < i.
                accumulated=sum(A[i][j]*(new[j] if metodo=='gauss_seidel' and j<i else old[j])
                                for j in range(n) if j!=i)
                new[i]=(b[i]-accumulated)/A[i][i]
                if not math.isfinite(new[i]) or abs(new[i])>1e100:
                    reason='Las aproximaciones se hicieron no finitas o crecieron excesivamente; el método no converge con estos datos.'
                    break
            if reason: break
            x=new
            ax, residual, residual_norm=_residual(A,b,x)
            change=max(abs(a-c) for a,c in zip(new,old))
            filas.append({'k':k,'x':x[:],'residuo':residual_norm,'cambio':change,'Ax':ax,'vector_residual':residual})
            if residual_norm<=tol and change<=tol:
                converged=True
                reason='Ambos criterios de tolerancia se cumplieron.'
                break
        if not reason:
            reason=f'Se alcanzó el máximo de {limit} iteraciones sin cumplir ambos criterios.'
    last=filas[-1]
    return {'metodo':metodo, 'A':A,'b':b,'A_original':originalA,'b_original':originalb,
            'reordenada':reordered, 'orden_filas':[i+1 for i in order],
            'diagnostico':diagnosis,'x0':filas[0]['x'],'filas':filas,
            'solucion':last['x'],'iteraciones':last['k'],'residuo':last['residuo'],
            'cambio':last['cambio'],'residual_vector':last['vector_residual'],
            'Ax':last['Ax'],'convergencia':converged,'motivo':reason,
            'tolerancia':tol,'max_it':limit}
