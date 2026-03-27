from flask import Flask
from app.controllers.make_payment_controller import register_error_handlers
from app.routes.make_payment_routes import make_payment_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(make_payment_bp)
    register_error_handlers(app)
    return app
