import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.data_processor import DataProcessor # noqa: E402

data = DataProcessor()



def supertrend_static_sl_price(atr_offset_multiplier: float, trade_side: str):
    """
    Declares price of static stop_loss order based on supertrend indicator by including an atr
    offset.

    Parameters:
        atr_offset_multiplier (float): A multiplier factor that will be applied on the ATR offset.
        trade_side (str): Direction of trade is eather "buy" | "sell".

    Returns:
        stop_loss_price (float):
    """
    if trade_side not in ['sell', 'buy']:
        raise ValueError(f'Wrong value of "{trade_side}" is provided for "trade_side", it must be'
                         ' eather "buy" | "sell".')

    # bring the value of supertrend indicator
    indicators_df = data.get_indicators_df()
    supertrend_value = indicators_df.at[-1, 'supertrend_value']
    atr_value = indicators_df.at[-1, 'atr_value']

    if trade_side == "buy":
        sl_price = supertrend_value - (atr_offset_multiplier * atr_value)
    else:
        sl_price = supertrend_value + (atr_offset_multiplier * atr_value)

    return sl_price