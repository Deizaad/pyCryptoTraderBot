import pandas as pd
import pandas_ta as ta    # type: ignore


def pandas_supertrend(kline_df, **kwargs) -> pd.DataFrame:    # FIXME NO-005
    """
    Supertrend indicator function using pandas_ta library.

    Parameters:
        kline_df (DataFrame): The OHLC DataFrame.
        window (float): The ATR length for calculating SuperTrend. Can be set in config file.
        multiplier (float): The ATR multiplier. Can be set in config file.

    Returns:
        DataFrame: A DataFrame with two columns 'supertrend' and 'supertrend_side'.
    """
    window = kwargs.get('window')
    factor = kwargs.get('factor')
    print(window, factor)
    # kline_df = kwargs.get('kline')
    # print(kline_df)
    if kline_df is None:
        return pd.DataFrame()
    
    _df = ta.supertrend(kline_df['high'], kline_df['low'], kline_df['close'], window, factor)
    
    if _df is None:
        # logging.error()
        return pd.DataFrame()
    
    _df = _df.iloc[:, 0:2]
    _df.columns = ['supertrend', 'supertrend_side']

    return _df