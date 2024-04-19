import os
from dotenv import load_dotenv
import requests

# Load api token
load_dotenv('.env')
API_KEY: str | None = os.getenv('MAIN_TOKEN', default=None)  # TODO NO-001
print(API_KEY)

# Get connection to exchange
BASE_URL = 'https://api.nobitex.ir/'
TESTNET = 'https://testnetapi.nobitex.ir/'

response = requests.get(BASE_URL + '/v2/depth/USDTIRT')
print(response)
print(response.json())

payload = {}

headers = {
  'Authorization': 'Token ' + API_KEY
}

response2 = requests.get(BASE_URL + '/users/profile', headers=headers, data=payload)
# response = requests.request("GET", url, headers=headers, data=payload)

print(response2)
print(response2.json())

SYMBOL = 'USDTIRT'


# Function to fetch trades data
def fetch_trades_data():
    response = requests.get(BASE_URL + f'/v2/trades/{SYMBOL}')
    response.raise_for_status()  # Raise an exception for non-2xx status codes
    return response.json()


print(fetch_trades_data())


"""
TODO NO-001 configure 'os.getenv' to return "Token is not configured" in case of None.

"""