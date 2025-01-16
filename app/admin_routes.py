

from app import app
from flask import render_template, request, redirect, url_for
from app.models import *

@app.route('/admin')
def admin():
    return render_template('adminPages/adminhome.html')

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        users = User.query.all()
        return render_template('adminPages/users.html', users=users)

@app.route('/users_search', methods=['GET', 'POST'])
def users_search():
    username = request.args.get('username')  # Fetch 'username' from the query string
    users = []
    if username:
        users = User.query.filter(User.username.ilike(f"%{username}%")).all()  # Fetch matching users
    return render_template('adminPages/users.html', users=users)
@app.route('/flags')
def flags():
    flagged = db.session.query(User, Moderation).join(Moderation, User.id == Moderation.user_id).all()
    return render_template('adminPages/flagged.html', flagged=flagged)

@app.route('/posts_admin')
def posts_admin():
    posts = db.session.query(User, Post).join(Post, User.id == Post.user_id).all()
    return render_template('adminPages/posts.html', posts=posts)

@app.route('/posts_search', methods=['GET'])
def posts_search():
    username = request.args.get('username')  # Fetch 'username' from the query string
    if username:
        posts = (
            db.session.query(User, Post)
            .join(Post, User.id == Post.user_id)
            .filter(User.username == username)
            .all()
        )
        return render_template('adminPages/posts.html', posts=posts, username=username)
    else:
        return render_template('adminPages/posts.html', posts=[], username=None)
