from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///wander.db"
app.config['UPLOAD_FOLDER'] = 'app/static/Images'
db = SQLAlchemy(app)
app.config['secret key'] = os.getenv('SECRET_KEY')
app.app_context().push()

from app import routes
from app import models
from app import utility_ai