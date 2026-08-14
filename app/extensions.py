from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_smorest import Api
from werkzeug.exceptions import HTTPException
from flask import jsonify

db = SQLAlchemy()
migrate = Migrate()

class CustomApi(Api):
    def handle_http_exception(self, error: HTTPException):
        # Intercept HTTPException, format validation errors to match tests
        status_code = error.code
        # Convert webargs/marshmallow 422 Unprocessable Entity to 400 Bad Request
        if status_code == 422:
            status_code = 400
            
        payload = {
            'success': False,
            'error': 'Validation Error' if status_code == 400 else error.name,
            'message': error.description
        }
        
        # If it is a webargs validation error, the details are under data['messages']
        data = getattr(error, 'data', None)
        if data and 'messages' in data:
            payload['message'] = str(data['messages'])
            
        headers = {}
        if hasattr(error, 'get_headers'):
            for k, v in error.get_headers():
                if k.lower() != 'content-type':
                    headers[k] = v
        headers['Content-Type'] = 'application/json'
        return jsonify(payload), status_code, headers

api = CustomApi()

