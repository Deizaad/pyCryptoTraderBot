import sys
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.trading import trade_logs # noqa: E402



# =================================================================================================
async def supertrend_setupfunc(
    kline_df: pd.DataFrame, indicator_df: pd.DataFrame, properties: dict
) -> pd.DataFrame:

    """
    Generate trading signals based on indicator DataFrame for single_supertrend setup.

    Parameters:
        kline_df (pd.DataFrame): DataFrame containing kline data.
        indicator_df (pd.DataFrame): DataFrame containing indicator data.

    Returns:
        pd.DataFrame: DataFrame containing the generated signals.
    """
    print(kline_df)
    print(indicator_df)
    try:
        signal_df = pd.DataFrame(index=indicator_df.index)
        signal_df['supertrend'] = 0

        _supertrend = indicator_df['supertrend_side']
        _prev_supertrend = indicator_df['supertrend_side'].shift(1)

        signal_df.loc[(_supertrend == 1) & (_prev_supertrend == -1), 'supertrend'] = 1
        signal_df.loc[(_supertrend == -1) & (_prev_supertrend == 1), 'supertrend'] = -1

        print(signal_df)
        return signal_df
    except Exception as err:
        trade_logs.error(f"Error while generating signals in supertrend_setupfunc() func: {err}")
        return pd.DataFrame()
# ________________________________________________________________________________ . . .


# Definition of other setup functions ...
# =================================================================================================