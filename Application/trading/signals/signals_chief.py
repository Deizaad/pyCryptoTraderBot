import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.data.data_processor import DataProcessor    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.trading.market.validation_chief import start_market_validation    # noqa: E402

data = DataProcessor()
jarchi = EventHandler()



# =================================================================================================
# Register events
jarchi.register_event(Event.THERE_IS_NO_TRADE, [])
jarchi.register_event(Event.TRADE_GOT_CLOSED, [])    #MOVE_IT_TO_WHERE_IT_GETS_EMITTED
# =================================================================================================



# =================================================================================================
async def start_signals_engine():
    """
    Starts signals engine workeflow.
    """
    jarchi.attach(pre_market_validation_flow, Event.TRADE_GOT_CLOSED)
    jarchi.attach(pre_market_validation_flow, Event.THERE_IS_NO_TRADE)

    jarchi.attach(post_market_validation_flow, Event.MARKET_IS_VALID)

    await jarchi.emit(Event.THERE_IS_NO_TRADE)
# ________________________________________________________________________________ . . .


async def stop_signals_engine():
    """
    Stops signals engine workflow.
    """
    jarchi.detach(pre_market_validation_flow, Event.TRADE_GOT_CLOSED)
# ________________________________________________________________________________ . . .


async def post_market_validation_flow():
    """
    Performing jobs on "MARKET_IS_VALID" event.
    """
    jarchi.attach(data.computing_indicators, Event.NEW_KLINE_DATA)
    jarchi.attach(data.generating_signals, Event.NEW_INDICATORS_DATA)
# ________________________________________________________________________________ . . .


async def pre_market_validation_flow():
    """
    Performs jobs on "there_is_no_open_trade" event.
    """
    await start_market_validation()

    jarchi.detach(data.generating_signals, Event.NEW_INDICATORS_DATA)
    jarchi.detach(data.computing_indicators, Event.NEW_KLINE_DATA)
# ________________________________________________________________________________ . . .
# =================================================================================================