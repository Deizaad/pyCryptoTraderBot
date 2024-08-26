import sys
import pytz
import logging
import importlib
import pandas as pd
from typing import Any
from datetime import datetime
from dotenv import dotenv_values
from persiantools.jdatetime import JalaliDateTime    # type: ignore

path = dotenv_values('project_path.env').get('PYTHONPATH')
sys.path.append(path) if path else None

from Application.utils.load_json import load                        # noqa: E402
from Application.utils.simplified_event_handler import EventHandler # noqa: E402

jarchi = EventHandler()



def has_signal(signals_df: pd.DataFrame, column) -> str | None:
    """
    Checks the signals in the last two rows of the specified column in signals dataframe.

    Parameters:
        signals_df (DataFrame):
        column ():

    Returns:
        has_signals (str | None): Eather 'new_signal' | 'late_signal' | None.
    """
    last_value = signals_df[column].iloc[-1]
    second_last_value = signals_df[column].iloc[-2]

    if last_value != 0:
        return 'new_signal'
    elif second_last_value != 0:
        return 'late_signal'
    else:
        return None
# ________________________________________________________________________________ . . .


def extract_strategy_field_value(field : str) -> Any:
    """
    Extracts the value of a strategy field.

    Raises:
        ValueError:
    
    Returns:
        extracted_value (Any):
    """
    value = load(r'Application/configs/strategy.json').get(field, None)

    if not value:
        raise ValueError(f"Can not find value of '{field}' field 'strategy.json' config file, "\
                         "it has not been quantified with a value, or perhaps you misspelled it.")
    
    return value
# ________________________________________________________________________________ . . .


def extract_non_singular_strategy_setup(
        setup_name                      : str,
        config                          : dict,
        setup_functions_module_path     : str,
        indicator_functions_module_path : str | None = None,
        validator_functions_module_path : str | None = None
    ):
    """
    Extracts function objects, properties and indicators (if there is any) of a specified field in
    strategy config file from the given modules.

    Parameters:
        setup_name (str): The field in the strategy config from which to extract objects.
        config (dict): The pre-loaded json configuration dictionary.
        chief_module_path (str): Path to the module where the setup functions are defined.
        indicators_module_path (str): Path to the module where the indicator functions are defined.

    Returns:
        extracted_system (list): A list of dictionaries containing function objects and their associated properties/indicators.
    """
    extracted_system = []

    # Import function modules
    chief_module = importlib.import_module(setup_functions_module_path)
    indicators_module = importlib.import_module(indicator_functions_module_path)\
                        if indicator_functions_module_path \
                        else None
    
    validators_module = importlib.import_module(validator_functions_module_path)\
                        if validator_functions_module_path\
                        else None

    # extract the setups with properties
    for setup in config.get(setup_name, []):
        setup_func_name = setup["name"]
        setup_func_obj  = getattr(chief_module, setup_func_name)
        setup_instance  = {"name"       : setup_func_name,
                           "function"   : setup_func_obj,
                           "properties" : setup.get("properties", {}),
                           "indicators" : [],
                           "validators" : []}
        
        # extract setup's indicators if there are any
        for indicator in setup.get("indicators", []):
            indicator_func_name = indicator["name"]
            indicator_func_obj  = getattr(indicators_module, indicator_func_name)
            indicator_instance  = {"name"       : indicator_func_name,
                                   "function"   : indicator_func_obj,
                                   "properties" : indicator.get("properties", {})}
            
            # include extracted indicator to setup
            setup_instance["indicators"].append(indicator_instance)

        # extract setup's validators if there are any
        for validator in setup.get("validators", []):
            validator_func_name = validator["name"]
            validator_func_obj  = getattr(validators_module, validator_func_name)
            validator_instance  = {"name": validator_func_name,
                                   "function": validator_func_obj,
                                   "properties": validator.get("properties", {})}
            
            # Include extracted validator to setup
            setup_instance["validators"].append(validator_instance)

        # Add setup_instance to extracted_system list
        extracted_system.append(setup_instance)

    return extracted_system
# ________________________________________________________________________________ . . .


