import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User                      # noqa: E402
from Application.data.data_processor import DataProcessor   # noqa: E402
from Application.trading.slippage import compute_slippage   # noqa: E402
from Application.trading import strategy_fields as strategy # noqa: E402

data = DataProcessor()



# =================================================================================================
async def compute_position_margin_size(portfolio_balance : float,
                                       entry_price       : float,
                                       stop_loss_price   : float):
    """
    Executes the chosen position sizing function to return the position size.

    Parameters:
        portfolio_balance (float):
        entry_price (float):
        stop_loss_price (float):
    
    Returns:
        position_size (float):
    """
    position_sizing_func = strategy.POSITION_SIZING_APPROACH['function']
    params = {'portfolio_balance'  : portfolio_balance,
              'risk_per_trade_pct' : strategy.RISK_PER_TRADE,
              'entry_price'        : entry_price,
              'stop_loss_price'    : stop_loss_price,
              'maker_fee'          : User.Fee.MAKER,
              'taker_fee'          : User.Fee.TAKER,
              'src_currency'       : strategy.TRADING_PAIR['src_currency'],
              'dst_currency'       : strategy.TRADING_PAIR['dst_currency']}

    tolerance_pct = strategy.POSITION_SIZING_APPROACH.get(
        'properties'
    )['slippage_adjusted_position_size_tolerace_pct']

    initial_size = await position_sizing_func(**params)
    slippage = compute_slippage(position_size=initial_size, order_book=data.get_order_book())
    params['slippage'] = slippage

    final_size = await position_sizing_func(**params)

    while abs(final_size - initial_size) > (tolerance_pct * final_size):
        slippage = compute_slippage(position_size=final_size, order_book=data.get_order_book())
        params['slippage'] = slippage

        final_size = await position_sizing_func(**params)

    return final_size
# ________________________________________________________________________________ . . .


# =================================================================================================