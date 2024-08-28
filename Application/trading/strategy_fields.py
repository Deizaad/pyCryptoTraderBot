import sys
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                                # noqa: E402
from Application.data.data_tools import extract_strategy_field_value,\
                                        extract_singular_strategy_setup,\
                                        extract_non_singular_strategy_setup # noqa: E402



# try @memoization or caching these constants...
# =================================================================================================
TRADING_PAIR: dict = {
    'src_currency': extract_strategy_field_value('trading_pair')['src_currency'],
    'dst_currency': extract_strategy_field_value('trading_pair')['dst_currency']}
# ________________________________________________________________________________ . . .


ENTRY_SYSTEM: list = extract_non_singular_strategy_setup(
    setup_name                      = 'entry_signal_setups',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.signals.setup_functions',
    indicator_functions_module_path = 'Application.trading.analysis.indicator_functions',
    validator_functions_module_path = 'Application.trading.signals.signal_validation_functions'
)
# ________________________________________________________________________________ . . .


RISK_PER_TRADE: float = extract_strategy_field_value('risk_per_trade')
# ________________________________________________________________________________ . . .



# =================================================================================================