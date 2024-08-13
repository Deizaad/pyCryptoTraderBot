import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.data.data_processor import DataProcessor    # noqa: E402
from Application.trading.trade_engine import start_trade_engine    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.execution.scheduler import watch_transitions    # noqa: E402

jarchi = EventHandler()
data   = DataProcessor()



# =================================================================================================
async def run():
    """
    
    """
    # Attach listeners to events
    jarchi.attach(start_trade_engine, Event.START_ACTIVITY)
    jarchi.attach(data.start_fetching_kline, Event.START_ACTIVITY)


    # Schedule activity
    await watch_transitions()
# ________________________________________________________________________________ . . .
# =================================================================================================