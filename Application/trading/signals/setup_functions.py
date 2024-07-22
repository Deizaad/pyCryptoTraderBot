import os
import sys
import logging
import importlib
import pandas as pd
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.configs import config as cfg    # noqa: E402
from Application.trading.analysis.indicator_classes import Supertrend    # noqa: E402



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

    try:
        for setup in selected_setups:
            setup_name = setup['name']
            if setup_name in setup_functions:
                func = setup_functions[setup_name]
                selected_functions[setup_name] = {
                    'function': setup_functions[setup_name],
                    'properties': setup['properties']
                }
                required_indicators[setup_name] = func.required_indicators
            else:
                raise NameError(f'Setup "{setup_name}" from config file could not be found in' \
                                 'defined setup functions. Perhaps you meisspell it?')

        return selected_functions, required_indicators
    except NameError as err:
        logging.error(err)
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
async def supertrend_setupfunc(
    kline_df: pd.DataFrame, indicator_df: pd.DataFrame, properties: dict
) -> pd.DataFrame:

    """
    Generate trading signals based on indicator DataFrame for single_supertrend setup.

    Parameters:
        kline_df (pd.DataFrame): DataFrame containing kline data.
        indicator_df (pd.DataFrame): DataFrame containing indicator data.

    Returns:
        pd.DataFrame: DataFrame containing the generated signals.
    """
    print(kline_df)
    print(indicator_df)
    try:
        signal_df = pd.DataFrame(index=indicator_df.index)
        signal_df['supertrend'] = 0

        _supertrend = indicator_df['supertrend_side']
        _prev_supertrend = indicator_df['supertrend_side'].shift(1)

        signal_df.loc[(_supertrend == 1) & (_prev_supertrend == -1), 'supertrend'] = 1
        signal_df.loc[(_supertrend == -1) & (_prev_supertrend == 1), 'supertrend'] = -1

        print(signal_df)
        return signal_df
    except Exception as err:
        logging.error(f"Error while generating signals in supertrend_setupfunc() func: {err}")
        return pd.DataFrame()
# ________________________________________________________________________________ . . .


# Definition of other setup functions ...
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
    print(selected, '\n', indicators)