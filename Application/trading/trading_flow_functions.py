"""This module consists of functions that declare trading approach and workflow"""
import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.simplified_event_handler import EventHandler                         # noqa: E402
from Application.trading.orders.order_executioner import stop_loss_executioner,\
                                                         trade_entry_executioner,\
                                                         take_profit_executioner,\
                                                         combo_tp_sl_executioner            # noqa: E402

jarchi = EventHandler()



async def approach_01(properties):
    """
    This approach enters into trades via a limit 
    """
    # perform position_sizing

    # # attach listeners to NEW_VALID_SIGNAL
    # jarchi.attach(trade_entry_executioner, Event.VALID_ENTRY_SIGNAL)

    # # attach listeners to LATE_SIGNAL

    # # attach listeners to TRADE_GOT_CLOSED