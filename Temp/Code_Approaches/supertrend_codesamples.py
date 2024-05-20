# def calculate_supertrend(df, window=14, multiplier=3):
#     """
#     Calculate supertrend for a DataFrame of OHLC data.
#     """
    
#     # Make a copy of the DataFrame to avoid modifying the original
#     _df = df.copy()  
    
#     _df['prev_close'] = _df['close'].shift(1)

#     _df['atr'] = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)

#     midrange = (_df['high'] + _df['low']) / 2
#     offset = multiplier * _df['atr']
    
#     _df['top_band'] = midrange + offset
#     _df['bottom_band'] = midrange - offset
#     _df['prev_top_band'] = _df['top_band'].shift(1)
#     _df['prev_bottom_band'] = _df['bottom_band'].shift(1)

#     # _df['supertrend'] = np.nan

#     # Calculate st_bullish 
#     _df['st_bullish'] = np.nan
#     max_upper = np.maximum(_df['top_band'], _df['prev_top_band'])
#     _df['st_bullish'] = np.where(
#         _df['prev_close'] > _df['prev_top_band'], 
#         max_upper, 
#         _df['top_band']
#     )

#     # Calculate st_bearish
#     _df['st_bearish'] = np.nan
#     max_lower = np.minimum(_df['bottom_band'], _df['prev_bottom_band'])
#     _df['st_bearish'] = np.where(
#         _df['prev_close'] < _df['prev_bottom_band'],
#         max_lower,
#         _df['bottom_band']
#     )

#     _df['direction'] = 'up'


#     # if _df['direction'] == 'dn'and _df['close'] > _df['prev_bottom_band']:
#     #     _df['direction'] = 'up'
#     # elif _df['direction'] == 'up' and _df['close'] < _df['prev_top_band']:
#     #     _df['direction'] = 'dn'
#     # else:
#     #     _df['direction'] = _df['direction']

#     # _df['direction'] = np.where(
#     #     (_df['direction'] == 'up' and (_df['close'] < _df['prev_top_band'])),
#     #     'dn',
#     #     np.where(
#     #         (_df['direction'] == 'dn'and (_df['close'] > _df['prev_bottom_band'])),
#     #         'up',
#     #         _df['direction']
#     #     )
#     # )

#     return _df







# def calculate_supertrend(df, period=14, multiplier=3):
#     """
#     Applies Supertrend strategy to a DataFrame
    
#     Parameters:
#         df (DataFrame): Input DataFrame with OHLC data.
#         period (int): Lookback period for Supertrend calculation.
#         multiplier (float): Multiplier for Supertrend calculation.
    
#     Returns:
#         DataFrame: Original DataFrame with 'supertrend' column appended.
#     """
#     _df = df.copy()


#     # Calculate ATR
#     _df['atr'] = ta.atr(_df['high'], _df['low'], _df['close'], length=period)

#     # Calculate basic upper and lower bands
#     _df['basic_ub'] = (_df['high'] + _df['low']) / 2 + multiplier * _df['atr']
#     _df['basic_lb'] = (_df['high'] + _df['low']) / 2 - multiplier * _df['atr']

#     # Initialize variables
#     _df['final_ub'] = 0.00
#     _df['final_lb'] = 0.00

#     for i in range(period, len(_df)):
#         _df['final_ub'].iloc[i] = np.where(
#             (_df['basic_ub'].iloc[i] < _df['final_ub'].iloc[i-1]) or (_df['close'].iloc[i-1] > _df['final_ub'].iloc[i-1]),
#             _df['basic_ub'].iloc[i], _df['final_ub'].iloc[i-1]
#         )

#         _df['final_lb'].iloc[i] = np.where(
#             (_df['basic_lb'].iloc[i] > _df['final_lb'].iloc[i-1]) or (_df['close'].iloc[i-1] < _df['final_lb'].iloc[i-1]),
#             _df['basic_lb'].iloc[i], _df['final_lb'].iloc[i-1]
#         )

