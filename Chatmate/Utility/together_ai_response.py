import os
from together import Together

# Initialize the Together client
api_key = os.getenv('TOGETHER_API_KEY')
if not api_key:
    raise ValueError("API key for Together is missing. Please set the TOGETHER_API_KEY environment variable.")

client = Together(api_key=api_key)

def generate_response_with_llama(input_text):
    """
    Generate a response using the Together API with the Llama-3 model.
    """
    try:
        print("Generating response with Llama-3...")

        # Create the API request
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": input_text}
            ],
            max_tokens=512,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>"],
            stream=True
        )

        print("Response generated with Llama-3!")

        # Stream and extract response
        return "".join(_response_stream(response))

    except Exception as e:
        print(f"Error generating response: {e}")
        return "An error occurred while generating the response."

def _response_stream(response):
    """
    Stream and yield text from the response chunks.
    """
    try:
        for chunk in response:
            # Safely access the content based on the structure of the chunk
            if hasattr(chunk, 'text'):
                yield chunk.text
            elif hasattr(chunk, 'choices') and hasattr(chunk.choices[0], 'text'):
                yield chunk.choices[0].text
            else:
                raise AttributeError("Unexpected response structure: missing 'text' or 'choices[0].text' attributes.")
    except AttributeError as e:
        print(f"Error processing response stream: {e}")
        raise
