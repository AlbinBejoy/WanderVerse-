import flash
from app import app
from flask import render_template, request, redirect, url_for
from app.utility_ai import *
from app.models import *
from werkzeug.utils import secure_filename


@app.route('/old')
def hello_world():  # put application's code here
    return render_template("logo.html")


@app.route('/')
def home():  # put application's code here
    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Post.status == 'live')
        .group_by(Post.id)
        .all()
    )
    return render_template('creed.html', results=results)



@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # Validate task content
        task = request.form.get('content')
        if not task:
            return "Task content is required", 400

        add = make(task)
        post_id=add.id
        if add.status=='Flagged':
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
    # Get the post from the database
    post = Post.query.get_or_404(post_id)

    # Retrieve highlights, activities, and places visited from the database
    highlights = Highlight.query.filter_by(post_id=post_id).all()
    activities = Activities.query.filter_by(post_id=post_id).all()
    places_visited = PlacesVisited.query.filter_by(post_id=post_id).all()

    # Retrieve images associated with the post (if any)
    images = Images.query.filter_by(post_id=post_id).all()

    # Prepare the data to pass to the template
    highlights_text = [highlight.highlight for highlight in highlights]
    activities_text = [activity.activity for activity in activities]
    places_visited_text = [place.place for place in places_visited]

    # Render the template with the retrieved data
    return render_template(
        'post.html',
        post=post,
        images=images,
        highlights=highlights_text,
        activities=activities_text,
        places_visited=places_visited_text
    )
@app.route('/My_blogs', methods=['GET', 'POST'])
def my_blogs():
    user_id = 1
    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Post.user_id == user_id)
        .filter(Post.status == 'live')
        .group_by(Post.id)
        .all()
    )
    return render_template('my_blogs.html', results=results)


@app.route('/trash', methods=['GET', 'POST'])
def trash():
    user_id = 1
    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Post.user_id == user_id)
        .filter(Post.status == 'trash')
        .group_by(Post.id)
        .all()
    )
    return render_template('trash.html', results=results)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = 1  # Placeholder for the logged-in user
    user = db.session.query(User).filter_by(id=user_id).first()

    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('my_blogs'))

    if request.method == 'POST':
        if request.form.get('username'):
            user.username = request.form['username']
            db.session.commit()
            flash('Profile updated successfully!', 'success')

        return redirect(url_for('profile'))

    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Post.user_id == user_id)
        .filter(Post.status == 'live')
        .group_by(Post.id)
        .all()
    )

    return render_template('profile.html', user=user, results=results)

@app.route('/delete/<int:post_id>', methods=['GET', 'POST'])
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'trash'  # Updated to set 'status' to 'trash'
    db.session.add(post)
    db.session.commit()
    return redirect('/profile')


@app.route('/restore/<int:post_id>', methods=['GET', 'POST'])
def restore(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'live'  # Updated to set 'status' to 'draft'
    db.session.add(post)
    db.session.commit()
    return redirect('/profile')


@app.route('/delete_trash/<int:post_id>', methods=['GET', 'POST'])
def delete_trash(post_id):
    post = Post.query.get_or_404(post_id)
    images = Images.query.filter_by(post_id=post_id).all()  # Fetch all images related to the post

    for image in images:
        db.session.delete(image)

    db.session.delete(post)
    db.session.commit()
    return redirect(request.referrer or '/trash')  # Redirect to the referring page or fallback to '/trash'


@app.route('/display/<int:user_id>')
def display(user_id):
    user = User.query.get_or_404(user_id)
    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Post.user_id == user_id)
        .filter(Post.status == 'live')
        .group_by(Post.id)
        .all()
    )
    return render_template('display.html', user=user, results=results)


@app.route('/categories', methods=['GET', 'POST'])
def categories():
    # Query posts and associated images
    results = (
        db.session.query(Post, db.func.group_concat(Images.image1))
        .join(Images, Post.id == Images.post_id)
        .filter(Post.status == 'live')  # No user-specific filtering
        .group_by(Post.id)
        .all()
    )

    # Group posts by category
    categories = {}
    for post, images_str in results:
        if post.category:  # Ensure category is not None or empty
            if post.category not in categories:
                categories[post.category] = []
            categories[post.category].append((post, images_str))
    return render_template('categories.html', results=categories)



@app.route('/category/<category_name>', methods=['GET'])
def category_details(category_name):
    # Query all posts for the given category (removed user_id filter)
    results = (
        db.session.query(Post, db.func.group_concat(Images.image1))
        .join(Images, Post.id == Images.post_id)
        .filter(Post.status == 'live', Post.category == category_name)  # Filter category and non-trashed posts
        .group_by(Post.id)
        .all()
    )

    return render_template('category_details.html', category=category_name, posts=results)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_id = 1  # Placeholder for the logged-in user
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            # Update user information from the form
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.phone_number = request.form.get('phone_number')

            # Handle profile picture upload
            profile_pic = request.files.get('profile_picture')
            if profile_pic and profile_pic.filename != '':
                # Secure the filename and save the file
                filename = secure_filename(profile_pic.filename)
                profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(profile_pic_path)
                user.profile_pic = filename  # Update the profile_pic field in the database

            # Commit changes to the database
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))  # Redirect to the profile page

        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash(f'An error occurred: {str(e)}', 'danger')
            app.logger.error(f'Error updating profile: {str(e)}')  # Log the error

    return render_template('edit_profile.html', user=user)