#     # Calculate Supertrend
#     _df['supertrend'] = np.where(_df['close'] > _df['final_ub'], 1.0, np.where(_df['close'] < _df['final_lb'], -1.0, 0.0))

#     return _df

# Example usage
# Load data into DataFrame (assuming OHLC data is present)
# df = pd.read_csv('your_data.csv')

# Apply Supertrend strategy
# df = supertrend_strategy(df)

# Print DataFrame
# print(df)


























    # for i in range(len(_df)):
    #     if _df['close'].iloc[i-1] > _df['prev_upper_band']:
    #         _df.at[_df.index[i], 'st_bullish'] = max(_df['upper_band'], _df['prev_upper_band'])
    #     else:
    #         _df.at[_df.index[i], 'st_bullish'] = _df['upper_band']

    #     if _df['close'].iloc[i-1] < _df['prev_lower_band']:
    #         min(_df['lower_band'], _df['prev_lower_band'])
    #     else:
    #         _df.at[_df.index[i], 'st_bearish'] = _df['lower_band']

                
                
                                              
         






































# def calculate_supertrend(df, window=14, multiplier=3):
#     """
#     Calculate supertrend for a DataFrame of OHLC data.
#     """
#     _df = df.copy()  # Make a copy of the DataFrame to avoid modifying the original
    
#     atr = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)
#     _df['atr'] = atr

#     midrange = (_df['high'] + _df['low']) / 2
#     offset = multiplier * _df['atr'].values

#     _df['upper_band'] = midrange + offset
#     _df['lower_band'] = midrange - offset

#     supertrend = np.where(_df['close'] > _df['upper_band'], _df['lower_band'], 
#                           np.where(_df['close'] < _df['lower_band'], _df['upper_band'], np.nan))
    
#     _df['supertrend'] = np.nan
#     _df['supertrend'] = supertrend
#     _df['supertrend'] = _df['supertrend'].ffill()  # Forward-fill NaN values
    
#     return _df



























# def calculate_supertrend(df, window=14, multiplier=3):
#     """
#     Calculate supertrend for a DataFrame of OHLC data.
#     """
#     # Copy the DataFrame to avoid modifying the original
#     _df = df.copy()

#     # Calculate ATR
#     atr = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)
#     _df['atr'] = atr

#     # Calculate basic Supertrend components
#     midrange = (_df['high'] + _df['low']) / 2
#     offset = multiplier * _df['atr']

#     _df['upper_band'] = midrange + offset
#     _df['lower_band'] = midrange - offset

    
#     # Calculate Supertrend
#     _df['supertrend'] = np.nan
#     for i in range(1, len(_df)):
#         if _df['close'].iloc[i] > _df['upper_band'].iloc[i-1]:
#             _df.at[_df.index[i], 'supertrend'] = _df['lower_band'].iloc[i]
#         elif _df['close'].iloc[i] < _df['lower_band'].iloc[i-1]:
#             _df.at[_df.index[i], 'supertrend'] = _df['upper_band'].iloc[i]
#         else:
#             _df.at[_df.index[i], 'supertrend'] = _df['supertrend'].iloc[i-1]

    
#     return _df

# Example usage:
# new_df = calculate_supertrend(kline_df)







































# def calculate_supertrend(df, window=14, multiplier=3):
#     """
#     Calculate supertrend for a DataFrame of OHLC data.
#     """
#     _df = df
    
#     _df['supertrend'] = np.nan
#     _df['prev_supertrend'] = _df['supertrend'].shift(1)

#     atr = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)
#     _df['atr'] = atr

#     midrange = (_df['high'] + _df['low']) / 2
#     offset = multiplier * _df['atr']

#     upper_band = midrange + offset
#     lower_band = midrange - offset
#     _df['upper_band'] = upper_band
#     _df['lower_band'] = lower_band

