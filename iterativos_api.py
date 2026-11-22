"""Endpoints Flask para los métodos iterativos de sistemas lineales."""
from flask import Blueprint, jsonify, request
from iterativos_motor import (EJEMPLO_A, EJEMPLO_B, EJEMPLO_ECUACIONES,
                              ErrorIterativo, ecuaciones_a_matriz,
                              resolver_iterativo, validar_matriz)

iterativos_api = Blueprint('iterativos_api', __name__)


def _body():
    data = request.get_json(silent=True)
    if not isinstance(data,dict):
        raise ErrorIterativo('No se recibieron datos del sistema.')
    return data


def _sistema(data):
    if data.get('entrada') == 'ecuaciones':
        A,b,nombres=ecuaciones_a_matriz(data.get('ecuaciones'),data.get('n'))
        return A,b,nombres
    A,b=validar_matriz(data.get('A'),data.get('b'))
    return A,b,[f'x{i+1}' for i in range(len(A))]


def _config(data,method=None):
    A,b,names=_sistema(data)
    method=method or data.get('metodo','jacobi')
    r=resolver_iterativo(A,b,method,data.get('x0'),data.get('tolerancia',1e-4),
                       data.get('max_it',100),data.get('reordenar',True))
    r['nombres']=names
    return r


@iterativos_api.post('/api/iterativos/parse')
def parse():
    try:
        data=_body()
        A,b,names,exactA,exactB=ecuaciones_a_matriz(data.get('ecuaciones'),data.get('n'),con_texto=True)
        return jsonify({'ok':True,'A':A,'b':b,'nombres':names,'A_texto':exactA,'b_texto':exactB})
    except (ErrorIterativo,ValueError,TypeError) as ex:
        return jsonify({'ok':False,'error':str(ex)}),400


@iterativos_api.post('/api/iterativos/resolver')
def solve():
    try:
        return jsonify({'ok':True,**_config(_body())})
    except (ErrorIterativo,ValueError,TypeError) as ex:
        return jsonify({'ok':False,'error':str(ex)}),400


@iterativos_api.post('/api/iterativos/comparar')
def compare():
    try:
        data=_body()
        return jsonify({'ok':True,
                        'jacobi':_config(data,'jacobi'),
                        'gauss_seidel':_config(data,'gauss_seidel')})
    except (ErrorIterativo,ValueError,TypeError) as ex:
        return jsonify({'ok':False,'error':str(ex)}),400


@iterativos_api.get('/api/iterativos/ejemplo')
def example():
    return jsonify({'ok':True,'A':EJEMPLO_A,'b':EJEMPLO_B,
                    'ecuaciones':EJEMPLO_ECUACIONES,
                    'x0':[0,0,0,0]})
