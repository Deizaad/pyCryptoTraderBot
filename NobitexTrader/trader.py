import time

from .config import OHLC
from .nb_api.market import get_OHLC, get_trades, print_OHLC, update_trades

# Initiate a dataframe to store OHLC data
kline_df = get_OHLC(
    OHLC.SYMBOL,
    OHLC.RESOLUTION,
    int(time.time()),
)


print(
    "       Initial OHLC data", f"             size: {len(kline_df)}\n"
)  # DONE NO-002
print(kline_df)
time.sleep(2)


# # Print OHLC live update
print_OHLC(kline_df)


update_trades(10, get_trades)
