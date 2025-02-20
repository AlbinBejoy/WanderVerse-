from app import app
from flask import render_template, request, redirect, url_for
from app.models import *

@app.route('/admin')
def admin():
    return render_template('adminPages/adminhome.html')

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        users = User.query.all()  # Fetch all users
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
    # Fetch flagged posts using the updated Post.status field
    flagged = (
        db.session.query(User, Post)
        .join(Post, User.id == Post.user_id)
        .filter(Post.status == 'Flagged')  # Use 'flagged' status for flagged posts
        .all()
    )
    return render_template('adminPages/flagged.html', flagged=flagged)

@app.route('/posts_admin')
def posts_admin():
    # Fetch posts with associated users
    posts = (
        db.session.query(User, Post)
        .join(Post, User.id == Post.user_id)
        .filter(Post.status != 'flagged')  # Exclude trashed posts
        .all()
    )
    return render_template('adminPages/posts.html', posts=posts)

@app.route('/posts_search', methods=['GET'])
def posts_search():
    username = request.args.get('username')  # Fetch 'username' from the query string
    posts = []
    if username:
        posts = (
            db.session.query(User, Post)
            .join(Post, User.id == Post.user_id)
            .filter(User.username.ilike(f"%{username}%"))  # Match by username
            .filter(Post.status != 'flagged')  # Exclude trashed posts
            .all()
        )
    return render_template('adminPages/posts.html', posts=posts, username=username)


@app.route('/delete_admin/<int:post_id>', methods=['GET', 'POST'])
def delete_admin(post_id):
    post = Post.query.get_or_404(post_id)
    images = Images.query.filter_by(post_id=post_id).all()  # Fetch all images related to the post

    # Delete all associated images
    for image in images:
        db.session.delete(image)

    db.session.delete(post)  # Delete the post
    db.session.commit()
    return redirect(request.referrer or '/posts_admin')  # Redirect to the referring page or fallback URL

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).all()
    images = Images.query.filter_by(user_id=user_id).all()
    db.session.delete(user)
    for image in images:
        db.session.delete(image)
    for post in posts:
        db.session.delete(post)
    db.session.commit()
    return redirect('/users_admin')