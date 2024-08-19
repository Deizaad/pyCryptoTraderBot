import sys
import asyncio
import logging
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load    # noqa: E402
from Application.data.data_tools import extract_strategy_fields_functions    # noqa: E402

# Extract trading system functions
ENTRY_SYSTEM: list  = extract_strategy_fields_functions(
    field                           = 'entry_signal_setups',
    config                          = load(r'Application/configs/strategy.json'),
    setup_functions_module_path     = 'Application.trading.signals.setup_functions',
    indicator_functions_module_path = 'Application.trading.analysis.indicator_functions',
    validator_functions_module_path = 'Application.trading.signals.signal_validation_functions'
)


async def generate_signals(trading_system : list,
                           kline_df       : pd.DataFrame,
                           indicators_df  : pd.DataFrame):
    """
    Executes setup functions from given trading system asynchronously.
    """
    coroutines_set = set()

    for setup in trading_system:
        coroutines_set.add(setup['function'](kline_df     = kline_df,
                                             indicator_df = indicators_df,
                                             properties   = setup['properties']))

        logging.info(f'Setup "{setup['name']}" has been added to signal setups.')

    try:
        results = await asyncio.gather(*coroutines_set)
    except asyncio.CancelledError:
            logging.error("An signal generation task got canceled in "\
                          "'signal_generator.generate_signals()' function.")
    except Exception as err:
        logging.error(f'Inside "signal_generator.generate_signals()": {err}')

    signal_df = pd.DataFrame(index=kline_df.index)
    for result in results:
            if not result.empty:
                signal_df = signal_df.merge(
                    result, left_index=True, right_index=True, how='left'
                )

    return signal_df
# ________________________________________________________________________________ . . .


async def validate_signals(kline_df      : pd.DataFrame,
                           indicators_df : pd.DataFrame,
                           setup_name    : pd.DataFrame):
    """
    Executes signal validation functions from given trading system asynchronously.
    """
    coroutines_set = set()

    for setup in ENTRY_SYSTEM:
        for validator in setup.get("validators", []):
            coroutines_set.add(setup['function'](kline_df      = kline_df,
                                                 indicators_df = indicators_df,
                                                 setup_name    = setup_name,
                                                 properties    = validator['properties']))             
# ________________________________________________________________________________ . . .


# if __name__ == '__main__':