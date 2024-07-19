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
# from Application.trading.signals.signal_factory import SignalFactory



# =================================================================================================
class SignalChief:
    """
    
    """
    def __init__(self):
        pass
        # ____________________________________________________________________________ . . .


    def declare_setups(self, path_to_setups_module: str, configs: dict):
        """
        Declares chosen strategy setups.
        """
        self.declared_setup_functions: dict[Callable, dict] = {}
        selected_setups, _ = get_selected_setups(path_to_setups_module, configs)

        for setup in selected_setups:
            setup_func: Callable = selected_setups[setup]['function']
            properties: dict     = selected_setups[setup]['properties']

            self.declared_setup_functions[setup_func] = properties

            logging.info(f'Setup "{setup_func}" has been added to "declared_setup_functions".')
        # ____________________________________________________________________________ . . .


    async def generate_signals(self, kline_df: pd.DataFrame, indicator_df: pd.DataFrame):
        """
        Executes setup functions asynchronously to return generated signals as a dataframe.
        """
        tasks =[]
        for function in self.declared_setup_functions:
            tasks.append(function(kline_df=kline_df,
                                  indicator_df=indicator_df,
                                  properties=self.declared_setup_functions[function]))

        try:
            results = await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logging.error("A task was cancelled during cook_indicators.")
            raise

        signal_df = pd.DataFrame(index=kline_df.index)

        for result in results:
            if not result.empty:
                signal_df = signal_df.merge(
                    result, left_index=True, right_index=True, how='left'
                )

        return signal_df
# =================================================================================================



# =================================================================================================
class SignalSupervisor:
    """
    SignalSupervisor class monitors indicator DataFrame and generates signals.
    """
    # def __init__(self, kline_df: pd.DataFrame, indicator_df:pd.DataFrame, interval: float = 1.0):
    #     try:
    #         self.kline_df = kline_df
    #         self.indicator_df = indicator_df
    #         # self.signal_factory = SignalFactory()
    #         self.signals_config = self._load_config(r"C:\Users\tshoj\OneDrive\Programming\AlgorithmicTrading\Bots\Workspace_2\NobitexTrader\NobitexTrader\signal_config.json")
    #         self.interval = interval
    #         self.signal_df = pd.DataFrame(index=kline_df.index)
    #         self.observers: list = []
    #     except Exception as err:
    #         logging.error(f"Error initializing SignalSupervisor: {err}")
    # ____________________________________________________________________________ . . .


    # def _load_config(self, path):
    #     try:
    #         with open(path, 'r') as file:
    #             signals_config = json.load(file)
    #         return signals_config
    #     except FileNotFoundError:
    #         logging.error(f"Config file not found at {path}")
    #         raise
    #     except json.JSONDecodeError:
    #         logging.error(f"Error decoding JSON from the config file at {path}")
    #         raise
    #     except Exception as e:
    #         logging.error(f"Unexpected error loading config file: {e}")
    #         raise
    # ____________________________________________________________________________ . . .


    # def attach(self, observer):
    #     """
        
    #     """
    #     try:
    #         self.observers.append(observer)
    #     except Exception as e:
    #         logging.error(f"Error attaching observer: {e}")
    # ____________________________________________________________________________ . . .


    # def notify(self, signal_df):
    #     """
        
    #     """
    #     for observer in self.observers:
    #         try:
    #             observer.update(signal_df)
    #         except Exception as err:
    #             logging.error(f"Error while notifying observer: {err}")
    # ____________________________________________________________________________ . . .


    # def _monitor(self, last_index, last_volume) -> Tuple[bool, Any, float]:
    #     """
    #     Monitor the Kline DataFrame for updates.
        
    #     Args:
    #         last_index: The last recorded index in the DataFrame.
    #         last_volume: The last recorded volume in the DataFrame.
        
    #     Returns:
    #         tuple: A tuple containing a boolean indicating if an update is needed,
    #                the current index, and the current volume.
    #     """
    #     try:
    #         current_index = self.kline_df.index[-1]
    #         current_volume = self.kline_df.iloc[-1].get('volume', 0)
            
    #         has_news = (current_volume != last_volume) or (current_index != last_index)
            
    #         return has_news, current_index, current_volume
        
    #     except IndexError as err:
    #         logging.error(f"Error in _monitor method: {err}")
    #         return False, last_index, last_volume
    # ____________________________________________________________________________ . . .


    # async def _job(self):
    #     """
    #     Takes signal functions from list to apply them to the appropriate DataFrames.
    #     """
    #     try:
    #         for signal_config in self.signals_config['signals_config']:
    #             try:
    #                 signal_type = signal_config['type']
    #                 params = signal_config.get('parameters', {})
    #                 setup = self.signal_factory.generate(signal_type, params)

    #                 if signal_type == 'single_supertrend':
    #                     new_signals = setup.apply(self.kline_df, self.indicator_df)
    #                 else:
    #                     new_signals = pd.DataFrame()
    #                     print('error in signal_type mapping')

    #                 self.signal_df = self.signal_df.combine_first(new_signals)
    #                 self.notify(new_signals)
                
    #             except Exception as err:
    #                 logging.error(f"Error in _job method for signal type {signal_type}: {err}")
    #     except Exception as err:
    #         logging.error(f"Error in _job method: {err}")
    # ____________________________________________________________________________ . . .


    # async def perform(self):
    #     """
    #     Continuously calls '_monitor' and '_job' methods to generate signals on dataframe.
    #     """
    #     if self.kline_df.empty:
    #         logging.warning("Kline dataframe is empty. Exiting perform method.")
    #         return

    #     last_index = self.kline_df.index[-1]
    #     last_volume = self.kline_df.iloc[-1].get('volume', 0)

    #     while True:
    #         try:
    #             has_news, current_index, current_volume = self._monitor(last_index, last_volume)
            
    #             if has_news:
    #                 await self._job()
    #                 last_index = current_index
    #                 last_volume = current_volume

    #             await asyncio.sleep(self.interval)
            
    #         except Exception as err:
    #             logging.error(f"Error in perform method: {err}")
    #             await asyncio.sleep(self.interval)
    # ____________________________________________________________________________ . . .


    # def deliver(self):
    #     return self.signal_df
# =================================================================================================