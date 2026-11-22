"""Aplicación web de Choco Lab: Python controla toda la lógica numérica."""
from __future__ import annotations

from flask import Flask, jsonify, render_template, request
import sympy as sp
from motor import X

from motor import EntradaInvalida, biseccion, regla_falsa, newton_raphson, secante, candidatos, crear_funcion, datos_grafico

from laboratorio_api import lab_api
from iterativos_api import iterativos_api

app = Flask(__name__)
app.register_blueprint(lab_api)
app.register_blueprint(iterativos_api)
app.json.ensure_ascii = False
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024


@app.get('/')
def inicio():
    return render_template('index.html')


@app.post('/api/preview')
def vista():
    try:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise EntradaInvalida('No se han enviado datos válidos.')
        f = crear_funcion(body.get('formula', ''))
        rango_a = body.get('min', -10)
        rango_b = body.get('max', 10)
        grafica = datos_grafico(f, rango_a, rango_b)
        roots = candidatos(f, rango_a, rango_b)
        resultado = {'ok': True, 'formula': str(f.expr), 'grafica': grafica,
                     'candidatos': roots, 'advertencia':
                     'La búsqueda numérica detecta candidatos por cambios de signo o ceros muestreados; no garantiza encontrar todas las raíces.'}
        if body.get('metodo') == 'newton_raphson':
            # La vista previa contiene la derivada antes de ejecutar iteraciones.
            derivada = sp.diff(f.expr, X)
            resultado['derivada_latex'] = sp.latex(derivada)
            resultado['derivada_mathml'] = sp.printing.mathml(derivada, printer='presentation')
        return jsonify(resultado)
    except EntradaInvalida as exc:
        return jsonify({'ok':False,'error':str(exc)}), 400
    except Exception:
        app.logger.exception('Error interno en /api/preview')
        return jsonify({'ok':False,'error':'No fue posible interpretar o graficar esta función. Revisa su sintaxis y su dominio.'}),400


@app.post('/api/solve')
def resolver():
    try:
        body=request.get_json(silent=True)
        if not isinstance(body,dict):
            raise EntradaInvalida('No se han enviado datos válidos.')
        f=crear_funcion(body.get('formula',''))
        metodo=body.get('metodo','biseccion')
        if metodo not in ('biseccion','regla_falsa','newton_raphson','secante'):
            raise EntradaInvalida('Método numérico desconocido.')
        if metodo == 'newton_raphson':
            result = newton_raphson(f, body.get('x0'), body.get('tolerancia', 0.0001), body.get('max_it', 100))
        elif metodo == 'secante':
            result = secante(f, body.get('x0'), body.get('x1'), body.get('tolerancia', 0.0001), body.get('max_it', 100))
        else:
            algoritmo = biseccion if metodo == 'biseccion' else regla_falsa
            result = algoritmo(f, body.get('a'), body.get('b'), body.get('tolerancia', 0.0001))
        return jsonify({'ok':True,**result})
    except EntradaInvalida as exc:
        return jsonify({'ok':False,'error':str(exc)}),400
    except Exception:
        app.logger.exception('Error interno en /api/solve')
        return jsonify({'ok':False,'error':'No fue posible resolver el ejercicio. Revisa la función y los valores iniciales.'}),400


if __name__ == '__main__':
    from threading import Timer
    import webbrowser
    url = 'http://127.0.0.1:5000'
    print(f'\nCHOCOLAB | Abre {url} en tu navegador\n')
    Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host='127.0.0.1',port=5000,debug=False)
