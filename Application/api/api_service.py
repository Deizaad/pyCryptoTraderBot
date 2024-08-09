import sys
import httpx
import asyncio
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None



# =================================================================================================
class APIService:
    async def _request(self, 
                       client         : httpx.AsyncClient, 
                       method         : str,
                       url            : str, 
                       endpoint       : str, 
                       timeout        : float,
                       tries_interval : float,
                       tries          : int,
                       *,
                       params         : dict[str, str] | None = None, 
                       data           : dict[str, str] | None = None, 
                       headers        : dict[str, str] | None = None) -> dict:
        
        for attempt in range(tries):
            try:
                response = await client.request(method  = method, 
                                                url     = f"{url}{endpoint}", 
                                                params  = params, 
                                                json    = data, 
                                                headers = headers, 
                                                timeout = timeout)
                
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
                  client         : httpx.AsyncClient,
                  url            : str,
                  endpoint       : str,
                  timeout        : float,
                  tries_interval : float,
                  tries          : int,
                  *,
                  params         : dict[str, str] | None = None,
                  data           : dict[str, str] | None = None,
                  headers        : dict[str, str] | None = None):
        
        return await self._request(client         = client,
                                   method         = "GET",
                                   url            = url,
                                   endpoint       = endpoint,
                                   timeout        = timeout,
                                   tries_interval = tries_interval,
                                   tries          = tries,
                                   params         = params,
                                   data           = data,
                                   headers        = headers)
    # ____________________________________________________________________________ . . .


    async def post(self,
                   client         : httpx.AsyncClient,
                   url            : str,
                   endpoint       : str,
                   timeout        : float,
                   tries_interval : float,
                   tries          : int,
                   *,
                   data           : dict[str, str] | None = None,
                   headers        : dict[str, str] | None = None):
        
        return await self._request(client         = client,
                                   method         = "POST",
                                   url            = url,
                                   endpoint       = endpoint,
                                   timeout        = timeout,
                                   tries_interval = tries_interval,
                                   tries          = tries,
                                   data           = data,
                                   headers        = headers)
    # ____________________________________________________________________________ . . .


    async def put(self,
                  client         : httpx.AsyncClient,
                  url            : str,
                  endpoint       : str,
                  timeout        : float,
                  tries_interval : float,
                  tries          : int,
                  *,
                  data           : dict[str, str] | None = None):
        
        return await self._request(
            client, "POST", url, endpoint, timeout, tries_interval, tries, data=data
            )
    # ____________________________________________________________________________ . . .


    async def delete(self,
                     client         : httpx.AsyncClient,
                     url            : str,
                     endpoint       : str,
                     timeout        : float,
                     tries_interval : float,
                     tries          : int,
                     *,
                     data           : dict[str, str] | None = None
            ):
        
        return await self._request(
            client, "POST", url, endpoint, timeout, tries_interval, tries, data=data
            )
# =================================================================================================