import os
import time
import requests

# Fetch the API URL and Authorization token from environment variables
API_URL = os.getenv("HUGGINGFACE_API_URL")
API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query_huggingface_api(payload, retries=3, delay=20):
    """
    Send a request to the Hugging Face API and handle errors, including model loading state.
    """
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            
            # Handle model loading (503)
            if response.status_code == 503:
                print(f"Model is loading. Retrying in {delay} seconds...")
                time.sleep(delay)
                continue

            # Check for successful response
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                print("Authorization error: The token might be invalid or expired.")
                print("Please check your Hugging Face API token.")
            else:
                print(f"HTTP error occurred: {http_err}")
                print(f"Response content: {response.text}")  # For debugging
            break

        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            break

        except Exception as err:
            print(f"An unexpected error occurred: {err}")
            break

    return {}  # Return an empty dict if an error occurs

def generate_response_with_llama(input_text):
    """
    Generate a response using the Llama-3 model via Hugging Face API.
    """
    payload = {
        "inputs": input_text,
    }
    
    result = query_huggingface_api(payload)

    # Extract response text based on the API response format
    try:
        if result and isinstance(result, list) and 'generated_text' in result[0]:
            response_text = result[0]['generated_text']
        else:
            response_text = ""
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error extracting response text: {e}")
        response_text = ""
    
    return response_text
