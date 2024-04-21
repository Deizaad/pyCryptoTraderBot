import os
import requests
import pandas as pd
from persiantools.jdatetime import JalaliDateTime
import time
from tqdm import tqdm
import nobitex_data
import logging

# Configure logging
logging.basicConfig(filename='nobitex_data.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

payload: dict[str, str] = {}

headers: dict[str, str] = {
    'Authorization': 'Token ' + nobitex_data.API_KEY
}

SYMBOL = nobitex_data.USDTIRT


# Function to fetch and process OHLC data
def get_ohlc_data():
    url = nobitex_data.BASE_URL
    endpoint = 'market/udf/history'

    params = {
        'symbol': SYMBOL,
        'resolution': '5',
        'from': '1562058167',
        'to': int(nobitex_data.CURRENT_TIME),
        'countback': '500'
    }

    try:
        response = requests.request("GET", url + endpoint, params=params, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        ohlc_data = response.json()

        # Extract the necessary data from the API response
        timestamps = ohlc_data['t']
        open_prices = ohlc_data['o']
        high_prices = ohlc_data['h']
        low_prices = ohlc_data['l']
        close_prices = ohlc_data['c']
        volumes = ohlc_data['v']

        # Convert Unix timestamps to datetime objects
        dates = [JalaliDateTime.fromtimestamp(ts) for ts in timestamps]

        # Create a DataFrame with the OHLC data
        ohlc_df = pd.DataFrame({
            'Date': dates,
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volumes
        })

        # Set the 'Date' column as the index
        ohlc_df.set_index('Date', inplace=True)

        return ohlc_df

    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred while fetching OHLC data: {http_err}')
        logging.error(f'Response status code: {http_err.response.status_code}')
        logging.error(f'Response reason: {http_err.response.reason}')
        logging.error(f'Response text: {http_err.response.text}')

    except Exception as err:
        logging.error(f'Other error occurred while fetching OHLC data: {err}')

    return pd.DataFrame()  # Return an empty DataFrame in case of an error


print("       __OHLC_dataframe__", "             size: \n")
print(get_ohlc_data())
time.sleep(4)


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
        logging.error(f'HTTP error occurred while fetching trades data: {http_err}')
        logging.error(f'Response status code: {http_err.response.status_code}')
        logging.error(f'Response reason: {http_err.response.reason}')
        logging.error(f'Response text: {http_err.response.text}')

    except Exception as err:
        logging.error(f'Other error occurred while fetching trades data: {err}')

    return pd.DataFrame()  # Return an empty DataFrame in case of an error


# Clear console function
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Continuously fetch and process real-time trades data
max_iterations = 2
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
        logging.error(f"Error fetching or processing trades data: {e}")
        pbar.close()
        break

    # Wait for a certain amount of time before fetching new data
    time.sleep(4)


print(" Completed fetching trades data.")
logging.info("Completed fetching trades data.")