from .nobitex_data import CURRENT_TIME


class OHLC:
    SYMBOL: str = "USDTIRT"
    RESOLUTION: str = "1"
    TO = int(CURRENT_TIME)
    FROM = 0
    COUNTBACK = 500
    PAGE = 1


class TRADES:
    SYMBOL: str = "USDTIRT"
