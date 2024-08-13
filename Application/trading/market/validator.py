import sys
import asyncio
import logging
import pandas as pd
from functools import partial
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load    # noqa: E402
from Application.utils.event_channels import Event    # noqa: E402
from Application.data.data_processor import DataProcessor  # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.data.data_tools import extract_strategy_fields_functions  # noqa: E402

data = DataProcessor()
jarchi = EventHandler()

jarchi.register_event(Event.MARKET_IS_VALID, [])



# =================================================================================================
class MarketValidator:
    async def start_market_validation(self):
        """
        Performs market validation based on chosen validator in config file.
        """
        try:
            # Extract validation setups from strategy.json file
            self.validation_setups = extract_strategy_fields_functions(
                field                          ='market_validation',
                config                         =load(r'Application/configs/strategy.json'),
                setup_functions_module_path    ='Application.trading.signals.setup_functions',
                indicator_functions_module_path='Application.trading.analysis.indicator_functions'
            )

            # Define the partial function for computing validation indicators
            self.PARTIAL_compute_validation_indicators = partial(
                data.computing_validation_indicators, validation_setups=self.validation_setups
            )

            # Attach validation_indicator_functions compution to new_kline
            jarchi.attach(self.PARTIAL_compute_validation_indicators, Event.NEW_KLINE_DATA)

            # Attach validator_functions_coroutines to new_indicators
            jarchi.attach(self.execute_validator_functions, Event.NEW_VALIDATION_INDICATOR_DATA)

            # Attach stop_market_validation to market_is_valid event
            jarchi.attach(self._stop_market_validation, Event.MARKET_IS_VALID)

        except Exception as err:
            logging.error(f'Error occured while validating market: {err}')
    # ____________________________________________________________________________ . . .


    async def execute_validator_functions(self,
                                          kline_df                 : pd.DataFrame,
                                          validation_indicators_df : pd.DataFrame):
        """
        Executes validator functions Asynchronously and emits on MARKET_IS_VALID event channel.

        Parameters:
            validator_functions (set): The set of market validator functions to be executed.
        """
        try:
            coroutines = set()
            for setup in self.validation_setups:
                coroutines.add(setup["function"](
                    kline_df=kline_df,
                    validation_indicators_df=validation_indicators_df,
                    properties=setup['properties']
                ))

            results = await asyncio.gather(*coroutines, return_exceptions=True)

            if all(result=='valid' for result in results):
                logging.info('Market validated successfully.')
                logging.info(f'Broadcasting "{Event.MARKET_IS_VALID}" event from '\
                            '"trading.market.validator.market_validator()" function.')
                
                await jarchi.emit(Event.MARKET_IS_VALID)

        except Exception as err:
            logging.error('Inside "trading.market.validator._execute_validator_functions()": ',
                          err)
    # ____________________________________________________________________________ . . .


    async def _stop_market_validation(self):
        """
        Stops further market validation processes.
        """
        jarchi.detach(listener=self.execute_validator_functions,
                      event=Event.NEW_VALIDATION_INDICATOR_DATA)

        jarchi.detach(listener=self.PARTIAL_compute_validation_indicators,
                      event=Event.NEW_KLINE_DATA)
        
        logging.info('Further market validation processes stopped.')
    # ____________________________________________________________________________ . . .
# =================================================================================================



# =================================================================================================
def bypass_market_validation(kline_df                 : pd.DataFrame,
                             validation_indicators_df : pd.DataFrame,
                             properties               : dict) -> str:
    """
    Returns:
        validation (str): Always returns 'valid'.
    """
    # Other validator functions would get supplies here like:
    # kline_df = data.get_kline_df()
    # validation_indicators_df = data.get_validation_indicators_df()

    return 'valid'
# =================================================================================================