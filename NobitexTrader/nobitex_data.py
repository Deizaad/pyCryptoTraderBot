import os
from dotenv import load_dotenv


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
        TRADES_RL = 4    # Rate Limit: 15p/m = 4s

        OHLC = '/market/udf/history'
        OHLC_RL = 1    # Rate Limt: 60p/m = 1s

        class Order:
            class Place:
                FUTURES = '/margin/orders/add'
                SPOT = '/market/orders/add'

    # class Symbol:
    #     USDTIRT = 'USDTIRT'

if __name__ == '__main__':
    print(Nobitex.USER.API_KEY)