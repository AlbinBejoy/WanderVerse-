from flask_login import UserMixin
from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.Integer, unique=True, nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    highlight = db.Column(db.String(255), nullable=True)
    top_attractions = db.Column(db.String(255), nullable=False)
    Category = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.String(255), nullable=False)
    tips = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trash=db.Column(db.Boolean, nullable=False, default=False)

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image1 = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Moderation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String, nullable=False)
    Flagged = db.Column(db.Boolean, nullable=False)
    sexuality = db.Column(db.String(255), nullable=False)
    violence = db.Column(db.String(255), nullable=False)
    harassment = db.Column(db.String(255), nullable=False)
    illicit = db.Column(db.String(255), nullable=False)
    self_harm=db.Column(db.String(255), nullable=False)
    hate=db.Column(db.String(255), nullable=False)