#     _df['prev_upper_band'] = _df['upper_band'].shift(1)
#     _df['prev_lower_band'] = _df['lower_band'].shift(1)

#     def supertrend(row):
#         if row['close'] > row['upper_band']:
#             return row['lower_band']
#         elif row['close'] < row['lower_band']:
#             return row['upper_band']
#         else:
#             return row['prev_supertrend']

#     _df['supertrend'] = _df.apply(supertrend, axis=1)

#     return _df




    # for i in range(len(_df)):
    #     row = _df.iloc[i]
    #     prev_row = _df.iloc[i - 1] if i > 0 else row

        



    #     if row['close'] > prev_row['upper_band']:
    #         supertrend = upper_band
    #     elif row['close'] < prev_row['lower_band']:
    #         supertrend = lower_band
    #     else:
    #         supertrend = prev_row['supertrend']

    #     supertrend_values.append(supertrend)

    # _df['supertrend'] = supertrend_values
    
    # return _df














# # Example usage in main code
# kline_df = pd.DataFrame()

# OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)

# kline_df = OHLC_Engine.get(int(time.time()))[0]
# OHLC_Engine = OHLCData(kline_df, OHLC.SYMBOL, OHLC.RESOLUTION)

# print("       Initial OHLC data", f"             size: {len(kline_df)}\n")    # DONE NO-002
# print(kline_df)
# time.sleep(2)
# while True:
#     kline_df = OHLC_Engine.live()[0]
#     kline_df = calculate_supertrend(kline_df)  # Calculate and add supertrend
#     print("Live dataframe \n", kline_df)
#     time.sleep(5)



















































# def calculate_supertrend(row, prev_row, multiplier, window):
#     atr = talib.ATR(row['high'], row['low'], row['close'], timeperiod=window)
    
#     midrange = (row['high'] + row['low']) / 2
#     offset = multiplier * atr
#     upper_band = midrange + offset
#     lower_band = midrange - offset

#     if row['close'] > prev_row['upper_band']:
#         return upper_band
#     elif row['close'] < prev_row['lower_band']:
#         return lower_band
#     else:
#         return prev_row['supertrend']


# def process_data(df, multiplier, window):
        
#         # Apply supertrend calculation to each row
#         # df['supertrend'] = df.apply(lambda row: calculate_supertrend(row, df.iloc[row.name - 1], multiplier, window) if row.name > 0 else 0, axis=1)
#         _df = df
#         _df['supertrend'] = _df.apply(lambda row: calculate_supertrend(
#              row, 
#              _df.loc[row.name - datetime.timedelta(minutes=1)], 
#              multiplier, 
#              window 
#              if row.name > _df.index.min() else None), axis=1)
#         return _df






















# # Define the custom function to calculate supertrend
# def calculate_supertrend(df, window=10, multiplier=3):
#     _df = df
#     atr = talib.ATR(_df['high'].values, _df['low'].values, _df['close'].values, window)
#     _df['atr'] = atr

#     midrange = (_df['high'] + _df['low']) / 2
#     offset = multiplier * _df['atr']

#     upper_band = midrange + offset
#     lower_band = midrange - offset

#     _df['upper_band'] = upper_band
#     _df['lower_band'] = lower_band

#     supertrend = [0] * len(_df)  # Initialize supertrend
    
#     # Calculate supertrend
#     for i in range(1, len(_df)):
#         if _df['close'].iloc[i] > upper_band.iloc[i - 1]:
#             supertrend[i] = upper_band.iloc[i]
#             print(upper_band.iloc[i])
#         elif _df['close'].iloc[i] < lower_band.iloc[i - 1]:
#             supertrend[i] = lower_band.iloc[i]
#             print(lower_band.iloc[i])
#         else:
#             supertrend[i] = supertrend[i - 1]
#             print(supertrend[i - 1])

#     _df['supertrend'] = supertrend

