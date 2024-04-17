import os
from dotenv import load_dotenv

load_dotenv('.env')

API_KEY=os.getenv('nobitexToken', default=None)

print(API_KEY)