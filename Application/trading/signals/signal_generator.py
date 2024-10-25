import sys
import asyncio
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.trading import trade_logs                  # noqa: E402
from Application.trading import strategy_fields as strategy # noqa: E402



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

        trade_logs.info(f'Setup "{setup['name']}" has been added to signal setups.')

    try:
        results = await asyncio.gather(*coroutines_set)
    except asyncio.CancelledError:
            trade_logs.error("An signal generation task got canceled in "\
                          "'signal_generator.generate_signals()' function.")
    except Exception as err:
        trade_logs.error(f'Inside "signal_generator.generate_signals()": {err}')

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

    for setup in strategy.ENTRY_SYSTEM:
        for validator in setup.get("validators", []):
            coroutines_set.add(setup['function'](kline_df      = kline_df,
                                                 indicators_df = indicators_df,
                                                 setup_name    = setup_name,
                                                 properties    = validator['properties']))             
# ________________________________________________________________________________ . . .


# if __name__ == '__main__':