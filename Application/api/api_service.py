import sys
import httpx
import asyncio
import logging
from dotenv import dotenv_values

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.logs import get_logger, get_log_level # noqa: E402


# Initializing the logger
# TPL_logs stands for Trading Platforms Linkage Logs
TPL_logs : logging.Logger = get_logger(logger_name='TPL_logs', log_level=get_log_level('TPL'))


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
                       headers        : dict[str, str] | None = None) -> httpx.Response:
        
        for attempt in range(tries):
            try:
                response = await client.request(method  = method, 
                                                url     = f"{url}{endpoint}", 
                                                params  = params, 
                                                json    = data, 
                                                headers = headers, 
                                                timeout = timeout)
                
                print('request object:\t', response.request)
                print('request data:\t', data)
                print('response:\t', response)
                print('response dict:\t', response.json())
                return response

            except httpx.HTTPError as err:
                print(err)
                TPL_logs.error(f"HTTP request error: {err}")
                if attempt < tries - 1:
                    await asyncio.sleep(tries_interval)

            except Exception as err:
                print(err)
                TPL_logs.error(f"Unexpected error: {err}")
                if attempt < tries - 1:
                    await asyncio.sleep(tries_interval)

        raise  httpx.NetworkError('Inside _request method of APIService class:'
                                  '\n\tAPI request failed after retries')
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
                  headers        : dict[str, str] | None = None) -> httpx.Response:
        
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
                   headers        : dict[str, str] | None = None) -> httpx.Response:
        
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
                  data           : dict[str, str] | None = None) -> httpx.Response:
        
        return await self._request(
            client, "POST", url, endpoint, timeout, tries_interval, tries, data=data)
    # ____________________________________________________________________________ . . .


    async def delete(self,
                     client         : httpx.AsyncClient,
                     url            : str,
                     endpoint       : str,
                     timeout        : float,
                     tries_interval : float,
                     tries          : int,
                     *,
                     data           : dict[str, str] | None = None) -> httpx.Response:
        
        return await self._request(
            client, "POST", url, endpoint, timeout, tries_interval, tries, data=data)
# =================================================================================================