import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.trading.orders.order_executioner import stop_loss_executioner,\
                                                         trade_entry_executioner,\
                                                         combo_tp_sl_executioner,\
                                                         take_profit_executioner    # noqa: E402

jarchi = EventHandler()



async def start_orders_engine():
    """
    Starts the orders engine.
    """
    jarchi.attach(stop_loss_executioner, Event.VALID_SL_SIGNAL)
    jarchi.attach(take_profit_executioner, Event.VALID_TP_SIGNAL)
    jarchi.attach(combo_tp_sl_executioner, Event.VALID_TP_SL_SIGNAL)
    jarchi.attach(trade_entry_executioner, Event.VALID_ENTRY_SIGNAL)



async def orders_state_machine():
    """
    Manages state of orders.
    """
    pass