#     return _df











# # class Supertrend:
# #     def __init__(self):

# # def compute():

# def update_with_calculations(df):
#     def supertrend(row):
#         # Perform calculations on specific cells of the row
#         result = row['high'] * row['low'] + row['close']
        
#         # Return a Series with the existing row and the new result
#         return pd.Series([row['cell1'], row['cell2'], row['cell3'], result])

#     # Create a new DataFrame with the updated data and the new column
#     new_df = df.apply(supertrend, result_type='expand', axis=1)

#     # Rename the columns
#     new_df.columns = ['cell1', 'cell2', 'cell3', 'new_column']
    
#     return new_df

# # Call the function whenever the DataFrame updates
# updated_df = update_with_calculations(df)







# def calculate_supertrend(df, atr_period, multiplier):
#     """
#     Calculate the SuperTrend indicator for a given DataFrame.

#     Args:
#         df (pd.DataFrame): The OHLC DataFrame.
#         atr_period (int): The ATR period (typically 10).
#         multiplier (float): The multiplier for the SuperTrend calculation (typically 3).

#     Returns:
#         pd.DataFrame: The DataFrame with SuperTrend values added.
#     """
#     high_array = df['high'].values
#     low_array = df['low'].values
#     close_array = df['close'].values

#     # Calculate the ATR (Average True Range)
#     atr = talib.ATR(high_array, low_array, close_array, atr_period)

#     # Calculate the ATR (Average True Range)
#     atr = abstract.ATR(high_array, low_array, close_array, atr_period)

#     # Calculate the SuperTrend
#     previous_supertrend = 0
#     supertrend = []
#     trend_stat = None

    
#     for i in range(len(df)):
#         high = high_array[i]
#         low = low_array[i]
#         close = close_array[i]
#         current_atr = atr[i]

#         midrange = (high + low) / 2
#         offset = (multiplier * current_atr)

#         upper_band = midrange + offset
#         lower_band = midrange - offset



#         """ If the current Supertrend is equal to the previous Upper Band and the current close 
#             price is less than or equal to the current Upper Band, 
#             then the current Supertrend = Current Upper Band."""
#         if supertrend == upper_band[i-1] and close <= upper_band: 
#             supertrend = upper_band


        
#         """ If the current Supertrend is equal to the previous Upper Band and the current close 
#             price is greater than the current Upper Band, 
#             then the current Supertrend = Current Lower Band."""
#         if supertrend == upper_band[i-1] and close > upper_band:
#             supertrend = lower_band


#         """ If the current Supertrend is equal to the previous Lower Band and the current close 
#             price is greater than or equal to the current Lower Band, 
#             then the current Supertrend = Current Lower Band."""
#         if supertrend == lower_band[i-1] and  close >= lower_band:
#             supertrend = lower_band


#         """ If the current Supertrend is equal to the previous Lower Band and the current close 
#             price is less than the current Lower Band, 
#             then the current Supertrend = Current Upper Band."""
#         if supertrend == lower_band[i-1] and  close < lower_band:
#             supertrend = upper_band


#         """ If none of the above conditions are met, then the current Supertrend = 0."""
#         else:
#             supertrend = 0

#         """Logic for first candle: """
        


#         trend_stat







#         if i == 0:
#             supertrend.append(0)
#         elif (previous_supertrend == previous_supertrend) and (close <= basic_upper_band) and (close >= basic_lower_band):
#             supertrend.append(previous_supertrend)
#         else:
#             if previous_supertrend == 0:
#                 supertrend.append(basic_upper_band)
#             else:
#                 supertrend.append(basic_lower_band)

#         previous_supertrend = supertrend[-1]
        
#     # Add the SuperTrend values to the DataFrame
#     df['SuperTrend'] = pd.Series(supertrend, index=df.index)

#     return df


# ohlc_df_with_supertrend = None



