import os
from groq import Groq

def generate_response_with_llama(query, model=None):
    """
    Generate a response using the specified Groq model.
    """
    try:
        # Fetch the API key and model from an environment variable for security purposes
        model = model or os.getenv('GROQ_MODEL')
        api_key = os.getenv('GROQ_API_KEY')
        print("api_key", api_key)

        if not api_key:
            raise ValueError("API key is missing. Please set the GROQ_API_KEY environment variable.")

        # Initialize the Groq client with the API key
        client = Groq(api_key=api_key)

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

    except ValueError as ve:
        # Handle missing API key or other value-related issues
        print(f"ValueError: {ve}")
        return "There was an issue with your request."

    except Exception as e:
        # Handle general exceptions and log the error
        print(f"An error occurred: {e}")
        return "An error occurred while processing your request."

