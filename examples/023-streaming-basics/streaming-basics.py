# Streaming Basics
# Learn how to get started with streaming responses in Instructor for real-time processing. This guide covers different streaming techniques and progress tracking.
# Traditional LLM responses require waiting for the complete generation before processing can begin.
# Streaming allows you to receive and process partial responses as they're generated, enabling more responsive applications.

# Import necessary libraries
import instructor
import asyncio
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel
from typing import Dict, Any
from instructor import Partial

# Define a simple model for demonstration
class User(BaseModel):
    name: str
    age: int
    bio: str

# Patch the OpenAI client
client = instructor.from_openai(OpenAI())

# Basic streaming example
def stream_user_info():
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=User,
        stream=True,  # Enable streaming
        messages=[
            {"role": "user", "content": "Generate a profile for a fictional user named Alice who is 28 years old."}
        ]
    )

    # Each chunk contains the partial model constructed so far
    for chunk in stream:
        print(f"Received chunk: {chunk}")
        
    # Return the final complete object
    return chunk

user = stream_user_info()
print(f"\nFinal result: {user}")

# Field-by-field progress tracking with Partial
def stream_user_with_partial():
    user_stream = client.chat.completions.create_partial(
        model="gpt-3.5-turbo",
        response_model=User,
        messages=[
            {"role": "user", "content": "Generate a profile for a fictional user named Bob who is 35 years old and works as a software developer."}
        ]
    )

    # Show progress as each field gets filled in
    print("Streaming user data:")

    for partial_user in user_stream:
        # Fields appear as they're generated by the model
        print(f"Current state: name={partial_user.name}, age={partial_user.age}, bio={partial_user.bio!r}")

# Example output:
# Current state: name=None, age=None, bio=None
# Current state: name='Bob', age=None, bio=None
# Current state: name='Bob', age=35, bio=None
# Current state: name='Bob', age=35, bio='Software developer with 10 years of experience...'

# Custom progress tracking with streaming
class ProgressTracker:
    def __init__(self):
        self.progress = {}

    # Monitor completion percentage and track field updates
    def update(self, partial_user: Partial[User]):
        # Calculate what percentage of fields are now populated
        total_fields = len(User.model_fields)
        populated = sum(1 for v in [partial_user.name, partial_user.age, partial_user.bio] if v is not None)
        completion = int(populated / total_fields * 100)
        
        # Build a dictionary of only the fields that have values
        data = {}
        if partial_user.name is not None:
            data["name"] = partial_user.name
        if partial_user.age is not None:
            data["age"] = partial_user.age
        if partial_user.bio is not None:
            data["bio"] = partial_user.bio

        self.progress = {
            "completion": f"{completion}%",
            "data": data
        }

        return self.progress

def stream_with_progress():
    tracker = ProgressTracker()

    user_stream = client.chat.completions.create_partial(
        model="gpt-3.5-turbo",
        response_model=User,
        messages=[
            {"role": "user", "content": "Generate a profile for a fictional user named Carol who is 42 years old."}
        ]
    )

    for partial_user in user_stream:
        progress = tracker.update(partial_user)
        print(f"Progress: {progress['completion']} - Current data: {progress['data']}")

# Example output:
# Progress: 33% - Current data: {'name': 'Carol'}
# Progress: 66% - Current data: {'name': 'Carol', 'age': 42}
# Progress: 100% - Current data: {'name': 'Carol', 'age': 42, 'bio': 'Carol is a passionate...'}

# Async streaming for non-blocking operation
async def stream_async():
    async_client = instructor.from_openai(AsyncOpenAI())

    # Use async/await pattern for non-blocking streaming
    user_stream = await async_client.chat.completions.create_partial(
        model="gpt-3.5-turbo",
        response_model=User,
        messages=[
            {"role": "user", "content": "Generate a profile for a fictional user named Dave who is 31 years old."}
        ]
    )

    # Process stream with async for loop
    async for partial_user in user_stream:
        print(f"Async stream update: {partial_user}")

# Run the async function
asyncio.run(stream_async())

