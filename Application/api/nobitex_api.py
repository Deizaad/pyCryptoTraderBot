import os
import sys
import time
import httpx
import logging
import asyncio
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pydispatch import dispatcher    # type: ignore
from aiolimiter import AsyncLimiter
from persiantools.jdatetime import JalaliDateTime    # type: ignore

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

import Application.configs.admin_config as aconfig    # noqa: E402
from Application.utils.event_channels import Event    # noqa: E402
from Application.api.api_service import APIService    # noqa: E402
from Application.data.exchange import Nobitex as nb    # noqa: E402
from Application.configs.config import MarketData as md    # noqa: E402
from Application.data.data_tools import Tehran_timestamp    # noqa: E402


# =================================================================================================
class Market:
    def __init__(self, api_service: APIService, client: httpx.AsyncClient):
        self.service = api_service
        self.client = client
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
                    url: str = nb.URL.MAIN, 
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
            url (str, optional): The base URL for the request. Defaults to nb.URL.MAIN.
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

        wait_time: float = 0.0
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

                    wait_time = self._wait_time(max_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait_time) if (wait_time > 0) else None

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
        wait_time: float = 0.0
        last_fetch_time: float = 0.0

        start = self._last_timestamp(current_data)

        async with client:
            async with AsyncLimiter(max_rate, rate_period):
                while True:
                    wait_time = self._wait_time(max_interval, time.time(), last_fetch_time)
                    await asyncio.sleep(wait_time) if (wait_time > 0) else None

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


    def _wait_time(self, max_interval, current_time, last_fetch_time) -> float:
        wait_time = max(0, (max_interval - (current_time - last_fetch_time)))
        return wait_time
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
    # ____________________________________________________________________________ . . .


    async def live_kline(self,
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
        Continuously fetches kline data for the last given candles.

        Parameters:
            
        Returns:
        """
        # Sender constant for PyDispatcher:
        LIVE_KLINE = 'Live kline'

        last_fetch_time: float = 0.0
        wait_time: float = 0.0

        async with  self.client:
            async with AsyncLimiter(max_rate, rate_period):
                while True:
                    await asyncio.sleep(wait_time) if wait_time > 0 else None

                    try:
                        data = await self.kline(symbol, 
                                                resolution, 
                                                Tehran_timestamp(),
                                                timeout,
                                                tries_interval,
                                                tries,
                                                countback=required_candles)
                        
                        dispatcher.send(Event.SUCCESS_FETCH, LIVE_KLINE, kline=data)
                    except httpx.RequestError as err:
                        print(f"Request failed: {err}.")

                    last_fetch_time = time.time()
                    wait_time = self._wait_time(max_interval, time.time(), last_fetch_time)
    # ____________________________________________________________________________ . . .


    async def mock_kline(self,
                         symbol: str,
                         resolution: str,
                         countback: int,
                         max_retries,
                         timeout: float,
                         tries_interval: float,
                         tries: int,
                         max_interval: float,
                         max_rate: int,
                         rate_period: int = 60):
        """
        Continuously fetches kline data for the last given candles.

        Parameters:
            
        Returns:
        """
        # Sender constant for PyDispatcher:
        LIVE_KLINE = 'Live kline'

        request_count = 0
        start_time = time.time()

        last_fetch_time: float = 0.0
        wait_time: float = 0.0

        async with  self.client:
            async with AsyncLimiter(max_rate, rate_period):
                while True:
                    await asyncio.sleep(wait_time) if wait_time > 0 else None

                    success = False
                    retry_count = 0

                    while not success and retry_count < max_retries:
                        try:
                            data = await self.kline(symbol,
                                                    resolution,
                                                    int(time.time()),
                                                    timeout,
                                                    tries_interval,
                                                    tries,
                                                    countback=countback)
                            
                            dispatcher.send(Event.SUCCESS_FETCH, LIVE_KLINE, kline=data)
                            success = True
                        except httpx.RequestError as err:
                            retry_count += 1
                            print(f"Request failed: {err}. Retrying {retry_count}/{max_retries}..")
                            await asyncio.sleep(0.1)  # Short delay before retrying

                    if not success:
                        print("Max retries reached. Skipping this request.")
                        continue

                    last_fetch_time = time.time()
                    wait_time = self._wait_time(max_interval, time.time(), last_fetch_time)

                    request_count += 1
                    elapsed_time = time.time() - start_time
                    print(f"Request #{request_count} at {elapsed_time:.2f}s: {data}")

                    if elapsed_time >= 60:
                        print(f"Total requests in the last 60 seconds: {request_count}")
                        await asyncio.sleep(3)
                        start_time = time.time()
                        request_count = 0
# =================================================================================================



# =================================================================================================
class Order:
    def __init__(self, api_service: APIService):
        self.service = api_service
    # ____________________________________________________________________________ . . .


    async def place(self,
                    client: httpx.AsyncClient,
                    type : str,
                    execution : str,
                    price : float,
                    srcCurrency : str,
                    dstCurrency : str,
                    amount : float,
                    *,
                    timeout: float,
                    try_interval: float,
                    tries: int,
                    token: str = nb.USER.API_KEY,
                    url: str = nb.URL.MAIN,
                    mode : str | None = None,
                    stopPrice : float = np.nan,
                    stopLimitPrice : float = np.nan,
                    leverage : float = np.nan,
                    clientOrderId : str = 'null'):
        """
        Parameters:
            type (str): Trade direction.
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

        Returns (dict): State of order whether it filled or not.
        """
        endpoint = nb.Endpoint.Order.Place.endpoint

        payload = {
            'execution': execution,
            'mode': mode,
            'srcCurrency': srcCurrency,
            'dstCurrency': dstCurrency,
            'type': type,
            'leverage': leverage,
            'amount': amount,
            'price': price,
            'stopPrice': stopPrice,
            'stopLimitPrice': stopLimitPrice,
            'clientOrderId': clientOrderId
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
        
        response = await self.service.post(
            client, url, endpoint, timeout, try_interval, tries, data=payload, headers=headers
            )

        return response
    # ____________________________________________________________________________ . . .


    async def positions(self, client: httpx.AsyncClient, category: str, srcCurrency: str, dstCurrency: str, status: str):
        """
        Parameters:
            category (str): The category of market. Eather "spot" or "futures".
        """
        if category != 'spot' and category != 'futures':
            raise ValueError(f"""Wrong category of "{category}" is provided. It most be eather
                             "spot" or "futures".""")
        
        match category:
            case 'spot':
                payload: dict = {}
                endpoint: str = nb.Endpoint.ORDERS
                tries_interval: float = nb.Endpoint.ORDERS_MI
            case 'futures':
                payload: dict = {'srcCurrency': srcCurrency,
                                 'dstCurrency': dstCurrency,
                                 'status': status}

                endpoint: str = nb.Endpoint.POSITIONS
                tries_interval: float = nb.Endpoint.POSITIONS_MI

        data = await self.service.get(client=client,
                                      url=nb.URL.MAIN,
                                      endpoint=endpoint,
                                      timeout=aconfig.Order.Positions.TIMEOUT,
                                      tries_interval=tries_interval,
                                      tries=aconfig.Order.Positions.TRIES,
                                      params=payload)
        
        return data
    # ____________________________________________________________________________ . . .


    async def status(self):
        pass
    # ____________________________________________________________________________ . . .


    async def cancel(self):
        pass
    # ____________________________________________________________________________ . . .


    async def close_all(self):
        pass
# =================================================================================================



# =================================================================================================
class Account:
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



async def oredr_test():
    service = APIService()
    order = Order(service)

    async with httpx.AsyncClient() as client:
        response = await order.place(client,
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


if __name__ == '__main__':
    # asyncio.run(oredr_test())

    market = Market(APIService(), httpx.AsyncClient())
    # asyncio.run(market.mock_kline(md.OHLC.SYMBOL,
    #                               md.OHLC.RESOLUTION,
    #                               500,
    #                               3,
    #                               5.0,
    #                               nb.Endpoint.OHLC_MI,
    #                               3,
    #                               nb.Endpoint.OHLC_MI,
    #                               nb.Endpoint.OHLC_RL,
    #                               nb.Endpoint.OHLC_RP))
    
    asyncio.run(market.live_kline(symbol=md.OHLC.SYMBOL,
                                  resolution=md.OHLC.RESOLUTION,
                                  required_candles=md.OHLC.SIZE,
                                  timeout=5.0,
                                  tries_interval=nb.Endpoint.OHLC_MI,
                                  tries=3,
                                  max_interval=nb.Endpoint.OHLC_MI,
                                  max_rate=nb.Endpoint.OHLC_RL,
                                  rate_period=nb.Endpoint.OHLC_RP))