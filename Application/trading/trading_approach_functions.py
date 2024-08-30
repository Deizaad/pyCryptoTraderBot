"""This module consists of functions that declare trading approach and workflow"""
import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.event_channels import Event                                          # noqa: E402
from Application.data.exchange import Nobitex as nb                                         # noqa: E402
from Application.data.data_processor import DataProcessor                                   # noqa: E402
from Application.trading import strategy_fields as strategy                                 # noqa: E402
from Application.utils.simplified_event_handler import EventHandler                         # noqa: E402
from Application.trading.orders.order_executioner import stop_loss_executioner,\
                                                         trade_entry_executioner,\
                                                         take_profit_executioner,\
                                                         combo_tp_sl_executioner            # noqa: E402
from Application.trading.position_sizing.position_sizer import compute_position_margin_size # noqa: E402

jarchi = EventHandler()
data = DataProcessor()



async def approach_01(properties):
    """
    This approach enters into trades via a limit 
    """
    # perform position_sizing
    position_size_without_slippage = await compute_position_margin_size(
        portfolio_balance  = data.get_portfolio_balance(),          # MOVE THE COPUTION OF POSITION SIZE TO A PROPER PLACE AS HERE IS JUST TO DECLARE THE WORKFLOW
        risk_per_trade_pct = strategy.RISK_PER_TRADE,
        entry_price        = data.get_market_price(),
        stop_loss_price    = data.get_next_trade().at[0, 'init_sl'],
        maker_fee          =
    )

    # # attach listeners to NEW_VALID_SIGNAL
    # jarchi.attach(trade_entry_executioner, Event.VALID_ENTRY_SIGNAL)

    # # attach listeners to LATE_SIGNAL

    # # attach listeners to TRADE_GOT_CLOSED