def extract_singular_strategy_setup(setup_name            : str,
                                    config                : dict,
                                    setup_functions_module_path : str):
    """
    Extracts function, and properties of a sigular strategy setup.

    Parameters:
        setup_name (str): The field name in the strategy.json config file from which to extract objects.
        config (dict): The pre-loaded json configuration dictionary.
        setup_functions_module_path (str): Path to the module where the setup functions are defined.

    Returns:
        extracted_setup (dict): A dictionary containing extracted setup along with it's function object and assiciated properties.
    """
    try:
        funcs_module = importlib.import_module(setup_functions_module_path)

        name = config[setup_name]['name']
        extracted_setup = {'name'       : name,
                           'function'   : getattr(funcs_module, name),
                           'properties' : config[setup_name]['properties']}

        return extracted_setup

    except AttributeError as err:
        logging.error(f"Module '{funcs_module}' has no function named '{name}'. {err} ")
        return {}
    except ModuleNotFoundError as err:
        logging.error(f"There is no module with path '{setup_functions_module_path}', perhaps you misspelled it? {err}")
        return {}
# ________________________________________________________________________________ . . .


def parse_kline_to_df(raw_kline: dict) -> pd.DataFrame:
    """
    This function turns raw kline dict to pandas DataFrame.
    """
    tz = pytz.timezone('Asia/Tehran')

    kline_df = pd.DataFrame({
        'time'  : [JalaliDateTime.fromtimestamp(timestamp, tz) for timestamp in raw_kline['t']],
        'open'  : raw_kline['o'],
        'high'  : raw_kline['h'],
        'low'   : raw_kline['l'],
        'close' : raw_kline['c'],
        'volume': raw_kline['v']
    }).set_index('time')

    return kline_df
# ________________________________________________________________________________ . . .


def parse_orders(raw_orders: dict) -> pd.DataFrame:
    """
    Converts raw orders data into a dataframe.

    Parameters:
        raw_orders (dict): Raw orders data received from exchange API.
    
    Returns (DataFrame): A dataframe containing orders data.
    """
    orders: list = []
    orders.extend(raw_orders['orders'])
    orders_df = pd.json_normalize(orders)
    orders_df = orders_df.loc[:,['clientOrderId',
                                 'tradeType',
                                 'type',
                                 'srcCurrency',
                                 'dstCurrency',
                                 'price',
                                 'amount',
                                 'totalPrice',
                                 'leverage',
                                 'totalOrderPrice',
                                 'matchedAmount',
                                 'unmatchedAmount',
                                 'execution',
                                 'side',
                                 'isMyOrder']]
    return orders_df
# ________________________________________________________________________________ . . .


def parse_positions(raw_positions: dict) -> pd.DataFrame:
    """
    Converts raw positions data into a dataframe.

    Parameters:
        raw_positions (dict): Raw positions data received from exchange API.

    Returns (DataFrame): A dataframe containing positions data.
    """
    positions: list = []
    if 'positions' in raw_positions:
        positions.extend(raw_positions['positions'])
    elif 'orders' in raw_positions:
        positions.extend(raw_positions['orders'])

    positions_df = pd.json_normalize(positions)

    if not positions_df.empty:
        if 'created_at' in positions_df.columns:
            positions_df.rename(columns={'created_at': 'createdAt'}, inplace=True)
        # positions_df.set_index('id', inplace=True)

    return positions_df
# ________________________________________________________________________________ . . .


def parse_wallets_to_df(raw_wallets: dict, drop_void: bool = True) -> pd.DataFrame:
    """
    Converts raw wallets data to a pandas DataFrame.
    """
    wallets = []
    raw_wallets = raw_wallets.get('wallets', [])

    for wallet in raw_wallets:
        balance = float(wallet['balance'])
        if not drop_void or balance != 0:
            wallets.append({'currency'          : wallet['currency'].upper(),
                            'id'                : wallet['id'],
                            'balance'           : balance,
                            'blocked'           : float(wallet['blockedBalance']),
                            'active_balance'    : float(wallet['activeBalance']),
                            'rial_balance'      : wallet['rialBalance'],
                            'rial_balance_sell' : wallet['rialBalanceSell'],
                            'deposit_address'   : wallet['depositAddress'],
                            'deposit_tag'       : wallet['depositTag']})
            
    df = pd.DataFrame(wallets)
    df.set_index('currency', inplace=True)

    return df
