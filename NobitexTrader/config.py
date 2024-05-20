from NobitexTrader.nobitex_data import *


class OHLC:
    SYMBOL: str = 'USDTIRT'
    RESOLUTION: str = '1'
    TO= int(CURRENT_TIME)
    FROM= 0
    COUNTBACK= 500
    PAGE= 1
    SIZE: int = 1000

class TRADES:
    SYMBOL: str = 'USDTIRT'

class supertrend:
    WINDOW=14
    FACTOR=3