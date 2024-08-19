import sys
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402

jarchi = EventHandler()

jarchi.register_event(Event.VALID_TP_SIGNAL, [])
jarchi.register_event(Event.VALID_SL_SIGNAL, [])
jarchi.register_event(Event.VALID_TP_SL_SIGNAL, [])
jarchi.register_event(Event.VALID_ENTRY_SIGNAL, [])



# =================================================================================================
async def all_valid(kline_df      : pd.DataFrame,
                    indicators_df : pd.DataFrame,
                    setup_name    : str,
                    properties    : dict):
    """
    Emits on "VALID_ENTRY_SIGNAL" for all signals.
    """
    if 'entry' in setup_name:
        await jarchi.emit(Event.VALID_ENTRY_SIGNAL)
    elif 'tp_sl' in setup_name:
        await jarchi.emit(Event.VALID_TP_SL_SIGNAL)
    elif 'tp' in setup_name:
        await jarchi.emit(Event.VALID_TP_SIGNAL)
    elif 'sl' in setup_name:
        await jarchi.emit(Event.VALID_SL_SIGNAL)
# ________________________________________________________________________________ . . .


# =================================================================================================
