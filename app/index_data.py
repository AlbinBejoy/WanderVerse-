from app import app, db
from app.models import Post, User

def reindex():
    if not app.elasticsearch:
        print("Elasticsearch is disabled. No indexing performed.")
        return

    for post in Post.query.all():
        post.index()
    for user in User.query.all():
        user.index()
    print("Indexing complete!")

if __name__ == "__main__":
    with app.app_context():
        reindex()