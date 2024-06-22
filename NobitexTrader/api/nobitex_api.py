import time
import httpx
import asyncio
import numpy as np
from aiolimiter import AsyncLimiter

from NobitexTrader.api.api_service import APIService
from NobitexTrader.data.exchange import Nobitex as nb
from NobitexTrader.configs.config import MarketData as md


# =================================================================================================
class Market:
    def __init__(self, api_service: APIService, client: httpx.AsyncClient):
        self.service = api_service
        self.client = client
    # ____________________________________________________________________________ . . .


    async def kline(self,
                    symbol: str,
                    resolution: str,
                    end: str,
                    countback: str,
                    timeout: float,
                    tries_interval: float,
                    tries: int,
                    *,
                    start: str | None = None,
                    url: str = nb.URL.MAIN, 
                    endpoint: str = nb.Endpoint.OHLC) -> dict | None:
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
            'to': end,
            'countback': countback if start is None else None,
            'from': start
        }

        return await self.service.get(self.client, url, endpoint, timeout, tries_interval, tries, params=payload)
    # ____________________________________________________________________________ . . .


    async def live_kline(self,
                         symbol: str,
                         resolution: str,
                         countback: str,
                         max_retries,
                         timeout: float,
                         tries_interval: float,
                         tries: int,
                         max_interval: float,
                         max_rate: int,
                         rate_period: str = '60'):
        """
        Continuously fetches kline data for the last given candles.

        Parameters:
            
        Returns:
        """

        request_count = 0
        start_time = time.time()

        last_fetch_time = 0.0
        wait_time = max(0, max_interval - (time.time() - last_fetch_time))

        async with  self.client:
            async with AsyncLimiter(max_rate, int(rate_period)):
                while True:
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                    success = False
                    retry_count = 0

                    while not success and retry_count < max_retries:
                        try:
                            data = await self.kline(symbol,
                                                    resolution,
                                                    str(int(time.time())),
                                                    countback,
                                                    timeout,
                                                    tries_interval,
                                                    tries)
                            
                            success = True
                        except httpx.RequestError as err:
                            retry_count += 1
                            print(f"Request failed: {err}. Retrying {retry_count}/{max_retries}..")
                            await asyncio.sleep(0.1)  # Short delay before retrying

                    if not success:
                        print("Max retries reached. Skipping this request.")
                        continue

                    last_fetch_time = time.time()

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
    asyncio.run(oredr_test())

    market = Market(APIService(), httpx.AsyncClient())
    # asyncio.run(market.live_kline(md.OHLC.SYMBOL,
    #                               md.OHLC.RESOLUTION,
    #                               str(500),
    #                               3,
    #                               5.0,
    #                               nb.Endpoint.OHLC_MI,
    #                               3,
    #                               nb.Endpoint.OHLC_MI,
    #                               nb.Endpoint.OHLC_RL,
    #                               '60'))