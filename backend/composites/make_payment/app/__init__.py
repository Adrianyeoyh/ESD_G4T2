from flask import Flask
from app.controllers.boilerplate_controller import register_error_handlers
from app.routes.boilerplate_routes import billing_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(billing_bp)
    register_error_handlers(app)
    return app
