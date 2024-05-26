import time
import threading
import pandas as pd

from NobitexTrader.config import OHLC
from NobitexTrader.nb_api.market import *
from NobitexTrader.setups.supertrend import signal
from  NobitexTrader.analysis.supertrend import pandas_supertrend


# =================================================================================================
class DataManager:
    """
    Singleton Design Pattern
    """
    # Handle class instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(DataManager, cls).__new__(cls, *args, **kwargs)
                cls._instance.kline_df = pd.DataFrame()
                cls._instance.indicator_df = pd.DataFrame()
                cls._instance.signal_df = pd.DataFrame()
        return cls._instance
    # ____________________________________________________________________________ . . .


    # Handle kline dataframe
    def initiate_kline_df(self):
        kline_df = pd.DataFrame()
        OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)
        self.kline_df = OHLC_Engine.get(int(time.time()))[0]

    def populate_kline_df(self):
        OHLC_Engine = OHLCData(self.kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)
        self.kline_df = OHLC_Engine.live()[0]

    def get_kline_df(self):
        return self.kline_df
    # ____________________________________________________________________________ . . .


    # Handle indicator dataframe
    def populate_indicator_df(self):
        self.indicator_df = pandas_supertrend(self.kline_df)

    def get_indicator_df(self):
        return self.indicator_df
    # ____________________________________________________________________________ . . .


    # Handle signal dataframe
    def populate_signal_df(self):
        self.signal_df = signal(self.kline_df, self.indicator_df)

    def get_signal_df(self):
        return self.signal_df
    # ____________________________________________________________________________ . . .


    def trigger_live_update(self):
        def update_loop():
            while True:
                self.populate_kline_df()
                self.populate_indicator_df()
                self.populate_signal_df()
                time.sleep(4)
        threading.Thread(target=update_loop, daemon=True).start()
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
data_manager.initiate_kline_df()
data_manager.trigger_live_update()


if __name__ == '__main__':

    data_manager.show()
    time.sleep(4)