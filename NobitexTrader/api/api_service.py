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
                       params=None, 
                       data=None, 
                       headers=None, 
                       tries=3) -> dict | None:
        
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
                # logger.error(f"HTTP request error: {err}")
                if attempt < tries - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as err:
                # logger.error(f"Unexpected error: {err}")
                if attempt < tries - 1:
                    await asyncio.sleep(2 ** attempt)
        # raise Exception("API request failed after retries")
        empty_data: dict = {}
        return  empty_data
    # ____________________________________________________________________________ . . .


    async def get(self, client: httpx.AsyncClient, url, endpoint, timeout, params=None):
        return await self._request(client, "GET", url, endpoint, timeout, params=params)
    # ____________________________________________________________________________ . . .


    async def post(self, client: httpx.AsyncClient, url, endpoint, timeout, data, headers, tries):
        return await self._request(client, "POST", url, endpoint, timeout, headers=headers, data=data, tries=tries)
    # ____________________________________________________________________________ . . .


    async def put(self, client: httpx.AsyncClient, url, endpoint, timeout, data=None):
        return await self._request(client, "POST", url, endpoint, timeout, data=data)
    # ____________________________________________________________________________ . . .


    async def delete(self, client: httpx.AsyncClient, url, endpoint, timeout, data=None):
        return await self._request(client, "POST", url, endpoint, timeout, data=data)
# =================================================================================================