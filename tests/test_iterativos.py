"""Pruebas ejecutables con: python -m unittest discover -s tests -v"""
import math
import unittest
from iterativos_motor import (EJEMPLO_A, EJEMPLO_B, EJEMPLO_ECUACIONES,
                              ErrorIterativo, resolver_iterativo, ecuaciones_a_matriz)

class IterativosTests(unittest.TestCase):
    def test_parsear_ecuaciones(self):
        A,b,names=ecuaciones_a_matriz(EJEMPLO_ECUACIONES,4)
        self.assertEqual(A,EJEMPLO_A)
        self.assertEqual(b,EJEMPLO_B)
        self.assertEqual(names,['x1','x2','x3','x4'])

    def test_jacobi_clase(self):
        r=resolver_iterativo(EJEMPLO_A,EJEMPLO_B,'jacobi',max_it=100,tolerancia=1e-6)
        self.assertTrue(r['convergencia'])
        self.assertEqual(r['iteraciones'],20)
        self.assertAlmostEqual(r['filas'][1]['x'][1],2.272727272727,places=9)
        self.assertAlmostEqual(r['filas'][2]['x'][1],1.715909090909,places=9)
        self.assertLessEqual(r['residuo'],1e-6)
        self.assertLessEqual(r['cambio'],1e-6)
        self.assertTrue(r['diagnostico']['dominancia_estricta'])

    def test_gauss_seidel_clase(self):
        r=resolver_iterativo(EJEMPLO_A,EJEMPLO_B,'gauss_seidel',max_it=100,tolerancia=1e-6)
        self.assertTrue(r['convergencia'])
        self.assertEqual(r['iteraciones'],8)
        self.assertAlmostEqual(r['filas'][1]['x'][3],.878863636364,places=9)
        self.assertAlmostEqual(r['filas'][2]['x'][3],.984341219008,places=9)

    def test_corte_por_maximo(self):
        r=resolver_iterativo(EJEMPLO_A,EJEMPLO_B,'jacobi',max_it=2)
        self.assertFalse(r['convergencia'])
        self.assertEqual(r['iteraciones'],2)

    def test_matriz_sin_dominancia_puede_resolverse(self):
        r=resolver_iterativo([[2,1],[1,2]],[3,3],'jacobi',tolerancia=1e-6)
        self.assertTrue(r['convergencia'])
        self.assertAlmostEqual(r['solucion'][0],1,places=5)

    def test_tolerancia_predeterminada(self):
        for metodo in ('jacobi', 'gauss_seidel'):
            with self.subTest(metodo=metodo):
                r=resolver_iterativo(EJEMPLO_A,EJEMPLO_B,metodo)
                self.assertEqual(r['tolerancia'],0.0001)
                self.assertTrue(r['convergencia'])
                self.assertLessEqual(r['residuo'],0.0001)
                self.assertLessEqual(r['cambio'],0.0001)

    def test_reordenar_diagonal_nula(self):
        r=resolver_iterativo([[0,3],[4,1]],[6,5],'gauss_seidel',reordenar=True)
        self.assertTrue(r['reordenada'])
        self.assertTrue(r['convergencia'])
        self.assertAlmostEqual(r['solucion'][0],.75,places=5)
        self.assertAlmostEqual(r['solucion'][1],2,places=5)

    def test_diagonal_nula_sin_reordenar(self):
        with self.assertRaises(ErrorIterativo):
            resolver_iterativo([[0,1],[1,2]],[3,4],reordenar=False)

    def test_sistema_no_dominante_no_bloquea(self):
        r=resolver_iterativo([[1,3],[3,1]],[4,4],max_it=4)
        self.assertFalse(r['convergencia'])
        self.assertFalse(r['diagnostico']['dominancia_estricta'])

    def test_fracciones_y_vars(self):
        A,b,names=ecuaciones_a_matriz(['\\frac{1}{2}x_{1}+x_{2}=2','2x1-3x2=1'],2)
        self.assertEqual(A,[[.5,1.],[2.,-3.]])
        self.assertEqual(b,[2.,1.])

    def test_fracciones_conservadas_en_conversion_a_casillas(self):
        A,b,names,exactA,exactB=ecuaciones_a_matriz(
            ['1/3x1+x2=2','x1-1/2x2=1'],2,con_texto=True)
        self.assertEqual(exactA,[['1/3','1'],['1','-1/2']])
        self.assertEqual(exactB,['2','1'])
        self.assertAlmostEqual(A[0][0],1/3)

    def test_vector_inicial_ya_es_solucion(self):
        r=resolver_iterativo([[3,0],[0,2]],[6,-4],x0=[2,-2])
        self.assertTrue(r['convergencia'])
        self.assertEqual(r['iteraciones'],0)
        self.assertEqual(r['residuo'],0)

    def test_rechaza_entrada_maliciosa(self):
        for eq in ['__import__("os")=1','x1*x2=3','x1**2=3']:
            with self.subTest(eq=eq), self.assertRaises(ErrorIterativo):
                ecuaciones_a_matriz([eq,'x1+x2=4'],2)

if __name__=='__main__':unittest.main()
