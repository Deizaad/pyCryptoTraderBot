import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.trading.orders.order_executioner import trade_entry_executioner    # noqa: E402

jarchi = EventHandler()



async def start_orders_engine():
    """
    Starts the orders engine.
    """
    # Attach 'trade_entry_executioner' to 'new_valid_entry_signal' event.
    jarchi.attach(trade_entry_executioner, Event.)



async def orders_state_machine():
    """
    Manages state of orders.
    """
    pass