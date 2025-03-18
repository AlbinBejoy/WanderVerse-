from flask_login import UserMixin
from app import db, app
from sqlalchemy import event
from sqlalchemy import case

def add_to_index(index, model):
    if not app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    if not app.elasticsearch:
        return
    app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    """Query Elasticsearch and return IDs and total matches."""
    if not app.elasticsearch:
        return [], 0

    # Check if we're searching posts or users to dynamically define fields
    search_fields = ['title', 'location', 'category', 'content'] if index == 'post' else ['username', 'email']

    search = app.elasticsearch.search(
        index=index,
        body={
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': search_fields,
                    'fuzziness': 'AUTO'
                }
            },
            'from': (page - 1) * per_page,
            'size': per_page
        }
    )
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']

class SearchableMixin(object):
    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, cls):
                obj.index()  # Index after commit
        for obj in session._changes['update']:
            if isinstance(obj, cls):
                obj.index()
        for obj in session._changes['delete']:
            if isinstance(obj, cls):
                remove_from_index(cls.__tablename__, obj)
        session._changes = None


# Attach SQLAlchemy event listeners
event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
event.listen(db.session, 'after_commit', SearchableMixin.after_commit)



class User(db.Model, UserMixin, SearchableMixin):
    __tablename__ = 'user'
    __searchable__ = ['username', 'email']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.Integer, unique=True, nullable=False)
    profile_pic = db.Column(db.String(120), nullable=False, default='profile.jpg')

    @classmethod
    def search(cls, expression, page=1, per_page=10):
        """Search users using Elasticsearch."""
        if not app.elasticsearch:
            return [], 0

        # Get IDs and total results from Elasticsearch
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if not ids:
            return [], 0

        # Create conditions for preserving the order using case()
        when_conditions = [
            (id_, index) for index, id_ in enumerate(ids)
        ]

        # Correct usage of case() for ordering results
        order_case = case(
            {id_: index for id_, index in when_conditions},
            value=cls.id
        )

        # Fetch users and preserve the order
        results = cls.query.filter(cls.id.in_(ids)).order_by(order_case).all()
        return results, total

    def index(self):
        """Index a user to Elasticsearch."""
        if not app.elasticsearch:
            return
        payload = {
            'username': self.username,
            'email': self.email
        }
        app.elasticsearch.index(index="user", id=self.id, body=payload)



class Post(db.Model, SearchableMixin):
    __tablename__ = 'post'
    __searchable__ = ['title', 'location', 'category', 'content']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    tips = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status=db.Column(db.String, nullable=False, default='draft')
    content = db.Column(db.String, nullable=False)
    flagged = db.Column(db.Boolean, nullable=False,default=False)
    sexuality = db.Column(db.String(255), nullable=False,default=False)
    violence = db.Column(db.String(255), nullable=False,default=False)
    harassment = db.Column(db.String(255), nullable=False,default=False)
    illicit = db.Column(db.String(255), nullable=False,default=False)
    self_harm = db.Column(db.String(255), nullable=False,default=False)
    hate = db.Column(db.String(255), nullable=False,default=False)

    def index(self):
        """Index a post/user to Elasticsearch."""
        if not app.elasticsearch:
            return
        payload = {}
        for field in self.__searchable__:
            payload[field] = getattr(self, field)
        app.elasticsearch.index(index=self.__tablename__, id=self.id, body=payload)

    @classmethod
    @classmethod
    def search(cls, expression, page=1, per_page=10, exclude_user_id=None):
        """Search posts using Elasticsearch."""
        if not app.elasticsearch:
            return [], 0

        # Get IDs and total results from Elasticsearch
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if not ids:
            return [], 0

        # Create conditions for preserving the order using case()
        when_conditions = [
            (id_, index) for index, id_ in enumerate(ids)
        ]

        # Correct usage of case()
        order_case = case(
            {id_: index for id_, index in when_conditions},
            value=cls.id
        )

        # Apply filters to exclude the user's own posts and only show 'live' posts
        query = cls.query.filter(
            cls.id.in_(ids),
            cls.status == 'live'  # Only show posts that are live
        )

        # Exclude the user's own posts if exclude_user_id is passed
        if exclude_user_id:
            query = query.filter(cls.user_id != exclude_user_id)

        # Fetch posts and maintain order
        results = query.order_by(order_case).all()
        return results, total


class Highlight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    highlight = db.Column(db.String(255), nullable=True)

class Activities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    activity = db.Column(db.String(255), nullable=True)

class PlacesVisited(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    place = db.Column(db.String(255), nullable=True)

class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image1 = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)

class Favorites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

