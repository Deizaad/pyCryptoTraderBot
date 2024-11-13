import sys
import time
import httpx
import logging
import asyncio
import numpy as np
import pandas as pd
from dotenv import dotenv_values
from aiolimiter import AsyncLimiter
from typing import Any, AsyncGenerator
from persiantools.jdatetime import JalaliDateTime    # type: ignore

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User                       # noqa: E402
from Application.api.utils import wait_time                  # noqa: E402
import Application.configs.admin_config as aconfig           # noqa: E402
from Application.api.api_service import APIService           # noqa: E402
from Application.data.exchange import Nobitex as nb          # noqa: E402
# from Application.configs.config import MarketData as md    # noqa: E402
from Application.data.data_tools import parse_orders,\
                                        parse_positions,\
                                        parse_order_book,\
                                        Tehran_timestamp,\
                                        parse_wallets_to_df  # noqa: E402
from Application.utils.logs import get_logger, get_log_level # noqa: E402


# Initializing the logger
# NL_logs stands for Nobitex Linkage Logs
NL_logs : logging.Logger = get_logger(logger_name='NL_logs', log_level=get_log_level('NL'))





class Market:
    def __init__(self, api_service: APIService):
        self.service = api_service
    # ____________________________________________________________________________ . . .


    async def live_fetch_market_price(self,
                                      src_currency : str,
                                      dst_currency : str) -> AsyncGenerator[float | int, Any]:
        """
        It's an async generator function which constantly fetches the market price of given trading
        pair.

        Parameters:
            http_agent (AsyncClient): The HTTP client used to make the request.
            src_currecy (str): Source currency.
            dst_currency (str): Destination currency is eather 'usdt' | 'rls'.

        Yields:
            market_price (float | int): Market price for given trading pair.
        """
        last_fetch_time: float = 0.0
        limiter = AsyncLimiter(max_rate    = nb.Endpoint.MARKET_STATS_RL,
                               time_period = nb.Endpoint.MARKET_STATS_RP)

        payload = {'srcCurrency': src_currency,
                   'dstCurrency': dst_currency}
        
        async with httpx.AsyncClient() as http_agent:
            while True:
                await limiter.acquire()
                wait = wait_time(nb.Endpoint.MARKET_STATS_MI, time.time(), last_fetch_time)
                await asyncio.sleep(wait) if (wait > 0) else None

                response = await self.service.get(client         = http_agent,
                                                  url            = nb.URL,
                                                  endpoint       = nb.Endpoint.MARKET_STATS,
                                                  timeout        = aconfig.Market.OHLC.TIMEOUT,
                                                  tries_interval = nb.Endpoint.MARKET_STATS_MI,
                                                  tries          = aconfig.Market.OHLC.TRIES,
                                                  params         = payload)
                
                last_fetch_time = time.time()

                market_price = response.json()['stats'][f'{src_currency}-{dst_currency}']['latest']
                yield market_price
    # ____________________________________________________________________________ . . .


    async def kline(self,
                    http_agent     : httpx.AsyncClient,
                    symbol         : str,
                    resolution     : str,
                    end            : int,
                    timeout        : float,
                    tries_interval : float,
                    tries          : int,
                    *,
                    url            : str        = nb.URL, 
                    endpoint       : str        = nb.Endpoint.OHLC,
                    page           : int | None = None,
                    countback      : int | None = None,
                    start          : int | None = None,) -> dict:
        """
        Fetches Kline data for a given symbol.

        Parameters:
            http_agent (AsyncClient): The HTTP client used to make the request.
            symbol (str): The trading symbol (e.g., 'BTCUSDT').
            resolution (str): The time interval for the data ('1', '5', '15', '30', '60', '180', 
            '240', '360', '720', 'D', '2D', '3D').
            end (str): The end timestamp or 'latest' for current time.
            countback (str): Number of data points to retrieve.
            timeout (float): Request timeout in seconds.
            tries_interval (float): The time period to wait before retrying request in seconds.
            tries (int): Number of tries for request.
            start (str, optional): The start timestamp or 'oldest' for the oldest available data.
            url (str, optional): The base URL for the request. Defaults to nb.URL.
            endpoint (str, optional): The API endpoint. Defaults to nb.Endpoint.OHLC.
            max_rate (str, optional): The maximum rate limit for API calls. Defaults to 
            nb.Endpoint.OHLC_RL.
            time_period (str, optional): The time period in seconds over which the rate limit 
            applies. Defaults to 60.

        Returns:
            dict: Response data containing Kline information.
            None: In case of failed attempts of request calls.
        """

        payload = {
            'symbol': symbol,
            'resolution': resolution,
            'to': str(end),
            'countback': str(countback) if start is None else None,
            'from': str(start),
            'page': str(page)
        }

        def is_valid(value):
            """
            Checks if the key-value pair should be included in the payload.

            Args:
                value (any): The value to check.

            Returns:
                bool: True if the key-value pair is valid, False otherwise.            
            """
            if value is None or value == str(None):
                return False
            if isinstance(value, float) and np.isnan(value):
                return False
            if value == 'null':
                return False
            
            return True

        payload = {key: value for key, value in payload.items() if is_valid(value)}

        response = await self.service.get(client         = http_agent,
                                      url            = url,
                                      endpoint       = endpoint,
                                      timeout        = timeout,
                                      tries_interval = tries_interval,
                                      tries          = tries,
                                      params         = payload)    # type: ignore

        return response.json()
    # ____________________________________________________________________________ . . .


    async def initiate_kline(self,
                             symbol: str,
                             resolution: str,
                             required_candles: int,
                             timeout: float,
                             tries_interval: float,
                             tries: int):

        async with httpx.AsyncClient() as http_agent:
            data = await self.kline(http_agent     = http_agent,
                                    symbol         = symbol,
                                    resolution     = resolution,
                                    end            = Tehran_timestamp(),
                                    timeout        = timeout,
                                    tries_interval = tries_interval,
                                    tries          = tries,
                                    countback      = required_candles)
                
        return data
    # ____________________________________________________________________________ . . .


    async def populate_kline(self,
                             initial_df: pd.DataFrame,
                             symbol: str,
                             resolution: str,
                             required_candles: int,
                             timeout: float,
                             tries_interval: float,
                             tries: int,
                             max_interval: float,
                             max_rate: int,
                             rate_period: int):
        """
        This method is an AsyncGenerator function that gives current kline data and number of 
        required candles (determined in configs) then it fetches kline data in a loop and yield it 
        untill the number of fetched data be greather than or equal to number of required candles.
        It most be called in a loop to get the new data untill the number of required candles is 
        satisfied.
        """

        wait: float = 0.0
        last_fetch_time: float = 0.0

        data: dict = {}
        fetched_count: int = initial_df.shape[0]
        is_first_iteration = True

        async with httpx.AsyncClient() as http_agent:
            async with AsyncLimiter(max_rate, rate_period):
                while fetched_count < required_candles:
                    countback = required_candles - fetched_count

                    if is_first_iteration:
                        end = self._prior_timestamp(initial_df, timeframe=resolution)
                        is_first_iteration = False
                    else:
                        end = self._prior_timestamp(data, timeframe=resolution)

                    wait = wait_time(max_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait) if (wait > 0) else None

                    data = await self.kline(http_agent     = http_agent,
                                            symbol         = symbol,
                                            resolution     = resolution,
                                            end            = end,
                                            timeout        = timeout,
                                            tries_interval = tries_interval,
                                            tries          = tries,
                                            countback      = countback)
                    
                    last_fetch_time = time.time()
                    fetched_count += len(data['t'])
                    
                    yield data
    # ____________________________________________________________________________ . . .


    async def update_kline(self,
                           current_data: pd.DataFrame,
                           symbol: str,
                           resolution: str,
                           timeout: float,
                           tries_interval: float,
                           tries: int,
                           max_interval: float,
                           max_rate: int,
                           rate_period: int):
        """
        This method fetches kline data from the last timestamp of current data to the current time.
        Preferably it might be called in a loop to keep sending fetch request continuously.
        """
        wait: float = 0.0
        last_fetch_time: float = 0.0

        start = self._last_timestamp(current_data)

        async with httpx.AsyncClient() as http_agent:
            async with AsyncLimiter(max_rate, rate_period):
                while True:
                    wait = wait_time(max_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait) if (wait > 0) else None

                    new_data = await self.kline(http_agent     = http_agent,
                                                symbol         = symbol,
                                                resolution     = resolution,
                                                end            = Tehran_timestamp(),
                                                timeout        = timeout,
                                                tries_interval = tries_interval,
                                                tries          = tries,
                                                start          = start)
                    
                    last_fetch_time = time.time()
                    start = self._last_timestamp(new_data)
                    yield new_data
    # ____________________________________________________________________________ . . .


    async def live_fetch_order_book(self,
                                    http_agent: httpx.AsyncClient,
                                    src_currency: str,
                                    dst_currency: str):
        """
        It's an async generator function which constantly fetches the market order book of given
        trading pair.

        Parameters:
            http_agent (AsyncClient): The HTTP agent which is used to make the request call.
            src_currecy (str): Source currency.
            dst_currency (str): Destination currency is eather 'usdt' | 'rls'.

        Yields:
        - order_book_asks_df (DataFrame): Ask orders DataFrame with columns 'price' and 'volume'.
        - order_book_bids_df (DataFrame): Bid orders DataFrame with columns 'price' and 'volume'.
        - midprice (float):
        """
        last_fetch_time: float = 0.0
        limiter = AsyncLimiter(max_rate    = nb.Endpoint.ORDER_BOOK_RL,
                               time_period = nb.Endpoint.ORDER_BOOK_RP)

        endpoint = nb.Endpoint.ORDER_BOOK +  f'{src_currency.upper() + dst_currency.upper()}'

        async with http_agent:
            while True:
                await limiter.acquire()
                wait = wait_time(nb.Endpoint.ORDER_BOOK_MI, time.time(), last_fetch_time)
                await asyncio.sleep(wait) if (wait > 0) else None

                response = await self.service.get(
                    client         = http_agent,
                    url            = nb.URL,
                    endpoint       = endpoint,
                    timeout        = aconfig.Market.OrderBook.TIMEOUT,
                    tries_interval = nb.Endpoint.ORDER_BOOK_MI,
                    tries          = aconfig.Market.OrderBook.TRIES
                )

                last_fetch_time = time.time()

                order_book_asks_df, order_book_bids_df, midprice = parse_order_book(
                    raw_order_book = response.json()
                )

                yield order_book_asks_df, order_book_bids_df, midprice
    # ____________________________________________________________________________ . . .


    def _prior_timestamp(self, data: pd.DataFrame | dict, *, timeframe: str) -> int:
        """
        This is an internal sub_method for '_init_fetch' method which returns the timestamp of the 
        first candle of given data. Which is used for sending the subsequent 'initial_fetch' 
        requests.
        """
        try:
            timeframes: dict[str, int] = {'1'  : 60,
                                          '5'  : 300,
                                          '15' : 900,
                                          '30' : 1_800,
                                          '60' : 3_600,
                                          '180': 10_800,
                                          '240': 14_400,
                                          '360': 21_600,
                                          '720': 43_200,
                                          'D'  : 86_400,
                                          '2D' : 172_800,
                                          '3D' : 259_200}
            
            if timeframe not in timeframes.keys():
                raise ValueError(f'Provided resolution (timeframe) {timeframe} is not in \
                                 Nobitex\'s approved resolutions or has wrong data type of \
                                 {type(timeframe)}, str is only accepted.')
            
            # offset_time: int = timeframes.get(timeframe, 0)
            
            if isinstance(data, pd.DataFrame):
                first_timestamp = int(JalaliDateTime.to_gregorian(data.index.min()).timestamp())
            else:
                first_timestamp = int(data['t'][0])

            prior_timestamp: int = first_timestamp# - offset_time

            return prior_timestamp
        except ValueError as err:
            NL_logs.error('Inside "_prior_timestamp()" method of "nobitex_api.Market" class: ',err)
            return 0
    # ____________________________________________________________________________ . . .


    def _last_timestamp(self, data: pd.DataFrame | dict) -> int:    # FIXME NO-006
        """
        This method returns the integer timestamp of last row of data whether data is of type dict
        or DataFrame.
        """
        if isinstance(data, dict):
            last_timestamp = int(data['t'][-1])

        elif isinstance(data, pd.DataFrame):
            Jalali_datetime = data.index.max()
            last_timestamp  = JalaliDateTime.to_gregorian(Jalali_datetime).timestamp()
            last_timestamp  = int(last_timestamp)

        return last_timestamp
