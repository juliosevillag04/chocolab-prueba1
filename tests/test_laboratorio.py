"""Pruebas del motor nuevo: python -m unittest discover -s tests -v"""
import unittest
from laboratorio_api import ACTIONS

class LaboratorioTests(unittest.TestCase):
    def call(self, tool, **data):
        return ACTIONS[tool](data)

    def test_sistemas_unico(self):
        r=self.call('sistemas',A=[[2,1],[1,-1]],b=[[5],[1]],metodo='gauss_jordan')
        self.assertEqual(r['clasificacion'],'unica')
        self.assertTrue(r['verificacion'])
        self.assertEqual(r['solucion'],[2.0,1.0])

    def test_sistemas_infinitos(self):
        r=self.call('sistemas',A=[[1,1],[2,2]],b=[[3],[6]])
        self.assertEqual(r['clasificacion'],'infinitas')
        self.assertEqual(len(r['variables_libres']),1)

    def test_sistemas_incompatibles(self):
        r=self.call('sistemas',A=[[1,1],[1,1]],b=[[2],[3]])
        self.assertEqual(r['clasificacion'],'inconsistente')

    def test_traducir_ecuaciones(self):
        r=self.call('traducir_ecuaciones',variables=2,ecuaciones=['2x+y=5','x-y=1'])
        self.assertEqual(r['A'],[[2.0,1.0],[1.0,-1.0]])
        self.assertEqual(r['b'],[[5.0],[1.0]])

    def test_factorizar_lu(self):
        r=self.call('sistemas',A=[[2,1],[1,-1]],metodo='factorizar')
        self.assertTrue(r['verificacion'])
        self.assertTrue(r['pasos'])

    def test_resolver_lu(self):
        r=self.call('sistemas',A=[[2,1],[1,-1]],b=[[5],[1]],metodo='lu')
        self.assertEqual(r['solucion'],['2','1'])
        self.assertTrue(r['verificacion'])

    def test_operaciones_libres(self):
        objs=[{'nombre':'A','tipo':'Matriz','valores':[[1,2],[3,4]]},
              {'nombre':'u','tipo':'Vector','valores':[[2],[1]]},
              {'nombre':'v','tipo':'Vector','valores':[[1],[3]]}]
        r=self.call('operaciones',objetos=objs,expresion='A(u+v)')
        self.assertEqual(r['resultado'],[['11'],['25']])
        self.assertEqual(len(r['pasos']),2)

    def test_inversa_exacta(self):
        r=self.call('operaciones',objetos=[{'nombre':'A','valores':[[1,2],[3,4]]}],expresion='A^-1')
        self.assertTrue(r['invertible'])
        self.assertEqual(r['resultado'],[['-2','1'],['3/2','-1/2']])
        self.assertTrue(r['verificacion'])

    def test_inversa_singular(self):
        r=self.call('operaciones',objetos=[{'nombre':'A','valores':[[1,2],[2,4]]}],expresion='A^-1')
        self.assertFalse(r['invertible'])

    def test_combinacion_lineal(self):
        objs=[{'nombre':'u','tipo':'Vector','valores':[[1],[0]]},
              {'nombre':'v','tipo':'Vector','valores':[[0],[1]]},
              {'nombre':'b','tipo':'Vector','valores':[[2],[3]]}]
        r=self.call('combinaciones',objetos=objs,objetivo='b',generadores=['u','v'])
        self.assertTrue(r['es_combinacion'])
        self.assertEqual(r['pesos'],[2.0,3.0])

    def test_determinantes_cuatro_metodos(self):
        for mode in ['cofactores','gauss','lu']:
            with self.subTest(mode=mode):
                r=self.call('determinantes',A=[[1,2],[3,4]],metodo=mode)
                self.assertEqual(r['determinante'],'-2')
                self.assertTrue(r['verificacion'])
        r=self.call('determinantes',A=[[1,2,3],[3,1,2],[2,3,1]],metodo='sarrus')
        self.assertEqual(r['determinante'],'18')

    def test_sarrus_exclusivo_3x3(self):
        with self.assertRaises(ValueError):
            self.call('determinantes',A=[[1,2],[3,4]],metodo='sarrus')

    def test_fracciones_en_ambas_entradas_y_pivote_pequeno(self):
        eq = ['1/3x + 2y = 4/3', '0.000000000001y = 0.000000000001']
        entrada = self.call('traducir_ecuaciones', ecuaciones=eq, variables=2, exacto=True)
        self.assertEqual(entrada['A'][0][0], '1/3')
        for datos in (dict(entrada='ecuaciones', ecuaciones=eq, variables=2), entrada):
            with self.subTest(datos=datos):
                r = self.call('sistemas', **datos, exacto=True)
                self.assertEqual(r['solucion'], ['-2', '1'])
                self.assertEqual(r['prueba']['Ax'], r['prueba']['b'])
                self.assertTrue(all('columna' in paso for paso in r['pasos']))

    def test_verificacion_de_toda_la_familia_y_contradiccion(self):
        r = self.call('sistemas', A=[[1,2,3]], b=[[4]], exacto=True)
        self.assertEqual(r['prueba']['Ax'], [['4']])
        self.assertEqual(r['prueba']['direcciones'], [['-2',1,0], ['-3',0,1]])
        self.assertEqual(r['prueba']['imagenes'], [[['0']], [['0']]])
        r = self.call('sistemas', A=[[1],[1]], b=[[0],[2]], exacto=True)
        self.assertEqual(r['prueba']['contradiccion'], ['0','2'])

    def test_contrastar_una_igualdad_falsa(self):
        objs = [{'nombre':'A','valores':[[0,1],[2,3]]}]
        r = self.call('operaciones', objetos=objs, expresion='det(A)=2')
        self.assertFalse(r['comparacion'])
        self.assertTrue(r['verificacion'])
        self.assertEqual(r['referencia'], '-2')
        self.assertEqual(r['pasos'][0]['transformaciones'][0]['matriz'], [['2','3'],['0','1']])

    def test_recorrido_de_menores_y_signo_por_intercambio(self):
        r = self.call('determinantes', A=[[1,2,3],[0,4,5],[0,6,7]], metodo='cofactores')
        camino = r['datos']['recorrido']
        menor = next(p for p in camino if p['tipo']=='menor')
        self.assertEqual(menor['menor'], [['4','5'],['6','7']])
        self.assertEqual(camino[-1]['valor'], r['determinante'])
        r = self.call('determinantes', A=[[0,1],[2,3]], metodo='lu')
        self.assertEqual(r['datos']['intercambios'], 1)
        self.assertEqual(r['datos']['producto_pa'], r['datos']['producto_lu'])
        self.assertEqual(r['determinante'], '-2')

    def test_conversion_binario_fraccion(self):
        r=self.call('bases',numero='110.11',base=2)
        self.assertEqual(r['equivalencias']['10'],'6.75')
        self.assertEqual(r['equivalencias']['16'],'6.C')

    def test_conversion_hexadecimal(self):
        r=self.call('bases',numero='A.F',base=16)
        self.assertEqual(r['equivalencias']['10'],'10.9375')

    def test_romanos_vinculum(self):
        r=self.call('romanos',origen='Arábigo',valor='4000')
        self.assertEqual(r['teclado'],'(IV)')
        r=self.call('romanos',origen='Romano',valor='(IV)CM')
        self.assertEqual(r['arabigo'],'4900')

    def test_romanos_operacion_mixta(self):
        r=self.call('romanos',modo='operar',a='(IV)',b='6',tipo_a='Romano',tipo_b='Arábigo',operador='+')
        self.assertEqual(r['resultado'],'4006')
        self.assertEqual(r['teclado'],'(IV)VI')

    def test_no_evaluar_codigo_arbitrario(self):
        with self.assertRaises(ValueError):
            self.call('operaciones',objetos=[],expresion='__import__("os").system("x")')

if __name__=='__main__': unittest.main()
