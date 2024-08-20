import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load    # noqa: E402
from Application.data.data_tools import extract_strategy_fields_functions    # noqa: E402


ENTRY_ORDERING_SETUP       = extract_strategy_fields_functions(
    field                           = 'entry_order_placement_setup',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.orders.ordering_functions'
)
TAKE_PROFIT_ORDERING_SETUP = extract_strategy_fields_functions(
    field                           = 'take_profit_order_placement_setup',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.orders.ordering_functions'
)
STOP_LOSS_ORDERING_SETUP   = extract_strategy_fields_functions(
    field                           = 'stop_loss_order_placement_setup',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.orders.ordering_functions'
)
COMBO_TP_SL_ORDERING_SETUP = extract_strategy_fields_functions(
    field                           = 'combo_of_tp_sl_order_placement_setup',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.orders.ordering_functions'
)



async def trade_entry_executioner():
    """
    
    """
    pass
# ________________________________________________________________________________ . . .


async def take_profit_executioner():
    """
    
    """
    pass
# ________________________________________________________________________________ . . .


async def stop_loss_executioner():
    """
    
    """
    pass
# ________________________________________________________________________________ . . .


async def combo_tp_sl_executioner():
    """
    
    """
    pass
# ________________________________________________________________________________ . . .