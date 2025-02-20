from flask import flash
from app import app
from app import login_manager
from flask import render_template, request, redirect, url_for
from app.utility_ai import *
from app.models import *
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']

        # Handle profile picture upload
        profile_pic = 'profile.jpg'  # default image
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_pic = filename

        # Validate unique fields
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect(url_for('register'))

        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered!')
            return redirect(url_for('register'))

        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            phone_number=phone_number,
            profile_pic=profile_pic
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Logged in successfully!')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password!')

    return render_template('login.html')


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
@login_required
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
                    user_id=current_user.get_id(),  # Replace with the current logged-in user ID
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
    user=User.query.get_or_404(post.user_id)

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
        user=user,
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
@login_required
def trash():
    user_id = current_user.get_id()
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
@login_required
def profile():
    user_id = current_user.get_id()  # Placeholder for the logged-in user
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
@login_required
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
@login_required
def categories():
    user_id = current_user.get_id()
    results = (
        db.session.query(Post, db.func.group_concat(Images.image1))
        .join(Images, Post.id == Images.post_id)
        .filter(Post.status == 'live')
        .filter(Post.user_id!=user_id)# No user-specific filtering
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
@login_required
def category_details(category_name):
    user_id = current_user.get_id()
    # Query all posts for the given category (removed user_id filter)
    results = (
        db.session.query(Post, db.func.group_concat(Images.image1))
        .join(Images, Post.id == Images.post_id)
        .filter(Post.status == 'live', Post.category == category_name)
        .filter(Post.user_id!=user_id)# Filter category and non-trashed posts
        .group_by(Post.id)
        .all()
    )

    return render_template('category_details.html', category=category_name, posts=results)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = current_user.get_id() # Placeholder for the logged-in user
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))