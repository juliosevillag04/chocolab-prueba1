"""API de Álgebra Lineal y Temas Complementarios para integrarse en Flask existente.
Mantiene los motores originales en Python y devuelve pasos estructurados para HTML.
"""
import ast
import os
import operator
from math import prod
import sympy as sp
import random
import re
from fractions import Fraction
from flask import Blueprint, request, jsonify
from algebra_nucleo import (_leer_numero, _dimensiones, _multiplicar_matrices,
                           EvaluadorOriginal, ConversorBases)
from algebra_eliminacion import (resolver_sistema, convertir_sistema_ecuaciones,
                                invertir_matriz_gauss_jordan)
from algebra_lu import (factorizar_lu, resolver_axb_lu,
                        generar_matriz_lu_aleatoria, generar_sistema_lu_aleatorio)
from algebra_determinantes import (resolver_determinante, analizar_eficiencia, calcular_sarrus, medir_tiempos_metodos)
from romanos_motor import (parse_value, parse_arabic_integer, roman_to_arabic_extended,
                          arabic_to_extended_keyboard, arabic_to_extended_roman,
                          roman_if_possible, pretty_number, _extended_components)

lab_api=Blueprint('lab_api',__name__)
MAX_DIM=15

def ser(x):
    if isinstance(x,Fraction):return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'
    if isinstance(x,float):return round(x,12) if abs(x)<1e10 else x
    if isinstance(x,(str,int,bool)) or x is None:return x
    if isinstance(x,(list,tuple)):return [ser(a) for a in x]
    if isinstance(x,dict):return {str(k):ser(v) for k,v in x.items()}
    return str(x)

def matrix(raw,name='A',square=False,maxn=MAX_DIM):
    if not isinstance(raw,list) or not raw or len(raw)>maxn or any(not isinstance(r,list) for r in raw):
        raise ValueError(f'{name}: introduce una matriz de 1 a {maxn} filas.')
    cols=len(raw[0]);
    if cols<1 or cols>maxn or any(len(r)!=cols for r in raw):
        raise ValueError(f'{name}: todas las filas deben tener entre 1 y {maxn} columnas iguales.')
    if square and cols!=len(raw):raise ValueError(f'{name} debe ser cuadrada (n×n).')
    valores = []
    for i, row in enumerate(raw, 1):
        fila = []
        for j, valor in enumerate(row, 1):
            try:
                fila.append(_leer_numero(str(valor).replace(',', '.')))
            except ValueError as exc:
                raise ValueError(f'{name}({i},{j}) · {exc}') from exc
        valores.append(fila)
    return valores

def vector(raw,name='b'):
    v=matrix(raw,name)
    if len(v[0])==1:return v
    if len(v)==1:return [[q] for q in v[0]]
    raise ValueError(f'{name} debe tener una sola columna (vector).')

def parse_objects(raw):
    if not isinstance(raw,list) or len(raw)>20:raise ValueError('Puedes guardar hasta 20 objetos.')
    out={}
    for obj in raw:
        if not isinstance(obj,dict):raise ValueError('Datos de objeto incompletos.')
        name=str(obj.get('nombre','')).strip()
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',name) or name in ('det','T','inv'):
            raise ValueError(f'El nombre «{name}» no es válido; usa letras y números.')
        if name in out:raise ValueError(f'Ya existe un objeto llamado «{name}».')
        tipo=obj.get('tipo','Matriz')
        data=vector(obj.get('valores'),name) if tipo=='Vector' else matrix(obj.get('valores'),name)
        out[name]={'tipo':tipo,'valor':data}
    return out

def numeros_gauss(valor, exacto):
    """El editor pide fracciones. Los clientes anteriores reciben sus valores numéricos."""
    if exacto:
        return ser(valor)
    if isinstance(valor, (list, tuple)):
        return [numeros_gauss(v, False) for v in valor]
    if isinstance(valor, Fraction):
        return float(valor)
    return valor