# def update_supertrend(kline_df, atr_period, multiplier):
#     global ohlc_df_with_supertrend

#     # If ohlc_df_with_supertrend is not initialized, initialize it with the input DataFrame
#     if ohlc_df_with_supertrend is None:
#         ohlc_df_with_supertrend = kline_df.copy()

#     # Concatenate the new data with the existing SuperTrend DataFrame
#     ohlc_df_with_supertrend = pd.concat([ohlc_df_with_supertrend, kline_df])

#     # Remove duplicates and sort the DataFrame
#     ohlc_df_with_supertrend = ohlc_df_with_supertrend[~ohlc_df_with_supertrend.index.duplicated(keep='last')]
#     ohlc_df_with_supertrend = ohlc_df_with_supertrend.sort_index()

#     # Calculate the SuperTrend on the updated DataFrame
#     ohlc_df_with_supertrend = calculate_supertrend(ohlc_df_with_supertrend, atr_period, multiplier)

#     return ohlc_df_with_supertrend













# # import vectorbt as vbt
# # import dask.dataframe as dd

# # class supertrend:
# #     def __init__(self, ohlc_data, period=10, multiplier=3.0):
# #         self.ohlc_data = dd.from_pandas(ohlc_data, npartitions=4)
# #         self.period = period
# #         self.multiplier = multiplier

# #     def _atr(self, high, low, close, period):
# #         atr = vbt.indicators.ATR.run(high, low, close, period)
# #         return dd.from_dask_array(atr)

# #     def _supertrend(self, high, low, close):
# #         atr = self._atr(high, low, close, self.period)
# #         supertrend = vbt.indicators.trend.supertrend(high, low, close, atr, self.period, self.multiplier)
# #         return dd.from_dask_array(supertrend)

# #     def compute(self):
# #         high, low, close = self.ohlc_data['High'], self.ohlc_data['Low'], self.ohlc_data['Close']
# #         supertrend_values = self._supertrend(high, low, close)
# #         self.ohlc_data['SuperTrend'] = supertrend_values.compute()
# #         return self.ohlc_data






# Periods = input(title="ATR Period", type=input.integer, defval=10)
# src = input(hl2, title="Source")
# Multiplier = input(title="ATR Multiplier", type=input.float, step=0.1, defval=3.0)

# atr= atr(Periods)

# up=src-(Multiplier*atr)
# up1 = nz(up[1],up)
# up := close[1] > up1 ? max(up,up1) : up

# dn=src+(Multiplier*atr)
# dn1 = nz(dn[1], dn)
# dn := close[1] < dn1 ? min(dn, dn1) : dn

# trend = 1
# trend := nz(trend[1], trend)
# trend := trend == -1 and close > dn1 ? 1 : trend == 1 and close < up1 ? -1 : trend

# upPlot = plot(trend == 1 ? up : na, title="Up Trend", style=plot.style_linebr, linewidth=2, color=color.green)
# buySignal = trend == 1 and trend[1] == -1
# plotshape(buySignal ? up : na, title="UpTrend Begins", location=location.absolute, style=shape.circle, size=size.tiny, color=color.green, transp=0)
# plotshape(buySignal and showsignals ? up : na, title="Buy", text="Buy", location=location.absolute, style=shape.labelup, size=size.tiny, color=color.green, textcolor=color.white, transp=0)
# dnPlot = plot(trend == 1 ? na : dn, title="Down Trend", style=plot.style_linebr, linewidth=2, color=color.red)
# sellSignal = trend == -1 and trend[1] == 1
# plotshape(sellSignal ? dn : na, title="DownTrend Begins", location=location.absolute, style=shape.circle, size=size.tiny, color=color.red, transp=0)
# plotshape(sellSignal and showsignals ? dn : na, title="Sell", text="Sell", location=location.absolute, style=shape.labeldown, size=size.tiny, color=color.red, textcolor=color.white, transp=0)
# mPlot = plot(ohlc4, title="", style=plot.style_circles, linewidth=0)
# longFillColor = highlighting ? (trend == 1 ? color.green : color.white) : color.white
# shortFillColor = highlighting ? (trend == -1 ? color.red : color.white) : color.white
# fill(mPlot, upPlot, title="UpTrend Highligter", color=longFillColor)
# fill(mPlot, dnPlot, title="DownTrend Highligter", color=shortFillColor)
# alertcondition(buySignal, title="SuperTrend Buy", message="SuperTrend Buy!")
# alertcondition(sellSignal, title="SuperTrend Sell", message="SuperTrend Sell!")
# changeCond = trend != trend[1]
# alertcondition(changeCond, title="SuperTrend Direction Change", message="SuperTrend has changed direction!")










