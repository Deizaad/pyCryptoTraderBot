class OHLC:
    TRIES=3
    TIMEOUT=3.5

class Trade:
    class Fetch:
        class Orders:
            TRIES=5
            TIMEOUT=4.0

        class Positions:
            TRIES=5
            TIMEOUT=4.0
    
    class Place:
        class CancelOrders:
            TRIES=3
            TIMEOUT=3.5

        class ClosePosition:
            TRIES=3
            TIMEOUT=3.5

class Account:
    class Wallets:
        TRIES=5
        TIMEOUT=4.0

    class Balance:
        TRIES=5
        TIMEOUT=4.0