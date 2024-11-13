import sys
import httpx
import asyncio
import pandas as pd
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User                                                      # noqa: E402
from Application.utils.logs import get_logger                                               # noqa: E402
from Application.data.exchange import Nobitex                                               # noqa: E402
from Application.api import nobitex_api as NB_API                                           # noqa: E402
from Application.utils.event_channels import Event                                          # noqa: E402
import Application.configs.admin_config as Aconfig                                          # noqa: E402
from Application.api.api_service import APIService                                          # noqa: E402
# from Application.data.validator import is_consistent                                      # noqa: E402
from Application.data.data_tools import has_signal,\
                                        df_has_news,\
                                        update_dataframe,\
                                        parse_kline_to_df                                   # noqa: E402
from Application.trading import strategy_fields as strategy                                 # noqa: E402
from Application.utils.simplified_event_handler import EventHandler                         # noqa: E402
from Application.trading.signals.signal_generator import generate_signals                   # noqa: E402
from Application.trading.stop_loss.stop_loss import declare_static_sl_price                 # noqa: E402
from Application.trading.analysis.indicator_supervisor import compute_indicators,\
                                                              compute_validation_indicators # noqa: E402
from Application.trading.position_sizing.position_sizer import compute_position_margin_size # noqa: E402


bot_logs = get_logger(logger_name='bot_logs')




