# Gemini Integration

# Use Instructor with Google's Gemini models for structured data extraction.
#
# <b>pip install "instructor[google-genai]"</b>
import instructor
from google import genai
from pydantic import BaseModel


# <b>Initialize and patch the client</b>
# <i>(with gemini api key)</i>
API_KEY = "YOUR_API_KEY"
client = genai.Client(api_key=API_KEY)
client = instructor.from_genai(client, mode=instructor.Mode.GENAI_TOOLS)

# <b>Initialize and patch the client</b>
# <i>(with vertex)</i>
client = genai.Client(vertexai=True, project="your-project-id", location="us-central1")
client = instructor.from_genai(client, mode=instructor.Mode.GENAI_TOOLS)


# <b>Basic usage</b>
#
# Model suggestions:
# - gemini-2.0-flash-lite (fastest)
# - gemini-2.0-flash (faster)
# - gemini-2.5-pro-preview-03-25 (best)
class User(BaseModel):
    name: str
    age: int


response = client.chat.completions.create(
    model="gemini-2.0-flash-001",
    messages=[{"role": "user", "content": "Extract: Jason is 25 years old"}],
    response_model=User,
)
print(response)  # User(name='Jason', age=25)
print(f"Name: {response.name}, Age: {response.age}")  # Name: Jason , Age: 25


# <b>Ensure property ordering</b>
# By default, the API orders properties alphabetically which may be a problem if, for "example", you want to include an `examples` attribute and ensure it appears first.
# #
# In that case, you can add a `Config` class with a `propertyOrdering` attribute and explicitly list the properties in the order they should appear.
class User(BaseModel):
    name: str
    age: int

    class Config:
        propertyOrdering = ["name", "age"]


response = client.chat.completions.create(
    model="gemini-2.0-flash-001",
    messages=[{"role": "user", "content": "Extract: Jason is 25 years old"}],
    response_model=User,
)
print(response)  # User(name='Jason', age=25)
print(f"Name: {response.name}, Age: {response.age}")  # Name: Jason, Age: 25


# <b>Including a system instruction</b>
#
# Use either the `system` parameter or add a system message
response = client.chat.completions.create(
    model="gemini-2.0-flash-001",
    # system="Make everyone 10 years younger you find!",
    messages=[
        {
            "role": "system",
            "content": "Make everyone 10 years younger you find!",
        },
        {
            "role": "user",
            "content": "Extract: Jason is 25 years old",
        },
    ],
    response_model=User,
)
print(response)  # User(name='Jason', age=15)
print(f"Name: {response.name}, Age: {response.age}")  # Name: Jason, Age: 15
