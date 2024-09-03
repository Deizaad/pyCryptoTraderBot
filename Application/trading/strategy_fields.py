import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                                # noqa: E402
from Application.data.data_tools import extract_strategy_field_value,\
                                        extract_singular_strategy_setup,\
                                        extract_non_singular_strategy_setup # noqa: E402

strategy_config = load(r'Application/configs/strategy.json')


# try @memoization or caching these constants...
# =================================================================================================
TRADING_PAIR: dict = {
    'src_currency': extract_strategy_field_value('trading_pair')['src_currency'],
    'dst_currency': extract_strategy_field_value('trading_pair')['dst_currency']
}
# ________________________________________________________________________________ . . .


ENTRY_SYSTEM: list = extract_non_singular_strategy_setup(
    setup_name                      = 'entry_signal_setups',
    config                          = strategy_config,
    setup_functions_module_path     = 'Application.trading.signals.setup_functions',
    indicator_functions_module_path = 'Application.trading.analysis.indicator_functions',
    validator_functions_module_path = 'Application.trading.signals.signal_validation_functions'
)
# ________________________________________________________________________________ . . .


STATIC_SL_APPROACH: dict = extract_singular_strategy_setup(
    setup_name                  = 'static_stop_loss_setup',
    config                      = strategy_config,
    setup_functions_module_path = 'Application.trading.stop_loss.setup_functions'
)
# ________________________________________________________________________________ . . .


RISK_PER_TRADE: float = extract_strategy_field_value('risk_per_trade')
# ________________________________________________________________________________ . . .


POSITION_SIZING_APPROACH: dict = extract_singular_strategy_setup(
    setup_name                  = 'position_sizing_approach',
    config                      = strategy_config,
    setup_functions_module_path = 'Application.trading.position_sizing.position_sizing_functions'
)
# ________________________________________________________________________________ . . .


MARKET_VALIDATION_SYSTEM = extract_non_singular_strategy_setup(
    setup_name                      = 'market_validation',
    config                          = strategy_config,
    setup_functions_module_path     = 'Application.trading.market.validation_functions',
    indicator_functions_module_path = 'Application.trading.analysis.indicator_functions'
)
# ________________________________________________________________________________ . . .


TRADING_FLOW_APPROACH = extract_singular_strategy_setup(
    setup_name                  = 'trading_workflow_approach',
    config                      = strategy_config,
    setup_functions_module_path = 'Application.trading.trading_flow_functions'
)
# =================================================================================================