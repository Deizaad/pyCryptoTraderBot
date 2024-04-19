import os
from dotenv import load_dotenv
import requests
from collections import deque

# Load api token
load_dotenv('.env')
API_KEY: str | None = os.getenv('MAIN_TOKEN', default=None)  # TODO #NO-001 configure 'os.getenv' to return "Token is not configured"
                                                             # in case of None.
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
    return response.json()

print(fetch_trades_data())

## First approch to Process trades data using deque: ##
# Maximum number of trades to keep in memory
MAX_TRADES = 1000

# Initialize the deque to store trades
trades_deque = deque(maxlen=MAX_TRADES)

# Function to process the trades data
def process_trades_data(trades_data):
    if trades_data['status'] == 'ok':
        for trade in trades_data['trades']:
            # Append the trade to the deque
            trades_deque.append(trade)
            print(f"Trade added: {trade}")

process_trades_data(fetch_trades_data())