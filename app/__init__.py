from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv, find_dotenv
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    load_dotenv(find_dotenv())

    app.config["SECRET_KEY"] = os.environ.get("HD_SECRET_KEY_FLASK")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    
    app.config['MAIL_USERNAME'] = os.environ.get("DESIGNATED_EMAIL")
    app.config['MAIL_PASSWORD'] = os.environ.get("DESIGNATED_EMAIL_PW")
    
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    
    db.init_app(app)

    return app

app = create_app()
app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

mail = Mail(app)

Serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

from app import routes
