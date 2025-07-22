
import openai
import os

my_secret = os.environ['Finance']
openai.api_key = my_secret

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[{"role":"user","content":"Sales were 100 in Jan and 150 in Feb. What is the percent increase?"}],
  temperature = 0,
)

print(response['choices'][0]['message']['content'])