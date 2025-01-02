from app import app
from flask import render_template, request, redirect, url_for
from app.models import Images


@app.route('/')
def hello_world():  # put application's code here
    return render_template("main.html")

@app.route('/create')
def create():
    image = Images.query.get(1)
    if not image:
        return "Image not found", 404
    return render_template('creat_page.html', image_filename=image.image1)



