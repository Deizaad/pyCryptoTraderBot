class Market:
    class OHLC:
        TRIES=3
        TIMEOUT=3.5

    class OrderBook:
        TRIES=2
        TIMEOUT=3


class Trade:
    class Fetch:
        class Orders:
            TRIES=5
            TIMEOUT=4.0

        class Positions:
            TRIES=5
            TIMEOUT=4.0
    
    class Place:
        class PlaceOrder:
            TRIES=3
            TIMEOUT=2.5
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