# import pandas as pd
# import numpy as np
# import pandas_ta as ta

# def calculate_supertrend(df, atr_period=10, atr_multiplier=3.0, change_atr_method=True, show_signals=True, highlighting=True):
#     """
#     Calculate the Supertrend indicator.
    
#     Parameters:
#     _df (pd.DataFrame): DataFrame with columns ['open', 'high', 'low', 'close']
#     atr_period (int): ATR period
#     atr_multiplier (float): ATR multiplier for upper/lower bands
#     change_atr_method (bool): Use ATR (True) or SMA of TR (False)
#     show_signals (bool): Include buy/sell signals in the output
#     highlighting (bool): Include trend highlighting in the output
    
#     Returns:
#     pd.DataFrame: DataFrame with Supertrend indicator and signals
#     """
    
#     _df = df.copy()

#     # Calculate ATR
#     _df['tr'] = ta.true_range(_df['high'], _df['low'], _df['close'])
#     _df['atr'] = ta.atr(_df['high'], _df['low'], _df['close'], atr_period) if change_atr_method else _df['tr'].rolling(atr_period).mean()

#     # Calculate basic bands
#     _df['hl2'] = (_df['high'] + _df['low']) / 2
#     _df['upper_band'] = _df['hl2'] - (atr_multiplier * _df['atr'])
#     _df['lower_band'] = _df['hl2'] + (atr_multiplier * _df['atr'])

#     # Initialize Supertrend columns
#     _df['trend'] = 0
#     _df['upper_band'] = _df['upper_band'].shift(1)
#     _df['lower_band'] = _df['lower_band'].shift(1)
#     _df['in_uptrend'] = True

#     # Supertrend calculation loop
#     for current in range(1, len(_df)):
#         previous = current - 1

#         if _df['close'][current] > _df['upper_band'][previous]:
#             _df.at[current, 'in_uptrend'] = True
#         elif _df['close'][current] < _df['lower_band'][previous]:
#             _df.at[current, 'in_uptrend'] = False
#         else:
#             _df.at[current, 'in_uptrend'] = _df.at[previous, 'in_uptrend']

#             if _df.at[previous, 'in_uptrend']:
#                 _df.at[current, 'lower_band'] = max(_df.at[current, 'lower_band'], _df.at[previous, 'lower_band'])
#             else:
#                 _df.at[current, 'upper_band'] = min(_df.at[current, 'upper_band'], _df.at[previous, 'upper_band'])

#         _df.at[current, 'trend'] = 1 if _df.at[current, 'in_uptrend'] else -1

#     # Generate signals
#     _df['buy_signal'] = (_df['trend'] == 1) & (_df['trend'].shift(1) == -1)
#     _df['sell_signal'] = (_df['trend'] == -1) & (_df['trend'].shift(1) == 1)

#     # Highlighting columns
#     if highlighting:
#         _df['long_fill'] = np.where(_df['in_uptrend'], _df['close'], np.nan)
#         _df['short_fill'] = np.where(~_df['in_uptrend'], _df['close'], np.nan)
#     else:
#         _df['long_fill'] = np.nan
#         _df['short_fill'] = np.nan

