import sys
from functools import partial
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load    # noqa: E402
from Application.utils.event_channels import Event    # noqa: E402
from Application.data.data_processor import DataProcessor    # noqa: E402
from Application.trading.market.validator import MarketValidator    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.data.data_tools import extract_strategy_fields_functions    # noqa: E402

data = DataProcessor()
jarchi = EventHandler()
market_validator = MarketValidator()


# Extract trading system functions
ENTRY_SYSTEM: list  = extract_strategy_fields_functions(
    field                           = 'entry_signal_setups',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.signals.setup_functions',
    indicator_functions_module_path = 'Application.trading.analysis.indicator_functions'
)

PARTIAL_generating_signals = partial(data.generating_signals, trading_system=ENTRY_SYSTEM)
PARTIAL_computing_indicators = partial(data.computing_indicators, trading_system=ENTRY_SYSTEM)



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
    jarchi.attach(PARTIAL_computing_indicators, Event.NEW_KLINE_DATA)
    jarchi.attach(PARTIAL_generating_signals, Event.NEW_INDICATORS_DATA)
# ________________________________________________________________________________ . . .


async def pre_market_validation_flow():
    """
    Performs jobs on "there_is_no_open_trade" event.
    """
    await market_validator.start_market_validation()

    jarchi.detach(PARTIAL_generating_signals, Event.NEW_INDICATORS_DATA)
    jarchi.detach(PARTIAL_computing_indicators, Event.NEW_KLINE_DATA)
# ________________________________________________________________________________ . . .
# =================================================================================================