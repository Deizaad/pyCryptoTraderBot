import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime

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

payload: dict[str, str] = {}

headers: dict[str, str]= {
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


# Function to Process the trades data from the API and return a Pandas DataFrame
def process_trades_data(trades_data):
    trades_list = trades_data.get("trades", [])
    trades_df = pd.DataFrame(trades_list)

    # Convert Unix timestamp to datetime
    trades_df["time"] = trades_df["time"].apply(lambda x: datetime.fromtimestamp(x / 1000))

    # Convert price and volume to numeric types
    trades_df["price"] = trades_df["price"].astype(float)
    trades_df["volume"] = trades_df["volume"].astype(float)

    return trades_df


print(process_trades_data(fetch_trades_data()))