#     return _df

# # Example usage
# if __name__ == "__main__":
#     # Example DataFrame with OHLC data
#     # data = {
#     #     'open': [100, 102, 101, 105, 107, 108, 109, 110, 112, 115],
#     #     'high': [104, 106, 105, 108, 110, 111, 112, 113, 116, 117],
#     #     'low': [99, 101, 100, 103, 105, 106, 107, 108, 111, 114],
#     #     'close': [103, 105, 104, 107, 109, 110, 111, 112, 115, 116]
#     # }

#     data = pd.read_csv(
#         r"C:\Users\tshoj\OneDrive\Programming\AlgorithmicTrading\Bots\Workspace_2\NobitexTrader\Temp\BTCUSDT-15m-2023-01-01\BTCUSDT-15m-2023-01-01.csv",
#         sep=''
#     )

#     # df = pd.DataFrame(data)
#     df = calculate_supertrend(data)


#     # print(_df)
#     with pd.option_context('display.max_rows', None):
#         print(df)
    










# def calculate_supertrend(df, atr_period=7, atr_multiplier=3):
#     """
#     Calculate Supertrend indicator.
    
#     Parameters:
#     df (pd.DataFrame): DataFrame with columns ['open', 'high', 'low', 'close']
#     atr_period (int): ATR period
#     atr_multiplier (float): ATR multiplier for upper/lower bands
    
#     Returns:
#     pd.DataFrame: DataFrame with 'supertrend' column
#     """
#     _df = df.copy()
#     # Calculate ATR
#     _df['atr'] = ta.atr(_df['high'], _df['low'], _df['close'], atr_period)

#     # Calculate Upper and Lower bands
#     _df['hl2'] = (_df['high'] + _df['low']) / 2
#     _df['upper_band'] = _df['hl2'] + (atr_multiplier * _df['atr'])
#     _df['lower_band'] = _df['hl2'] - (atr_multiplier * _df['atr'])

#     # Initialize Supertrend columns
#     _df['trend_up'] = 0.0
#     _df['trend_down'] = 0.0
#     _df['supertrend'] = 1

#     for current in range(1, len(_df.index)):
#         previous = current - 1
        
#         _df.at[current, 'trend_up'] = _df.at[current, 'upper_band'] if (_df.at[current, 'upper_band'] < _df.at[previous, 'trend_up'] or _df.at[previous, 'close'] > _df.at[previous, 'trend_up']) else _df.at[previous, 'trend_up']
        
#         _df.at[current, 'trend_down'] = _df.at[current, 'lower_band'] if (_df.at[current, 'lower_band'] > _df.at[previous, 'trend_down'] or _df.at[previous, 'close'] < _df.at[previous, 'trend_down']) else _df.at[previous, 'trend_down']
        
#         _df.at[current, 'supertrend'] = 1 if _df.at[current, 'close'] > _df.at[previous, 'trend_down'] else -1 if _df.at[current, 'close'] < _df.at[previous, 'trend_up'] else _df.at[previous, 'supertrend']

#     return _df

# # Example usage
# if __name__ == "__main__":
#     # Example DataFrame with OHLC data
#     # data = {
#     #     'open': [100, 102, 101, 105, 107],
#     #     'high': [104, 106, 105, 108, 110],
#     #     'low': [99, 101, 100, 103, 105],
#     #     'close': [103, 105, 104, 107, 109]
#     # }

#     data = pd.read_csv(
#         r"C:\Users\tshoj\OneDrive\Programming\AlgorithmicTrading\Bots\Workspace_2\NobitexTrader\Temp\BTCUSDT-15m-2023-01-01\BTCUSDT-15m-2023-01-01.csv",
#         sep=''
#     )

#     # df = pd.DataFrame(data)
#     df = calculate_supertrend(data)


#     # print(_df)
#     with pd.option_context('display.max_rows', None):
#         print(df)