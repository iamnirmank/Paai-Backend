import os
from groq import Groq

def generate_response_with_llama(query, model="llama-3.1-70b-versatile"):
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

        print("Chat completion response:", chat_completion)

        # Extract and return the content from the response
        return chat_completion.choices[0].message.content

    except Exception as e:
        # Handle and print any exceptions that occur
        print(f"An error occurred: {e}")
        return ""