import logging
import time

import pandas as pd
import requests
from persiantools.jdatetime import JalaliDateTime
from tqdm import tqdm

import NobitexTrader.config as config
import NobitexTrader.nobitex_data as nb
from NobitexTrader.nb_api.utils import clear_console


__all__ = ["get_OHLC", "update_OHLC", "print_OHLC", "get_trades", "update_trades"]
# __OHLC__ = ["get_OHLC", "update_OHLC", "print_OHLC"]
# __market_trades__ = ["get_trades", "update_trades"]


# Logging:
# =================================================================================================
logging.basicConfig(  # Configure logging
    filename="nobitex_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
# =================================================================================================


# OHLC data:
# =================================================================================================


# Function to fetch OHLC data into a dataframe
def get_OHLC(symbol, res, end, start=0):
    endpoint = "market/udf/history"

    if start == 0:
        params = {
            "symbol": symbol,
            "resolution": res,
            "to": end,
            "countback": config.OHLC.COUNTBACK,
        }
    else:
        params = {"symbol": symbol, "resolution": res, "to": end, "from": start}

    try:
        response = requests.request("GET", nb.BASE_URL + endpoint, params=params)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        data = response.json()

        # Extract the necessary data from the API response
        timestamps = data["t"]
        open_prices = data["o"]
        high_prices = data["h"]
        low_prices = data["l"]
        close_prices = data["c"]
        volumes = data["v"]

        # Convert Unix timestamps to datetime objects
        dates = [JalaliDateTime.fromtimestamp(ts) for ts in timestamps]

        # Create a DataFrame with the OHLC data
        ohlc_df = pd.DataFrame(
            {
                "Date": dates,
                "Open": open_prices,
                "High": high_prices,
                "Low": low_prices,
                "Close": close_prices,
                "Volume": volumes,
            }
        )

        # Set the 'Date' column as the index
        ohlc_df.set_index("Date", inplace=True)

        return ohlc_df

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching OHLC data: {http_err}")
        logging.error(f"Response status code: {http_err.response.status_code}")
        logging.error(f"Response reason: {http_err.response.reason}")
        logging.error(f"Response text: {http_err.response.text}")

    except Exception as err:
        logging.error(f"Other error occurred while fetching OHLC data: {err}")

    return pd.DataFrame()  # Return an empty DataFrame in case of an error


# ____________________________________________________________________________ . . .


# Function to Update OHLC data
def update_OHLC(df):
    # Get the timestamp of the most recent entry in the DataFrame
    last_index = df.index.max()
    last_timestamp = JalaliDateTime.to_gregorian(last_index)
    last_timestamp = int(last_timestamp.timestamp())

    # Fetch new data starting from the last timestamp
    new_data = get_OHLC(
        config.OHLC.SYMBOL, config.OHLC.RESOLUTION, int(time.time()), last_timestamp
    )

    # Check if the new data contains any new timestamps
    new_timestamps = new_data.index.unique()
    existing_timestamps = df.index.unique()
    new_timestamps = new_timestamps[~new_timestamps.isin(existing_timestamps)]

    # Update the existing rows with the latest data if the timestamps match
    df.update(new_data)

    # Concatenate the new data (excluding the updated rows) and drop the oldest rows
    new_data_to_concat = new_data.loc[new_data.index.isin(new_timestamps)]
    updated_df = pd.concat([df, new_data_to_concat])
    updated_df = updated_df.sort_index(ascending=False).head(500).sort_index()

    return new_data, updated_df, new_data_to_concat, last_index


# ____________________________________________________________________________ . . .


# Function to print updates constantly
def print_OHLC(df, update_interval=10):
    while True:
        try:
            df = update_OHLC(df)[1]
            print("last Index: \n", update_OHLC(df)[3], "\n")
            print("new data: \n", update_OHLC(df)[0], "\n")
            print("new data to concat: \n", update_OHLC(df)[2], "\n")
            print("       Live OHLC data", f"             size: {len(df)}\n")
            print(df)
            print(f"DataFrame updated at {JalaliDateTime.to_jalali(time.time())} \n\n")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        time.sleep(update_interval)


# =================================================================================================


# Trades:
# =================================================================================================


# Function to fetch and process trades data
def get_trades():
    try:
        endpoint = "v2/trades/"
        response = requests.get(nb.BASE_URL + endpoint + config.TRADES.SYMBOL)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        trades_data = response.json()

        trades_list = trades_data.get("trades", [])
        trades_df = pd.DataFrame(trades_list)

        # Convert Unix timestamp to JalaliDateTime
        trades_df["time"] = trades_df["time"].apply(
            lambda t: JalaliDateTime.fromtimestamp(t / 1000).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )[:-3]
        )  # FIXED NO-001

        # Convert price and volume to numeric types
        trades_df["price"] = trades_df["price"].astype(float)
        trades_df["volume"] = trades_df["volume"].astype(float)

        return trades_df

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching trades data: {http_err}")
        logging.error(f"Response status code: {http_err.response.status_code}")
        logging.error(f"Response reason: {http_err.response.reason}")
        logging.error(f"Response text: {http_err.response.text}")

    except Exception as err:
        logging.error(f"Other error occurred while fetching trades data: {err}")

    return pd.DataFrame()  # Return an empty DataFrame in case of an error


# ____________________________________________________________________________ . . .


# function to


def update_trades(max_iterations, get_trades_func):
    """
    Fetches real-time trades data for a specified number of iterations.

    Args:
        max_iterations (int): The maximum number of iterations to fetch trades data.
        get_trades_func (callable): A function that fetches trades data.

    Returns:
        pd.DataFrame: A DataFrame containing the fetched trades data.
    """
    pbar = tqdm(
        total=max_iterations,
        desc="Fetching trades data",
        unit="batch",
        colour="#660066",
    )
    iteration = 0
    trades_df = pd.DataFrame()  # Initialize an empty DataFrame to store trades data

    while iteration < max_iterations:
        try:
            fetched_trades_df = get_trades_func()
            if fetched_trades_df is not None:
                trades_df = pd.concat([fetched_trades_df, trades_df], ignore_index=True)
                clear_console()
                print(
                    "       __Trades_dataframe__",
                    f"             size: {len(trades_df)}\n",
                )
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

    return trades_df  # FIXME NO-003
