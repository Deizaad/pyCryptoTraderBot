import os
from dotenv import load_dotenv
import requests
import pandas as pd
from persiantools.jdatetime import JalaliDateTime
import time

# Load API token
load_dotenv('.env')
noneTOKEN_str = "Token is not configured"
API_KEY = os.getenv('MAIN_TOKEN', noneTOKEN_str)    # DONE NO-001
print(API_KEY)

# Get connection to exchange
BASE_URL = 'https://api.nobitex.ir/'
TESTNET = 'https://testnetapi.nobitex.ir/'

response = requests.get(BASE_URL + '/v2/depth/USDTIRT')
print(response)
print(response.json())

payload: dict[str, str] = {}

headers: dict[str, str] = {
    'Authorization': 'Token ' + API_KEY
}

response2 = requests.get(BASE_URL + '/users/profile', headers=headers, data=payload)

print(response2)
print(response2.json())

SYMBOL = 'USDTIRT'

# Initialize an empty DataFrame to store trades data
trades_df = pd.DataFrame()


# Function to fetch trades data
def fetch_trades_data():
    response = requests.get(BASE_URL + f'/v2/trades/{SYMBOL}')
    response.raise_for_status()  # Raise an exception for non-2xx status codes
    return response.json()


print(fetch_trades_data())


# Function to process the trades data from the API and return a Pandas DataFrame
def process_trades_data(trades_data):
    trades_list = trades_data.get("trades", [])
    trades_df = pd.DataFrame(trades_list)

    # Convert Unix timestamp to JalaliDateTime
    trades_df["time"] = trades_df["time"].apply(lambda t: JalaliDateTime.fromtimestamp(t / 1000))
                                                                                     # FIXME NO-001

    # Convert price and volume to numeric types
    trades_df["price"] = trades_df["price"].astype(float)
    trades_df["volume"] = trades_df["volume"].astype(float)

    return trades_df


# Continuously fetch and process real-time trades data
while True:
    try:
        trades_data = fetch_trades_data()
        fetched_trades_df = process_trades_data(trades_data)
        trades_df = pd.concat([fetched_trades_df, trades_df], ignore_index=True)
        print(f"New trades data added to DataFrame. DataFrame size: {len(trades_df)}")
        with pd.option_context('display.max_rows', None):
            print(trades_df)
    except Exception as e:
        print(f"Error fetching or processing trades data: {e}")

    # Wait for a certain amount of time before fetching new data
    time.sleep(6)  # Wait for 1 minute