import json
import easyocr
import re
from os import abort
from flask import flash
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
        return redirect(url_for('recommend'))

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
            print("Flash message: Username already exists!")
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
            new_user.index()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))

    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('recommend'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form

        # Check if admin login
        if username == 'admin' and password == 'Admin@123':
            flash('Admin login successful!')
            return redirect(url_for('admin'))

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Logged in successfully!')
            return redirect(next_page) if next_page else redirect(url_for('recommend'))
        else:
            flash('Invalid username or password!')

    return render_template('login.html')

@app.route('/old')
def hello_world():  # put application's code here
    return render_template("wanderverse.html")


@app.route('/')
def home():  # put application's code here
    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Post.status == 'live')
        .group_by(Post.id)
        .all()
    )
    return render_template('logo.html', results=results)



@app.route('/create', methods=['GET','POST'])
@login_required
def create():
    user_id = current_user.get_id()
    post = None #Initialize post variable

    if request.method == 'POST':
        # Validate task content
        task = request.form.get('content')
        if not task:
            return "Task content is required", 400

        add = make(task,user_id=user_id)
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
        add.index()
        return redirect('/posts/{post_id}'.format(post_id=post_id))

        # Check if editing an existing draft
        post_id = request.args.get('post_id')
        if post_id:
            post = Post.query.get_or_404(post_id)

    return render_template('creat_page.html', post=post)


@app.route('/process_ocr', methods=['POST'])
@login_required
def process_ocr():
    if 'image' not in request.files:
        return json.dumps({'error': 'No file part'}), 400, {'Content-Type': 'application/json'}

    file = request.files['image']
    if file.filename == '':
        return json.dumps({'error': 'No selected file'}), 400, {'Content-Type': 'application/json'}

    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file temporarily
        file.save(file_path)

        try:
            # Perform OCR with EasyOCR
            reader = easyocr.Reader(['en'])  # Specify languages as needed
            result = reader.readtext(file_path, detail=0)
            text = " ".join(result)

            # Clean up the file after processing
            os.remove(file_path)

            return json.dumps({
                'success': True,
                'text': text
            }), 200, {'Content-Type': 'application/json'}
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}
    else:
        return json.dumps({'error': 'File type not allowed'}), 400, {'Content-Type': 'application/json'}


# Helper function to check allowed file types
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'tiff', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/flagged')
def flagged():
    return render_template('moderate.html')





@app.route('/posts/<int:post_id>')
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
    user_favorites = {fav.post_id for fav in Favorites.query.filter_by(user_id=current_user.id).all()}

    # Render the template with the retrieved data
    return render_template(
        'post.html',
        user=user,
        post=post,
        images=images,
        highlights=highlights_text,
        activities=activities_text,
        places_visited=places_visited_text,
        user_favorites=user_favorites
    )
@app.route('/My_blogs')
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


@app.route('/trash')
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

@app.route('/delete/<int:post_id>')
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'trash'  # Updated to set 'status' to 'trash'
    db.session.add(post)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/restore/<int:post_id>')
