import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.trading.strategy_fields import TRADING_FLOW_APPROACH # noqa: E402



def start_live_trading_flow():
    """
    Executes the chosen trading approach.
    """
    return TRADING_FLOW_APPROACH['function'](properties=TRADING_FLOW_APPROACH['properties'])