import os
import sys
import pytz
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from persiantools.jdatetime import JalaliDateTime    # type: ignore

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402


jarchi = EventHandler()


def parse_kline_to_df(raw_kline: dict) -> pd.DataFrame:
    """
    This function turns raw kline dict to pandas DataFrame.
    """
    tz = pytz.timezone('Asia/Tehran')

    kline_df = pd.DataFrame({
        'time'  : [JalaliDateTime.fromtimestamp(timestamp, tz) for timestamp in raw_kline['t']],
        'open'  : raw_kline['o'],
        'high'  : raw_kline['h'],
        'low'   : raw_kline['l'],
        'close' : raw_kline['c'],
        'volume': raw_kline['v']
    }).set_index('time')

    return kline_df
# ________________________________________________________________________________ . . .


def parse_orders(raw_orders: dict) -> pd.DataFrame:
    """
    Converts raw orders data into a dataframe.

    Parameters:
        raw_orders (dict): Raw orders data received from exchange API.
    
    Returns (DataFrame): A dataframe containing orders data.
    """
    orders: list = []
    orders.extend(raw_orders['orders'])
    orders_df = pd.json_normalize(orders)
    orders_df = orders_df.loc[:,['clientOrderId',
                                 'tradeType',
                                 'type',
                                 'srcCurrency',
                                 'dstCurrency',
                                 'price',
                                 'amount',
                                 'totalPrice',
                                 'leverage',
                                 'totalOrderPrice',
                                 'matchedAmount',
                                 'unmatchedAmount',
                                 'execution',
                                 'side',
                                 'isMyOrder']]
    return orders_df
# ________________________________________________________________________________ . . .


def parse_positions(raw_positions: dict) -> pd.DataFrame:
    """
    Converts raw positions data into a dataframe.

    Parameters:
        raw_positions (dict): Raw positions data received from exchange API.

    Returns (DataFrame): A dataframe containing positions data.
    """
    positions: list = []
    if 'positions' in raw_positions:
        positions.extend(raw_positions['positions'])
    elif 'orders' in raw_positions:
        positions.extend(raw_positions['orders'])

    positions_df = pd.json_normalize(positions)

    if not positions_df.empty:
        if 'created_at' in positions_df.columns:
            positions_df.rename(columns={'created_at': 'createdAt'}, inplace=True)
        # positions_df.set_index('id', inplace=True)

    return positions_df
# ________________________________________________________________________________ . . .


def parse_wallets_to_df(raw_wallets: dict, drop_void: bool = True) -> pd.DataFrame:
    """
    Converts raw wallets data to a pandas DataFrame.
    """
    wallets = []
    raw_wallets = raw_wallets.get('wallets', [])

    for wallet in raw_wallets:
        balance = float(wallet['balance'])
        if not drop_void or balance != 0:
            wallets.append({'currency'          : wallet['currency'].upper(),
                            'id'                : wallet['id'],
                            'balance'           : balance,
                            'blocked'           : float(wallet['blockedBalance']),
                            'active_balance'    : float(wallet['activeBalance']),
                            'rial_balance'      : wallet['rialBalance'],
                            'rial_balance_sell' : wallet['rialBalanceSell'],
                            'deposit_address'   : wallet['depositAddress'],
                            'deposit_tag'       : wallet['depositTag']})
            
    df = pd.DataFrame(wallets)
    df.set_index('currency', inplace=True)

    return df
# ________________________________________________________________________________ . . .


def Tehran_timestamp():
    """
    This function returns the timestamp for current time in 'Asia/Tehran' timezone.
    """
    timezone = pytz.timezone('Asia/Tehran')
    time = datetime.now(timezone)
    timestamp = int(time.timestamp())

    return timestamp
# ________________________________________________________________________________ . . .


def update_dataframe(origin_df: pd.DataFrame, late_df: pd.DataFrame, size: int):
    """
    This function updates any dataframe with new data while keeping the dataframe size constant.
    The origin_df also can be an empty dataframe.
    """
    # Return the late_df with proper size if origin_df is empty
    if origin_df.empty:
        if len(late_df) <= size:
            updated_df = late_df
        else:
            updated_df = late_df.sort_index(ascending=False).head(size).sort_index()
        return updated_df

    # get new rows
    existing_indexes = origin_df.index.unique()
    received_indexes = late_df.index.unique()
    new_indexes = received_indexes[~received_indexes.isin(existing_indexes)]
    new_rows    = late_df.loc[late_df.index.isin(new_indexes)]

    # update existing dataframe (existing rows) with new values
    origin_df.update(late_df)
    
    # update existing dataframe with new rows
    updated_df = pd.concat([origin_df, new_rows])

    # drop oldest rows
    if len(updated_df) > size:
        updated_df = updated_df.sort_index(ascending=False).head(size).sort_index()
    
    return updated_df
# ________________________________________________________________________________ . . .


def df_has_news(origin_df: pd.DataFrame, late_df: pd.DataFrame):
    """
    
    """
    # Check if late_df has indexes that are not in origin_df
    if not late_df.index.difference(origin_df.index).empty:
        return True
    
    # Check for updated cells in overlapping rows
    common_index = origin_df.index.intersection(late_df.index)
    origin_common = origin_df.loc[common_index]
    late_common = late_df.loc[common_index]

    # Compare cell by cell for the common rows
    updated_cells = late_common.ne(origin_common) & late_common.notnull()
    
    # Check if there are any updated cells
    if updated_cells.any().any():
        return True
    
    # If no new rows or updated cells found
    return False
# ________________________________________________________________________________ . . .


def turn_Jalali_to_gregorian(series: pd.Series):
    """
    Converts JalaliDateTime values of a series into GregorianDateTime values.
    """
    if isinstance(series.min(), JalaliDateTime):
        gregorian_index = series.apply(lambda jdatetime: JalaliDateTime.to_gregorian(jdatetime))
    else:
        gregorian_index = series

    return gregorian_index
# ________________________________________________________________________________ . . .


def broadcast_open_positions_event(futures_poss_df: pd.DataFrame, spot_poss_df: pd.DataFrame):
    """
    Broadcasts "OPEN_POSITIONS" event for each or both "spot" and "futures" markets if there are
    any open positions.

    Parameters:
        futures_poss_df (DataFrame): Futures market's open positions dataframe.
        spot_poss_df (DataFrame): Spot market's open positions dataframe.
    """
    if (not futures_poss_df.empty) and (not spot_poss_df.empty):
        logging.info(f'Broadcasting "{Event.OPEN_POSITIONS_futures}" and '\
                        f'"{Event.OPEN_POSITIONS_spot}" events from '\
                        '"DataProcessor._initiate_positions()" method.')
        
        event_to_emit = [
            (Event.OPEN_POSITIONS_spot, {'spot_positions_df': spot_poss_df}),
            (Event.OPEN_POSITIONS_futures, {'futures_positions_df': futures_poss_df})
        ]
        jarchi.bulk_emit(*event_to_emit)

    elif not futures_poss_df.empty:
        logging.info(f'Broadcasting "{Event.OPEN_POSITIONS_futures}" event from'\
                        '"DataProcessor._initiate_positions()" method.')
        
        jarchi.emit(event=Event.OPEN_POSITIONS_futures,
                    futures_positions_df=futures_poss_df)
        
    elif not spot_poss_df.empty:
        logging.info(f'Broadcasting "{Event.OPEN_POSITIONS_spot}" event from'\
                        '"DataProcessor._initiate_positions()" method.')
        
        jarchi.emit(event=Event.OPEN_POSITIONS_spot,
                    spot_positions_df=spot_poss_df)
# ________________________________________________________________________________ . . .