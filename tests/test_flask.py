"""Tests HTTP reales cuando Flask está disponible en el equipo."""
import unittest
try:
    from app import app
    FLASK_INSTALADO = True
except ImportError:
    FLASK_INSTALADO = False

@unittest.skipUnless(FLASK_INSTALADO,'Flask no está instalado en este entorno de pruebas.')
class PruebasHTTP(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
    def test_inicio_y_estilos(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/static/css/estilos.css').status_code,200)
    def test_preview(self):
        r=self.client.post('/api/preview',json={'formula':'x^2-4','min':-3,'max':3})
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json['candidatos']),2)
    def test_solve(self):
        r=self.client.post('/api/solve',json={'formula':'x^2-2','a':1,'b':2,'tolerancia':.0001})
        self.assertEqual(r.status_code,200)
        self.assertLess(abs(r.json['raiz']-2**.5),.0001)
    def test_error(self):
        r=self.client.post('/api/solve',json={'formula':'x^2+4','a':1,'b':2})
        self.assertEqual(r.status_code,400)
        self.assertFalse(r.json['ok'])
