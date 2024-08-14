import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.execution.actions.disaster_actions import recovery_mechanism    # noqa: E402
from Application.trading.signals.signals_chief import start_signals_engine #, stop_signals_engine    # noqa: E402

jarchi = EventHandler()



# =================================================================================================
async def start_trade_engine():
    """
    Starts trade engine.
    """
    await recovery_mechanism()

    jarchi.attach(start_signals_engine, Event.RECOVERY_MECHANISM_ACCOMPLISHED)
# ________________________________________________________________________________ . . .


async def stop_trade_engine():
    """
    
    """
    pass
# =================================================================================================