def solve_matrix(A, b, mode='gauss_jordan', names=None, exacto=False):
    if len(b) != len(A):
        raise ValueError(f'b necesita {len(A)} componentes.')
    n = len(A[0])
    names = names or [f'x{i+1}' for i in range(n)]
    if mode == 'lu':
        r = resolver_axb_lu(A, [row[0] for row in b])
        return ser({'tipo':'lu', 'clasificacion':'unica', 'solucion':r['x'], 'nombres':names,
                    'L':r['L'], 'U':r['U'], 'y':r['y'], 'b':r['b'], 'Ax':r['Ax'],
                    'Ly':r['Ly'], 'Ux':r['Ux'], 'producto_LU':r['producto_LU'],
                    'verificacion':all(r[k] for k in ('verificacion','verificacion_Ly','verificacion_Ux','verificacion_Ax')),
                    'pasos':r['pasos'], 'pasos_y':r['pasos_y'], 'pasos_x':r['pasos_x'], 'matriz_original':A})

    raw = [row + [b[i][0]] for i, row in enumerate(A)]
    r = resolver_sistema(raw, n)
    reduced = r['matriz_reducida']
    selected = [p for p in r['pasos'] if mode != 'gauss' or p['fase'] == 'escalonamiento']
    parameters, directions, proof = [], [], {}
    particular = None
    if r['clasificacion'] == 'inconsistente':
        index = r['fila_inconsistente']
        row = r['matriz_escalonada'][index]
        check = all(x == 0 for x in row[:-1]) and row[-1] != 0
        proof = {'fila':index, 'contradiccion':row}
    else:
        x = r['solucion']
        if x is None:
            particular = [0] * n
            for i, j in r['pivotes']:
                particular[j] = reduced[i][-1]
            x = particular
            for free in r['variables_libres']:
                direction = [0] * n
                direction[free] = 1
                for i, j in r['pivotes']:
                    direction[j] = -reduced[i][free]
                directions.append(direction)
            for j, name in enumerate(names):
                terms = str(x[j]) if x[j] else ''
                for k, direction in enumerate(directions, 1):
                    c = direction[j]
                    if c:
                        sign = ' − ' if c < 0 and terms else '−' if c < 0 else ' + ' if terms else ''
                        terms += sign + (str(abs(c)) + '·' if abs(c) != 1 else '') + f't{k}'
                parameters.append({'variable':name, 'expresion':terms or '0'})
        ax = _multiplicar_matrices(A, [[v] for v in x])
        kernels = [_multiplicar_matrices(A, [[v] for v in d]) for d in directions]
        check = ax == b and all(all(row[0] == 0 for row in v) for v in kernels)
        proof = {'x':x, 'Ax':ax, 'b':b, 'direcciones':directions, 'imagenes':kernels}

    return {'tipo':'gauss', 'clasificacion':r['clasificacion'], 'verificacion':check,
            'solucion':numeros_gauss(r['solucion'], exacto), 'particular':numeros_gauss(particular, exacto),
            'parametros':parameters, 'prueba':ser(proof), 'nombres':names, 'modo':mode,
            'matriz_original':ser(raw), 'matriz_escalonada':numeros_gauss(r['matriz_escalonada'], exacto),
            'matriz_reducida':numeros_gauss(reduced, exacto), 'pivotes':r['pivotes'],
            'variables_libres':r['variables_libres'], 'fila_inconsistente':r['fila_inconsistente'],
            'pasos':[dict(ser(p), matriz=numeros_gauss(p['matriz'], exacto)) for p in selected]}


def action_sistemas(data):
    mode=data.get('metodo','gauss_jordan')
    if mode not in ('gauss','gauss_jordan','lu','factorizar'):raise ValueError('Selecciona Gauss, Gauss-Jordan o LU.')
    if data.get('entrada')=='ecuaciones':
        eqs=data.get('ecuaciones')
        if not isinstance(eqs,list) or not 1<=len(eqs)<=MAX_DIM:raise ValueError('Introduce de 1 a 15 ecuaciones.')
        n=int(data.get('variables',3))
        if not 1<=n<=MAX_DIM:raise ValueError('Introduce de 1 a 15 variables.')
        raw,names=convertir_sistema_ecuaciones(eqs,n)
        A=matrix([r[:-1] for r in raw]);b=vector([[r[-1]] for r in raw])
    else:
        A=matrix(data.get('A'),'A',square=(mode in ('lu','factorizar')))
        b=vector(data.get('b'),'b') if mode!='factorizar' else None
        names = data.get('nombres')
        if not (isinstance(names, list) and len(names) == len(A[0])
                and all(isinstance(n, str) and re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', n) for n in names)
                and len(set(names)) == len(names)):
            names = [f'x{i+1}' for i in range(len(A[0]))]
    if mode=='factorizar':
        r=factorizar_lu(A)
        return ser({'tipo':'factorizar', 'L':r['L'], 'U':r['U'], 'verificacion':r['verificacion'],
                    'matriz_original':A, 'producto_LU':r['producto_LU'], 'pasos':r['pasos']})
    if mode=='lu' and len(A)!=len(A[0]):raise ValueError('La resolución por LU requiere matriz cuadrada.')
    return solve_matrix(A,b,mode,names,data.get('exacto', False))


def referencia_expresion(nodo, objetos):
    """Contrasta el árbol ya validado por el evaluador con aritmética racional de SymPy."""
    if isinstance(nodo, ast.Name):
        return sp.Matrix(objetos[nodo.id]['valor'])
    if isinstance(nodo, ast.Constant):
        return sp.Rational(str(nodo.value))
    if isinstance(nodo, ast.UnaryOp):
        value = referencia_expresion(nodo.operand, objetos)
        return -value if isinstance(nodo.op, ast.USub) else value
    if isinstance(nodo, ast.BinOp):
        operation = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv}
        return operation[type(nodo.op)](referencia_expresion(nodo.left, objetos),
                                        referencia_expresion(nodo.right, objetos))
    if isinstance(nodo, ast.Call) and nodo.func.id in ('T', 'det'):
        value = referencia_expresion(nodo.args[0], objetos)
        return value.T if nodo.func.id == 'T' else value.det()
    raise ValueError('Operación desconocida en la comprobación.')


