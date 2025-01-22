from flask_login import UserMixin
from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.Integer, unique=True, nullable=False)
    profile_pic = db.Column(db.String(120), nullable=False, default='profile.jpg')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    tips = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status=db.Column(db.String, nullable=False, default='draft')
    content = db.Column(db.String, nullable=False)
    flagged = db.Column(db.Boolean, nullable=False,default=False)
    sexuality = db.Column(db.String(255), nullable=False,default=False)
    violence = db.Column(db.String(255), nullable=False,default=False)
    harassment = db.Column(db.String(255), nullable=False,default=False)
    illicit = db.Column(db.String(255), nullable=False,default=False)
    self_harm = db.Column(db.String(255), nullable=False,default=False)
    hate = db.Column(db.String(255), nullable=False,default=False)

class Highlight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    highlight = db.Column(db.String(255), nullable=True)

class Activities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    activity = db.Column(db.String(255), nullable=True)

class PlacesVisited(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    place = db.Column(db.String(255), nullable=True)

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image1 = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)


