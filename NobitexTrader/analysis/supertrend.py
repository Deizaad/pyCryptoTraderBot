import talib
import numpy as np
from NobitexTrader.config import supertrend

def calculate_supertrend(df, window=supertrend.WINDOW, multiplier=supertrend.FACTOR):
    """
    Calculate supertrend for a DataFrame of OHLC data.
    """
    
    # Make a copy of the DataFrame to avoid modifying the original
    _df = df.copy()  
    
    _df['prev_close'] = _df['close'].shift(1)

    _df['atr'] = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)

    midrange = (_df['high'] + _df['low']) / 2
    offset = multiplier * _df['atr']
    
    _df['top_band'] = midrange + offset
    _df['prev_top_band'] = _df['top_band'].shift(1)
    _df['top_band'] = np.where(
        (_df['top_band'] < _df['prev_top_band']) | (_df['prev_close'] > _df['prev_top_band']),
        _df['top_band'],
        _df['prev_top_band']
    )    
    
    _df['bottom_band'] = midrange - offset
    _df['prev_bottom_band'] = _df['bottom_band'].shift(1)
    _df['bottom_band'] = np.where(
        (_df['bottom_band'] > _df['prev_bottom_band']) | (_df['prev_close'] < _df['prev_bottom_band']),
        _df['bottom_band'],
        _df['prev_bottom_band']
    )


    _df['side'] = np.nan
    _df['supertrend'] = np.nan

    conditions = [
        np.isnan(_df['atr'].shift(1)),
        (_df['supertrend'].shift(1) == _df['prev_top_band']) & (_df['close'] > _df['top_band']),
        (_df['supertrend'].shift(1) == _df['prev_top_band']) & (_df['close'] <= _df['top_band']),
        (_df['supertrend'].shift(1) != _df['prev_top_band']) & (_df['close'] < _df['bottom_band']),
        (_df['supertrend'].shift(1) != _df['prev_top_band']) & (_df['close'] >= _df['bottom_band'])
    ]
    choices = [1, -1, 1, 1, -1]
    _df['side'] = np.select(conditions, choices, default=np.nan)

    _df['supertrend'] = np.where(_df['side'] == -1, _df['bottom_band'], _df['top_band'])
    return _df#[['atr', 'top_band', 'prev_top_band', 'bottom_band', 'prev_bottom_band', 'side', 'supertrend']]