import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.trading.trade_engine import start_trade_engine    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.execution.scheduler import register_activity_events, watch_transitions    # noqa: E402

jarchi = EventHandler()



async def run():
    """
    
    """
    register_activity_events()
    jarchi.attach(start_trade_engine, Event.START_ACTIVITY)

    watch_transitions()
# ________________________________________________________________________________ . . .