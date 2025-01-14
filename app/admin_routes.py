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


@app.route('/flags')
def flags():
    flagged = db.session.query(User, Moderation).join(Moderation, User.id == Moderation.user_id).all()
    return render_template('adminPages/flagged.html', flagged=flagged)