from flask import Flask
from flask_cors import CORS

from config import Config
from routes.health import health_bp
from routes.inventory import inventory_bp
from routes.master_data import master_data_bp
from routes.orders import orders_bp
from routes.products import products_bp
from routes.reports import reports_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    app.register_blueprint(health_bp)
    app.register_blueprint(master_data_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
