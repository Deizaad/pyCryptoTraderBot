import os
import numpy as np
from dotenv import load_dotenv

from NobitexTrader.configs.config import Order


# __all__ = ["API_KEY", "CURRENT_TIME", "BASE_URL", "TESTNET"]


class Nobitex:
    class USER:
        load_dotenv('.env')
        noneTOKEN_str = "Token is not configured"
        API_KEY = os.getenv('MAIN_TOKEN', noneTOKEN_str)    # DONE NO-001

    class URL:
        MAIN = 'https://api.nobitex.ir'
        TEST = 'https://testnetapi.nobitex.ir'

    class Endpoint:
        TRADES = '/v2/trades/'
        TRADES_MI: str = '4'    # Maximum Interval = 4s
        TRADES_RL: str = '15'    # Rate Limit: 15p/m

        OHLC = '/market/udf/history'
        OHLC_MI: str = '1'    # Maximum Interval = 1s
        OHLC_RL: str = '60'    # Rate Limit = 60p/m

        class Order:
            class Place:
                FUTURES = '/margin/orders/add'
                SPOT = '/market/orders/add'

                _conds = [Order.CATEGORY == 'futures',
                         Order.CATEGORY == 'spot']
                _choices = [FUTURES,
                           SPOT]
                endpoint = np.select(_conds, _choices)

    # class Symbol:
    #     USDTIRT = 'USDTIRT'

if __name__ == '__main__':
    print(Nobitex.USER.API_KEY)