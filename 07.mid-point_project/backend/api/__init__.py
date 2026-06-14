from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    try:
        from api.routes.seller_routes import seller_bp
        from api.routes.buyer_routes import buyer_bp
    except ModuleNotFoundError as e:
        raise ImportError(f"Error importing modules: {e}")

    app.register_blueprint(seller_bp, url_prefix="/api/seller")
    app.register_blueprint(buyer_bp, url_prefix="/api/buyer")

    return app