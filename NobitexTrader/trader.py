import time

from NobitexTrader.nb_api.market import *
from NobitexTrader.data_manager import DataManager


data_manager = DataManager()
# kline_df = data_manager.get_kline_df()

# print("       Initial OHLC data", f"             size: {len(kline_df)}\n")    # DONE NO-002
# print(kline_df)
# time.sleep(2)


while True:
    data_manager.show()

    # with pd.option_context('display.max_rows', 20):   
        # print("Live dataframe \n", kline_df)
        # print("pandas generated supertrend \n", indicator_df)

    time.sleep(5)


update_trades(10, get_trades)
