import time
from NobitexTrader.config import OHLC
from NobitexTrader.nb_api.market import *

# Initiate a dataframe to store OHLC data
kline_df = get_OHLC(
    OHLC.SYMBOL,
    OHLC.RESOLUTION,
    int(time.time()),
)


print("       Initial OHLC data", "             size: \n")    # TODO NO-002
print(kline_df)
time.sleep(2)


# # Print OHLC live update
# print_OHLC(kline_df)


update_trades(10, get_trades)