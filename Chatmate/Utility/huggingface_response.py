import os
import time
import requests

API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-70B"
headers = {"Authorization": f"Bearer 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"}

def query_huggingface_api(payload, retries=3, delay=20):
    """Send a request to the Hugging Face API and handle errors, including loading state."""
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            if response.status_code == 503:  # Service Unavailable, model loading
                print(f"Model is loading. Waiting {delay} seconds before retry...")
                time.sleep(delay)
                continue
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                print("Authorization error: The token might be invalid or expired.")
                print("Please check your Hugging Face API token and update it in the .env file.")
            else:
                print(f"HTTP error occurred: {http_err}")
                print(f"Response content: {response.text}")  # Print response content for debugging
            break
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            break
        except Exception as err:
            print(f"An unexpected error occurred: {err}")
            break
    return {}  # Return an empty dict if an error occurs

def generate_response_with_llama(input_text):
    """Generate a response using the Llama-3 model via Hugging Face API."""
    payload = {
        "inputs": input_text,
    }
    
    result = query_huggingface_api(payload)
    
    # Extract response text based on the API response format
    try:
        response_text = result[0]['generated_text'] if result and isinstance(result, list) and 'generated_text' in result[0] else ""
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error extracting response text: {e}")
        response_text = ""
    
    return response_text
