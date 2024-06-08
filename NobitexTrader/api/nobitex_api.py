import time
import httpx
import asyncio
from aiolimiter import AsyncLimiter

from NobitexTrader.api.api_service import APIService
from NobitexTrader.data.exchange import Nobitex as nb
from NobitexTrader.configs.config import MarketData as md



# =================================================================================================
class Market:
    def __init__(self, api_service: APIService):
        self.service = api_service
    # ____________________________________________________________________________ . . .


    async def kline(self,
                    client: httpx.AsyncClient,
                    symbol: str,
                    resolution: str,
                    end: str,
                    countback: str,
                    timeout: float,
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

        return await self.service.get(client, url, endpoint, timeout, payload)
    # ____________________________________________________________________________ . . .


    async def live_kline(self,
                         client: httpx.AsyncClient,
                         symbol: str,
                         resolution: str,
                         countback: str,
                         max_retries,
                         timeout: float,
                         max_interval: float,
                         max_rate: str,
                         rate_period: str = '60',):
        """
        Continuously fetches kline data for the last given candles.

        Parameters:
            
        Returns:
        """
        
        market = Market(self.service)

        request_count = 0
        start_time = time.time()

        last_fetch_time = 0.0
        wait_time = max(0, max_interval - (time.time() - last_fetch_time))

        async with  client:
            async with AsyncLimiter(int(max_rate), int(rate_period)):
                while True:
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                    success = False
                    retry_count = 0

                    while not success and retry_count < max_retries:
                        try:
                            data = await market.kline(
                                client, symbol, resolution, str(int(time.time())), countback, timeout
                            )
                            success = True
                        except httpx.RequestError as err:
                            retry_count += 1
                            print(f"Request failed: {err}. Retrying {retry_count}/{max_retries}...")
                            await asyncio.sleep(0.1)  # Short delay before retrying

                    if not success:
                        print("Max retries reached. Skipping this request.")
                        continue

                    last_fetch_time = time.time()

                    request_count += 1
                    elapsed_time = time.time() - start_time
                    print(f"Request #{request_count} at {elapsed_time:.2f} seconds: {data}")
                    # print(data)

                    if elapsed_time >= 60:
                        print(f"Total requests in the last 60 seconds: {request_count}")
                        await asyncio.sleep(3)
                        start_time = time.time()
                        request_count = 0
# =================================================================================================


if __name__ == '__main__':
    market = Market(APIService())
    asyncio.run(market.live_kline(httpx.AsyncClient(),
                                  md.OHLC.SYMBOL,
                                  md.OHLC.RESOLUTION,
                                  str(500),
                                  3,
                                  5.0,
                                  int(nb.Endpoint.OHLC_MI),
                                  nb.Endpoint.OHLC_RL,
                                  '60'))