import os, json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
res = client.chat.completions.create(
    model='llama3-8b-8192',
    messages=[
        {'role': 'system', 'content': 'Output valid JSON.'},
        {'role': 'user', 'content': 'Say {"hello": "world"}'}
    ],
    response_format={'type': 'json_object'}
)
print('OUTPUT:', res.choices[0].message.content)
