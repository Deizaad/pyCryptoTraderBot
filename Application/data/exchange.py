import os
import sys
import numpy as np
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.configs.config import Order  # noqa: E402


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
        TRADES_MI: float = 4.0    # Maximum Interval = 4s
        TRADES_RL: int = 15    # Rate Limit = 15p/m
        TRADES_RP: int = 60    # Rate period = 60 second

        OHLC = '/market/udf/history'
        OHLC_MI: float = 1.0    # Maximum Interval = 1s
        OHLC_RL: int = 60    # Rate Limit = 60p/m
        OHLC_RP: int = 60    # Rate period = 60 second

        POSITIONS: str = '/positions/list'
        POSITIONS_MI: float = 2.0
        POSITIONS_RL: int = 30
        POSITIONS_RP: int = 60

        ORDERS: str = '/market/orders/list'
        ORDERS_MI: float = 2.0
        ORDERS_RL: int = 30
        ORDERS_RP: int = 60

        WALLETS: str = '/users/wallets/list'
        WALLETS_MI: float = 6.0
        WALLETS_RL: int = 20
        WALLETS_RP: int = 120

        class Order:
            class Place:
                FUTURES = '/margin/orders/add'
                FUTURES_MI: float = 6.0
                FUTURES_RL: int = 100
                FUTURES_RP: int = 600    # Rate period = 600 second

                SPOT = '/market/orders/add'
                SPOT_MI: float = 3
                SPOT_RL: int = 200
                SPOT_RP: int = 600  # Rate period = 600 second

                _conds = [Order.CATEGORY == 'futures',
                         Order.CATEGORY == 'spot']
                _choices = [FUTURES,
                           SPOT]
                endpoint = np.select(_conds, _choices)

    # class Symbol:
    #     USDTIRT = 'USDTIRT'

if __name__ == '__main__':
    print(Nobitex.USER.API_KEY)