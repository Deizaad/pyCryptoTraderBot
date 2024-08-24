import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                            # noqa: E402
from Application.data.data_tools import extract_singular_strategy_setup # noqa: E402

POSITION_SIZING_APPROACH = extract_singular_strategy_setup(
    setup_name = 'position_sizing_approach',
    config = load(r'Application/configs/strategy.json'),
    functions_module_path = 'Application.trading.position_sizing.position_sizing_functions'
)



# =================================================================================================
async def compute_position_margin_size(portfolio_balance  : float,
                                       risk_per_trade_pct : float,
                                       entry_price        : float,
                                       stop_loss_price    : float,
                                       slippage_pct       : float,
                                       maker_fee          : float,
                                       taker_fee          : float,
                                       src_currency       : str,
                                       dst_currency       : str,
                                       funding_rate_fee   : float | None = None):
    """
    Executes the chosen position sizing function to return the position size.
    """
    position_sizing_func = POSITION_SIZING_APPROACH['function']

    result = await position_sizing_func(portfolio_balance,
                                        risk_per_trade_pct,
                                        entry_price,
                                        stop_loss_price,
                                        slippage_pct,
                                        maker_fee,
                                        taker_fee,
                                        src_currency,
                                        dst_currency,
                                        funding_rate_fee)
    
    return result
# ________________________________________________________________________________ . . .


# =================================================================================================