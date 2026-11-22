"""Pruebas automáticas: python -m unittest discover -s tests -v"""
import math
import unittest

from motor import EntradaInvalida, biseccion, candidatos, crear_funcion, datos_grafico

class PruebasChocoLab(unittest.TestCase):
    def verificar_error_de_excel(self, resultado, iteraciones_esperadas):
        self.assertEqual(resultado['iteraciones'], iteraciones_esperadas)
        self.assertEqual(len(resultado['filas']), iteraciones_esperadas)
        for fila in resultado['filas']:
            # La columna Error reproduce exactamente |f(c)|.
            self.assertAlmostEqual(fila['error'], abs(fila['fc']), places=12)
        # No debe detenerse antes de satisfacer la tolerancia del residuo.
        for fila in resultado['filas'][:-1]:
            self.assertGreater(fila['error'], 0.0001)
        self.assertLessEqual(resultado['filas'][-1]['error'], 0.0001)
        self.assertAlmostEqual(resultado['residuo'], resultado['filas'][-1]['error'], places=12)
        self.assertEqual(resultado['filas'][-1]['decision'], 'Precisión alcanzada')
        self.assertIn('|f(c)|', resultado['motivo'])

    def test_ejercicio_izquierda(self):
        f=crear_funcion('x^4-5x^3+0.5x^2-11x+10')
        r=biseccion(f,0.6,1,0.0001)
        self.verificar_error_de_excel(r, 15)
        self.assertAlmostEqual(r['raiz'],0.76392822265625,places=12)
        self.assertEqual(r['filas'][0]['decision'],'b ← c')
        self.assertAlmostEqual(r['filas'][0]['error'],0.6304,places=7)

    def test_ejercicio_derecha(self):
        f=crear_funcion('x^4-5x^3+0.5x^2-11x+10')
        r=biseccion(f,5,5.4,0.0001)
        self.verificar_error_de_excel(r, 19)
        self.assertAlmostEqual(r['raiz'],5.236067962646484,places=12)
        roots=candidatos(f)
        self.assertEqual(len(roots),2)
        self.assertEqual((roots[0]['a'],roots[0]['b']),(0.6,1.0))
        self.assertEqual((roots[1]['a'],roots[1]['b']),(5.0,5.4))
        self.assertEqual([r['etiqueta'] for r in roots],['A','B'])

    def test_latex_y_multiplicacion_implicita(self):
        self.assertAlmostEqual(crear_funcion(r'\frac{x^2}{2}+2x').en(2),6)
        self.assertAlmostEqual(crear_funcion(r'\sin(\pi/2)').en(0),1)
    def test_terminar_cero_en_extremo(self):
        r=biseccion(crear_funcion('x^2+x^3'),0,0.1)
        self.assertEqual(r['iteraciones'],0)
        self.assertEqual(r['raiz'],0)
    def test_discontinuidad(self):
        with self.assertRaises(EntradaInvalida):biseccion(crear_funcion('1/(x-1)'),0,2)
    def test_sin_cambio(self):
        with self.assertRaises(EntradaInvalida):biseccion(crear_funcion('x^2+4'),-2,2)
    def test_entrada_peligrosa(self):
        for s in ['__import__("os").system("echo bad")','x+y','cos(x);7']:
            with self.subTest(s=s),self.assertRaises(EntradaInvalida):crear_funcion(s)
    def test_seno(self):
        r=biseccion(crear_funcion('sin(x)'),3,4)
        self.assertAlmostEqual(r['raiz'],math.pi,delta=0.0001)
    def test_multiples_raices(self):
        roots=candidatos(crear_funcion('x^2+x^3'))
        self.assertEqual(len(roots),2)
    def test_grafica(self):
        graph=datos_grafico(crear_funcion('x^2-4'),-3,3)
        self.assertEqual(len(graph['x']),1400)
        self.assertEqual(len(graph['y']),1400)

if __name__=='__main__':unittest.main()
