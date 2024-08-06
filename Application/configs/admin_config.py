class OHLC:
    TRIES=3
    TIMEOUT=4.0

class Trade:
    class Fetch:
        class Orders:
            TRIES=5
            TIMEOUT=4.0

        class Positions:
            TRIES=5
            TIMEOUT=4.0
    
    class Place:
        pass

class Account:
    class Wallets:
        TRIES=5
        TIMEOUT=4.0

    class Balance:
        TRIES=5
        TIMEOUT=4.0