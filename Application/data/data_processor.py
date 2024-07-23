import os
import sys
import httpx
import asyncio
import logging
import pandas as pd
from httpx import AsyncClient
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.configs import config    # noqa: E402
from Application.utils.load_json import load    # noqa: E402
from Application.data.exchange import Nobitex    # noqa: E402
from Application.api import nobitex_api as NB_API    # noqa: E402
from Application.utils.event_channels import Event    # noqa: E402
import Application.configs.admin_config as Aconfig    # noqa: E402
from Application.api.api_service import APIService    # noqa: E402
# from Application.data.validator import is_consistent    # noqa: E402
from Application.utils.botlogger import initialize_logger    # noqa: E402 # Developement-temporary
from Application.data.data_tools import df_has_news,\
                                        update_dataframe,\
                                        parse_kline_to_df,\
                                        parse_positions_to_df,\
                                        broadcast_open_positions_event    # noqa: E402
from Application.utils.simplified_event_handler import EventHandler    # noqa: E402
from Application.trading.signals.signal_supervisor import SignalChief    # noqa: E402
from Application.trading.analysis.indicator_supervisor import IndicatorChief    # noqa: E402


initialize_logger()    # Developement-temporary



# =================================================================================================
class DataProcessor:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DataProcessor, cls).__new__(cls)
            cls._instance._initialize_dataframes()
        
        return cls._instance
    # ____________________________________________________________________________ . . .


    def __init__(self) -> None:
        self.jarchi = EventHandler()
        self.jarchi.register_event(Event.NEW_KLINE_DATA, ['kline_df', 'indicator_df'])
        self.jarchi.register_event(Event.OPEN_POSITIONS_futures, ['futures_positions_df'])
        self.jarchi.register_event(Event.OPEN_POSITIONS_spot, ['spot_positions_df'])
    # ____________________________________________________________________________ . . .


    def _initialize_dataframes(self):
        self.kline_df     = pd.DataFrame()
        self.indicator_df = pd.DataFrame()
        self.signal_df    = pd.DataFrame()
        self.futures_positions_df = pd.DataFrame()
        self.spot_positions_df    = pd.DataFrame()
        
        logging.info('DataProcessor initialized data with empty DataFrames!')
    # ____________________________________________________________________________ . . .


    async def initiate(self):
        """
        This method initiates other data processing methods or functions.
        """
        try:
            self.market = NB_API.Market(APIService(), AsyncClient())
            kline_task = self._initiate_kline(self.market,
                                              config.MarketData.OHLC.SYMBOL,
                                              config.MarketData.OHLC.RESOLUTION,
                                              config.MarketData.OHLC.SIZE,
                                              Aconfig.OHLC.TIMEOUT,
                                              Nobitex.Endpoint.OHLC_MI,
                                              Aconfig.OHLC.TRIES)

            self.analysis = IndicatorChief()
            indicator_task = self._awake_indicators(self.analysis)

            self.signal = SignalChief()
            signal_task = self._awake_signals(self.signal)

            self.order = NB_API.Order(APIService())
            positions_task = self._initiate_positions()

            await asyncio.gather(kline_task, indicator_task, signal_task, positions_task)

        except Exception as err:
            logging.error(f'Error while initiating data: {err}')
    # ____________________________________________________________________________ . . .


    async def live(self):
        try:
            kline_task = self._live_kline()

            await asyncio.gather(kline_task)
        except Exception as err:
            logging.error(f'Error in live data processing: {err}')
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
        logging.info('Initiating kline_df in DataProcessor._initiate_kline.')
        
        # Requesting first initial_fetch to current time
        logging.info('Sending First initial_fetch request for Kline data ...')
        data = await market.initiate_kline(AsyncClient(),
                                           symbol,
                                           resolution,
                                           required_candles,
                                           timeout,
                                           tries_interval,
                                           tries)

        data = parse_kline_to_df(data)

        if not data.equals(self.kline_df):
            self.kline_df = update_dataframe(self.kline_df, data, required_candles)

            # if is_consistent(self.kline_df, config.MarketData.OHLC.RESOLUTION):
            func_name=self._initiate_kline.__qualname__
            event_channel=Event.NEW_KLINE_DATA
            logging.info(f'Sending the \"{event_channel}\" event signal from \"{func_name}\" ...')
            self.jarchi.emit(Event.NEW_KLINE_DATA,
                             kline_df=self.kline_df,
                             indicator_df=self.indicator_df)
        # ________________________________________________________________________ . . .


        # Requesting subsequent initial_fetches to populate the kline dataframe to desired size
        logging.info('Sending subsequent initial_fetch requests for Kline data ...')
        try:
            is_first_subsequent_fetch = True

            async for new_data in market.populate_kline(AsyncClient(),
                                                        self.kline_df,
                                                        symbol,
                                                        resolution,
                                                        required_candles,
                                                        timeout,
                                                        tries_interval,
                                                        tries,
                                                        max_interval = Nobitex.Endpoint.OHLC_MI,
                                                        max_rate     = Nobitex.Endpoint.OHLC_RL,
                                                        rate_period  = Nobitex.Endpoint.OHLC_RP):

                if is_first_subsequent_fetch:
                    data = parse_kline_to_df(new_data)
                    is_first_subsequent_fetch = False
                else:
                    data = pd.concat([parse_kline_to_df(new_data), data])

            if not data.equals(self.kline_df):
                self.kline_df = pd.concat([data, self.kline_df])

                # if is_consistent(self.kline_df, config.MarketData.OHLC.RESOLUTION):
                func_name=self._initiate_kline.__qualname__
                event_channel=Event.NEW_KLINE_DATA
                logging.info(
                    f'Sending the \"{event_channel}\" event signal from \"{func_name}\" ...'
                )

                self.jarchi.emit(Event.NEW_KLINE_DATA,
                                 kline_df=self.kline_df,
                                 indicator_df=self.indicator_df)

        except Exception as err:
            logging.error(f'Error in requesting subsequent initial_fetches: {err}')
    # ____________________________________________________________________________ . . .


    async def _live_kline(self):
        logging.info('Sending live_fetch requests for Kline data ...')
        try:
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
                data = parse_kline_to_df(data)
                if not data.equals(self.kline_df) and df_has_news(self.kline_df, data):
                    self.kline_df = update_dataframe(self.kline_df,
                                                     data,
                                                     config.MarketData.OHLC.SIZE)
                    
                    # if is_consistent(self.kline_df, config.MarketData.OHLC.RESOLUTION):
                    func_name=self._live_kline.__qualname__
                    event_channel=Event.NEW_KLINE_DATA
                    logging.info(f'Sending "{event_channel}" event from "{func_name}" ...')
                    self.jarchi.emit(Event.NEW_KLINE_DATA,
                                     kline_df=self.kline_df,
                                     indicator_df=self.indicator_df)
                    
        except Exception as err:
            logging.error(f'Error during live kline fetching: {err}')
    # ____________________________________________________________________________ . . .


    async def _awake_indicators(self, indicator_chief: IndicatorChief):
        indicator_chief.declare_indicators('Application.trading.signals.setup_functions',
                                           load(r'Application/configs/signal_config.json'))
        
        self.jarchi.attach(self._compute_indicators,
                           Event.NEW_KLINE_DATA)
    # ____________________________________________________________________________ . . .


    async def _compute_indicators(self, kline_df):
        try:
            self.indicator_df = await self.analysis.cook_indicators(kline_df)
        except Exception as err:
            logging.error(f'Error while computing indicators: {err}')
    # ____________________________________________________________________________ . . .


    async def _awake_signals(self, signal_chief: SignalChief):
        signal_chief.declare_setups('Application.trading.signals.setup_functions',
                                    load(r'Application/configs/signal_config.json'))
        
        self.jarchi.attach(self._generate_signals,
                           Event.NEW_KLINE_DATA)
    # ____________________________________________________________________________ . . .


    async def _generate_signals(self, kline_df: pd.DataFrame, indicator_df: pd.DataFrame):
        try:
            if (not kline_df.empty) and (not indicator_df.empty):
                self.signal_df = await self.signal.generate_signals(kline_df, indicator_df)

        except Exception as err:
            logging.error(f'Inside "_generate_signal()" method of DataProcessor: {err}')
    # ____________________________________________________________________________ . . .


    async def _initiate_positions(self):
        """
        Initiates positions DataFrame by populating it with all open positions.
        """
        logging.info('Initiating "positions_df" ...')

        results = await self.order.init_fetch_positions(client = httpx.AsyncClient(),
                                                        token  = Nobitex.USER.API_KEY)
        
        # check if it's needed to fetch for populating the positions_df
        for result in results:
            if 'positions' in result:
                futures_has_next = result['hasNext']
            if 'orders' in result:
                spot_has_next = result['hasNext']

        if spot_has_next or futures_has_next:
            # Code block olace holder for invoking the populate_positions()
            raise NotImplementedError('There is no code implemented for when open positions has '\
                                      'next pages!')

        self.futures_positions_df, self.spot_positions_df = parse_positions_to_df(results)

        # broadcast OPEN_POSITION event in case there are any open positions
        broadcast_open_positions_event(futures_poss_df=self.futures_positions_df,
                                       spot_poss_df=self.spot_positions_df)
# =================================================================================================



async def main():
    data = DataProcessor()
    await data.initiate()
    await data.live()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError as e:
        logging.error(f"RuntimeError in main: {e}")