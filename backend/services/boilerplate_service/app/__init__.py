from flask import Flask
from backend.services.boilerplate_service.app.routes.boilerplate_routes import invoice_bp
from app.config.db import Base, engine

def create_app():
    app = Flask(__name__)
    app.register_blueprint(invoice_bp)
    Base.metadata.create_all(bind=engine)
    return app