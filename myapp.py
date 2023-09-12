from flask import Flask
from flask_bootstrap import Bootstrap
from extensions import db, login_manager
from models.models import User
from routes.auth import auth as auth_blueprint
from routes.main import main as main_blueprint


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'tapan14378'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Bootstrap(app)

    # Set login view
    login_manager.login_view = 'auth.login'

    # Register blueprints
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
