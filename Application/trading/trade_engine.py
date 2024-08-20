import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.execution.actions.disaster_actions import recovery_mechanism    # noqa: E402



# =================================================================================================
async def start_trade_engine():
    """
    Starts trade engine.
    """
    await recovery_mechanism()
# ________________________________________________________________________________ . . .


async def stop_trade_engine():
    """
    
    """
    pass
# =================================================================================================