from app import app
from flask import render_template, request, redirect, url_for
from app.utility_ai import *
from app.models import *


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!-'

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        task=request.form['content']
        add=make(task)
        db.session.add(add)
        db.session.commit()
        return redirect('/create')
    return render_template('creat_page.html')



