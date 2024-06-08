import os
import time
import asyncio
import logging
import threading
import pandas as pd

from NobitexTrader.configs.config import MarketData as md
from NobitexTrader.api.nb_api.market import OHLCData
from NobitexTrader.trading.signals.setups.supertrend import signal
from NobitexTrader.trading.analysis.supertrend import pandas_supertrend
# from NobitexTrader.trading.signals.signal_supervisor import SignalSupervisor


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')



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
        try:
            self.kline_df = pd.DataFrame()
            self.indicator_df = pd.DataFrame()
            self.signal_df = pd.DataFrame()
        except Exception as err:
            logging.error(f"Error initializing dataframes: {err}")
    # ____________________________________________________________________________ . . .


    def initiate(self):
        try:
            asyncio.run(self._initiate_kline_df())
            # try:
            #     self.signal_supervisor = SignalSupervisor(self.kline_df, self.indicator_df)
            # except Exception as err:
            #     logging.error(f"Error initiating signal dataframe: {err}")
            # asyncio.run(self._initiate_signal_df())
        except Exception as err:
            logging.error(f"Error initiating data manager: {err}")
    # ____________________________________________________________________________ . . .


    # Handle kline dataframe
    async def _initiate_kline_df(self):
        try:
            kline_df = pd.DataFrame()
            _ohlc = OHLCData(kline_df, md.OHLC.SYMBOL, md.OHLC.RESOLUTION)
            _current_time = int(time.time())
            self.kline_df, _ = await _ohlc.get(_current_time)
        except Exception as err:
            logging.error(f"Error initiating kline dataframe: {err}")

    async def _populate_kline_df(self):
        try:
            ohlc = OHLCData(self.kline_df, md.OHLC.SYMBOL, md.OHLC.RESOLUTION)
            self.kline_df, _, _, _, _ = await ohlc.live()
        except Exception as err:
            logging.error(f"Error populating kline dataframe: {err}")

    def get_kline_df(self):
        return self.kline_df
    # ____________________________________________________________________________ . . .


    # Handle indicator dataframe
    async def _populate_indicator_df(self):
        try:
            self.indicator_df = pandas_supertrend(self.kline_df)
        except Exception as err:
            logging.error(f"Error populating indicator dataframe: {err}")

    def get_indicator_df(self):
        return self.indicator_df
    # ____________________________________________________________________________ . . .


    # Handle signal dataframe
    # async def _initiate_signal_df(self):
    #     try:
    #         self.signal_supervisor = SignalSupervisor(self.kline_df, self.indicator_df)
    #     except Exception as err:
    #         logging.error(f"Error initiating signal dataframe: {err}")

    async def _populate_signal_df(self):
        try:
            self.signal_df = signal(self.kline_df, self.indicator_df)
            # await self.signal_supervisor.perform()
            # self.signal_df = self.signal_supervisor.deliver()
        except Exception as err:
            logging.error(f"Error populating signal dataframe: {err}")

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
            except Exception as err:
                logging.error(f'An error occurred during live update: {err}')
                await asyncio.sleep(4)
        
    # ____________________________________________________________________________ . . .
        

    def show(self):
        while True:
            try:
                print('Kline dataframe:', '\n', self.kline_df.tail(15), '\n\n')
                print('Indicator dataframe:', '\n', self.indicator_df.tail(15), '\n\n')
                # with pd.option_context('display.max_rows', None):
                #     print(self.signal_df)
                print('Signal dataframe:', '\n', self.signal_df.tail(15), '\n\n')
                time.sleep(4)
            except Exception as err:
                logging.error(f"Error displaying dataframes: {err}")
                time.sleep(4)
# =================================================================================================



# Initiate Dataframes
data_manager = DataManager()
data_manager.initiate()
data_manager.live_update()


if __name__ == '__main__':
    try:
        data_manager.show()
    except Exception as err:
        logging.error(f"Error in main block: {err}")