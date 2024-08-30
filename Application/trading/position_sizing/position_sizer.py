import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                            # noqa: E402
from Application.data.data_processor import DataProcessor               # noqa: E402
from Application.trading.slippage import compute_slippage               # noqa: E402
from Application.data.data_tools import extract_singular_strategy_setup # noqa: E402

data = DataProcessor()

POSITION_SIZING_APPROACH = extract_singular_strategy_setup(
    setup_name = 'position_sizing_approach',
    config = load(r'Application/configs/strategy.json'),
    setup_functions_module_path = 'Application.trading.position_sizing.position_sizing_functions'
)



# =================================================================================================
async def compute_position_margin_size(portfolio_balance  : tuple[float, float],
                                       risk_per_trade_pct : float,
                                       entry_price        : float,
                                       stop_loss_price    : float,
                                       maker_fee          : float,
                                       taker_fee          : float,
                                       src_currency       : str,
                                       dst_currency       : str,
                                       slippage           : float | None = None,
                                       funding_rate_fee   : float | None = None):
    """
    Executes the chosen position sizing function to return the position size.

    Parameters:
        portfolio_balance (tuple[float, float]): 
    
    Returns:

    """
    position_sizing_func = POSITION_SIZING_APPROACH['function']
    params = {'portfolio_balance'  : portfolio_balance,
              'risk_per_trade_pct' : risk_per_trade_pct,
              'entry_price'        : entry_price,
              'stop_loss_price'    : stop_loss_price,
              'maker_fee'          : maker_fee,
              'taker_fee'          : taker_fee,
              'src_currency'       : src_currency,
              'dst_currency'       : dst_currency,
              'funding_rate_fee'   : funding_rate_fee}

    if not slippage:
        position_size = await position_sizing_func(**params)
    
    elif slippage:
        initial_size = await position_sizing_func(**params)
        slippage = compute_slippage(position_size=initial_size, order_book=data.get)

        params['slippage'] = slippage

    return position_size
# ________________________________________________________________________________ . . .


# =================================================================================================