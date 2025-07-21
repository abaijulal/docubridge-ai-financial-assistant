
import openai
import os
import requests

# Get the API key from environment variables
my_secret = os.environ.get('FinanceAPI')

if my_secret:
    # If it's an OpenAI API key, use it with OpenAI
    if my_secret.startswith('sk-'):
        openai.api_key = my_secret
        print("OpenAI API key configured")
    else:
        # If it's a URL or other API endpoint, make a request
        try:
            response = requests.get(my_secret)
            print("API Response:")
            print(response.text)
        except Exception as e:
            print(f"Error making request: {e}")
else:
    print("FinanceAPI environment variable not found")
    print("Please set up your API key in the Secrets tab")
