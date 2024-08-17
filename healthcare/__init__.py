import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    SECRET_KEY = '5791628bb0b13ce0c676dfde280ba245'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///healthcare.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CONTRACT_FILE = os.path.join(BASE_DIR, 'static', 'Contract_File')
    APP_LOGO = os.path.join(BASE_DIR, 'static', 'App_Logo')

    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = ''


flask_app = Flask(__name__)
flask_app.config.from_object(Config)

db = SQLAlchemy(flask_app)
bcrypt = Bcrypt(flask_app)
login_manager = LoginManager(flask_app)
mail = Mail(flask_app)

with flask_app.app_context():
    import healthcare.models
    db.create_all()

login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

from healthcare.public.routes import public
from healthcare.admin.routes import admin
from healthcare.client.routes import client

flask_app.register_blueprint(public)
flask_app.register_blueprint(admin)
flask_app.register_blueprint(client)
