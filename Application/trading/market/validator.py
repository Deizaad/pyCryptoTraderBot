import sys
import asyncio
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.trading import trade_logs                          # noqa: E402
from Application.utils.event_channels import Event                  # noqa: E402
from Application.trading import strategy_fields as strategy         # noqa: E402
from Application.utils.simplified_event_handler import EventHandler # noqa: E402

jarchi = EventHandler()
jarchi.register_event(Event.MARKET_IS_VALID, [])



async def execute_validator_functions(kline_df                 : pd.DataFrame,
                                      validation_indicators_df : pd.DataFrame):
    """
    Executes validator functions Asynchronously and emits on MARKET_IS_VALID event channel.

    Parameters:
        validator_functions (set): The set of market validator functions to be executed.
    """
    try:
        coroutines = set()
        for setup in strategy.MARKET_VALIDATION_SYSTEM:
            coroutines.add(setup["function"](
                kline_df                 = kline_df,
                validation_indicators_df = validation_indicators_df,
                properties               = setup['properties']
            ))

        results = await asyncio.gather(*coroutines)

        if all(result=='valid' for result in results):
            trade_logs.info('Market validated successfully.')
            trade_logs.info(f'Broadcasting "{Event.MARKET_IS_VALID}" event from '\
                        '"trading.market.validator.execute_validator_functions()" function.')
            
            await jarchi.emit(Event.MARKET_IS_VALID)

    except Exception as err:
        trade_logs.error('Inside "trading.market.validator.execute_validator_functions()": ',
                        err)
# ____________________________________________________________________________ . . .

