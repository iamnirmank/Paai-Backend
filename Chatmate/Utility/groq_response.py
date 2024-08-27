import os
from groq import Groq

def generate_response_with_llama(query, model="llama3-8b-8192"):
    """
    Generate a response using the specified Groq model.
    """
    try:
        # Initialize the Groq client with API key from environment variable
        client = Groq(api_key="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")

        # Create a chat completion request
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model=model,
        )

        # Extract and return the content from the response
        return chat_completion.choices[0].message.content

    except Exception as e:
        # Handle and print any exceptions that occur
        print(f"An error occurred: {e}")
        return ""