import os
import sys
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

import asyncio
import httpx

# from NobitexTrader.logging import logger



# =================================================================================================
class APIService:
    async def _request(self, 
                       client: httpx.AsyncClient, 
                       method: str, 
                       url: str, 
                       endpoint: str, 
                       timeout: float,
                       tries_interval: float,
                       tries: int,
                       *,
                       params=None, 
                       data=None, 
                       headers=None) -> dict:
        
        for attempt in range(tries):
            try:
                response = await client.request(method, 
                                                f"{url}{endpoint}", 
                                                params=params, 
                                                json=data, 
                                                headers=headers, 
                                                timeout=timeout)
                
                if response.status_code == 200:
                    return response.json()
                # else:
                #     logger.error(f"API request failed: {response.status_code} {response.text}")
            except httpx.HTTPError as err:
                print(err)
                # logger.error(f"HTTP request error: {err}")
                if attempt < tries - 1:
                    await asyncio.sleep(tries_interval)
            except Exception as err:
                print(err)
                # logger.error(f"Unexpected error: {err}")
                if attempt < tries - 1:
                    await asyncio.sleep(tries_interval)
        # raise Exception("API request failed after retries")
        empty_data: dict = {}
        return  empty_data
    # ____________________________________________________________________________ . . .


    async def get(self,
                  client: httpx.AsyncClient,
                  url: str,
                  endpoint: str,
                  timeout: float,
                  tries_interval: float,
                  tries: int,
                  *,
                  params: dict[str, str] | None = None):
        
        return await self._request(
            client, "GET", url, endpoint, timeout, tries_interval, tries, params=params
            )
    # ____________________________________________________________________________ . . .


    async def post(self,
                   client: httpx.AsyncClient,
                   url,
                   endpoint,
                   timeout,
                   interval,
                   tries,
                   *,
                   data,
                   headers):
        
        return await self._request(
            client, "POST", url, endpoint, timeout, interval, tries, data=data, headers=headers
            )
    # ____________________________________________________________________________ . . .


    async def put(
            self, client: httpx.AsyncClient, url, endpoint, timeout, interval, tries, *, data=None
            ):
        
        return await self._request(
            client, "POST", url, endpoint, timeout, interval, tries, data=data
            )
    # ____________________________________________________________________________ . . .


    async def delete(
            self, client: httpx.AsyncClient, url, endpoint, timeout, interval, tries, *, data=None
            ):
        
        return await self._request(
            client, "POST", url, endpoint, timeout, interval, tries, data=data
            )
# =================================================================================================