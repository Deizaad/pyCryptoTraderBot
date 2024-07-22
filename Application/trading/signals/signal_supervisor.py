import os
import sys
import asyncio
import logging
import pandas as pd
from typing import Callable
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.trading.signals.setup_functions import get_selected_setups    # noqa: E402



# =================================================================================================
class SignalChief:
    def declare_setups(self, path_to_setups_module: str, configs: dict):
        """
        Declares chosen strategy setups.
        """
        self.declared_setup_functions: dict[Callable, dict[str, float]] = {}

        selected_setups, _ = get_selected_setups(path_to_setups_module, configs)

        for setup in selected_setups:
            setup_func: Callable = selected_setups[setup]['function']
            properties: dict     = selected_setups[setup]['properties']

            self.declared_setup_functions[setup_func] = properties

            logging.info(f'Setup "{setup}" has been added to "declared_setup_functions".')
    # ____________________________________________________________________________ . . .


    async def generate_signals(self, kline_df: pd.DataFrame, indicator_df: pd.DataFrame):
        """
        Executes setup functions asynchronously to return generated signals as a dataframe.
        """
        tasks = []
        for function in self.declared_setup_functions:
            tasks.append(function(kline_df=kline_df,
                                  indicator_df=indicator_df,
                                  properties=self.declared_setup_functions[function]))

        try:
            results: list[pd.DataFrame] = await asyncio.gather(*tasks)
        except asyncio.CancelledError as err:
            logging.error(f"A task got cancelled in generate_signals() of SignalChief: {err}")
            raise
        except Exception as err:
            logging.error(f'Inside generate_signals() method of SignalChief: {err}')

        signal_df = pd.DataFrame(index=kline_df.index)

        for result in results:
            if not result.empty:
                signal_df = signal_df.merge(
                    result, left_index=True, right_index=True, how='left'
                )

        return signal_df
# =================================================================================================