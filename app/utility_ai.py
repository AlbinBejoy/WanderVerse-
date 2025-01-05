from app.models import *
import openai
from pydantic import BaseModel,Field
from dotenv import load_dotenv
import os
import pickle

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

class Travel(BaseModel):
    Title: str=Field(description="Title of travel")
    Location: str
    Duration: str
    TopAttractions: str
    Highlights: list[str]=Field(description="Wat happened on each day with day number included")
    Tips: str
    Category: str=Field(description="Which of the following categories the blog fits: Business,Leisure,Family,Religious,Sports,Educational")


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
                highlight=pickle.dumps(response_content.Highlights),
                top_attractions=response_content.TopAttractions,
                tips=response_content.Tips,
                duration=response_content.Duration,
                Category=response_content.Category,
                user_id=1
            )
            return new_data




    except Exception as e:
        print("An error occurred:", e)



def moderate(blog):
    response = client.moderations.create(
        model="omni-moderation-latest",  # Use a valid moderation model name
        input=blog
    )

    # Access results using dot notation
    results = response.results[0]
    categories = results.categories

    new_data = Moderation(
        user_id=1,
        content=blog,
        Flagged=results.flagged,
        sexuality=categories.sexual,
        violence=categories.violence,
        harassment=categories.harassment,
        illicit=categories.illicit,
        self_harm=categories.self_harm,
        hate=categories.hate,
    )
    return new_data