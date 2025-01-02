from app import app
from flask import render_template, request, redirect, url_for

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!-'

@app.route('/create')
def create():
    return render_template('creat_page.html')

