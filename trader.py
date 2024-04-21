import os
import requests
import pandas as pd
from persiantools.jdatetime import JalaliDateTime
import time
from tqdm import tqdm
import nobitex_data

payload: dict[str, str] = {}

headers: dict[str, str] = {
    'Authorization': 'Token ' + nobitex_data.API_KEY
}

SYMBOL = nobitex_data.USDTIRT


# Function to fetch trades data
def fetch_trades_data():
    response = requests.get(nobitex_data.BASE_URL + f'v2/trades/{SYMBOL}')
    response.raise_for_status()  # Raise an exception for non-2xx status codes
    return response.json()


# Initialize an empty DataFrame to store trades data
trades_df = pd.DataFrame()


# Function to process the trades data from the API and return a Pandas DataFrame
def process_trades_data(trades_data):
    trades_list = trades_data.get("trades", [])
    trades_df = pd.DataFrame(trades_list)

    # Convert Unix timestamp to JalaliDateTime
    trades_df["time"] = trades_df["time"].apply(
        lambda t: JalaliDateTime.fromtimestamp(t / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    )    # FIXED NO-001

    # Convert price and volume to numeric types
    trades_df["price"] = trades_df["price"].astype(float)
    trades_df["volume"] = trades_df["volume"].astype(float)

    return trades_df

# Clear console function
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Continuously fetch and process real-time trades data
max_iterations = 100
pbar = tqdm(total=max_iterations, desc="Fetching trades data", unit="batch", colour='#660066')
iteration = 0
while iteration < max_iterations:
    try:
        trades_data = fetch_trades_data()
        fetched_trades_df = process_trades_data(trades_data)
        trades_df = pd.concat([fetched_trades_df, trades_df], ignore_index=True)
        clear_console()
        print(f"DataFrame size: {len(trades_df)}")
        print(trades_df)
        pbar.update(1)
        iteration += 1
    except Exception as e:
        print(f"Error fetching or processing trades data: {e}")
        pbar.close()
        break

    # Wait for a certain amount of time before fetching new data
    time.sleep(6)

print("Completed fetching trades data.")