import sys
import pandas as pd
from typing import Callable
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.trading.strategy_fields import STATIC_SL_APPROACH # noqa: E402


def trailing_order():
    """
    
    """
    pass


def place_static_stop_loss():
    """
    
    """
    pass


def declare_static_sl_price(trade_side: str, indicators_df: pd.DataFrame):
    """
    
    """
    func: Callable = STATIC_SL_APPROACH['function']
    properties = STATIC_SL_APPROACH['properties']

    stop_loss_price = func(trade_side=trade_side, indicators_df=indicators_df, **properties)
    return stop_loss_price