import os
from dotenv import load_dotenv

load_dotenv('.env')

API_KEY=os.environ['nobitexToken']

print(API_KEY)