def valor_referencia(nodo, objetos):
    value = referencia_expresion(nodo, objetos)
    return ser(value.tolist() if isinstance(value, sp.MatrixBase) else value)


def action_operaciones(data):
    objs=parse_objects(data.get('objetos',[]))
    expression=str(data.get('expresion','')).strip()
    if len(expression)>220:raise ValueError('La expresión es demasiado larga.')
    m=re.fullmatch(r'([A-Za-z][A-Za-z0-9_]*)\s*(?:\^\s*\{-?1\}|\^\s*-1|\^\(-1\)|⁻¹)',expression)
    m2=re.fullmatch(r'inv\(([A-Za-z][A-Za-z0-9_]*)\)',expression,flags=re.I)
    if m or m2:
        name=(m or m2).group(1)
        if name not in objs:raise ValueError(f'No existe una matriz llamada «{name}».')
        A=matrix(objs[name]['valor'],name,square=True)
        r=invertir_matriz_gauss_jordan(A)
        return {'columna_sin_pivote':r['columna_sin_pivote'], 'reducida':ser(r['matriz_reducida']),
            'producto_a_inversa':ser(r['producto_a_inversa']), 'producto_inversa_a':ser(r['producto_inversa_a']),
            'tipo':'inversa','nombre':name,'invertible':r['invertible'],'resultado':ser(r['inversa']),
            'pasos':ser(r['pasos']),
            'original':ser(r['matriz_aumentada_inicial']),'verificacion':r['invertible'] and
            r['producto_a_inversa']==[[Fraction(int(i==j)) for j in range(len(A))] for i in range(len(A))] and
            r['producto_inversa_a']==[[Fraction(int(i==j)) for j in range(len(A))] for i in range(len(A))]}
    ev=EvaluadorOriginal(objs)
    if expression.count('=')>1:raise ValueError('Escribe una sola igualdad.')
    sides=expression.split('=',1); steps=[]
    node,_=ev._analizar_lado(sides[0]);r=ev._evaluar(node,steps)
    ref = valor_referencia(node, objs)
    check = ref == ser(r)
    boundary = len(steps)
    equals=None;rhs=None
    if len(sides)==2:
        node2,_=ev._analizar_lado(sides[1]);rhs=ev._evaluar(node2,steps)
        if isinstance(r,list)!=isinstance(rhs,list) or (isinstance(r,list) and _dimensiones(r)!=_dimensiones(rhs)):
            raise ValueError('Los dos lados de la igualdad no tienen tipos o dimensiones compatibles.')
        equals=r==rhs
        check = check and valor_referencia(node2, objs) == ser(rhs)
    return {'tipo':'expresion','resultado':ser(r),'tipo_resultado':'matriz' if isinstance(r,list) else 'escalar',
        'comparacion':equals, 'lado_derecho':ser(rhs), 'referencia':ref, 'verificacion':check,
        'expresion':expression, 'inicio_derecho':boundary,
        'normalizada':' = '.join(ev._normalizar_expresion(side) for side in sides),
        'pasos':[{'operacion':p['tipo'],'detalle':p.get('simbolo',''),'a':ser(p.get('a')),
                  'b':ser(p.get('b')),'resultado':ser(p.get('r')),
                  'etiqueta_a':p.get('ea'),'etiqueta_b':p.get('eb'),
                  'transformaciones':ser(p.get('transformaciones', [])),
                  'explicacion':ser(p.get('detalle',[]))} for p in steps]}