# =================================================================================================



class Trade:
    def __init__(self, api_service: APIService):
        self.service = api_service
    # ____________________________________________________________________________ . . .


    async def fetch_asset_deceimals(self):
        """
        
        """
        pass
    # ____________________________________________________________________________ . . .


    async def _base_place_order(self,
                               http_agent   : httpx.AsyncClient,
                               token        : str,
                               environment  : str,
                               side         : str,
                               src_currency : str,
                               dst_currency : str,
                               amount       :float,
                               **kwargs):
        """
        Base order placement method called by child methods.

        Parameters:
            http_agent (httpx.AsyncClient): HTTP client for making requests.
            token (str): User Authorization token.
            environment (str): 'spot' or 'futures' to specify the trading environment.
            side (str): Order side ('buy' or 'sell').
            src_currency (str): Source currency.
            dst_currency (str): Destination currency.
            amount (float): Amount to trade.
            kwargs: Other additional parameters.

        Returns:
            request_response (dict): The response of order placement from the exchange.
        """
        if environment not in {'spot', 'futures'}:
            raise ValueError(f'Invalid environment :"{environment}". Must be "spot" or "futures".')
        
        mode = kwargs.get('mode')
        execution = kwargs.get('execution')
        if execution and mode:
            raise ValueError("Cannot specify both 'execution' and 'mode'.")
        
        headers = {'Authorization': f'Token {token}'}
        payload: dict  = {'type'          : side, # IMPELEMENT DEFAULT VALUES FOR .get FUNCTIONS.
                          'srcCurrency'   : src_currency,
                          'dstCurrency'   : dst_currency,
                          'amount'        : str(amount)}   # Implement a function to be called here to correct the "price" and "amount" floating point numbers.


        if environment == 'spot':
            endpoint       = nb.Endpoint.PLACE_SPOT_ORDER
            tries_interval = nb.Endpoint.PLACE_SPOT_ORDER_MI

        else: # environment == 'futures'
            endpoint       = nb.Endpoint.PLACE_FUTURES_ORDER
            tries_interval = nb.Endpoint.PLACE_FUTURES_ORDER_MI
            payload['leverage'] = str(kwargs.get('leverage'))


        if execution:
            payload['execution'] = execution
            if execution in {'limit', 'stop_limit'}:
                payload['price'] = str(kwargs.get('price'))
            if execution in {'stop_limit', 'stop_market'}:
                payload['stopPrice'] = str(kwargs.get('stop_price'))

        elif mode:
            payload.update({'mode'          : mode,
                            'price'         : str(kwargs.get('price')),
                            'stopPrice'     : str(kwargs.get('stop_price')),
                            'stopLimitPrice': str(kwargs.get('stop_limit_price'))})


        if kwargs.get('client_oid'):
            payload['clientOrderId'] = kwargs.get('client_oid')


        response = await self.service.post(client         = http_agent,
                                           url            = nb.URL,
                                           endpoint       = endpoint,
                                           timeout        = aconfig.Trade.Place.PlaceOrder.TIMEOUT,
                                           tries_interval = tries_interval,
                                           tries          = aconfig.Trade.Place.PlaceOrder.TRIES,
                                           data           = payload,
                                           headers        = headers)

        return response.json()
    # ____________________________________________________________________________ . . .





    async def place_spot_limit_order(self,
                               http_agent   : httpx.AsyncClient,
                               token        : str,
                               side         : str,
                               src_currency : str,
                               dst_currency : str,
                               amount       : float,
                               price        : float,
                               client_oid   : str):
        """
        Places limit order on spot market.

        Parameters:

        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'spot',
                                                execution    = 'limit',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                price        = price,
                                                client_oid   = client_oid)
        
        return response
    # ____________________________________________________________________________ . . .


    async def place_spot_market_order(self,
                                http_agent   : httpx.AsyncClient,
                                token        : str,
                                side         : str,
                                src_currency : str,
                                dst_currency : str,
                                amount       : float,
                                client_oid   : str | None = None):
        """
        Places market order on spot market.

        Parameters:

        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'spot',
                                                execution    = 'market',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                client_oid   = client_oid)

        return response
    # ____________________________________________________________________________ . . .


    async def place_spot_stop_limit_order(self,
                                    http_agent   : httpx.AsyncClient,
                                    token        : str,
                                    side         : str,
                                    src_currency : str,
                                    dst_currency : str,
                                    amount       : float,
                                    price        : float,
                                    stop_price   : float,
                                    client_oid   : str | None = None):
        """
        Places stop_limit order on spot market.
        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'spot',
                                                execution    = 'stop_limit',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                price        = price,
                                                stop_price   = stop_price,
                                                client_oid   = client_oid)
        
        return response
    # ____________________________________________________________________________ . . .


    async def place_spot_stop_market_order(self,
                                     http_agent   : httpx.AsyncClient,
                                     token        : str,
                                     side         : str,
                                     src_currency : str,
                                     dst_currency : str,
                                     amount       : float,
                                     stop_price   : float,
                                     client_oid   : str | None = None):
        """
        Places stop_market order on spot market.
        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'spot',
                                                execution    = 'stop_market',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                stop_price   = stop_price,
                                                client_oid   = client_oid)

        return response
    # ____________________________________________________________________________ . . .


    async def place_spot_oco_order(self,
                                   http_agent     : httpx.AsyncClient,
                                   token          : str,
                                   side           : str,
                                   src_currency   : str,
                                   dst_currency   : str,
                                   amount         : float,
                                   tp_price       : float,
                                   sl_stop_price  : float,
                                   sl_limit_price : float,
                                   client_oid     : str):
        """
        Places oco (one-cancels-other) orders including a limit and a stop_limit order, which preferably is used for tp and sl orders.

        Parameters:

        """
        response = await self._base_place_order(http_agent       = http_agent,
                                                token            = token,
                                                environment      = 'spot',
                                                mode             = 'oco',
                                                side             = side,
                                                src_currency     = src_currency,
                                                dst_currency     = dst_currency,
                                                amount           = amount,
                                                price            = tp_price,
                                                stop_price       = sl_stop_price,
                                                stop_limit_price = sl_limit_price,
                                                client_oid       = client_oid)

        return response
    # ____________________________________________________________________________ . . .





    async def place_futures_limit_order(self,
                                  http_agent   : httpx.AsyncClient,
                                  token        : str,
                                  side         : str,
                                  src_currency : str,
                                  dst_currency : str,
                                  amount       : float,
                                  price        : float,
                                  leverage     : float,
                                  client_oid   : str):
        """
        Places limit order on futures market.
        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'futures',
                                                execution    = 'limit',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                price        = price,
                                                leverage     = leverage,
                                                client_oid   = client_oid)
        
        return response
    # ____________________________________________________________________________ . . .


    async def place_futures_market_order(self,
                                         http_agent   : httpx.AsyncClient,
                                         token        : str,
                                         side         : str,
                                         src_currency : str,
                                         dst_currency : str,
                                         amount       : float,
                                         leverage     : float,
                                         client_oid   : str):
        """
        Places limit order on futures market.
        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'futures',
                                                execution    = 'market',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                leverage     = leverage,
                                                client_oid   = client_oid)

        return response
    # ____________________________________________________________________________ . . .


    async def place_futures_stop_limit_order(self,
                                       http_agent   : httpx.AsyncClient,
                                       token        : str,
                                       side         : str,
                                       src_currency : str,
                                       dst_currency : str,
                                       amount       : float,
                                       price        : float,
                                       stop_price   : float,
                                       leverage     : float,
                                       client_oid   : str):
        """
        Places stop_limit order on futures market.
        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'futures',
                                                execution    = 'stop_limit',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                price        = price,
                                                stop_price   = stop_price,
                                                leverage     = leverage,
                                                client_oid   = client_oid)
        
        return response
    # ____________________________________________________________________________ . . .


    async def place_futures_stop_market_order(self,
                                              http_agent   : httpx.AsyncClient,
                                              token        : str,
                                              side         : str,
                                              src_currency : str,
                                              dst_currency : str,
                                              amount       : float,
                                              stop_price   : float,
                                              leverage     : float,
                                              client_oid   : str):
        """
        Places stop_market order on futures market.
        """
        response = await self._base_place_order(http_agent   = http_agent,
                                                token        = token,
                                                environment  = 'futures',
                                                execution    = 'stop_market',
                                                side         = side,
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                stop_price   = stop_price,
                                                leverage     = leverage,
                                                client_oid   = client_oid)

        return response


    async def place_futures_oco_order(self,
                                      http_agent     : httpx.AsyncClient,
                                      token          : str,
                                      side           : str,
                                      src_currency   : str,
                                      dst_currency   : str,
                                      amount         : float,
                                      tp_price       : float,
                                      sl_stop_price  : float,
                                      sl_limit_price : float,
                                      leverage       : float,
                                      client_oid     : str):
        """
        Places oco (one-cancels-other) orders including a limit and a stop_limit order, which preferably is used for tp and sl orders.

        Parameters:

        """
        response = await self._base_place_order(http_agent       = http_agent,
                                                token            = token,
                                                environment      = 'futures',
                                                mode             = 'oco',
                                                side             = side,
                                                src_currency     = src_currency,
                                                dst_currency     = dst_currency,
                                                amount           = amount,
                                                price            = tp_price,
                                                stop_price       = sl_stop_price,
                                                stop_limit_price = sl_limit_price,
                                                leverage         = leverage,
                                                client_oid       = client_oid)

        return response
    # ____________________________________________________________________________ . . .





    async def fetch_orders(self,
                           client       : httpx.AsyncClient,
                           token        : str,
                           *,
                           req_interval : float,
                           max_rate     : int,
                           rate_period  : int,
                           status       : str = 'all',
                           src_currency : str | None = None,
                           dst_currency : str | None = None):
        """
        Fetches list of user's orders.

        Parameters:
            client (httpx.AsyncClient): HTTP client.
            token (str): User's API token.
            req_interval (float): Interval between requests in seconds.
            max_rate (int): Maximum number of requests.
            rate_period (int): Period in seconds for rate limiting.
            status (str): The status of orders. Expects eather "all" | "open" | "done" | "close".
            src_currency (str): Source currency.
            dst_currency (str): Destination currency is eather "rls" | "usdt".

        Yields: A DataFrame containing orders data.
        """
        last_fetch_time: float = 0.0

        headers = {'Authorization': 'Token ' + token}
        payload: dict[str, str] = {'status'  : status,
                                   'details' : '2',
                                   'page'    : str(1),
                                   'pageSize': '100'}

        if src_currency and dst_currency:
            payload['dstCurrency'] = dst_currency
            payload['srcCurrency'] = src_currency

        params: dict = {'url'            : nb.URL,
                        'endpoint'       : nb.Endpoint.ORDERS,
                        'timeout'        : aconfig.Trade.Fetch.Orders.TIMEOUT,
                        'tries_interval' : nb.Endpoint.ORDERS_MI,
                        'tries'          : aconfig.Trade.Fetch.Orders.TRIES,
                        'data'           : payload,
                        'headers'        : headers}

        async with client:
            limiter = AsyncLimiter(max_rate, rate_period)
            while True:
                await limiter.acquire()
                wait = wait_time(req_interval, time.time(), last_fetch_time)
                await asyncio.sleep(wait) if (wait > 0) else None

                response = await self.service.get(**params, client=client)

                last_fetch_time = time.time()
                orders_df = parse_orders(response.json())
                has_next: bool = response.json()['hasNext']
                payload['page']= str(2)

                while has_next:
                    await limiter.acquire()
                    wait = wait_time(req_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait) if (wait > 0) else None

                    new_response = await self.service.get(**params, client=client)

                    last_fetch_time = time.time()
                    has_next = new_response.json()['hasNext']
                    payload['page'] = str(int(payload['page']) + 1)

                    new_orders_df = parse_orders(new_response.json())
                    orders_df = pd.concat([orders_df, new_orders_df])
                
                yield orders_df
    # ____________________________________________________________________________ . . .


    async def fetch_nofile_orders(self):
        pass
    # ____________________________________________________________________________ . . .


    async def fetch_positions(self,
                              client     : httpx.AsyncClient,
                              token      : str,
                              status     : str,
                              page       : int,
                              srcCurrency: str | None = None,
                              dstCurrency: str | None = None):
        """
        Fetch list of user's positions.

        Parameters:
            client (httpx.AsyncClient): The HTTP client.
            token (str): User API token.
            status (str): The status of positions. Expects eather "active" | "past".
            page (int): To request a specific page of responses in case "hasNext" flag is "True".
            srcCurrency (str): Source currency.
            dstCurrency (str): Destination currency is eather "rls" | "usdt".

        Returns: A dictionary containing 3 elements: -request status, -positions, and -hasNext flag
        """
        payload = {'status': status, 'page': str(page), 'pageSize': '100'}
        if srcCurrency and dstCurrency:
            payload['dstCurrency'] = dstCurrency
            payload['srcCurrency'] = srcCurrency

        headers = {'Authorization': 'Token ' + token}

        response = await self.service.get(client         = client,
                                      url            = nb.URL,
                                      endpoint       = nb.Endpoint.POSITIONS,
                                      timeout        = aconfig.Trade.Fetch.Positions.TIMEOUT,
                                      tries_interval = nb.Endpoint.POSITIONS_MI,
                                      tries          = aconfig.Trade.Fetch.Positions.TRIES,
                                      data           = payload,
                                      headers        = headers)

        return response.json()
    # ____________________________________________________________________________ . . .


    async def fetch_open_positions(self,
                                   client      : httpx.AsyncClient,
                                   token       : str,
                                   req_interval: float,
                                   max_rate    : int,
                                   rate_period : int):
        """
        Fetches all open positions of user for the given market environment.

        Parameters:
            client (httpx.AsyncClient): HTTP client.
            token (str): Client's API token.
            req_interval (float): Interval between requests in seconds.
            max_rate (int): Maximum number of requests.
            rate_period (int): Period in seconds for rate limiting.

        Yields:
            pd.DataFrame: A dataframe containing positions data.
        """
        last_fetch_time: float = 0.0
        params: dict = {'client': client,
                        'token' : token,
                        'status': 'active'}

        async with client:
            limiter = AsyncLimiter(max_rate, rate_period)
            while True:
                await limiter.acquire()
                wait = wait_time(req_interval, time.time(), last_fetch_time)
                await asyncio.sleep(wait) if (wait > 0) else None

                data = await self.fetch_positions(**params, page=1)

                last_fetch_time = time.time()
                positions_df = parse_positions(data)
                has_next: bool = data['hasNext']
                page: int = 2

                while has_next:
                    await limiter.acquire()
                    wait = wait_time(req_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait) if (wait > 0) else None

                    new_data = await self.fetch_positions(**params, page=page)

                    last_fetch_time = time.time()
                    has_next = new_data['hasNext']
                    page += 1

                    new_positions_df = parse_positions(new_data)
                    positions_df = pd.concat([positions_df, new_positions_df])

                yield positions_df
    # ____________________________________________________________________________ . . .


    async def status(self):
        pass
    # ____________________________________________________________________________ . . .


    async def cancel_pending_order(self,
                                   http_agent : httpx.AsyncClient,
                                   *,
                                   token      : str,
                                   id         : str | None = None,
                                   client_id  : str | None = None):
        """
        Cancels a specific pending order.

        Parameters:
            http_agent (AsyncClient): The HTTP agent.
            token (str): User API token.
            id (str): The order id provided by exchange.
            client_id (str): The order id defined by bot.

        Raises:
            ValueError:

        Returns:
            requset_response (dict): A dictionary containing response of request or an empty
            dictionary.
        """
        try:
            headers = {'Authorization': 'Token ' + token}

            payload = {'status': 'canceled'}
            if id:
                payload['order'] = id
            elif client_id:
                payload['clientOrderId'] = client_id
            else:
                raise ValueError('One of "id" parameters ("id" or "client_id") is mandatory.')

            response = await self.service.post(client         = http_agent,
                                         url            = nb.URL,
                                         endpoint       = nb.Endpoint.UPDATE_STATUS,
                                         timeout        = aconfig.Trade.Place.CancelOrders.TIMEOUT,
                                         tries_interval = nb.Endpoint.UPDATE_STATUS_MI,
                                         tries          = aconfig.Trade.Place.CancelOrders.TRIES,
                                         data           = payload,
                                         headers        = headers)

            return response.json()

        except ValueError as err:
            NL_logs.error(f'Missing parameter for "cancel_pending_order()" method: {err}')
            return {}
        except Exception as err:
            NL_logs.error(f'Inside "nobitex_api.Trade.cancel_pending_order()" method: {err}')
            return {}
    # ____________________________________________________________________________ . . .


    async def cancel_all_orders(self,
                                client : httpx.AsyncClient,
                                token  : str):
        """
        Cancels all pending orders.

        Parameters:
            client (AsyncClient): The HTTP agent.
            token (str): User's API token.
        
        Returns:
            success (str): It returns eather literal 'succeeded' or 'failed' base on success.
        """
        headers = {'Authorization': 'Token ' + token}

        response = await self.service.post(
            client         = client,
            url            = nb.URL,
            endpoint       = nb.Endpoint.CANCEL_ORDERS,
            timeout        = aconfig.Trade.Place.CancelOrders.TIMEOUT,
            tries_interval = nb.Endpoint.CANCEL_ORDERS_MI,
            tries          = aconfig.Trade.Place.CancelOrders.TRIES,
            headers        = headers
        )

        return 'succeeded' if response.json()['status'] == 'ok' else 'failed'
    # ____________________________________________________________________________ . . .


    async def close_position(self,
                             http_agent   : httpx.AsyncClient,
                             token        : str,
                             id           : str,
                             execution    : str,
                             amount       : float,
                             side         : str,
                             src_currecy  : str | None = None,
                             dst_currency : str | None = None,
                             price        : float | str | None = None, # CAN BE 'market' FOR MARKET ORDER EXECUTIONS?
                             stop_price   : float | None = None):
        """
        Close a position.

        Parameters:
            http_agent (AsyncClient): The HTTP agent.
            token (str): User API token.
            id (str): The position id provided by exchange.
            execution (str): The order execution method. Expects eather 'market' | 'limet' | 'stop_market' | 'stop_limit'.
            amount (float): The asset amount from total position's amount that you want to close.
            side
            src_currecy (str - optional): Source currency.
            dst_currency (str - optional): Destination currency is eather 'usdt' | 'rls'.
            price (float): It's the current market price for 'merket' order executions, or the limit closing price for 'limit' order executions.
            stop_price (float): The price that activates 'stop' orders.

        Raises:
            ValueError:

        Returns:
            request_response(dict): A dictionary containing requst response.
        """
        try:
            endpoint = f'/positions/{id}/close'
            headers  = {'Authorization': 'Token ' + token}
            payload  = {'execution' : execution,
                        'amount'    : str(amount),
                        'price'     : str(price),
                        'type'      : side}

            if ((execution=='stop_limit') or (execution=='stop_market') and stop_price):
                payload['stopPrice'] = str(stop_price)

            elif ((execution=='stop_limit') or (execution=='stop_market') and not stop_price):
                raise ValueError('parameter "stop_price" most be provided for "stop_limit" or '\
                                '"stop_market" order execution methods.')
            
            if src_currecy and dst_currency:
                payload['srcCurrency'] = src_currecy
                payload['dstCurrency'] = dst_currency

            response = await self.service.post(
                client         = http_agent,
                url            = nb.URL,
                endpoint       = endpoint,
                timeout        = aconfig.Trade.Place.ClosePosition.TIMEOUT,
                tries_interval = nb.Endpoint.CLOSE_POSITION_MI,
                tries          = aconfig.Trade.Place.ClosePosition.TRIES,
                data           = payload,
                headers        = headers
            )

            return response.json()
        except ValueError as err:
            NL_logs.error(f'Inside "nobitex_api.Trade.close_position()" method: {err}')
            return {}
    # ____________________________________________________________________________ . . .


    async def close_all_positions(self, token: str):
        """
        Closes all active positions by market price.

        Parameters:
            token (str): User's API token.

        Returns:
            success (str): It returns eather literal 'succeeded' or 'failed' base on success.
        """
        # fetching all active positions
        positions_df = await anext(
            self.fetch_open_positions(
                client       = httpx.AsyncClient(),
                token        = token,
                req_interval = nb.Endpoint.POSITIONS_MI,
                max_rate     = nb.Endpoint.POSITIONS_RL,
                rate_period  = nb.Endpoint.POSITIONS_RP
            )
        )


        # Validate positions_df
        if positions_df.empty:
            NL_logs.info('There are no active positions to be closed!')
            return 'succeeded'

        required_specs = {'id', 'liability', 'srcCurrency', 'dstCurrency'}
        if not required_specs.issubset(positions_df.columns):
            raise ValueError(f'positions DataFrame must contain columns: {required_specs}')


        # Extract unique trading pairs of open positions
        positions_pairs: list[tuple] = []
        for _, position in positions_df.iterrows():
            positions_pairs.append((position['srcCurrency'], position['dstCurrency']))

        positions_pairs = list(set(positions_pairs))


        # Fetch market price for trading pairs
        market = Market(APIService())
        market_prices: dict = {}

        for src, dst in positions_pairs:
            market_prices[f'{src}-{dst}'] = await anext(market.live_fetch_market_price(
                src_currency = src,
                dst_currency = dst
            ))


        # Prepare coroutines for closing positions
        NL_logs.info(f'There are "{positions_df.size}" positions to be closed: \n'\
                     f'{positions_df[['srcCurrency', 'dstCurrency', 'id']]}')

        coroutines = []
        for _, position in positions_df.iterrows():
            try:
                src_currecy  = position.get('srcCurrency')
                dst_currency = position.get('dstCurrency')

                price = market_prices[f'{src_currecy}-{dst_currency}']
                if isinstance(price, int):
                    price = str(int(price/10)) if dst_currency == 'rls' else str(price)
                else:
                    price = str(price/10) if dst_currency == 'rls' else str(price)

                coroutines.append(
                    self.close_position(
                        http_agent   = httpx.AsyncClient(),
                        token        = token,
                        id           = position['id'],
                        execution    = 'market',
                        amount       = position['liability'],
                        side         = 'sell' if position['side'] == 'buy' else 'buy',
                        src_currecy  = src_currecy,
                        dst_currency = dst_currency,
                        price        = price
                    )
                )

            except Exception as err:
                NL_logs.error('Failed to prepare coroutine for closing the position '\
                              f'{position['id']}: {str(err)}')


        # Attempt to send 'close_position' requests
        results = await asyncio.gather(*coroutines, return_exceptions=True)


        # Process results and handle any exceptions
        close_results: list = []
        for position, result in zip(positions_df.to_dict('records'), results):
            if isinstance(result, Exception) or result.get('status') == 'failed':  # type: ignore
                NL_logs.error(f'Failed to close position {position["id"]}: {str(result)}')
                close_results.append({'id': position['id'],
                                      'status': 'failed',
                                      'error': str(result)})

            else:
                NL_logs.info(f'Successfully closed position "{position['id']}"')
                close_results.append({'id': position['id'],
                                      'status': 'success',
                                      'response': result})

        if all(result['status'] == 'success' for result in close_results):
            return 'succeeded'
        else:
            return 'failed'
# =================================================================================================



class Account:
    def __init__(self, api_service: APIService):
        self.service = api_service
        self.market = Market(api_service=self.service)
    # ____________________________________________________________________________ . . .


    async def wallets(self,
                      http_agent  : httpx.AsyncClient,
                      token       : str,
                      drop_void   : bool = True) -> pd.DataFrame:
        """
        Fetches user's wallets for given market environment.

        Parameters:
            client (httpx.AsyncClient): HTTP client.
            token (str): Client's API token.
            environment (str): Market environment. Most be eather "spot" or "margin".
            drop_void (bool): Excludes wallets with zero balance.

        Returns:
            wallets_df (DataFrame): Client's wallets data.
        """
        payload: dict = {'type': 'margin'}
        headers: dict = {'Authorization': 'Token ' + token}

        response = await self.service.get(client         = http_agent,
                             url            = nb.URL,
                             endpoint       = nb.Endpoint.WALLETS,
                             timeout        = aconfig.Account.Wallets.TIMEOUT,
                             tries_interval = nb.Endpoint.WALLETS_MI,
                             tries          = aconfig.Account.Wallets.TRIES,
                             data           = payload,
                             headers        = headers)

        df = parse_wallets_to_df(raw_wallets=response.json(), drop_void=drop_void)

        return df
    # ____________________________________________________________________________ . . .


    async def live_fetch_portfolio_balance(self) -> AsyncGenerator[tuple[float, float], Any]:
        """
        It's an async generator function which constantly fetches portfolio balance of user.

        Yields:
            portfolio_balance (float): The sum of user's wallet balances in Rial.
        """
        last_fetch_time: float = 0.0
        limiter = AsyncLimiter(max_rate=nb.Endpoint.WALLETS_MI, time_period=nb.Endpoint.WALLETS_RP)

        async with httpx.AsyncClient() as http_agent:
            while True:
                await limiter.acquire()
                wait = wait_time(nb.Endpoint.WALLETS_MI, time.time(), last_fetch_time)
                await asyncio.sleep(wait) if (wait > 0) else None

                wallets_coroutine = self.wallets(http_agent = http_agent,
                                                 token      = User.TOKEN, # type: ignore
                                                 drop_void  = True)

                usd_price_rate_coroutine = anext(self.market.live_fetch_market_price(
                    src_currency = 'usdt',
                    dst_currency = 'rls'
                ))

                wallets_df, usd_price_rate = await asyncio.gather(wallets_coroutine,
                                                                  usd_price_rate_coroutine)

                last_fetch_time = time.time()

                portfolio_balance_rial = wallets_df['rial_balance'].sum()
                portfolio_balance_usd  = round((portfolio_balance_rial / float(usd_price_rate)), 2)

                yield portfolio_balance_rial, portfolio_balance_usd
    # ____________________________________________________________________________ . . .


    async def balance(self, http_agent: httpx.AsyncClient, token: str, currency: str):
        """
        Fetches the wallet balance of specific currency for user.

        Parameters:
            client (httpx.AsyncClient): HTTP client.
            token (str): Client's API token.
            currency (str): currency to get it's balance.

        Returns ():
        """
        payload: dict = {'currency': currency}
        headers: dict = {'Authorization': 'Token ' + token}

        api = APIService()
        response = await api.post(client         = http_agent,
                              url            = nb.URL,
                              endpoint       = nb.Endpoint.BALANCE,
                              timeout        = aconfig.Account.Balance.TIMEOUT,
                              tries_interval = nb.Endpoint.BALANCE_MI,
                              tries          = aconfig.Account.Balance.TRIES,
                              data           = payload,
                              headers        = headers)

        return response.json()
    # ____________________________________________________________________________ . . .


    async def live_fetch_user_profile(self, token: str):
        """
        _summary_

        Raises:
            KeyError
        """
        last_fetch_time: float = 0.0
        limiter = AsyncLimiter(max_rate=nb.Endpoint.PROFILE_RL, time_period=nb.Endpoint.PROFILE_RP)

        async with httpx.AsyncClient() as http_agent:
            while True:
                await limiter.acquire()
                wait = wait_time(nb.Endpoint.PROFILE_MI, time.time(), last_fetch_time)
                await asyncio.sleep(wait) if (wait > 0) else None

                response = await self.service.get(client         = http_agent,
                                              url            = nb.URL,
                                              endpoint       = nb.Endpoint.PROFILE,
                                              timeout        = aconfig.Account.Profile.TIMEOUT,
                                              tries_interval = nb.Endpoint.PROFILE_MI,
                                              tries          = aconfig.Account.Profile.TRIES,
                                              headers        = {'Authorization': 'Token ' + token})

                last_fetch_time = time.time()
                yield response.json()
    # ____________________________________________________________________________ . . .


    async def limits(self):
        pass
# =================================================================================================



class Transaction:
    async def withdarw(self):
        pass
    # ____________________________________________________________________________ . . .


    async def deposite(self):
        pass
# =================================================================================================





if __name__ == '__main__':

    async def live_fetch_market_price_test():
        market = Market(APIService())
        result = await anext(market.live_fetch_market_price('usdt', 'rls'))
        print(result)
    # asyncio.run(live_fetch_market_price_test())

    async def live_fetch_order_book_test():
        market = Market(APIService())
        asks, bids, midprice = await anext(market.live_fetch_order_book(httpx.AsyncClient(), 'usdt', 'irt'))
        print('asks_df:\n', asks, '\n\nbids_df:\n', bids, '\n\nmid_price:\n', midprice)
    # asyncio.run(live_fetch_order_book_test())



    async def fetch_orders_test():
        service = APIService()
        trade   = Trade(service)

        data = await anext(trade.fetch_orders(client = httpx.AsyncClient(),
                                            token  = User.TOKEN,     # type: ignore
                                            req_interval = nb.Endpoint.ORDERS_MI,
                                            max_rate = nb.Endpoint.ORDERS_RL,
                                            rate_period=nb.Endpoint.ORDERS_RP,
                                            status = 'all'))

        print(data)
    # asyncio.run(fetch_orders_test())

    async def fetch_positions_test():
        service = APIService()
        trade   = Trade(service)

        response = await trade.fetch_positions(client      = httpx.AsyncClient(),
                                            token       = User.TOKEN,    # type: ignore
                                            status      = 'active',
                                            page        = 1)
        print(response)
    # asyncio.run(fetch_positions_test())



    async def live_fetch_user_profile_test():
        account = Account(APIService())
        response = await anext(account.live_fetch_user_profile(User.TOKEN))    # type: ignore
        print(response)
    asyncio.run(live_fetch_user_profile_test())

    async def fetch_wallets_test():
        account = Account(APIService())

        response = await account.wallets(http_agent = httpx.AsyncClient(),
                                         token      = User.TOKEN,    # type: ignore
                                         drop_void  = True)

        print(response)
    # asyncio.run(fetch_wallets_test())

    async def live_fetch_portfolio_balance_test():
        account = Account(APIService())
        rls, usd = await anext(account.live_fetch_portfolio_balance())
        print('rial_balance:\t', rls, '\nusd_balance:\t', usd)
    # asyncio.run(live_fetch_portfolio_balance_test())

    async def fetch_balance_test():
        account = Account(APIService())

        response = await account.balance(http_agent = httpx.AsyncClient(),
                                        token      = User.TOKEN,    # type: ignore
                                        currency   = 'usdt')

        print(response)
    # asyncio.run(fetch_balance_test())



    async def cancel_all_orders_test():
        trade = Trade(APIService())

        response = await trade.cancel_all_orders(client = httpx.AsyncClient(),
                                                token  = User.TOKEN)    # type: ignore

        print(response)
    # asyncio.run(cancel_all_orders_test())

    async def close_position_test():
        trade = Trade(APIService())
        result = await trade.close_position(http_agent=httpx.AsyncClient(),
                                            token=User.TOKEN,    # type: ignore
                                            id='5053',
                                            execution='market',
                                            amount=0.0000089775,
                                            side='sell',
                                            src_currecy='btc',
                                            dst_currency='rls',
                                            price=360000003)
        
        print(result)
    # asyncio.run(close_position_test())

    async def close_all_positions_test():
        trade = Trade(APIService())
        results = await trade.close_all_positions(User.TOKEN)    # type: ignore
        print(results)
    # asyncio.run(close_all_positions_test())



    async def place_spot_limit_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_spot_limit_order(http_agent   = httpx.AsyncClient(),
                                                token        = User.TOKEN,    # type: ignore
                                                side         = 'buy',
                                                src_currency = 'btc',
                                                dst_currency = 'rls',
                                                amount       = 0.0006,
                                                price        = 9_998_000_000,
                                                client_oid   = 'orderTEST01')

        print(response)
    # asyncio.run(place_spot_limit_order_test())

    async def place_spot_market_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_spot_market_order(http_agent   = httpx.AsyncClient(),
                                                token        = User.TOKEN,    # type: ignore
                                                side         = 'buy',
                                                src_currency = 'btc',
                                                dst_currency = 'rls',
                                                amount       = 0.0006,
                                                client_oid   = 'orderTEST01')
        
        print(response)
    # asyncio.run(place_spot_market_order_test())

    async def place_spot_stop_limit_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_spot_stop_limit_order(http_agent   = httpx.AsyncClient(),
                                                    token        = User.TOKEN,    # type: ignore
                                                    side         = 'buy',
                                                    src_currency = 'btc',
                                                    dst_currency = 'rls',
                                                    amount       = 0.0006,
                                                    price        = 9_998_888_000,
                                                    stop_price   = 9_998_888_000,
                                                    client_oid   = 'orderTEST01')

        print(response)
    # asyncio.run(place_spot_stop_limit_order_test())

    async def place_spot_stop_market_order_test():
        service = APIService()
        trade = Trade(service)
        
        response = await trade.place_spot_stop_market_order(http_agent   = httpx.AsyncClient(),
                                                            token        = User.TOKEN,    # type: ignore
                                                            side         = 'buy',
                                                            src_currency = 'btc',
                                                            dst_currency = 'rls',
                                                            amount       = 0.0006,
                                                            stop_price   = 9_998_888_000,
                                                            client_oid   = 'orderTEST01')
        
        print(response)
    # asyncio.run(place_spot_stop_market_order_test())

    async def place_spot_oco_order_test():
        service = APIService()
        trade = Trade(service)
        
        response = await trade.place_spot_oco_order(http_agent     = httpx.AsyncClient(),
                                                    token          = User.TOKEN,    # type: ignore
                                                    side           = 'buy',
                                                    src_currency   = 'usdt',
                                                    dst_currency   = 'rls',
                                                    amount         = 50,
                                                    tp_price       = 570000,
                                                    sl_stop_price  = 590000,
                                                    sl_limit_price = 600000,
                                                    client_oid     = 'orderTest01')

        print(response)
    # asyncio.run(place_spot_oco_order_test())



    async def place_futures_limit_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_futures_limit_order(http_agent   = httpx.AsyncClient(),
                                                token        = User.TOKEN,    # type: ignore
                                                side         = 'buy',
                                                src_currency = 'usdt',
                                                dst_currency = 'rls',
                                                amount       = 50,
                                                price        = 58900,
                                                leverage     = 1,
                                                client_oid   = 'orderTest01')

        print(response)
    # asyncio.run(place_futures_limit_order_test())

    async def place_futures_market_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_futures_market_order(http_agent   = httpx.AsyncClient(),
                                                        token        = User.TOKEN,    # type: ignore
                                                        side         = 'buy',
                                                        src_currency = 'usdt',
                                                        dst_currency = 'rls',
                                                        amount       = 50,
                                                        leverage     = 1,
                                                        client_oid   = 'orderTest01')

        print(response)
    # asyncio.run(place_futures_market_order_test())

    async def place_futures_stop_limit_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_futures_stop_limit_order(http_agent   = httpx.AsyncClient(),
                                                            token        = User.TOKEN,    # type: ignore
                                                            side         = 'buy',
                                                            src_currency = 'usdt',
                                                            dst_currency = 'rls',
                                                            amount       = 50,
                                                            price        = 58900,
                                                            stop_price   = 58900,
                                                            leverage     = 1,
                                                            client_oid   = 'orderTest01')

        print(response)
    # asyncio.run(place_futures_stop_limit_order_test())

    async def place_futures_stop_market_order_test():
        service = APIService()
        trade = Trade(service)

        response = await trade.place_futures_stop_market_order(http_agent   = httpx.AsyncClient(),
                                                            token        = User.TOKEN,    # type: ignore
                                                            side         = 'buy',
                                                            src_currency = 'usdt',
                                                            dst_currency = 'rls',
                                                            amount       = 50,
                                                            stop_price   = 58900,
                                                            leverage     = 1,
                                                            client_oid   = 'orderTest01')

        print(response)
    # asyncio.run(place_futures_stop_market_order_test())

    async def place_futures_oco_order_test():
        service = APIService()
        trade = Trade(service)
        
        response = await trade.place_futures_oco_order(http_agent     = httpx.AsyncClient(),
                                                    token          = User.TOKEN,    # type: ignore
                                                    side           = 'buy',
                                                    src_currency   = 'usdt',
                                                    dst_currency   = 'rls',
                                                    amount         = 50,
                                                    tp_price       = 570000,
                                                    sl_stop_price  = 590000,
                                                    sl_limit_price = 600000,
                                                    leverage       = 1,
                                                    client_oid     = 'orderTest01')

        print(response)
    # asyncio.run(place_futures_oco_order_test())