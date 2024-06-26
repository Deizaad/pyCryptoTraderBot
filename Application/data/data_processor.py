import logging
import pandas as pd

from Application.api.nobitex_api import Market
from Application.configs.config import MarketData as md
from Application.utils.botlogger import initialize_logger    # Developement-temporary
from Application.data.data_tools import parse_kline_to_df


initialize_logger()    # Developement-temporary



# =================================================================================================
class DataProcessor:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DataProcessor ,cls).__new__(cls)
            cls._instance._initialize_dataframes()
        
        return cls._instance
    # ____________________________________________________________________________ . . .


    def _initialize_dataframes(self):
        self.kline_df     = pd.DataFrame()
        self.indicator_df = pd.DataFrame()
        self.signal_df    = pd.DataFrame()
    # ____________________________________________________________________________ . . .


    def initiate(self):
        """
        This method initiates other data processing methods or functions.
        """
        raise NotImplementedError('The initiate() method from DataProcessor class has no code!')
    # ____________________________________________________________________________ . . .


    def _initiate_kline(self, market: Market):
        """
        This method initiates the kline DataFrame by populating the 
        """
        self.kline_df = market.initiate_kline()
        
        while True:
            next(market.populate_kline(self.kline_df))

        logging.error('The _initiate_kline() method from DataProcessor class has no code!')
        raise NotImplementedError('The _initiate_kline() method from DataProcessor class has no code!')    
# =================================================================================================

data = DataProcessor()
data._initiate_kline()