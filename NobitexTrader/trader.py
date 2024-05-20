import pandas as pd
import time
from NobitexTrader.config import OHLC
from NobitexTrader.nb_api.market import *
from  NobitexTrader.analysis.supertrend import pandas_supertrend


kline_df = pd.DataFrame()

OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)

kline_df = OHLC_Engine.get(int(time.time()))[0]
OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)

print("       Initial OHLC data", f"             size: {len(kline_df)}\n")    # DONE NO-002
print(kline_df)
time.sleep(2)

# OHLC_Engine.print()
# OHLC_Engine.show_new()

while True:
    
    kline_df = OHLC_Engine.live()[0]
    secound_df = pandas_supertrend(kline_df)

    with pd.option_context('display.max_rows', None,):   
        print("Live dataframe \n", kline_df)
        print("pandas generated supertrend \n", secound_df)

    time.sleep(5)


update_trades(10, get_trades)
