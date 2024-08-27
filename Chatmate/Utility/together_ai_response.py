import os
from together import Together

# Initialize the Together client
api_key = os.environ.get('TOGETHER_API_KEY')
client = Together(api_key=api_key)

def generate_response_with_llama(input_text):
    """Generate a response using the Together API with Llama-3."""

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
    def response_stream():
        for chunk in response:        
            # Access the content correctly based on the actual structure
            # For example, if 'text' is the correct attribute to access
            if hasattr(chunk, 'text'):
                yield chunk.text
            elif hasattr(chunk, 'choices') and hasattr(chunk.choices[0], 'text'):
                yield chunk.choices[0].text
            else:
                raise AttributeError("The response chunk does not have the expected attributes.")
    
    # Extract and return the generated response
    return "".join(response_stream())
