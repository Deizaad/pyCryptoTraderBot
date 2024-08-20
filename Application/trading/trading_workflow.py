import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.data_tools import extract_trading_approach    # noqa: E402

TRADING_APPROACH_CONFIG = extract_trading_approach()



def start_live_trading_flow(trading_approach_config: dict):
    """
    Executes the chosen trading approach.
    """
    return trading_approach_config['function'](properties=trading_approach_config['properties'])