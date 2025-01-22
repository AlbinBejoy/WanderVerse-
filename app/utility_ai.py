from app.models import *
import openai
from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os

load_dotenv()
client = openai.OpenAI()
openai.api_key = os.getenv("OPENAI_API_KEY")


class Travel(BaseModel):
    Title: str=Field(description="Title of travel")
    Location: str=Field(description="Overall location of travel which is mentioned in a way all the places visited is covered in this region")
    Duration: str=Field(description="Duration of travel should always be in the format of number value followed by unit")
    PlacesVisited: list[str] = Field(description="List of places visited in this travel region, can include monuments hotels etc.")
    Activities: list[str] = Field(description="List of activities participated during this travel")
    Highlights: list[str]=Field(description="Wat happened on each day with day number included in at least 100 words")
    Tips: str
    Category: str=Field(description="Which of the following categories the blog fits: Business,Leisure,Family,Religious,Sports,Educational")

def moderate(blog, post_id):
    try:
        # Perform moderation using the AI model
        response = client.moderations.create(
            model="omni-moderation-latest",  # Use a valid moderation model name
            input=blog
        )

        # Extract moderation results
        results = response.results[0]
        categories = results.categories

        # Update the Post table with moderation data
        post = Post.query.get(post_id)
        if post:
            post.flagged = results.flagged
            post.sexuality = categories.sexual
            post.violence = categories.violence
            post.harassment = categories.harassment
            post.illicit = categories.illicit
            post.self_harm = categories.self_harm
            post.hate = categories.hate
            db.session.commit()
            return post
        else:
            raise ValueError(f"Post with id {post_id} does not exist.")

    except Exception as e:
        db.session.rollback()  # Rollback on error
        print(f"Error during moderation: {e}")
        return None


def draft(blog, post_id=None):
    try:
        if post_id:
            # Update an existing draft
            existing_post = Post.query.get(post_id)
            if existing_post:
                existing_post.content = blog
                existing_post.status = "draft"
                db.session.commit()
                return existing_post
            else:
                raise ValueError(f"Post with id {post_id} does not exist.")
        else:
            # Create a new draft
            new_draft = Post(
                title=None,  # Draft might not have a title yet
                location=None,
                tips=None,
                duration=None,
                category=None,
                user_id=1,  # Assuming a default user_id
                content=blog,
                status="draft",
                flagged=False,
                sexuality=False,
                violence=False,
                harassment=False,
                illicit=False,
                self_harm=False,
                hate=False
            )
            db.session.add(new_draft)
            db.session.commit()
            return new_draft

    except Exception as e:
        db.session.rollback()
        print(f"Error drafting post: {e}")
        return None


def make(blog, post_id=None):
    try:
        if post_id:
            # Update an existing post
            existing_post = Post.query.get(post_id)
            if existing_post:
                existing_post.content = blog
                existing_post.status = "draft"  # Update the status to draft
                db.session.commit()
            else:
                raise ValueError(f"Post with id {post_id} does not exist.")
        else:
            # Draft the new post
            draft_post = draft(blog)
            post_id = draft_post.id

        # Moderate the blog content
        moderation_result = moderate(blog, post_id)
        if moderation_result and moderation_result.flagged:
            flagged_post = Post.query.get(post_id)
            flagged_post.status = "Flagged"
            db.session.commit()
            return flagged_post

        # Parse the AI response
        chat_completion = openai.beta.chat.completions.parse(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": "You are an expert in travel and help summarize travel blogs."},
                {"role": "user", "content": blog}
            ],
            response_format=Travel,
        )

        response_content = chat_completion.choices[0].message.parsed
        post = Post.query.get(post_id)

        # Update post with processed content
        post.title = response_content.Title
        post.location = response_content.Location
        post.tips = response_content.Tips
        post.duration = response_content.Duration
        post.category = response_content.Category
        post.status = "live"  # Set status to live after processing

        # Save Highlights
        for highlight_text in response_content.Highlights:
            new_highlight = Highlight(
                user_id=1,  # Assuming the same user_id
                post_id=post.id,
                highlight=highlight_text
            )
            db.session.add(new_highlight)

        # Save Activities
        for activity_text in response_content.Activities:
            new_activity = Activities(
                user_id=1,  # Assuming the same user_id
                post_id=post.id,
                activity=activity_text
            )
            db.session.add(new_activity)

        # Save Places Visited
        for place_text in response_content.PlacesVisited:
            new_place = PlacesVisited(
                user_id=1,  # Assuming the same user_id
                post_id=post.id,
                place=place_text
            )
            db.session.add(new_place)

        db.session.commit()
        return post

    except Exception as e:
        db.session.rollback()
        print(f"Error creating or processing post: {e}")
        return None
