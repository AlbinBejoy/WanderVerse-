from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///wander.db"
app.config['UPLOAD_FOLDER'] = 'app/static/Images'
db = SQLAlchemy(app)
if os.getenv('SECRET_KEY') is None:
    app.config['SECRET_KEY'] = 'dev-temporary-key'  # Default key for development
else:
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.app_context().push()
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

from app import routes
from app import models
from app import utility_ai
from app import admin_routes