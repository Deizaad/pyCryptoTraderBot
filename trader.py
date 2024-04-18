import os
from dotenv import load_dotenv

load_dotenv('.env')

API_KEY=os.getenv('nobitexToken', default=None)    #TODO configure os.getenv to return "Token is not configured" in case of None.

print(API_KEY)
