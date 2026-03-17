from flask import Flask
from app.routes.invoice_routes import invoice_bp
from app.config.db import Base, engine

def create_app():
    app = Flask(__name__)
    app.register_blueprint(invoice_bp)
    Base.metadata.create_all(bind=engine)
    return app