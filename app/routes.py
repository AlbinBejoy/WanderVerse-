import pickle
from app import app
from flask import render_template, request, redirect, url_for
from app.utility_ai import *
from app.models import *
from werkzeug.utils import secure_filename


@app.route('/')
def hello_world():  # put application's code here
    return render_template("main.html")




@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # Validate task content
        task = request.form.get('content')
        if not task:
            return "Task content is required", 400

        check=moderate(task)
        if not check.Flagged:
            # Create task and save to database
            add = make(task)
            db.session.add(add)
            db.session.commit()
            post_id = add.id
        else:
            db.session.add(check)
            db.session.commit()
            return redirect('/flagged')

        # Handle multiple image uploads
        files = request.files.getlist('images')

        for file in files:
            if file and file.filename != '':
                # Secure the file name
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Save the file
                file.save(file_path)

                # Save file info to database
                img = Images(
                    user_id=1,  # Replace with the current logged-in user ID
                    post_id=post_id,
                    image1=filename  # Update field name to match your database
                )
                db.session.add(img)

        # Commit all image records
        db.session.commit()

        return redirect('/posts/{post_id}'.format(post_id=post_id))

    return render_template('creat_page.html')


@app.route('/flagged')
def flagged():
    return render_template('moderate.html')


@app.route('/posts/<int:post_id>', methods=['GET', 'POST'])
def posts(post_id):
    post = Post.query.get_or_404(post_id)
    highlights=pickle.loads(post.highlight)
    images = Images.query.filter_by(post_id=post_id).all()
    return render_template('post.html', post=post, images=images,highlights=highlights)


@app.route('/My_blogs', methods=['GET', 'POST'])
def my_blogs():
    user_id = 1
    results = (
        db.session.query(Post, db.func.group_concat(Images.image1))
        .join(Images, Post.id == Images.post_id)
        .filter(Post.user_id == user_id)
        .group_by(Post.id)
        .all()
    )
    return render_template('my_blogs.html', results=results)
