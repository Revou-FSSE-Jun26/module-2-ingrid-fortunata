import unittest
from app import create_app

class SwaggerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_swagger_ui_endpoint(self):
        response = self.client.get('/swagger-ui')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'swagger-ui', response.data.lower())

    def test_api_spec_json(self):
        response = self.client.get('/openapi.json')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['info']['title'], "RevoFashion API")
        self.assertEqual(data['openapi'], "3.0.3")
        self.assertIn('/users', data['paths'])
        self.assertIn('/products', data['paths'])
