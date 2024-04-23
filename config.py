import nobitex_data

class Nobitex:
    BASE_URL: str = 'https://api.nobitex.ir/'
    TESTNET: str = 'https://testnetapi.nobitex.ir/'

class OHLC:
    SYMBOL: str = 'USDTIRT'
    RESOLUTION: str = '5'
    TO= int(nobitex_data.CURRENT_TIME)
    FROM= 0
    COUNTBACK= 500
    PAGE= 1

class TRADES:
    SYMBOL: str = 'USDTIRT'