def action_combinaciones(data):
    objs=parse_objects(data.get('objetos',[]))
    modo=data.get('modo','objetivo')
    if modo=='analizar':
        names=data.get('generadores',[])
        if not isinstance(names,list) or len(names)<2:raise ValueError('Selecciona al menos dos vectores.')
        arr=[]
        for target in names:
            rest=[n for n in names if n!=target]
            arr.append({'objetivo':target,**_comb_individual(objs,target,rest,data.get('exacto', False))})
        return {'tipo':'analisis','analisis':arr}
    return {'tipo':'combinacion',**_comb_individual(objs,data.get('objetivo'),data.get('generadores',[]),data.get('exacto', False))}

def _comb_individual(objs,target,names,exacto=False):
    if target not in objs or objs[target]['tipo']!='Vector':raise ValueError('Selecciona un vector objetivo guardado.')
    if not isinstance(names,list) or not names:raise ValueError('Selecciona al menos un vector generador.')
    if target in names:raise ValueError('El vector objetivo no puede ser su propio generador.')
    b=objs[target]['valor'];dim=len(b);vec=[]
    for name in names:
        if name not in objs or objs[name]['tipo']!='Vector':raise ValueError(f'{name}: selecciona vectores existentes.')
        v=objs[name]['valor']
        if len(v)!=dim:raise ValueError(f'{name} tiene {len(v)} componentes, pero {target} tiene {dim}.')
        vec.append(v)
    A=[[v[i][0] for v in vec] for i in range(dim)]
    r=solve_matrix(A,b,'gauss_jordan',[f'c{i+1}' for i in range(len(names))],exacto)
    return {'es_combinacion':r['clasificacion']!='inconsistente','pesos':r.get('solucion') or r.get('particular'),
            'generadores':names,'objetivo':target,'resolucion':r}


def action_determinantes(data):
    A=matrix(data.get('A'),'A',square=True,maxn=8)
    mode=data.get('metodo','cofactores')
    if mode not in ('cofactores','sarrus','gauss','lu'):raise ValueError('Método de determinante desconocido.')
    if mode=='cofactores' and len(A)>6:raise ValueError('Para mostrar el árbol completo de cofactores, usa matrices de hasta 6×6.')
    r=resolver_determinante(A,mode)
    selected=r[mode]
    steps=selected.get('pasos',[])
    if mode == 'sarrus':
        selected = dict(selected, productos_positivos=[prod(d) for d in selected['positivos']],
                        productos_negativos=[prod(d) for d in selected['negativos']])
    out={'matriz_original':ser(A),'tipo':'determinante','metodo':mode,'determinante':ser(r['resultado']),
        'verificacion':r['verificacion_cruzada'],'recomendacion':r['analisis']['metodo'],
        'razon':r['analisis']['motivo'],'criterios':r['analisis']['criterios'],
        'valores_metodos':ser(r['valores']),'pasos':ser(steps),'datos':ser(selected),
        'rendimiento':ser(medir_tiempos_metodos(A, repeticiones=3)) if len(A)<=5 else None}
    return out


def action_bases(data):
    c=ConversorBases();base=int(data.get('base',10))
    if base not in (2,8,10,16):raise ValueError('Selecciona una base válida.')
    s=str(data.get('numero',''))
    if len(s)>100:raise ValueError('Máximo 100 caracteres para mantener la respuesta legible.')
    text=c._normalizar(s,base);num=c._a_decimal(text,base)
    forms={str(i):c._representar(num,i) for i in (10,2,8,16)}
    return {'tipo':'bases','base':base,'entrada':text,'equivalencias':forms,
        'expansion':c._expansion_posicional(text,base),
        'desarrollo':{str(i):c._pasos_division(num,i) for i in (2,8,16)}}


def action_romanos(data):
    modo=data.get('modo','convertir')
    if modo=='convertir':
        t=str(data.get('valor','')).strip()
        if len(t)>512:raise ValueError('Entrada demasiado extensa.')
        origen=data.get('origen','Arábigo')
        if origen=='Arábigo':
            n=parse_arabic_integer(t);grupos=_extended_components(n)
        else:
            n,_,_,grupos_in=roman_to_arabic_extended(t)
            grupos=[(g[0],g[1],g[3]) for g in grupos_in]
        return {'tipo':'romanos','arabigo':str(n),'romano':arabic_to_extended_roman(n),
          'teclado':arabic_to_extended_keyboard(n), 'desarrollo':[{'bloque':g[0],'nivel':g[1],'valor':str(g[2])} for g in grupos],
          'nota':'Cada barra superior o par de paréntesis multiplica el bloque por 1 000.'}
    if modo=='operar':
        a=parse_value(str(data.get('a','')),str(data.get('tipo_a','Arábigo')))
        b=parse_value(str(data.get('b','')),str(data.get('tipo_b','Arábigo')))
        op=data.get('operador','+')
        if op=='+':r=a+b
        elif op=='-':r=a-b
        elif op=='*':r=a*b
        elif op=='/':r=Fraction(a,b)
        else:raise ValueError('Operación inválida.')
        return {'tipo':'roman_operacion','a':str(a),'b':str(b),'operador':op,'resultado':pretty_number(r),
           'romano':roman_if_possible(r),'teclado':arabic_to_extended_keyboard(int(r)) if r.denominator==1 and r>0 else None,
           'roman_a':arabic_to_extended_roman(a),'roman_b':arabic_to_extended_roman(b),
           'nota':'La representación romana requiere resultado entero positivo.' if not roman_if_possible(r) else ''}
    raise ValueError('Modo romano desconocido.')



