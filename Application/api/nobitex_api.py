import sys
import time
import httpx
import logging
import asyncio
import numpy as np
import pandas as pd
from dotenv import dotenv_values
from aiolimiter import AsyncLimiter
from persiantools.jdatetime import JalaliDateTime    # type: ignore

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.data.user import User    # noqa: E402
from Application.api.utils import wait_time    # noqa: E402
import Application.configs.admin_config as aconfig    # noqa: E402
from Application.api.api_service import APIService    # noqa: E402
from Application.data.exchange import Nobitex as nb    # noqa: E402
# from Application.configs.config import MarketData as md    # noqa: E402
from Application.data.data_tools import parse_orders,\
                                        parse_positions,\
                                        Tehran_timestamp,\
                                        parse_wallets_to_df    # noqa: E402



# =================================================================================================
class Market:
    def __init__(self, api_service: APIService, client: httpx.AsyncClient):
        self.service = api_service
        self.client = client
    # ____________________________________________________________________________ . . .


    async def fetch_market_price(self,
                                 http_agent: httpx.AsyncClient,
                                 src_currency: str,
                                 dst_currency: str) -> float | int:
        """
        Fetches market price for given trading pair.

        Parameters:
            http_agent (AsyncClient): The HTTP agent.
            src_currecy (str): Source currency.
            dst_currency (str): Destination currency is eather 'usdt' | 'rls'.

        Returns:
            market_price (float): Market price for givan trading pair.
        """
        payload = {'srcCurrency': src_currency,
                   'dstCurrency': dst_currency}
        
        data = await self.service.get(client         = http_agent,
                                      url            = nb.URL,
                                      endpoint       = nb.Endpoint.MARKET_STATS,
                                      timeout        = aconfig.OHLC.TIMEOUT,
                                      tries_interval = nb.Endpoint.MARKET_STATS_MI,
                                      tries          = aconfig.OHLC.TRIES,
                                      params         = payload)
        
        market_price = data['stats'][f'{src_currency}-{dst_currency}']['latest']
        if '.' in str(market_price):
            market_price = float(market_price)
        else:
            market_price = int(market_price)

        return market_price
    # ____________________________________________________________________________ . . .


    async def kline(self,
                    symbol: str,
                    resolution: str,
                    end: int,
                    timeout: float,
                    tries_interval: float,
                    tries: int,
                    *,
                    page: int | None = None,
                    countback: int | None = None,
                    start: int | None = None,
                    url: str = nb.URL, 
                    endpoint: str = nb.Endpoint.OHLC) -> dict:
        """
        Fetches Kline data for a given symbol.

        Parameters:
            client (AsyncClient): The HTTP client used to make the request.
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

        data = await self.service.get(client=self.client,
                                      url=url,
                                      endpoint=endpoint,
                                      timeout=timeout,
                                      tries_interval=tries_interval,
                                      tries=tries,
                                      params=payload)    # type: ignore

        return data
    # ____________________________________________________________________________ . . .


    async def initiate_kline(self,
                             client: httpx.AsyncClient,
                             symbol: str,
                             resolution: str,
                             required_candles: int,
                             timeout: float,
                             tries_interval: float,
                             tries: int):

        async with client:
            data = await self.kline(symbol,
                                    resolution,
                                    Tehran_timestamp(),
                                    timeout,
                                    tries_interval,
                                    tries,
                                    countback=required_candles)
                
        return data
    # ____________________________________________________________________________ . . .


    async def populate_kline(self,
                             client: httpx.AsyncClient,
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

        async with client:
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

                    data = await self.kline(symbol,
                                            resolution,
                                            end,
                                            timeout,
                                            tries_interval,
                                            tries,
                                            countback=countback)
                    
                    last_fetch_time = time.time()
                    fetched_count += len(data['t'])
                    
                    yield data
    # ____________________________________________________________________________ . . .


    async def update_kline(self,
                           client: httpx.AsyncClient,
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

        async with client:
            async with AsyncLimiter(max_rate, rate_period):
                while True:
                    wait = wait_time(max_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait) if (wait > 0) else None

                    new_data = await self.kline(symbol         = symbol,
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
            logging.error('Inside "_prior_timestamp()" method of "nobitex_api.Market" class: ',err)
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


    async def place_order(self,
                          client         : httpx.AsyncClient,
                          side           : str,
                          execution      : str,
                          price          : float,
                          srcCurrency    : str,
                          dstCurrency    : str,
                          amount         : float,
                          *,
                          timeout        : float,
                          try_interval   : float,
                          tries          : int,
                          token          : str = User.TOKEN,    # type: ignore
                          url            : str = nb.URL,
                          mode           : str | None = None,
                          stopPrice      : float = np.nan,
                          stopLimitPrice : float = np.nan,
                          leverage       : float = np.nan,
                          clientOrderId  : str = 'null'):
        """
        Places normal orders.

        Parameters:
            side (str): Trade direction.
                Value: 'buy' | 'sell'

            execution (str): Method of trade execution.
                Value: 'limit' | 'market' | 'stop_limit' | 'stop_market'

            price (float): Order price.

            srcCurrency (str): Source currency.
                Value: Refer to possible currencies.

            dstCurrency (str): Detination currency.
                Value: 'usdt' | 'rls'

            amount (float): Position size.

            mode (str): Only defined for oco orders.
                Value: 'oco' | None

            stopPrice (float): Only defined if 'execution' is 'stop_limit' or 'stop_market',
                or for oco orders to set 'stop_market'.

            stopLimitPrice (float): Only defined for oco orders to set 'stop_limit'.

            leverage (float): The leverage value.
                Default: 1

            clientOrderId (str): The order id that can be set.
                Default: 'null'

        Returns:
            request_response (dict): State of order whether it filled or not.
        """
        endpoint = nb.Endpoint.Order.Place.endpoint

        payload = {
            'execution'     : execution,
            'mode'          : mode,
            'srcCurrency'   : srcCurrency,
            'dstCurrency'   : dstCurrency,
            'type'          : side,
            'leverage'      : str(leverage),
            'amount'        : str(amount),
            'price'         : str(price),
            'stopPrice'     : str(stopPrice),
            'stopLimitPrice': str(stopLimitPrice),
            'clientOrderId' : clientOrderId
        }

        def is_valid_key_value(key, value):
            """
            Check if the key-value pair should be included in the payload.

            Args:
                key (str): The key to check.
                value (any): The value to check.

            Returns:
                bool: True if the key-value pair is valid, False otherwise.            
            """
            if value is None:
                return False
            if isinstance(value, float) and np.isnan(value):
                return False
            if value == 'null':
                return False
            if key == 'execution' and mode:    # Ignores 'execution' if 'mode' provided (oco oredr)
                return False
            
            return True

        payload = {key: value for key, value in payload.items() if is_valid_key_value(key, value)}
        headers = {'Authorization': 'Token ' + token}
        
        response = await self.service.post(    # TEMPORARY DEVELOPMENT
            client, url, endpoint, timeout, try_interval, tries, data=payload, headers=headers # type: ignore
            )

        return response
    # ____________________________________________________________________________ . . .


    async def _base_place_order(self,
                               http_agent   : httpx.AsyncClient,
                               token        : str,
                               environment  : str,
                               execution    : str,
                               side         : str,
                               src_currency : str,
                               dst_currency : str,
                               amount       :float,
                               **kwargs):
        """
        This is the base order placement method that gonna be called by other child methods.

        Parameters:
        """
        headers = {'Authorization': 'Token ' + token}
        payload: dict  = {'type'          : side,
                          'execution'     : execution,  # IMPELEMENT DEFAULT VALUES FOR .get FUNCTIONS.
                          'srcCurrency'   : src_currency,
                          'dstCurrency'   : dst_currency,
                          'amount'        : str(amount)}   # Implement a function to be called here to correct the "price" and "amount" floating point numbers.

        if execution == 'limit' or execution == 'stop_limit':
            payload['price'] = str(kwargs.get('price'))

        if execution == 'stop_limit' or execution == 'stop_market':
            payload['stopPrice'] = str(kwargs.get('stop_price'))

        if kwargs.get('client_oid'):
            payload['clientOrderId'] = kwargs.get('client_oid')


        if environment != 'spot' and environment != 'futures':
            raise ValueError(f'Wrong value of {environment} is provided for "environment", it '\
                             'most be eather "spot" | "futures".')

        elif environment == 'spot':
            endpoint       = nb.Endpoint.PLACE_SPOT_ORDER
            tries_interval = nb.Endpoint.PLACE_SPOT_ORDER_MI

        elif environment == 'futures':
            endpoint       = nb.Endpoint.PLACE_FUTURES_ORDER
            tries_interval = nb.Endpoint.PLACE_FUTURES_ORDER_MI
            payload['leverage'] = str(kwargs.get('leverage'))
            print(payload)


        response = await self.service.post(client         = http_agent,
                                           url            = nb.URL,
                                           endpoint       = endpoint,
                                           timeout        = aconfig.Trade.Place.PlaceOrder.TIMEOUT,
                                           tries_interval = tries_interval,
                                           tries          = aconfig.Trade.Place.PlaceOrder.TRIES,
                                           data           = payload,
                                           headers        = headers)

        return response
    # ____________________________________________________________________________ . . .





    async def place_spot_limit(self,
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


    async def place_spot_market(self,
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


    async def place_spot_stop_limit(self,
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


    async def place_spot_stop_market(self,
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





    async def place_futures_limit(self,
                                  http_agent   : httpx.AsyncClient,
                                  token        : str,
                                  side         : str,
                                  src_currency : str,
                                  dst_currency : str,
                                  amount       : float,
                                  price        : float,
                                  leverage     : float):
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
                                                leverage     = leverage)
        
        return response
    # ____________________________________________________________________________ . . .


    async def place_futures_market(self,
                                   http_agent   : httpx.AsyncClient,
                                   side         : str,
                                   src_currency : str,
                                   dst_currency : str,
                                   amount       : float,
                                   client_oid   : str):
        """
        Places limit order on futures market.
        """
        # Fetch market price for trading pair
        market = Market(APIService(), httpx.AsyncClient())
        market_price = await market.fetch_market_price(http_agent   = httpx.AsyncClient(),
                                                       src_currency = src_currency,
                                                       dst_currency = dst_currency)

        response = await self._base_place_order(http_agent   = http_agent,
                                                environment  = 'futures',
                                                side         = side,
                                                execution    = 'market',
                                                src_currency = src_currency,
                                                dst_currency = dst_currency,
                                                amount       = amount,
                                                price        = market_price,
                                                client_oid   = client_oid)

        return response
    # ____________________________________________________________________________ . . .


    async def place_futures_stop_limit(self):
        """
        Places stop_limit order on futures market.
        """
        pass
    # ____________________________________________________________________________ . . .





    async def place_oco_order(self):
        """
        Places oco (one-cancels-other) orders.

        Parameters:

        """
        pass
    # ____________________________________________________________________________ . . .





    async def fetch_orders(self,
                           client       : httpx.AsyncClient,
                           token        : str,
                           *,
                           req_interval: float,
                           max_rate    : int,
                           rate_period : int,
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

                data = await self.service.get(**params, client=client)

                last_fetch_time = time.time()
                orders_df = parse_orders(data)
                has_next: bool = data['hasNext']
                payload['page']= str(2)

                while has_next:
                    await limiter.acquire()
                    wait = wait_time(req_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait) if (wait > 0) else None

                    new_data = await self.service.get(**params, client=client)

                    last_fetch_time = time.time()
                    has_next = new_data['hasNext']
                    payload['page'] = str(int(payload['page']) + 1)

                    new_orders_df = parse_orders(new_data)
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

        data = await self.service.get(client         = client,
                                      url            = nb.URL,
                                      endpoint       = nb.Endpoint.POSITIONS,
                                      timeout        = aconfig.Trade.Fetch.Positions.TIMEOUT,
                                      tries_interval = nb.Endpoint.POSITIONS_MI,
                                      tries          = aconfig.Trade.Fetch.Positions.TRIES,
                                      data           = payload,
                                      headers        = headers)

        return data
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

            response = self.service.post(client         = http_agent,
                                         url            = nb.URL,
                                         endpoint       = nb.Endpoint.UPDATE_STATUS,
                                         timeout        = aconfig.Trade.Place.CancelOrders.TIMEOUT,
                                         tries_interval = nb.Endpoint.UPDATE_STATUS_MI,
                                         tries          = aconfig.Trade.Place.CancelOrders.TRIES,
                                         data           = payload,
                                         headers        = headers)

            return response

        except ValueError as err:
            logging.error(f'Missing parameter for "cancel_pending_order()" method: {err}')
            return {}
        except Exception as err:
            logging.error(f'Inside "nobitex_api.Trade.cancel_pending_order()" method: {err}')
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

        return 'succeeded' if response['status'] == 'ok' else 'failed'
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

            return response
        except ValueError as err:
            logging.error(f'Inside "nobitex_api.Trade.close_position()" method: {err}')
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
            logging.info('There are no active positions to be closed!')
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
        market = Market(APIService(), httpx.AsyncClient())
        market_prices: dict = {}
        for src, dst in positions_pairs:
            market_prices[f'{src}-{dst}'] = await market.fetch_market_price(
                http_agent   = httpx.AsyncClient(),
                src_currency = src,
                dst_currency = dst
            )


        # Prepare coroutines for closing positions
        logging.info(f'There are "{positions_df.size}" positions to be closed: \n'\
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
                logging.error('Failed to prepare coroutine for closing the position '\
                              f'{position['id']}: {str(err)}')


        # Attempt to send 'close_position' requests
        results = await asyncio.gather(*coroutines, return_exceptions=True)


        # Process results and handle any exceptions
        close_results: list = []
        for position, result in zip(positions_df.to_dict('records'), results):
            if isinstance(result, Exception) or result.get('status') == 'failed':  # type: ignore
                logging.error(f'Failed to close position {position["id"]}: {str(result)}')
                close_results.append({'id': position['id'],
                                      'status': 'failed',
                                      'error': str(result)})

            else:
                logging.info(f'Successfully closed position "{position['id']}"')
                close_results.append({'id': position['id'],
                                      'status': 'success',
                                      'response': result})

        if all(result['status'] == 'success' for result in close_results):
            return 'succeeded'
        else:
            return 'failed'
# =================================================================================================



# =================================================================================================
class Account:

    async def wallets(self,
                      client: httpx.AsyncClient,
                      token: str,
                      environment: str,
                      drop_void: bool = True) -> pd.DataFrame:
        """
        Fetches user's wallets for given market environment.

        Parameters:
            client (httpx.AsyncClient): HTTP client.
            token (str): Client's API token.
            environment (str): Market environment. Most be eather "spot" or "margin".
            drop_void (bool): Excludes wallets with zero balance.

        Returns (DataFrame): Client's wallets data.
        """
        payload: dict = {'type': environment}
        headers: dict = {'Authorization': 'Token ' + token}

        api = APIService()
        data = await api.get(client         = client,
                             url            = nb.URL,
                             endpoint       = nb.Endpoint.WALLETS,
                             timeout        = aconfig.Account.Wallets.TIMEOUT,
                             tries_interval = nb.Endpoint.WALLETS_MI,
                             tries          = aconfig.Account.Wallets.TRIES,
                             data           = payload,
                             headers        = headers)

        df = parse_wallets_to_df(raw_wallets=data, drop_void=drop_void)

        return df
    # ____________________________________________________________________________ . . .


    async def balance(self, client: httpx.AsyncClient, token: str, currency: str):
        """
        Fetches the balance of specific currency for user.

        Parameters:
            client (httpx.AsyncClient): HTTP client.
            token (str): Client's API token.
            currency (str): currency to get it's balance.

        Returns ():
        """
        payload: dict = {'currency': currency}
        headers: dict = {'Authorization': 'Token ' + token}

        api = APIService()
        data = await api.post(client         = client,
                              url            = nb.URL,
                              endpoint       = nb.Endpoint.BALANCE,
                              timeout        = aconfig.Account.Balance.TIMEOUT,
                              tries_interval = nb.Endpoint.BALANCE_MI,
                              tries          = aconfig.Account.Balance.TRIES,
                              data           = payload,
                              headers        = headers)

        return data
    # ____________________________________________________________________________ . . .


    async def info(self):
        pass
    # ____________________________________________________________________________ . . .


    async def limits(self):
        pass
# =================================================================================================



# =================================================================================================
class Transaction:
    async def withdarw(self):
        pass
    # ____________________________________________________________________________ . . .


    async def deposite(self):
        pass
# =================================================================================================



async def fetch_market_price_test():
    market = Market(APIService(), httpx.AsyncClient())
    result = await market.fetch_market_price(httpx.AsyncClient(), 'btc', 'rls')
    print(result)


async def oredr_test():
    service = APIService()
    trade = Trade(service)

    response = await trade.place_order(httpx.AsyncClient(),
                                       'sell',
                                       'limit',
                                       38800,
                                       'btc',
                                       'usdt',
                                       0.0016,
                                       timeout=3,
                                       try_interval=nb.Endpoint.Order.Place.FUTURES_MI,
                                       tries=1)

    print(response)

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

async def fetch_positions_test():
    service = APIService()
    trade   = Trade(service)

    response = await trade.fetch_positions(client      = httpx.AsyncClient(),
                                           token       = User.TOKEN,    # type: ignore
                                           status      = 'active',
                                           page        = 1)
    print(response)


async def fetch_wallets_test():
    account = Account()

    response = await account.wallets(client      = httpx.AsyncClient(),
                                     token       = User.TOKEN,    # type: ignore
                                     environment = 'margin',
                                     drop_void   = True)

    print(response)

async def fetch_balance_test():
    account = Account()

    response = await account.balance(client   = httpx.AsyncClient(),
                                     token    = User.TOKEN,    # type: ignore
                                     currency = 'rls')

    print(response)


async def cancel_all_orders_test():
    trade = Trade(APIService())

    response = await trade.cancel_all_orders(client = httpx.AsyncClient(),
                                             token  = User.TOKEN)    # type: ignore

    print(response)

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

async def close_all_positions_test():
    trade = Trade(APIService())
    results = await trade.close_all_positions(User.TOKEN)    # type: ignore
    print(results)


async def place_spot_limit_order_test():
    service = APIService()
    trade = Trade(service)

    response = await trade.place_spot_limit(http_agent   = httpx.AsyncClient(),
                                            token        = User.TOKEN,    # type: ignore
                                            side         = 'buy',
                                            src_currency = 'btc',
                                            dst_currency = 'rls',
                                            amount       = 0.0006,
                                            price        = 9_998_000_000,
                                            client_oid   = 'orderTEST01')

    print(response)

async def place_spot_market_order_test():
    service = APIService()
    trade = Trade(service)

    response = await trade.place_spot_market(http_agent   = httpx.AsyncClient(),
                                             token        = User.TOKEN,    # type: ignore
                                             side         = 'buy',
                                             src_currency = 'btc',
                                             dst_currency = 'rls',
                                             amount       = 0.0006,
                                             client_oid   = 'orderTEST01')
    
    print(response)

async def place_spot_stop_limit_order_test():
    service = APIService()
    trade = Trade(service)

    response = await trade.place_spot_stop_limit(http_agent   = httpx.AsyncClient(),
                                                 token        = User.TOKEN,    # type: ignore
                                                 side         = 'buy',
                                                 src_currency = 'btc',
                                                 dst_currency = 'rls',
                                                 amount       = 0.0006,
                                                 price        = 9_998_888_000,
                                                 stop_price   = 9_998_888_000,
                                                 client_oid   = 'orderTEST01')

    print(response)

async def place_spot_stop_market_order_test():
    service = APIService()
    trade = Trade(service)
    
    response = await trade.place_spot_stop_market(http_agent   = httpx.AsyncClient(),
                                                  token        = User.TOKEN,    # type: ignore
                                                  side         = 'buy',
                                                  src_currency = 'btc',
                                                  dst_currency = 'rls',
                                                  amount       = 0.0006,
                                                  stop_price   = 9_998_888_000,
                                                  client_oid   = 'orderTEST01')
    
    print(response)


async def place_futures_limit_order_test():
    service = APIService()
    trade = Trade(service)

    response = await trade.place_futures_limit(http_agent   = httpx.AsyncClient(),
                                               token        = User.TOKEN,    # type: ignore
                                               side         = 'buy',
                                               src_currency = 'usdt',
                                               dst_currency = 'irt',
                                               amount       = 50,
                                               price        = 58900,
                                               leverage     = 1)

    print(response)

if __name__ == '__main__':
    # asyncio.run(fetch_market_price_test())
    # asyncio.run(oredr_test())

    # asyncio.run(fetch_orders_test())
    # asyncio.run(fetch_positions_test())

    # asyncio.run(fetch_wallets_test())
    # asyncio.run(fetch_balance_test())

    # asyncio.run(cancel_all_orders_test())
    # asyncio.run(close_position_test())
    # asyncio.run(close_all_positions_test())

    # asyncio.run(place_spot_limit_order_test())
    # asyncio.run(place_spot_market_order_test())
    # asyncio.run(place_spot_stop_limit_order_test())
    # asyncio.run(place_spot_stop_market_order_test())

    asyncio.run(place_futures_limit_order_test())