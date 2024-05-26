from time import time

class OHLC:
    SYMBOL: str = 'USDTIRT'
    RESOLUTION: str = '1'
    TO= int(time())
    FROM= 0
    COUNTBACK= 500
    PAGE= 1
    SIZE: int = 1000

class TRADES:
    SYMBOL: str = 'USDTIRT'

class Supertrend:
    WINDOW=14
    FACTOR=3

class Order:
    CATEGORY = 'futures'