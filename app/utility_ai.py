from app import db
from app.models import *
import openai
from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class Days(BaseModel):
    day: str=Field(description="Wat happened on each day with day number included")


class Travel(BaseModel):
    Title: str=Field(description="Title of travel")
    Location: str
    Duration: str
    TopAttractions: str
    Highlights: list[Days]
    Tips: str


def make(blog):
    try:
        chat_completion = openai.beta.chat.completions.parse(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": "you are an expert in travel and helps summarize travel blogs"},
                {"role": "user", "content": blog}
            ],
            response_format=Travel,
        )
        if blog != "":
            # Print the response content
            response_content = chat_completion.choices[0].message.parsed
            new_data=Post(
                title=response_content.Title,
                location=response_content.Location,
                top_attractions=response_content.TopAttractions,
                tips=response_content.Tips,
                user_id=1
            )
            return new_data




    except Exception as e:
        print("An error occurred:", e)