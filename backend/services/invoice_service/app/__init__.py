from flask import Flask
from app.routes.invoice_routes import invoice_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(invoice_bp)
    return app