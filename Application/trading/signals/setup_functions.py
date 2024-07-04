import os
import sys
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

import logging
import importlib
import pandas as pd

from Application.configs import config as cfg
from Application.trading.analysis.indicator_classes import Supertrend




# =================================================================================================
def get_selected_setups(module_path: str, config: dict) -> tuple[dict, dict]:
    """
    This function returns strategy setups from 'setup_functions' module that are selected in config
    file along with their properties.
    
    Parameters:
        module_path (str): Path to the module where setup functions are located.
        config (dict): A pre-loaded .json configuration file.
    
    Returns:
        tuple: A tuple containing two dictionaries:
            - selected_functions: Dictionary of selected setup functions and their properties.
            - required_indicators: Dictionary of required indicators and their parameters.
    """
    setups_module = importlib.import_module(module_path)
    setup_functions = {
        name: func for name, func in setups_module.__dict__.items()
        if callable(func) and hasattr(func, 'required_indicators')
    }

    selected_setups = config['setups']
    
    selected_functions = {}
    required_indicators = {}

    for setup in selected_setups:
        setup_name = setup['name']
        if setup_name in setup_functions:
            func = setup_functions[setup_name]
            selected_functions[setup_name] = {
                'function': setup_functions[setup_name],
                'properties': setup['properties']
            }
            required_indicators[setup_name] = func.required_indicators

    return selected_functions, required_indicators
# =================================================================================================



# =================================================================================================
def requires_indicators(*indicators):
    def decorator(func):
        func.required_indicators = indicators
        return func
    return decorator
# =================================================================================================



# =================================================================================================
@requires_indicators(Supertrend(cfg.Study.Supertrend.WINDOW, cfg.Study.Supertrend.FACTOR))
async def supertrend_setupfunc(kline_df: pd.DataFrame, indicator_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate trading signals based on indicator DataFrame for single_supertrend setup.

    Parameters:
        kline_df (pd.DataFrame): DataFrame containing kline data.
        indicator_df (pd.DataFrame): DataFrame containing indicator data.

    Returns:
        pd.DataFrame: DataFrame containing the generated signals.
    """
    if indicator_df is None:
        return pd.DataFrame()
    
    try:
        if not isinstance(kline_df, pd.DataFrame):
            raise ValueError("kline_df must be a pandas DataFrame")
        if not isinstance(indicator_df, pd.DataFrame):
            raise ValueError("indicator_df must be a pandas DataFrame")

        signal_df = pd.DataFrame(index=kline_df.index)
        signal_df['supertrend'] = 0

        if len(indicator_df) > 2:
            _supertrend = indicator_df['supertrend_side']
            _prev_supertrend = indicator_df['supertrend_side'].shift(1)

            signal_df.loc[(_supertrend == 1) & (_prev_supertrend == -1), 'supertrend'] = 1
            signal_df.loc[(_supertrend == -1) & (_prev_supertrend == 1), 'supertrend'] = -1

        return signal_df
    except Exception as err:
        logging.error(f"Error generating signal in SingleSupertrendStrategy: {err}")
        print(f"Error generating signal in SingleSupertrendStrategy: {err}")
        return pd.DataFrame()
# =================================================================================================


if __name__ == '__main__':
    selected, indicators = get_selected_setups('Application.trading.signals.setup_functions', {
        "setups": [
            {
                "name": "supertrend_setupfunc",
                "properties": {
                    "window": 14,
                    "factor": 3
                }
            }
        ]
        })
    print(selected, indicators)









# # =================================================================================================
# def get_setups():
#     setup_functions = {
#         name: func for name, func in globals().items()
#         if callable(func) and hasattr(func, 'required_indicators')
#     }
#     return setup_functions
# # =================================================================================================



# # =================================================================================================
# class SignalSetup:
#     def __init__(self):
#         pass
    
    
#     def apply(self, kline_df: pd.DataFrame, indicator_df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Applies the strategy to the provided dataframes and returns a signal dataframe.
#         """
#         raise NotImplementedError("generate_signal() must be implemented by subclasses.")
# # =================================================================================================



# # =================================================================================================
# class SuperTrendSetup(SignalSetup):
#     def apply(self, kline_df: pd.DataFrame, indicator_df: pd.DataFrame) -> pd.DataFrame:
#         """
#         Generate trading signals based on indicator DataFrame for single_supertrend setup.

#         Parameters:
#             kline_df (pd.DataFrame): DataFrame containing kline data.
#             indicator_df (pd.DataFrame): DataFrame containing indicator data.

#         Returns:
#             pd.DataFrame: DataFrame containing the generated signals.
#         """
#         if indicator_df is None:
#             return pd.DataFrame()
        
#         try:
#             if not isinstance(kline_df, pd.DataFrame):
#                 raise ValueError("kline_df must be a pandas DataFrame")
#             if not isinstance(indicator_df, pd.DataFrame):
#                 raise ValueError("indicator_df must be a pandas DataFrame")

#             signal_df = pd.DataFrame(index=kline_df.index)
#             signal_df['supertrend'] = 0

#             if len(indicator_df) > 2:
#                 _supertrend = indicator_df['supertrend_side']
#                 _prev_supertrend = indicator_df['supertrend_side'].shift(1)

#                 signal_df.loc[(_supertrend == 1) & (_prev_supertrend == -1), 'supertrend'] = 1
#                 signal_df.loc[(_supertrend == -1) & (_prev_supertrend == 1), 'supertrend'] = -1

#             return signal_df
#         except Exception as err:
#             logging.error(f"Error generating signal in SingleSupertrendStrategy: {err}")
#             print(f"Error generating signal in SingleSupertrendStrategy: {err}")
#             return pd.DataFrame()
# # =================================================================================================



# # =================================================================================================
# list = {
#     'single_supertrend': SuperTrendSetup
#     # Add other setup-functions here
# }
# # =================================================================================================