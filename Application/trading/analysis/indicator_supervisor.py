import os
import sys
import asyncio
import logging
import pandas as pd
from dotenv import load_dotenv
from typing import Callable, Any, List, Tuple, Dict

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.trading.analysis.indicator_tasks import tasks_dict  # noqa: E402
from Application.trading.signals.setup_functions import get_selected_setups  # noqa: E402


# =================================================================================================
class IndicatorChief:
    """
    Hello
    """
    def __init__(self):
        self.indicator_df = pd.DataFrame()
        self.indicators_set = set()
    # ____________________________________________________________________________ . . .


    def declare_indicators(self, path_to_setups_module: str, configs: Dict):
        """
        This method declares the required indicators.
        """
        _, self.required_indicators = get_selected_setups(path_to_setups_module, configs)

        for value in self.required_indicators.values():
            for item in value:
                if item not in self.indicators_set:
                    self.indicators_set.add(item)
                    logging.info(f'Indicator {item} has been added to indicators_set.')
    # ____________________________________________________________________________ . . .


    async def cook_indicators(self, kline_df: pd.DataFrame):
        """
        This method asynchronously executes indicator functions and returns the indicator DataFrame
        """
        tasks = []

        for item in self.indicators_set:
            for key in tasks_dict.keys():
                if isinstance(item, key):
                    tasks.append(tasks_dict[key](item, kline_df))

        try:
            results = await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logging.error("A task was cancelled during cook_indicators.")
            raise

        indicators_df = pd.DataFrame(index=kline_df.index)
        for result in results:
            print('result received in \'cook_indicators()\' method:\n', result)
            if not result.empty:
                indicators_df = indicators_df.merge(
                    result, left_index=True, right_index=True, how='left'
                )

        return indicators_df
# =================================================================================================



# supervisor = IndicatorChief(load(r'Application/configs/signal_config.json'))

# supervisor.attach()



# =================================================================================================
class IndicatorSupervisor:
    """
    Continuously monitors the kline_df for updates and recalculates indicators.

    Parameters:
    kline_df (pd.DataFrame): DataFrame containing OHLC data
    interval (float): Time interval in seconds to wait between checks for updates
    """
    def __init__(self, kline_df: pd.DataFrame, interval: float = 1.0):
        self.kline_df = kline_df.copy()
        self.interval = interval
        self.indicator_functions: List[Tuple[Callable, Tuple[Any, ...], Dict[str, Any]]] = []
        self.indicator_df = pd.DataFrame(index=self.kline_df.index)
    # ____________________________________________________________________________ . . .


    def involve(self, indicator_function: Callable, *args: Any, **kwargs: Any):
        """
        Register an indicator function along with its arguments to be applied to the Kline 
        DataFrame.

        Parameters:
        indicator_function (Callable): The indicator function to be applied
        *args: Positional arguments for the indicator function
        **kwargs: Keyword arguments for the indicator function
        """
        self.indicator_functions.append((indicator_function, args, kwargs))
    # ____________________________________________________________________________ . . .


    async def _update(self):
        """
        Apply all registered indicator functions to the Kline DataFrame and update the Indicator
        DataFrame.
        """
        for func, args, kwargs in self.indicator_functions:
            result = func(self.kline_df, *args, **kwargs)
            if isinstance(result, pd.Series):
                self.indicator_df[func.__name__] = result
            elif isinstance(result, pd.DataFrame):
                for column in result.columns:
                    self.indicator_df[column] = result[column]
            elif isinstance(result, tuple) and all(isinstance(x, pd.Series) for x in result):
                for i, series in enumerate(result):
                    self.indicator_df[f"{func.__name__}_{i+1}"] = series
    # ____________________________________________________________________________ . . .


    def _monitor(self, last_index, last_volume) -> Tuple[bool, Any, float]:
        """
        Monitor the Kline DataFrame for updates.
        
        Args:
            last_index: The last recorded index in the DataFrame.
            last_volume: The last recorded volume in the DataFrame.
        
        Returns:
            tuple: A tuple containing a boolean indicating if an update is needed,
                   the current index, and the current volume.
        """
        current_index = self.kline_df.index[-1]
        current_volume = self.kline_df.iloc[-1].get('volume', 0)
        
        has_news = (current_volume != last_volume) or (current_index != last_index)
        
        return has_news, current_index, current_volume
    # ____________________________________________________________________________ . . .


    async def perform(self):
        """
        Continuously monitor the Kline DataFrame for updates and apply registered indicator 
        functions.
        """
        if self.kline_df.empty:
            return

        last_index = self.kline_df.index[-1]
        last_volume = self.kline_df.iloc[-1].get('volume', 0)

        while True:
            has_news, current_index, current_volume = self._monitor(last_index, last_volume)
            
            if has_news:
                await self._update()
                last_index = current_index
                last_volume = current_volume
            
            await asyncio.sleep(self.interval)
    # ____________________________________________________________________________ . . .


    def get(self) -> pd.DataFrame:
        """
        Return the updated Indicator DataFrame.

        Returns:
        pd.DataFrame: DataFrame containing the calculated indicator values.
        """
        return self.indicator_df
# =================================================================================================
