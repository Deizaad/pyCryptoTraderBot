import os
import requests
import pandas as pd
from persiantools.jdatetime import JalaliDateTime
import time
from tqdm import tqdm
import nobitex_data as nb
import logging
from config import OHLC, TRADES

# Configure logging
logging.basicConfig(
    filename='nobitex_data.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Function to fetch and process OHLC data
def get_ohlc(symbol, res, end, start=0):
    endpoint = 'market/udf/history'

    if start == 0:
        params = {
            'symbol': symbol,
            'resolution': res,
            'to': end,
            'countback': OHLC.COUNTBACK,
        }
    else:
        params = {
            'symbol': symbol,
            'resolution': res,
            'to': end,
            'from': start
        }

    try:
        response = requests.request("GET", nb.BASE_URL + endpoint, params=params)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        data = response.json()

        # Extract the necessary data from the API response
        timestamps = data['t']
        open_prices = data['o']
        high_prices = data['h']
        low_prices = data['l']
        close_prices = data['c']
        volumes = data['v']

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


kline_df = get_ohlc(
    OHLC.SYMBOL,
    OHLC.RESOLUTION,
    OHLC.TO,
)

print("       __OHLC_dataframe__", "             size: \n")    # TODO NO-002
print(kline_df)
time.sleep(2)

# Function to Update OHLC data
def update_OHLC():
    # Get the timestamp of the most recent entry in the DataFrame
    last_timestamp = JalaliDateTime.to_gregorian(kline_df.index.max())
    last_timestamp = int(last_timestamp.timestamp())

    # Fetch new data starting from the last timestamp
    new_data = get_ohlc(OHLC.SYMBOL, OHLC.RESOLUTION, OHLC.TO, last_timestamp)
    
    # Check if the new data contains any new timestamps
    new_timestamps = new_data.index.unique()
    existing_timestamps = kline_df.index.unique()
    new_timestamps = new_timestamps[~new_timestamps.isin(existing_timestamps)]

    # Update the existing rows with the latest data if the timestamps match
    kline_df.update(new_data)

    # If there are new timestamps, 
    # concatenate the new data (excluding the updated rows) and drop the oldest rows
    if not new_timestamps.empty:
        new_data_to_concat = new_data.loc[~new_data.index.isin(kline_df.index)]
        updated_df = pd.concat([kline_df, new_data_to_concat])
        updated_df = updated_df.sort_index(ascending=False).head(500).sort_index()

    # If there are no new timestamps, return the updated DataFrame
    else:
        updated_df = kline_df

    return last_timestamp, new_data, updated_df


print('Last timestamp is: ', update_OHLC()[0], '\n\n', 
      update_OHLC()[1], '\n\n',
      update_OHLC()[2], '\n\n',
)
time.sleep(30)


# Function to fetch and process trades data
def get_trades_data():
    try:
        endpoint = 'v2/trades/'
        response = requests.get(nb.BASE_URL + endpoint + TRADES.SYMBOL)
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
            pbar.update(1)    # FIXME NO-002
            iteration += 1
    except Exception as e:
        logging.error(f"Error fetching or processing trades data: {e}")
        pbar.close()
        break

    # Wait for a certain amount of time before fetching new data
    time.sleep(4)


print(" Completed fetching trades data.")
logging.info("Completed fetching trades data.")