import time
import asyncio
import logging
import threading
import pandas as pd

from NobitexTrader.config import MarketData as md
from NobitexTrader.nb_api.market import *
from NobitexTrader.setups.supertrend import signal
from NobitexTrader.study.supertrend import pandas_supertrend


# =================================================================================================
class DataManager:
    """
    DataManager is a Singleton design class that manages data frames for kline, indicators, and 
    signals.
    """
    # Handle class instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(DataManager, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialize_dataframes()

        return cls._instance
    # ____________________________________________________________________________ . . .


    def _initialize_dataframes(self):
        self.kline_df = pd.DataFrame()
        self.indicator_df = pd.DataFrame()
        self.signal_df = pd.DataFrame()
    # ____________________________________________________________________________ . . .


    def initiate(self):
        asyncio.run(self._initiate_kline_df())
    # ____________________________________________________________________________ . . .


    # Handle kline dataframe
    async def _initiate_kline_df(self):
        kline_df = pd.DataFrame()
        _ohlc = OHLCData(kline_df, md.OHLC.SYMBOL, md.OHLC.RESOLUTION)
        _current_time = int(time.time())
        self.kline_df, _ = await _ohlc.get(_current_time)

    async def _populate_kline_df(self):
        ohlc = OHLCData(self.kline_df, md.OHLC.SYMBOL, md.OHLC.RESOLUTION)
        self.kline_df, _, _, _, _ = await ohlc.live()

    def get_kline_df(self):
        return self.kline_df
    # ____________________________________________________________________________ . . .


    # Handle indicator dataframe
    async def _populate_indicator_df(self):
        self.indicator_df = pandas_supertrend(self.kline_df)

    def get_indicator_df(self):
        return self.indicator_df
    # ____________________________________________________________________________ . . .


    # Handle signal dataframe
    async def _populate_signal_df(self):
        self.signal_df = signal(self.kline_df, self.indicator_df)

    def get_signal_df(self):
        return self.signal_df
    # ____________________________________________________________________________ . . .


    def live_update(self):
        def update_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._live_update())
        threading.Thread(target=update_loop, daemon=True).start()


    async def _live_update(self):
        while True:
            try:
                await asyncio.gather(self._populate_kline_df(),
                                     self._populate_indicator_df(),
                                     self._populate_signal_df())
            except Exception as e:
                logging.error(f'An error occurred during live update: {e}')
                await asyncio.sleep(4)
        
    # ____________________________________________________________________________ . . .
        

    def show(self):
        while True:
            print(self.kline_df)
            print(self.indicator_df)
            # with pd.option_context('display.max_rows', None):
            #     print(self.signal_df)
            print(self.signal_df)
            time.sleep(4)
# =================================================================================================


# Initiate Dataframes
data_manager = DataManager()
data_manager.initiate()
data_manager.live_update()


if __name__ == '__main__':

    data_manager.show()
    time.sleep(4)