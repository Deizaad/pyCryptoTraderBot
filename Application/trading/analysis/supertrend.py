import pandas as pd
from Application.configs.config import Study
import pandas_ta as ta    # type: ignore

def pandas_supertrend(kline_df: pd.DataFrame,
                      window=Study.Supertrend.WINDOW,
                      multiplier=Study.Supertrend.FACTOR) -> pd.DataFrame:    # FIXME NO-005
    """
    Supertrend indicator function.

    Parameters:
        kline_df (DataFrame): The OHLC DataFrame.

        window (float): The ATR length for calculating SuperTrend. Can be set in config file.
            
        multiplier (float): The ATR multiplier. Can be set in config file.

    Returns (DataFrame): A DataFrame with two columns 'supertrend' and 'supertrend_side'.
    """
    _df = ta.supertrend(kline_df['high'], kline_df['low'], kline_df['close'], window, multiplier).iloc[:, 0:2]
    _df.columns = ['supertrend', 'supertrend_side']
    return _df


# import talib
# import numpy as np


# def calculate_supertrend(df, window=supertrend.WINDOW, multiplier=supertrend.FACTOR):
#     """
#     Calculate supertrend for a DataFrame of OHLC data.
#     """
    
#     # Make a copy of the DataFrame to avoid modifying the original
#     _df = df.copy()  
    
#     _df['prev_close'] = _df['close'].shift(1)

#     _df['atr'] = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)

#     midrange = (_df['high'] + _df['low']) / 2
#     offset = multiplier * _df['atr']
    
#     _df['top_band'] = midrange + offset
#     _df['prev_top_band'] = _df['top_band'].shift(1)
#     _df['top_band'] = np.where(
#         (_df['top_band'] < _df['prev_top_band']) | (_df['prev_close'] > _df['prev_top_band']),
#         _df['top_band'],
#         _df['prev_top_band']
#     )    
    
#     _df['bottom_band'] = midrange - offset
#     _df['prev_bottom_band'] = _df['bottom_band'].shift(1)
#     _df['bottom_band'] = np.where(
#         (_df['bottom_band'] > _df['prev_bottom_band']) | (_df['prev_close'] < _df['prev_bottom_band']),
#         _df['bottom_band'],
#         _df['prev_bottom_band']
#     )    # FIXME NO-004


#     _df['side'] = np.nan
#     _df['supertrend'] = np.nan

#     conditions = [
#         np.isnan(_df['atr'].shift(1)),
#         (_df['supertrend'].shift(1) == _df['prev_top_band']) & (_df['close'] > _df['top_band']),
#         (_df['supertrend'].shift(1) == _df['prev_top_band']) & (_df['close'] <= _df['top_band']),
#         (_df['supertrend'].shift(1) != _df['prev_top_band']) & (_df['close'] < _df['bottom_band']),
#         (_df['supertrend'].shift(1) != _df['prev_top_band']) & (_df['close'] >= _df['bottom_band'])
#     ]
#     choices = [1, -1, 1, 1, -1]
#     _df['side'] = np.select(conditions, choices, default=np.nan)

#     _df['supertrend'] = np.where(_df['side'] == -1, _df['bottom_band'], _df['top_band'])
#     return _df#[['atr', 'top_band', 'prev_top_band', 'bottom_band', 'prev_bottom_band', 'side', 'supertrend']]