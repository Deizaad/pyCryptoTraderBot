import pandas as pd
import time
from NobitexTrader.config import OHLC
from NobitexTrader.nb_api.market import *


kline_df = pd.DataFrame()

OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)

kline_df = OHLC_Engine.get(int(time.time()))[0]
OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)

print("       Initial OHLC data", f"             size: {len(kline_df)}\n")    # DONE NO-002
print(kline_df)
time.sleep(2)

# OHLC_Engine.print()
OHLC_Engine.show_new()

update_trades(10, get_trades)