# =================================================================================================
class DataProcessor:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DataProcessor, cls).__new__(cls)
            cls._instance._initialize_data()
        
        return cls._instance
    # ____________________________________________________________________________ . . .

    def __init__(self) -> None:
        self.jarchi = EventHandler()
        self.account = NB_API.Account(APIService())
        self.market = NB_API.Market(APIService())

        self.jarchi.register_event(Event.NEW_KLINE_DATA, ['kline_df'])
        self.jarchi.register_event(Event.NEW_TRADING_SIGNAL, ['setup_name',
                                                              'kline_df',
                                                              'indicator_df'])
        
        self.jarchi.register_event(Event.LATE_TRADING_SIGNAL, ['setup_name',
                                                              'kline_df',
                                                              'indicator_df'])

        self.jarchi.register_event(Event.OPEN_POSITIONS_EXIST, ['positions_df'])
        self.jarchi.register_event(Event.NEW_VALIDATION_INDICATOR_DATA, ['kline_df',
                                                                         'indicator_df',
                                                                         'validation_indicators_df'])

        self.jarchi.register_event(Event.NEW_INDICATORS_DATA, ['kline_df', 'indicator_df'])
    # ____________________________________________________________________________ . . .

    def _initialize_data(self) -> None:
        self.kline_df                 : pd.DataFrame        = pd.DataFrame()
        self.signal_df                : pd.DataFrame        = pd.DataFrame()
        self.market_price             : float               = 0.0
        self.indicator_df             : pd.DataFrame        = pd.DataFrame()
        self.positions_df             : pd.DataFrame        = pd.DataFrame()
        self.next_trade_df            : pd.DataFrame        = pd.DataFrame(columns=['signal_time',
                                                                                    'entry_signal',
                                                                                    'entry',
                                                                                    'init_sl',
                                                                                    'size'])
        self.portfolio_balance        : tuple[float, float] = (0, 0)
        self.validation_indicators_df : pd.DataFrame        = pd.DataFrame()
        self.order_book: tuple[pd.DataFrame, pd.DataFrame, float] = (pd.DataFrame(),
                                                                     pd.DataFrame(),
                                                                     0.0)
        
        bot_logs.info('"DataProcessor" has initialized data values.')
    # ____________________________________________________________________________ . . .

    async def initiate(self):
        """
        This method initiates other data processing methods or functions.
        """
        try:
            self.market = NB_API.Market(APIService())
            kline_task = self._initiate_kline(
                market           = self.market,
                symbol           = strategy.TRADING_PAIR['symbol'],
                resolution       = strategy.TRADING_TIMEFRAME,
                required_candles = strategy.COMPUTION_SIZE,
                timeout          = Aconfig.Market.OHLC.TIMEOUT,
                tries_interval   = Nobitex.Endpoint.OHLC_MI,
                tries            = Aconfig.Market.OHLC.TRIES
            )

            # self.analysis = IndicatorChief()
            # indicator_task = self._awake_indicators(self.analysis)

            # self.signal = SignalChief()
            # signal_task = self._awake_signals(self.signal)

            self.trade = NB_API.Trade(APIService())
            # positions_task = self._initiate_positions()

            await asyncio.gather( kline_task)#, indicator_task, signal_task)# include positions_task to first

        except Exception as err:
            bot_logs.error(f'Error while initiating data: {err}')
    # ____________________________________________________________________________ . . .

    async def live(self):
        try:
            kline_coroutine     = self._live_kline()
            # positions_coroutine = self._live_positions()

            await asyncio.gather( kline_coroutine)# include positions_coroutine to first
        except Exception as err:
            bot_logs.error(f'Error in live data processing: {err}')
    # ____________________________________________________________________________ . . .





    async def start_fetching_kline(self):
        """
        Starts a mechanism that constantly fetches kline data.
        """
        await self._initiate_kline(
            market=self.market,
            symbol=strategy.TRADING_PAIR['symbol'],
            resolution=strategy.TRADING_TIMEFRAME,
            required_candles=strategy.COMPUTION_SIZE,
            timeout=Aconfig.Market.OHLC.TIMEOUT,
            tries_interval=Nobitex.Endpoint.OHLC_MI,
            tries=Aconfig.Market.OHLC.TRIES
        )

        await self._live_kline()
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
        bot_logs.info('Initiating kline_df in DataProcessor._initiate_kline.')
        
        # Requesting first initial_fetch to current time
        bot_logs.info('Sending First initial_fetch request for Kline data ...')
        data = await market.initiate_kline(symbol,
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
        # ________________________________________________________________________ . . .


        # Requesting subsequent initial_fetches to populate the kline dataframe to desired size
        bot_logs.info('Sending subsequent initial_fetch requests for Kline data ...')
        try:
            is_first_subsequent_fetch = True

            async for new_data in market.populate_kline(self.kline_df,
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
                bot_logs.info(
                    f'Sending the \"{event_channel}\" event signal from \"{func_name}\" ...'
                )

                await self.jarchi.emit(Event.NEW_KLINE_DATA,
                                 kline_df=self.kline_df)

        except Exception as err:
            bot_logs.error(f'Error in requesting subsequent initial_fetches: {err}')
    # ____________________________________________________________________________ . . .

    async def _live_kline(self):
        bot_logs.info('Sending live_fetch requests for Kline data ...')
        try:
            async for data in self.market.update_kline(
                current_data   = self.kline_df,
                symbol         = strategy.TRADING_PAIR['symbol'],
                resolution     = strategy.TRADING_TIMEFRAME,
                timeout        = Aconfig.Market.OHLC.TIMEOUT,
                tries_interval = Nobitex.Endpoint.OHLC_MI,
                tries          = Aconfig.Market.OHLC.TRIES,
                max_interval   = Nobitex.Endpoint.OHLC_MI,
                max_rate       = Nobitex.Endpoint.OHLC_RL,
                rate_period    = Nobitex.Endpoint.OHLC_RP
            ):
                data = parse_kline_to_df(data)
                if not data.equals(self.kline_df) and df_has_news(self.kline_df, data):
                    self.kline_df = update_dataframe(origin_df=self.kline_df,
                                                     late_df=data,
                                                     size=strategy.COMPUTION_SIZE)
                    
                    # if is_consistent(self.kline_df, config.MarketData.OHLC.RESOLUTION):
                    func_name=self._live_kline.__qualname__
                    event_channel=Event.NEW_KLINE_DATA
                    bot_logs.info(f'Sending "{event_channel}" event from "{func_name}" ...')
                    await self.jarchi.emit(Event.NEW_KLINE_DATA,
                                     kline_df=self.kline_df)

                    print(self.kline_df)
        except Exception as err:
            bot_logs.error(f'Error during live kline fetching: {err}')
    # ____________________________________________________________________________ . . .

    def get_kline_df(self):
        """
        Returns kline dataframe.
        """
        return self.kline_df
    # ____________________________________________________________________________ . . .





    async def start_fetching_market_price(self):
        """
        Starts a mechanism that constantly fetches market price.
        """
        await self._live_fetch_market_price()
    # ____________________________________________________________________________ . . .

    async def _live_fetch_market_price(self):
        async for data in self.market.live_fetch_market_price(
            src_currency = strategy.TRADING_PAIR['src_currency'],
            dst_currency = strategy.TRADING_PAIR['dst_currency']
        ):
            if data != self.market_price:
                self.market_price = data
    # ____________________________________________________________________________ . . .

    def get_market_price(self) -> float:
        """
        Returns the market price.
        """
        return self.market_price
    # ____________________________________________________________________________ . . .





    async def start_fetching_portfolio_balance(self):
        """
        Starts a mechanism that constantly fetches user's portfolio balance.
        """
        await self._live_portfolio_balance()
    # ____________________________________________________________________________ . . .

    async def _live_portfolio_balance(self):
        async for data in self.account.live_fetch_portfolio_balance():
            if data != self.portfolio_balance:
                self.portfolio_balance = data
    # ____________________________________________________________________________ . . .

    def get_portfolio_balance(self) -> tuple[float, float]:
        """
        Returns the wallets DataFrame.
        """
        return self.portfolio_balance
    # ____________________________________________________________________________ . . .




    async def start_fetching_order_book(self):
        """
        Starts a mechanism that constantly fetches the order book data.
        """
        await self._live_order_book()
    # ____________________________________________________________________________ . . .

    async def _live_order_book(self):
        async for data in self.market.live_fetch_order_book(
            http_agent=httpx.AsyncClient(),
            src_currency=strategy.TRADING_PAIR['src_currency'],
            dst_currency=strategy.TRADING_PAIR['dst_currency']
        ):
            if data != self.order_book:
                self.order_book = data
    # ____________________________________________________________________________ . . .

    def get_order_book(self) -> tuple[pd.DataFrame, pd.DataFrame, float]:
        """
        Returns the order book in shape of a tuple (asks_df, bids_df, mid_price).
        """
        return self.order_book
    # ____________________________________________________________________________ . . .





    async def computing_indicators(self):
        """
        Calls indicator computer function from IndicatorChief and emits on "NEW_INDICATORS_DATA" event channel.

        Parameters:
            trading_system (list): 
        """
        try:
            self.indicator_df = await compute_indicators(trading_system = strategy.ENTRY_SYSTEM,
                                                         kline_df       = self.kline_df)
            
            bot_logs.info(f'Broadcasting "{Event.NEW_INDICATORS_DATA}" event from '\
                         '"DataProcessor.computing_indicators()" method.')
            
            print(self.indicator_df)
            await self.jarchi.emit(Event.NEW_INDICATORS_DATA,
                                   kline_df     = self.kline_df,
                                   indicator_df = self.indicator_df)

        except Exception as err:
            bot_logs.error(f'Inside "DataProcessor.computing_indicators()" method: {err}')
    # ____________________________________________________________________________ . . .

    def get_indicators_df(self):
        """
        Returns indicators DataFrame.
        """
        return self.indicator_df
    # ____________________________________________________________________________ . . .





    async def computing_validation_indicators(self):
        """
        Calls computer function from IndicatorChief for validation indicators and emits on 
        corresponding event channel.

        Parameters:
            validation_setups (list): List of market validation setups is goinf to be used to extract indicator functions from.
        """
        try:
            self.validation_indicators_df = await compute_validation_indicators(
                validation_system = strategy.MARKET_VALIDATION_SYSTEM,
                kline_df          = self.kline_df
            )

            bot_logs.info(f'Broadcasting "{Event.NEW_VALIDATION_INDICATOR_DATA}" event from '\
                         '"DataProcessor.computing_validation_indicators()" method.')

            await self.jarchi.emit(Event.NEW_VALIDATION_INDICATOR_DATA,
                                   kline_df        = self.kline_df,
                                   indicator_df    = self.indicator_df,
                                   validation_indicators_df = self.validation_indicators_df)

        except Exception as err:
            bot_logs.error('Inside "DataProcessor.computing_validation_indicators()" method: ', err)
    # ____________________________________________________________________________ . . .

    def get_validation_indicators_df(self):
        """
        Returns validation indicators dataframe.
        """
        return self.validation_indicators_df
    # ____________________________________________________________________________ . . .





    async def generating_signals(self):
        """
        Calls trading signal generator function from SignalChief and emits on "NEW_TRADING_SIGNAL"
        event channel.

        Parameters:
        """
        try:
            self.signal_df = await generate_signals(trading_system = strategy.ENTRY_SYSTEM,
                                                    kline_df       = self.kline_df,
                                                    indicators_df  = self.indicator_df)
            
            for column in self.signal_df:
                if has_signal(self.signal_df, column) == 'new_signal':
                    bot_logs.info(f'Broadcasting "{Event.NEW_TRADING_SIGNAL}" event from'\
                                '"DataProcessor.generating_signals()" method.')
                    
                    await self.jarchi.emit(Event.NEW_TRADING_SIGNAL,
                                           kline_df      = self.kline_df,
                                           indicator_df  = self.indicator_df,
                                           setup_name    = column)

                elif has_signal(self.signal_df, column) == 'late_signal':
                    bot_logs.info(f'Broadcasting "{Event.LATE_TRADING_SIGNAL}" event from'\
                                '"DataProcessor.generating_signals()" method.')
                    
                    await self.jarchi.emit(Event.LATE_TRADING_SIGNAL,
                                           kline_df      = self.kline_df,
                                           indicator_df  = self.indicator_df,
                                           setup_name    = column)
                

        except Exception as err:
            bot_logs.error('Inside "DataProcessor.generating_signals()" method of DataProcessor: ',
                          err)
    # ____________________________________________________________________________ . . .





    async def set_next_trade_position_size(self):
        """
        Calls the position size computer function from 'position_sizer.py'.
        """
        self.next_trade_df.at[0, 'size'] = await compute_position_margin_size(
            portfolio_balance = self.portfolio_balance,
            entry_price       = self.next_trade_df.at[0, 'entry'],
            stop_loss_price   = self.next_trade_df.at[0, 'init_sl'],
            order_book        = self.order_book
        )
    # ____________________________________________________________________________ . . .
    
    async def set_next_trade_entry_price(self):
        """
        
        """
        pass
    # ____________________________________________________________________________ . . .

    async def set_next_trade_init_sl(self, trade_side: str):
        """
        Declares next trades's initial stop loss (by executing the chosen function) and stores it
        in the "next_trade_df".

        Parameters:
            trade_side (str): _Direction of trade is eather "buy" | "sell"._
        """
        init_sl_price = declare_static_sl_price(trade_side    = trade_side,
                                                indicators_df = self.indicator_df)

        self.next_trade_df.at[0, 'init_sl'] = init_sl_price
    # ____________________________________________________________________________ . . .

    def get_next_trade(self):
        """
        Returns the next_trade_df
        """
        return self.next_trade_df
    # ____________________________________________________________________________ . . .





    async def _initiate_positions(self):
        """
        Initiates positions DataFrame by populating it with all open positions.
        """
        bot_logs.info('Initiating "positions_df" ...')

        self.positions_df = await anext(self.trade.fetch_open_positions(
            client       = httpx.AsyncClient(),
            token        = User.TOKEN,    # type: ignore
            req_interval = Nobitex.Endpoint.POSITIONS_MI,
            max_rate     = Nobitex.Endpoint.POSITIONS_RL,
            rate_period  = Nobitex.Endpoint.POSITIONS_RP
        ))

        # broadcast OPEN_POSITIONS_EXIST event in case there are any open positions
        if not self.positions_df.empty:
            bot_logs.info(f'Broadcasting "{Event.OPEN_POSITIONS_EXIST}" event from '\
                         '"DataProcessor._initiate_positions()" method.')
            
            await self.jarchi.emit(event=Event.OPEN_POSITIONS_EXIST, positions_df=self.positions_df)
    # ____________________________________________________________________________ . . .

    async def _live_positions(self):
        """
        Constantly updates positions dataframe with new data.
        """
        async for new_positions in self.trade.fetch_open_positions(
            client       = httpx.AsyncClient(),
            token        = User.TOKEN,    # type: ignore
            req_interval = Nobitex.Endpoint.POSITIONS_MI,
            max_rate     = Nobitex.Endpoint.POSITIONS_RL,
            rate_period  = Nobitex.Endpoint.POSITIONS_RP
        ):
            if not new_positions.equals(self.positions_df) and df_has_news(
                self.positions_df, new_positions
            ):
                self.positions_df = new_positions

                bot_logs.info(f'Broadcasting "{Event.OPEN_POSITIONS_EXIST}" event from'\
                             '"DataProcessor._live_positions()" method.')

                await self.jarchi.emit(Event.OPEN_POSITIONS_EXIST, positions_df=self.positions_df)
# =================================================================================================



async def main():
    data = DataProcessor()
    # await data.initiate()
    # await data.live()
    await data.start_fetching_kline()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError as e:
        bot_logs.error(f"RuntimeError in main: {e}")