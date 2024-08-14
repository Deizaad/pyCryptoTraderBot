import asyncio
import logging
import pandas as pd


# =================================================================================================
async def compute_validation_indicators(validation_system: list, kline_df: pd.DataFrame):
    """
    Computes validation indicator functions asynchronously.

    Parameters:
        validation_system (list): List of market validation setups.
        kline_df (DataFrame): kline DataFrame.

    Retrns:
        v_indicators_df (DataFrame): A pandas Dataframe containing validation indicators values.
    """
    # Initialize coroutines
    coroutines_set = set()

    # Add indicator functions and their properties to coroutines
    for setup in validation_system:
        for indicator_config in setup.get("indicators", []):
            # Handle the case where there is no indicator to be computed
            if not indicator_config:
                return pd.DataFrame()
            coroutines_set.add(
                indicator_config["function"](properties = indicator_config["properties"],
                                             kline_df   = kline_df)
            )

            logging.info(f'Indicator {indicator_config["name"]} has been added to validation '\
                         'indicators.')

    # Executing coroutine objects
    try:
        if coroutines_set:
            results = await asyncio.gather(*coroutines_set)
        else:
            results = []
    except asyncio.CancelledError:
            logging.error("An indicator compution task got canceled in "\
                          "'compute_validation_indicators()' function.")
    except Exception as err:
        logging.error(f'Inside "compute_validation_indicators()": {err}')

    # Extract and merging indicator dataframes together
    indicators_df = pd.DataFrame(index=kline_df.index)
    if results:
        for result in results:
            if not result.empty:
                indicators_df = indicators_df.merge(
                    result, left_index=True, right_index=True, how='left'
                )

    return indicators_df
# ________________________________________________________________________________ . . .


async def compute_indicators(trading_system: list, kline_df: pd.DataFrame):
    """
    Computes indicator functions of given system asynchronously.

    Parameters: 
        trading_system (list): List of trading setups.
        kline_df (DataFrame): kline DataFrame.

    Returns:
        indicators_df (DataFrame): A pandas Dataframe containing indicators values.
    """
    coroutines_set = set()

    for setup in trading_system:
        for indicator_config in setup.get("indicators", []):
            # Handle the case where there is no indicator to be computed
            if not indicator_config:
                return pd.DataFrame()
            coroutines_set.add(
                indicator_config["function"](properties = indicator_config["properties"],
                                             kline_df   = kline_df)
            )

            logging.info(f'Indicator "{indicator_config["name"]}" has been added to Indicators.')

    try:
        if coroutines_set:
            results = await asyncio.gather(*coroutines_set)
        else:
            results = []
    except asyncio.CancelledError:
            logging.error("An indicator compution task got canceled in "\
                          "'compute_indicators()' function.")
    except Exception as err:
        logging.error(f'Inside "compute_indicators()": {err}')

    indicators_df = pd.DataFrame(index=kline_df.index)
    if results:
        for result in results:
            if not result.empty:
                indicators_df = indicators_df.merge(
                    result, left_index=True, right_index=True, how='left'
                )

    return indicators_df
# =================================================================================================



# =================================================================================================
# class IndicatorChief:
#     """
#     Hello
#     """
#     def __init__(self):
#         self.indicators_set = set()
#     # ____________________________________________________________________________ . . .


#     def declare_indicators(self, path_to_setups_module: str, configs: Dict):
#         """
#         This method declares the required indicators.
#         """
#         _, self.required_indicators = get_selected_setups(path_to_setups_module, configs)

#         for value in self.required_indicators.values():
#             for item in value:
#                 if item not in self.indicators_set:
#                     self.indicators_set.add(item)
#                     logging.info(f'Indicator {item} has been added to indicators_set.')
#     # ____________________________________________________________________________ . . .


#     async def cook_indicators(self, kline_df: pd.DataFrame):
#         """
#         This method asynchronously executes indicator functions and returns the indicator DataFrame
#         """
#         tasks = []

#         for item in self.indicators_set:
#             for key in coroutines_map.keys():
#                 if isinstance(item, key):
#                     tasks.append(coroutines_map[key](item, kline_df))

#         try:
#             results = await asyncio.gather(*tasks)
#         except asyncio.CancelledError:
#             logging.error("A task was cancelled during cook_indicators.")
#             raise

#         indicators_df = pd.DataFrame(index=kline_df.index)
#         for result in results:
#             if not result.empty:
#                 indicators_df = indicators_df.merge(
#                     result, left_index=True, right_index=True, how='left'
#                 )

#         return indicators_df
# # =================================================================================================