import sys
import asyncio
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event                                                # noqa: E402
from Application.data.data_processor import DataProcessor                                         # noqa: E402
from Application.execution.scheduler import watch_transitions                                     # noqa: E402
from Application.trading.trade_engine import start_trade_engine                                   # noqa: E402
from Application.utils.simplified_event_handler import EventHandler                               # noqa: E402
from Application.trading.trading_workflow import start_live_trading_flow                          # noqa: E402
from Application.execution.actions.common_actions import authorize_connection, heart_beat         # noqa: E402
from Application.trading.signals.signals_chief import start_signals_engine #, stop_signals_engine # noqa: E402

data = DataProcessor()
jarchi = EventHandler()



# =================================================================================================
async def run():
    """
    Runs the workflow of "base_live".
    """
    _attach_to_events()

    await authorize_connection()
    await watch_transitions()
    start_live_trading_flow()
# ________________________________________________________________________________ . . .


def _attach_to_events():
    """
    Attaches listeners to their corresponding event channels.
    """
    # Listeners of the 'RECOVERY_MECHANISM_ACCOMPLISHED' event channel
    jarchi.attach(start_signals_engine, Event.RECOVERY_MECHANISM_ACCOMPLISHED)

    # Listeners of the 'START_ACTIVITY' event channel
    jarchi.attach(data.start_fetching_kline, Event.START_ACTIVITY)
    jarchi.attach(data.start_fetching_portfolio_balance, Event.START_ACTIVITY)
    jarchi.attach(start_trade_engine, Event.START_ACTIVITY)
    
    # Listeners of the 'SUCCESS_AUTHORIZATION' event channel
    jarchi.attach(heart_beat, Event.SUCCESS_AUTHORIZATION)
# =================================================================================================