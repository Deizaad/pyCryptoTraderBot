import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.api.nobitex_api import Trade      # noqa: E402
from Application.api.api_service import APIService # noqa: E402

trade = Trade(APIService())


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