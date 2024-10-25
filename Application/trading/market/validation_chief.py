import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.trading import trade_logs                                   # noqa: E402
from Application.utils.event_channels import Event                           # noqa: E402
from Application.data.data_processor import DataProcessor                    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler          # noqa: E402
from Application.trading.market.validator import execute_validator_functions # noqa: E402

data = DataProcessor()
jarchi = EventHandler()



# =================================================================================================
async def start_market_validation():
    """
    Performs market validation based on chosen validator in config file.
    """
    try:
        # Attach validation_indicator_functions compution to new_kline
        jarchi.attach(data.computing_validation_indicators, Event.NEW_KLINE_DATA)

        # Attach validator_functions_coroutines to new_indicators
        jarchi.attach(execute_validator_functions, Event.NEW_VALIDATION_INDICATOR_DATA)

        # Attach stop_market_validation to market_is_valid event
        jarchi.attach(_stop_market_validation, Event.MARKET_IS_VALID)

    except Exception as err:
        trade_logs.error(f'Error occured while validating market: {err}')
# ________________________________________________________________________________ . . .


async def _stop_market_validation():
    """
    Stops further market validation processes.
    """
    jarchi.detach(listener=execute_validator_functions,
                    event=Event.NEW_VALIDATION_INDICATOR_DATA)

    jarchi.detach(listener=data.computing_validation_indicators,
                    event=Event.NEW_KLINE_DATA)
    
    trade_logs.info('Further market validation processes stopped.')
# =================================================================================================