# ________________________________________________________________________________ . . .


def Tehran_timestamp():
    """
    This function returns the timestamp for current time in 'Asia/Tehran' timezone.
    """
    timezone = pytz.timezone('Asia/Tehran')
    time = datetime.now(timezone)
    timestamp = int(time.timestamp())

    return timestamp
# ________________________________________________________________________________ . . .


def update_dataframe(origin_df: pd.DataFrame, late_df: pd.DataFrame, size: int):
    """
    This function updates any dataframe with new data while keeping the dataframe size constant.
    The origin_df also can be an empty dataframe.
    """
    # Return the late_df with proper size if origin_df is empty
    if origin_df.empty:
        if len(late_df) <= size:
            updated_df = late_df
        else:
            updated_df = late_df.sort_index(ascending=False).head(size).sort_index()
        return updated_df

    # get new rows
    existing_indexes = origin_df.index.unique()
    received_indexes = late_df.index.unique()
    new_indexes = received_indexes[~received_indexes.isin(existing_indexes)]
    new_rows    = late_df.loc[late_df.index.isin(new_indexes)]

    # update existing dataframe (existing rows) with new values
    origin_df.update(late_df)
    
    # update existing dataframe with new rows
    updated_df = pd.concat([origin_df, new_rows])

    # drop oldest rows
    if len(updated_df) > size:
        updated_df = updated_df.sort_index(ascending=False).head(size).sort_index()
    
    return updated_df
# ________________________________________________________________________________ . . .


def df_has_news(origin_df: pd.DataFrame, late_df: pd.DataFrame):
    """
    
    """
    # Check if late_df has indexes that are not in origin_df
    if not late_df.index.difference(origin_df.index).empty:
        return True
    
    # Check for updated cells in overlapping rows
    common_index = origin_df.index.intersection(late_df.index)
    origin_common = origin_df.loc[common_index]
    late_common = late_df.loc[common_index]

    # Compare cell by cell for the common rows
    updated_cells = late_common.ne(origin_common) & late_common.notnull()
    
    # Check if there are any updated cells
    if updated_cells.any().any():
        return True
    
    # If no new rows or updated cells found
    return False
# ________________________________________________________________________________ . . .


def turn_Jalali_to_gregorian(series: pd.Series):
    """
    Converts JalaliDateTime values of a series into GregorianDateTime values.
    """
    if isinstance(series.min(), JalaliDateTime):
        gregorian_index = series.apply(lambda jdatetime: JalaliDateTime.to_gregorian(jdatetime))
    else:
        gregorian_index = series

    return gregorian_index
# ________________________________________________________________________________ . . .


if __name__ == '__main__':
    system = extract_non_singular_strategy_setup(
        setup_name='entry_signal_setups',
        config=load(r'Application/configs/strategy.json'),
        setup_functions_module_path='Application.trading.signals.setup_functions',
        indicator_functions_module_path='Application.trading.analysis.indicator_functions',
        validator_functions_module_path='Application.trading.signals.signal_validation_functions'
    )

    print(system)


    def test_has_signal():
        data = {
            'entry_supertrend': [0, 0, 0, 1, 0],
            'tp_setup1': [0, 0, 0, -1, 0],
            'sl_setup1': [0, 0, 0, -1, 1],
            'some_other_column': [0, 0, 0, 1, -1]
        }
        index = pd.date_range(start="2023-01-01 09:00:00", periods=5, freq='min')
        df = pd.DataFrame(data, index=index)

        expected_signals = {
            'entry_supertrend': 'late_signal',
            'tp_setup1': 'late_signal',
            'sl_setup1': 'new_signal',
            'some_other_column': 'new_signal',
        }

        for column in df.columns:
            result = has_signal(df, column)
            assert result == expected_signals[column], f"Test failed for {column}. Expected {expected_signals[column]}, got {result}."

        print("All tests passed.")

    test_has_signal()


    field = 'risk_per_trade'
    value = extract_strategy_field_value(field)
    print(field, ': \t', value)