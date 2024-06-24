import asyncio
import pandas as pd
from pydispatch import dispatcher    # type: ignore
from typing import Callable, Any, List, Tuple, Dict

from NobitexTrader.utils.load_json import load
from NobitexTrader.utils.event_channels import Event
import NobitexTrader.trading.analysis.indicator_functions as indicators
from NobitexTrader.trading.analysis.indicators import Supertrend, MACD
from NobitexTrader.trading.signals.setup_functions import get_selected_setups


# =================================================================================================
class IndicatorChief:
    """
    Hello
    """
    def __init__(self):
        self.config = load(r'NobitexTrader\configs\signal_config.json')
        self.indicator_df = pd.DataFrame()

        self.attached_indicators = set()
        _, self.required_indicators = get_selected_setups(
            'NobitexTrader.trading.signals.setup_functions',
            self.config
        )
    # ____________________________________________________________________________ . . .


    def attach(self):
        for value in self.required_indicators.values():
            for item in value:
                if isinstance(item, Supertrend) and item not in self.attached_indicators:
                    """
                    Statement for attaching Supertrend indicator to dispatchers.
                    """
                    window = item.params[0]
                    factor = item.params[1]
                    properties = {'window': window, 'factor': factor}
                    
                    dispatcher.connect(
                        self._create_handler(indicators.pandas_supertrend, properties),
                        Event.SUCCESS_FETCH,
                        dispatcher.Any
                    )
                    
                    self.attached_indicators.add(item)
                # ________________________________________________________________ . . .

                if isinstance(item, MACD) and item not in self.attached_indicators:
                    """
                    Placeholder statement for 'MACD' indicator.
                    """
                    self.attached_indicators.add(item)
    # ____________________________________________________________________________ . . .


    def _create_handler(self, func, properties):
        def _handler(sender, **kwargs):
            kline = kwargs.get('kline')
            result_df = func(kline, **properties)
            print(result_df)
            # self.indicator_df = self.indicator_df.concat(result_df, ignore_index=True)
        return _handler
    # ____________________________________________________________________________ . . .
    

    def get(self) -> pd.DataFrame:
        return self.indicator_df
# =================================================================================================


supervisor = IndicatorChief()

supervisor.attach()

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
