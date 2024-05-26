import httpx
import numpy as np

from NobitexTrader.config import Order as ord
from NobitexTrader.exchange import Nobitex as nb


class Order():
    def place(self,
              type : str,
              execution : str,
              price : float,
              srcCurrency : str,
              dstCurrency : str,
              amount : float,
              mode : str | None = None,
              stopPrice : float = np.nan,
              stopLimitPrice : float = np.nan,
              leverage : float = np.nan,
              clientOrderId : str = 'null'):
        """
        Args:
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

        Returns:
        """

        endpoint_conditions = [
            ord.CATEGORY == 'futures',
            ord.CATEGORY == 'spot'
        ]
        endpoint_choice = [
            nb.Endpoint.Order.Place.FUTURES,
            nb.Endpoint.Order.Place.SPOT
        ]
        endpoint = np.select(endpoint_conditions, endpoint_choice)

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
            if key == 'execution' and mode:
                return False
            if value == 'null':
                return False
            return True
            # return value is not None and not (isinstance(value, float) and np.isnan(value)) and (key != 'execution' or not mode)

        payload = {key: value for key, value in payload.items() if is_valid_key_value(key, value)}

        headers = {'Authorization': 'Token ' + nb.USER.API_KEY}
        
        response = httpx.request("POST", f'{nb.URL.MAIN}{endpoint}', headers=headers, data=payload)

        return response.json()


if __name__ == '__main__':
    order = Order()
    response = order.place('sell', 'limit', 38800, 'btc', 'usdt', 0.0016)
    print(response)