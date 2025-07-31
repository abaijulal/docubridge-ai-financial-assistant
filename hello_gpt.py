import google.generativeai as genai
import os

try:
    my_secret = os.environ['Key1']
    genai.configure(api_key=my_secret)
except KeyError:
    print("Error: The environment variable 'Key1' is not set.")
    exit()

model = genai.GenerativeModel('gemini-1.5-flash')

# Send a prompt
try:
    response = model.generate_content("Sales were 100 in Jan and 150 in Feb. What is the percent increase?")
    # Print the response's text content
    print(response.text)
except Exception as e:
    print(f"An error occurred while generating content: {e}")