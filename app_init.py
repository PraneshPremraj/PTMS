from flask import Flask
from config import Config
from extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # where to send users who aren't logged in

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from auth import auth
    from dashboard import dashboard
    from projects import projects_bp
    from team import team_bp
    from tasks import tasks_bp
    from api import api_bp
    from settings import settings_bp
    from profile import profile_bp

    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(projects_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(profile_bp)

    return app