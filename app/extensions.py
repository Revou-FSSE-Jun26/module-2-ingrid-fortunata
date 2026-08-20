from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_smorest import Api
from werkzeug.exceptions import HTTPException
from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

class CustomApi(Api):
    def handle_http_exception(self, error: HTTPException):
        # Intercept HTTPException, format validation errors to match standard structure
        status_code = error.code
        if status_code == 422:
            status_code = 400
            
        error_code = "VALIDATION_ERROR" if status_code == 400 else error.name.upper().replace(' ', '_')
        
        payload = {
            'error_code': error_code,
            'message': error.description
        }
        
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

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "error_code": "UNAUTHORIZED",
        "message": "The token has expired."
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "error_code": "UNAUTHORIZED",
        "message": "Signature verification failed."
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        "error_code": "UNAUTHORIZED",
        "message": "Missing Authorization Header."
    }), 401
