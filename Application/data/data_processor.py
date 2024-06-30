import os
import sys
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

import asyncio
import logging
import pandas as pd
from httpx import AsyncClient

from Application.configs import config
from Application.data.exchange import Nobitex
from Application.api import nobitex_api as NB_API
import Application.configs.admin_config as Aconfig
from Application.api.api_service import APIService
from Application.utils.botlogger import initialize_logger    # Developement-temporary
from Application.data.data_tools import parse_kline_to_df, join_raw_kline


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
        
        logging.debug('DataProcessor initialized the data with empty DataFrames!')
    # ____________________________________________________________________________ . . .


    async def initiate(self):
        """
        This method initiates other data processing methods or functions.
        """
        try:
            async with asyncio.TaskGroup() as tg:
                self.market = NB_API.Market(APIService(), AsyncClient())
                kline_task = tg.create_task(self._initiate_kline(self.market,
                                                                 config.MarketData.OHLC.SYMBOL,
                                                                 config.MarketData.OHLC.RESOLUTION,
                                                                 config.MarketData.OHLC.SIZE,
                                                                 Aconfig.OHLC.TIMEOUT,
                                                                 Nobitex.Endpoint.OHLC_MI,
                                                                 Aconfig.OHLC.TRIES))

                # indicator_task = tg.create_task(self._initiate_analysis())

                # signal_task = tg.create_task(self._initiate_signals())

                await asyncio.gather(kline_task)

        except ExceptionGroup as errors:
            for err in errors.exceptions:
                print(f'error while initiating data: {err}')
    # ____________________________________________________________________________ . . .


    async def _initiate_kline(self,
                              market: NB_API.Market,
                              symbol: str,
                              resolution: str,
                              required_candles: int,
                              timeout: float,
                              tries_interval: float,
                              tries: int):
        """
        This method initiates the kline DataFrame by populating it to the desired size.
        """
        # Requesting first initial_fetch to current time
        data = await market.initiate_kline(AsyncClient(),
                                           symbol,
                                           resolution,
                                           required_candles,
                                           timeout,
                                           tries_interval,
                                           tries)
        
        self.kline_df = parse_kline_to_df(data)
        # ________________________________________________________________________ . . .


        # Requesting subsequent initial_fetches to populate the kline dataframe to desired size
        try:
            async for new_data in market.populate_kline(AsyncClient(),
                                                        data,
                                                        symbol,
                                                        resolution,
                                                        required_candles,
                                                        timeout,
                                                        tries_interval,
                                                        tries,
                                                        max_interval = Nobitex.Endpoint.OHLC_MI,
                                                        max_rate     = Nobitex.Endpoint.OHLC_RL,
                                                        rate_period  = Nobitex.Endpoint.OHLC_RP):

                data = join_raw_kline(data, new_data, 'PREPEND')

            self.kline_df = parse_kline_to_df(data)
        except Exception as err:
            print('error in requesting subsequent initial_fetches: ', err)
    # ____________________________________________________________________________ . . .


    async def live(self):
        async with asyncio.TaskGroup() as tg:
            kline_task = tg.create_task(self._live_kline())

            # indicator_task = tg.create_task(self._live_indicator())

            # signal_task = tg.create_task(self._live_signal())
            
            await asyncio.gather(kline_task)
    # ____________________________________________________________________________ . . .


    async def _live_kline(self):
        async for data in self.market.update_kline(
            client         = AsyncClient(),
            current_data   = self.kline_df,
            symbol         = config.MarketData.OHLC.SYMBOL,
            resolution     = config.MarketData.OHLC.RESOLUTION,
            timeout        = Aconfig.OHLC.TIMEOUT,
            tries_interval = Nobitex.Endpoint.OHLC_MI,
            tries          = Aconfig.OHLC.TRIES,
            max_interval   = Nobitex.Endpoint.OHLC_MI,
            max_rate       = Nobitex.Endpoint.OHLC_RL,
            rate_period    = Nobitex.Endpoint.OHLC_RP
        ):
            new_data = parse_kline_to_df(data)
            self.kline_df = pd.concat([self.kline_df, new_data])
            print(self.kline_df)
    # ____________________________________________________________________________ . . .


    def get_kline(self):
        """
        This method return the kline dataframe.
        """
        return self.kline_df
# =================================================================================================



data = DataProcessor()
asyncio.run(data.initiate())
asyncio.run(data.live())