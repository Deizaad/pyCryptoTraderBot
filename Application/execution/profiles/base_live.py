import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event                     # noqa: E402
from Application.data.data_processor import DataProcessor              # noqa: E402
from Application.execution.scheduler import watch_transitions          # noqa: E402
from Application.trading.trade_engine import start_trade_engine        # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402

data = DataProcessor()
jarchi = EventHandler()



# =================================================================================================
async def run():
    """
    Runs the workflow of "base_live".
    """
    _attach_to_events()
    await watch_transitions()
# ________________________________________________________________________________ . . .


def _attach_to_events():
    """
    Attaches listeners to their corresponding event channels.
    """
    # listeners of START_ACTIVITY event channel
    jarchi.attach(start_trade_engine, Event.START_ACTIVITY)
    jarchi.attach(data.start_fetching_kline, Event.START_ACTIVITY)
# =================================================================================================