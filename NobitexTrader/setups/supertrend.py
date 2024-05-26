import pandas as pd


def signal(kline_df: pd.DataFrame, indicator_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals based on kline and indicator DataFrames.

    Parameters:
        kline_df (pd.DataFrame): DataFrame containing kline data.

        indicator_df (pd.DataFrame): DataFrame containing indicator data.
    
    Returns:
        pd.DataFrame: DataFrame containing the generated signals.
    """
    if not isinstance(kline_df, pd.DataFrame):
        raise ValueError("kline_df must be a pandas DataFrame")
    if not isinstance(indicator_df, pd.DataFrame):
        raise ValueError("indicator_df must be a pandas DataFrame")
    
    # Initialize signal DataFrame with the same index as kline_df
    signal_df = pd.DataFrame(index=kline_df.index)

    
    # Generate signal for single supertrend entry setup
    signal_df['supertrend'] = 0
    
    if len(indicator_df) > 2:
        _supertrend = indicator_df['supertrend_side']
        _prev_supertrend = indicator_df['supertrend_side'].shift(1)
        
        # Set the 'supertrend' column based on conditions
        signal_df.loc[(_supertrend == 1) & (_prev_supertrend == -1), 'supertrend'] = 1
        signal_df.loc[(_supertrend == -1) & (_prev_supertrend == 1), 'supertrend'] = -1
    
        # if 'supertrend_side' in indicator_df.columns:
        #     signal_df['supertrend_side'] = indicator_df['supertrend_side']

    return signal_df



# =================================================================================================
# class Signal:
#     def entry(self, indicator_df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Generate entry signals based on indicator DataFrame.

#         Parameters:
#             indicator_df (pd.DataFrame): DataFrame containing indicator data.
        
#         Returns:
#             pd.DataFrame: DataFrame containing the generated signals.
#         """

#         self.indicator_df = indicator_df

#         if not isinstance(self.indicator_df, pd.DataFrame):
#             raise ValueError("indicator_df must be a pandas DataFrame")
        
#         signal_df = pd.DataFrame(index=self.indicator_df.index)
#         signal_df['supertrend'] = 0
        
#         if len(self.indicator_df) > 2:
#             _supertrend = self.indicator_df['supertrend_side']
#             _prev_supertrend = self.indicator_df['supertrend_side'].shift(1)
            
#             signal_df.loc[(_supertrend == 1) & (_prev_supertrend == -1), 'supertrend'] = 1
#             signal_df.loc[(_supertrend == -1) & (_prev_supertrend == 1), 'supertrend'] = -1
        
#             if 'supertrend_side' in self.indicator_df.columns:
#                 signal_df['supertrend_side'] = self.indicator_df['supertrend_side']

#         return signal_df
    # ____________________________________________________________________________ . . .