def restore(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = 'live'  # Updated to set 'status' to 'draft'
    db.session.add(post)
    db.session.commit()
    return redirect('/profile')


@app.route('/delete_trash/<int:post_id>')
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
    if user.id != current_user.id:
        results = (
            db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
            .outerjoin(Images, Post.id == Images.post_id)
            .filter(Post.user_id == user_id)
            .filter(Post.status == 'live')
            .group_by(Post.id)
            .all()
        )
        return render_template('display.html', user=user, results=results)
    else:
        return redirect('/profile')


@app.route('/categories')
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



@app.route('/category/<category_name>')
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


# Email validation regex pattern
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_id = current_user.get_id()
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            # Update user information from the form
            username = request.form.get('username')
            email = request.form.get('email')
            phone_number = request.form.get('phone_number')

            # Validate email
            if not email or not re.match(EMAIL_REGEX, email):
                flash('Please enter a valid email address (e.g., example@domain.com)', 'danger')
                return redirect(url_for('edit_profile'))

            # Validate phone number
            if not phone_number.isdigit() or len(phone_number) != 10:
                flash('Phone number must be exactly 10 digits.', 'danger')
                return redirect(url_for('edit_profile'))

            # Update user object if validations pass
            user.username = username
            user.email = email
            user.phone_number = phone_number

            # Handle profile picture upload
            profile_pic = request.files.get('profile_picture')
            if profile_pic and profile_pic.filename != '':
                filename = secure_filename(profile_pic.filename)
                profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(profile_pic_path)
                user.profile_pic = filename

            # Commit changes to the database
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            app.logger.error(f'Error updating profile: {str(e)}')

    return render_template('edit_profile.html', user=user)


@app.route('/save_draft', methods=['POST'])
def save_draft():
    user_id = current_user.get_id()
    content = request.form.get('content')
    post_id = request.form.get('post_id')  # Get post_id if editing an existing draft
    print(f"Save draft called with user_id: {user_id}, content: {content}")  # Log input parameters
    new_draft = draft(content, user_id=user_id,post_id=post_id)
    if new_draft:
        return json.dumps({'success': True}), 200
    else:
        return json.dumps({'success': False, 'error': 'Failed to save draft.'}), 500


@app.route('/my_drafts')
@login_required  # Ensure the user is logged in
def my_drafts():
    # Fetch drafts from the database for the current user
    drafts = Post.query.filter_by(user_id=current_user.id, status='draft').all()

    # Fetch images for each draft
    results = []
    for draft in drafts:
        images = Images.query.filter_by(post_id=draft.id).all()  # Get images associated with the draft
        images_str = ','.join([img.image1 for img in images])  # Create a comma-separated string of image paths
        results.append((draft, images_str))  # Append the draft and its images to results

    return render_template('my_drafts.html', results=results)
@app.route('/edit_draft/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_draft(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)  # Forbidden if the user does not own the draft

    # Fetch images associated with the post
    images = Images.query.filter_by(post_id=post_id).all()

    if request.method == 'POST':
        # Update the post with new data
        post.content = request.form['content']  # Always update content

        # Handle image uploads
        files = request.files.getlist('images')
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Save file info to database
                img = Images(
                    user_id=current_user.get_id(),
                    post_id=post.id,
                    image1=filename
                )
                db.session.add(img)

        db.session.commit()
        flash('Draft updated successfully!')
        return redirect(url_for('my_drafts'))  # Redirect to My Drafts page

    return render_template('creat_page.html', post=post, images=images)  # Pass images to the template

@app.route('/delete_draft/<int:post_id>', methods=['POST'])
@login_required
def delete_draft(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)  # Forbidden if the user does not own the draft

    # Delete associated images
    images = Images.query.filter_by(post_id=post_id).all()
    for image in images:
        db.session.delete(image)

    # Delete the post
    db.session.delete(post)
    db.session.commit()
    flash('Draft deleted successfully!')
    return redirect(url_for('my_drafts'))


@app.route('/submit_feedback', methods=['GET','POST'])
def submit_feedback():

    user_id = current_user.get_id()

    if request.method == 'POST':
        message = request.form.get('content')

        if not message:
            flash('Feedback cannot be empty.')
            return redirect(url_for('submit_feedback'))

        # Create new feedback
        new_feedback = Feedback(
            user_id = user_id,
            message = message,
        )

        db.session.add(new_feedback)
        db.session.commit()

        flash('Thank you for your feedback! We will review it shortly.')

    return render_template('feedback.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/recommend')
@login_required
def recommend():
    # Fetch most popular posts based on favorites
    popular_posts = (
        db.session.query(Post, db.func.count(Favorites.post_id).label('favorites_count'))
        .outerjoin(Favorites, Favorites.post_id == Post.id)  # Use outerjoin to include posts with no favorites
        .group_by(Post.id)
        .order_by(db.desc('favorites_count'), db.desc(Post.id))  # Order by favorites count, then by post ID as a fallback
        .filter(Post.status == 'live')
        .limit(10)  # Limit to top 10 posts
        .all()
    )

    # Extract Post objects from the tuples
    popular_posts = [post for post, _ in popular_posts]

    # Fetch personalized recommendations based on user's favorite categories
    user_favorite_categories = (
        db.session.query(Post.category)
        .join(Favorites, Favorites.post_id == Post.id)
        .filter(Favorites.user_id == current_user.id)
        .filter(Post.status == 'live')
        .distinct()
        .all()
    )

    # Extract category names
    favorite_categories = [category[0] for category in user_favorite_categories]

    # If no favorite categories are found, fall back to some default categories
    if not favorite_categories:
        favorite_categories = ['Leisure', 'Business', 'Family']  # Example default categories

    # Fetch posts that match the user's favorite categories, ensuring no duplicates
    personalized_posts = (
        db.session.query(Post)
        .filter(Post.category.in_(favorite_categories))
        .filter(Post.status == 'live')  # Ensure live posts only
        .distinct(Post.id)  # Ensure each post is unique by its ID
        .order_by(db.func.random())  # Randomize the order of posts
        .limit(15)  # Limit to 15 personalized posts
        .all()
    )

    # Attach images to posts
    all_posts = popular_posts + personalized_posts
    for post in all_posts:
        post.images = [img.image1 for img in Images.query.filter_by(post_id=post.id).all()]
        # Ensure post.images is not empty by providing a default image if no images are found
        if not post.images:
            post.images = ['default.jpg']  # Provide a default image

    return render_template('recommend.html', popular_posts=popular_posts, personalized_posts=personalized_posts)


@app.route('/toggle_favorite/<int:post_id>')
@login_required
def toggle_favorite(post_id):
    post = Post.query.get_or_404(post_id)
    fav = Favorites.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if fav:
        db.session.delete(fav)  # Remove from favorites
    else:
        new_fav = Favorites(user_id=current_user.id, post_id=post.id)
        db.session.add(new_fav)  # Add to favorites

    db.session.commit()
    return redirect(request.referrer or url_for('posts'))


@app.route('/favorites')
@login_required
def favorites():
    user_id = current_user.get_id()

    # Fetch posts that are favorited by the current user
    results = (
        db.session.query(Post, db.func.coalesce(db.func.group_concat(Images.image1), ''))
        .join(Favorites, Favorites.post_id == Post.id)
        .outerjoin(Images, Post.id == Images.post_id)
        .filter(Favorites.user_id == user_id)  # This now correctly belongs to query
        .filter(Post.status == 'live')
        .group_by(Post.id)
        .all()
    )

    return render_template('favorites.html', results=results)

@app.route('/search', methods=['GET'])
@login_required
def search():
    if not app.elasticsearch:
        flash("Search is currently disabled.")
        return redirect(url_for('home'))

    query = request.args.get('q', '')
    if len(query) < 3:
        flash('Please enter at least 3 characters for search.')
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)

    # Search for posts and users separately
    post_query, total_posts = Post.search(
        query, page, 10, exclude_user_id=current_user.id
    )
    user_query, total_users = User.search(query, page, 10)

    # Get images for each post
    post_ids = [post.id for post in post_query]
    images_query = (
        db.session.query(Images.post_id, db.func.group_concat(Images.image1).label("images"))
        .filter(Images.post_id.in_(post_ids))
        .group_by(Images.post_id)
        .all()
    )

    # Create a mapping of post_id to images
    images_dict = {post_id: images.split(",") if images else [] for post_id, images in images_query}

    # Attach images to posts
    for post in post_query:
        post.images = images_dict.get(post.id, ["default.jpg"])

    return render_template(
        'search_results.html',
        posts=post_query,
        users=user_query,
        query=query
    )

@app.route('/help', methods=['GET'])
@login_required
def help():
    return render_template('help.html')