def action_traducir_ecuaciones(data):
    eqs=data.get('ecuaciones')
    if not isinstance(eqs,list) or not 1<=len(eqs)<=MAX_DIM:
        raise ValueError('Introduce entre 1 y 15 ecuaciones.')
    cols=int(data.get('variables',3))
    if cols<1 or cols>MAX_DIM:raise ValueError('El número de variables debe ser de 1 a 15.')
    raw,names=convertir_sistema_ecuaciones(eqs,cols)
    exacto = data.get('exacto', False)
    return {'A':numeros_gauss([r[:-1] for r in raw], exacto),
            'b':numeros_gauss([[r[-1]] for r in raw], exacto), 'nombres':names}

def action_aleatorio(data):
    mode=data.get('modo','sistema');n=int(data.get('n',3))
    if not 1<=n<=MAX_DIM:raise ValueError('El ejercicio aleatorio admite de 1 a 15 filas.')
    if mode=='lu':d=generar_matriz_lu_aleatoria(n)
    elif mode=='sistema_lu':d=generar_sistema_lu_aleatorio(n)
    else:
        cols = int(data.get('columnas', n))
        if not 1 <= cols <= MAX_DIM: raise ValueError('Introduce de 1 a 15 columnas.')
        A=[[random.randint(-5,5) for _ in range(cols)] for _ in range(n)]
        x=[random.randint(-3,3) for _ in range(cols)]
        return {'A':ser(A),'b':ser([[sum(a*z for a,z in zip(row,x))] for row in A])}
    return {'A':ser(d['A']),'b':ser([[z] for z in d['b']]) if 'b' in d else None}

ACTIONS={'sistemas':action_sistemas,'operaciones':action_operaciones,'combinaciones':action_combinaciones,
         'determinantes':action_determinantes,'bases':action_bases,'romanos':action_romanos,'aleatorio':action_aleatorio,
         'traducir_ecuaciones':action_traducir_ecuaciones}

@lab_api.post('/api/lab/<action>')
def resolver_laboratorio(action):
    if action not in ACTIONS:return jsonify(ok=False,error='Herramienta desconocida.'),404
    raw=request.get_json(silent=True)
    if not isinstance(raw,dict):return jsonify(ok=False,error='Envía los datos del ejercicio.'),400
    try:return jsonify(ok=True,resultado=ACTIONS[action](raw))
    except (ValueError,TypeError,ZeroDivisionError,OverflowError,IndexError) as exc:
        return jsonify(ok=False,error='Choco dice: '+str(exc)),400
    except Exception:
        from flask import current_app
        current_app.logger.exception('Error en laboratorio %s',action)
        return jsonify(ok=False,error='Choco dice: ocurrió un error al resolver el ejercicio.'),500


@lab_api.get('/api/lab/ram')
def memoria_laboratorio():
    """Memoria del proceso Python local; no representa consumo del navegador."""
    try:
        import os
        if os.name=='nt':
            import ctypes
            from ctypes import wintypes
            class PMC(ctypes.Structure):
                _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),
                  ('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
                  ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),
                  ('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),
                  ('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
            c=PMC();c.cb=ctypes.sizeof(PMC)
            fn=ctypes.windll.psapi.GetProcessMemoryInfo
            fn(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(c),c.cb)
            mem=c.WorkingSetSize
        elif os.path.exists('/proc/self/statm'):
            with open('/proc/self/statm',encoding='utf-8') as fd:
                mem=int(fd.read().split()[1])*os.sysconf('SC_PAGE_SIZE')
        else:
            import resource,sys
            peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            mem=int(peak if sys.platform=='darwin' else peak*1024)
        return jsonify(ok=True,mb=round(mem/1048576,2))
    except Exception:
        return jsonify(ok=False,mb=None)
