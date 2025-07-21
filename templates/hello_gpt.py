pip install openai

import openai
import os
import requests

openai.api_key = my_secret = os.environ['FinanceAPI']

response = requests.get(my_secret)

print(response.text)

