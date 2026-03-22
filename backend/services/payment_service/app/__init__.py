from flask import Flask
from app.routes.payment_routes import payment_bp
from app.config.db import Base, engine
from flasgger import Swagger


def create_app():
    app = Flask(__name__)
    app.config["SWAGGER"] = {
        "title": "Payment Service API",
        "uiversion": 3
    }

    Swagger(app)
    app.register_blueprint(payment_bp)
    Base.metadata.create_all(bind=engine)
    return app