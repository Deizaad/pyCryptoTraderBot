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
# ____________________________________________________________________________ . . .


def parse_positions_to_df(raw_positions: tuple[dict, dict] | list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Converts raw positions data into a dataframe.

    Parameters:
        raw_positions (list[dict]): Raw positions data received from API.

    Returns (DataFrame): A dataframe containing positions data.
    """
    futures_positions: list = []
    spot_positions:    list = []

    for item in raw_positions:
        if 'positions' in item:
            futures_positions.extend(item['positions'])
        if 'orders' in item:
            spot_positions.extend(item['orders'])

    futures_df = pd.json_normalize(futures_positions) if futures_positions else pd.DataFrame()
    spot_df    = pd.json_normalize(spot_positions)    if spot_positions    else pd.DataFrame()

    if (not futures_df.empty) and (not spot_df.empty):
        # Standardizing column names
        spot_df.rename(columns={'created_at': 'createdAt'}, inplace=True)

        futures_df.set_index('id', inplace=True)
        spot_df.set_index('id', inplace=True)

    return futures_df, spot_df
# ____________________________________________________________________________ . . .


def Tehran_timestamp():
    """
    This function returns the timestamp for current time in 'Asia/Tehran' timezone.
    """
    timezone = pytz.timezone('Asia/Tehran')
    time = datetime.now(timezone)
    timestamp = int(time.timestamp())

    return timestamp
# ____________________________________________________________________________ . . .


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
# ____________________________________________________________________________ . . .


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
# ____________________________________________________________________________ . . .


def turn_Jalali_to_gregorian(series: pd.Series):
    """
    Converts JalaliDateTime values of a series into GregorianDateTime values.
    """
    if isinstance(series.min(), JalaliDateTime):
        gregorian_index = series.apply(lambda jdatetime: JalaliDateTime.to_gregorian(jdatetime))
    else:
        gregorian_index = series

    return gregorian_index
# ____________________________________________________________________________ . . .


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
# ____________________________________________________________________________ . . .



if __name__ == '__main__':
    raw_data = (
    {
        "status": "ok",
        "positions": [
            {
                "id": 128,
                "createdAt": "2022-10-20T11:36:13.604420+00:00",
                "srcCurrency": "btc",
                "dstCurrency": "rls",
                "side": "sell",
                "status": "Open",
                "marginType": "Isolated Margin",
                "collateral": "320000000",
                "leverage": "2",
                "openedAt": "2022-10-20T11:36:16.562038+00:00",
                "closedAt": None,
                "liquidationPrice": "25174302690",
                "entryPrice": "6400000000",
                "exitPrice": None,
                "delegatedAmount": "0.03",
                "liability": "0.0300450676",
                "totalAsset": "831712000",
                "marginRatio": "1.49",
                "liabilityInOrder": "0",
                "assetInOrder": "0",
                "unrealizedPNL": "−576435",
                "unrealizedPNLPercent": "−0.09",
                "expirationDate": "2022-11-20",
                "extensionFee": "320000"
            },
            {
                "id": 32,
                "createdAt": "2022-08-14T15:09:58.001901+00:00",
                "srcCurrency": "btc",
                "dstCurrency": "usdt",
                "side": "sell",
                "status": "Closed",
                "marginType": "Isolated Margin",
                "collateral": "2130",
                "leverage": "1",
                "openedAt": "2022-08-14T15:10:19.937801+00:00",
                "closedAt": "2022-08-17T18:39:52.890674+00:00",
                "liquidationPrice": "38986.54",
                "entryPrice": "21300",
                "exitPrice": "19900",
                "PNL": "118.46",
                "PNLPercent": "5.56"
            }
        ],
        "hasNext": False
    },
    {
        "status": "ok",
        "orders": [
            {
                "unmatchedAmount": "3.0000000000",
                "partial": False,
                "created_at": "2018-11-28T12:25:22.696029+00:00",
                "totalPrice": "25500000.00000000000000000000",
                "tradeType": "spot",
                "id": 173546223,
                "type": "sell",
                "execution": "Limit",
                "status": "Active",
                "srcCurrency": "Bitcoin",
                "dstCurrency": "Tether",
                "price": "9750.01",
                "amount": "0.0123",
                "matchedAmount": "0E-10",
                "averagePrice": "0",
                "fee": "0E-10",
                "clientOrderId": "order1"
            }
        ],
        "hasNext": False
    }
    )

    no_positions_data = [{'status': 'ok', 'orders': [], 'hasNext': False}, {'status': 'ok', 'positions': [], 'hasNext': False}]
    
    futures_df, spot_df = parse_positions_to_df(no_positions_data)
    print(futures_df, '\n', spot_df)