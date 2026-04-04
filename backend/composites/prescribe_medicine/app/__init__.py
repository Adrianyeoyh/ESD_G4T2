from flask import Flask
from app.routes.prescription_routes import prescribe_medicine_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(prescribe_medicine_bp)
    return app