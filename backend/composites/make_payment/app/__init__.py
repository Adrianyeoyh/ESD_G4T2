from flask import Flask
from backend.composites.make_payment.app.controllers.make_payment_controller import register_error_handlers
from backend.composites.make_payment.app.routes.make_payment_routes import make_payment_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(make_payment_bp)
    register_error_handlers(app)
    return app
