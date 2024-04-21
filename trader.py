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


# Function to fetch and process trades data
def get_trades_data():
    try:
        endpoint = 'v2/trades/'
        response = requests.get(nobitex_data.BASE_URL + endpoint + SYMBOL)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        trades_data = response.json()

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

    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        print(f'Response status code: {http_err.response.status_code}')
        print(f'Response reason: {http_err.response.reason}')
        print(f'Response text: {http_err.response.text}')

    except Exception as err:
        print(f'Other error occurred: {err}')


# Clear console function
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Continuously fetch and process real-time trades data
max_iterations = 5
pbar = tqdm(total=max_iterations, desc="Fetching trades data", unit="batch", colour='#660066')
iteration = 0
trades_df = pd.DataFrame()  # Initialize an empty DataFrame to store trades data

while iteration < max_iterations:
    try:
        fetched_trades_df = get_trades_data()
        if fetched_trades_df is not None:
            trades_df = pd.concat([fetched_trades_df, trades_df], ignore_index=True)
            clear_console()
            print("       __Trades_dataframe__", f"             size: {len(trades_df)}\n")
            print(trades_df)
            pbar.update(1)
            iteration += 1
    except Exception as e:
        print(f"Error fetching or processing trades data: {e}")
        pbar.close()
        break

    # Wait for a certain amount of time before fetching new data
    time.sleep(4)


print(" Completed fetching trades data.")