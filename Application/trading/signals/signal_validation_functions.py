import sys
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402

jarchi = EventHandler()

jarchi.register_event(Event.NEW_VALID_SIGNAL, [])



# =================================================================================================
async def all_valid(kline_df      : pd.DataFrame,
                    indicators_df : pd.DataFrame,
                    signals_df    : pd.DataFrame,
                    properties    : dict):
    """
    Emits on "VALID_ENTRY_SIGNAL" for all signals.
    """
    await jarchi.emit(Event.NEW_VALID_SIGNAL)
# ________________________________________________________________________________ . . .


# =================================================================================================
