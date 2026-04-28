from flask import Flask
from flask_cors import CORS
from app.models import db, init_db

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    CORS(app)

    init_db()

    @app.before_request
    def open_db():
        if db.is_closed():
            db.connect()

    @app.teardown_appcontext
    def close_db(exc):
        if not db.is_closed():
            db.close()

    from app.routes import bp
    app.register_blueprint(bp)

    return app
