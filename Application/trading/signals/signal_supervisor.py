import asyncio
import logging
import pandas as pd





# def declare_setups(category: str, path_to_setups_module: str, configs: Dict[str, Any]):
#     """
#     Declares chosen strategy setups and required indicators from config file.

#     Parameters:
#         category (str): Category of setup. Expects eather 'entry_signal_setups' | 'take_profit_setups' | 'stop_loss_setups'.
#         path_to_setups_module (str): The file path to the setups module where strategy setups are defined.
#         configs (Dict[str, Any]): Preloaded configuration dictionary that includes the selected setups and their properties.
    
#     Returns:
#         Tuple (Dict[Callable, Dict[str, Any]], Set):
#             - A dictionary mapping setup functions to their properties.
#             - A set of required indicators.
#     """
#     declared_indicators: Set[tuple] = set()
#     declared_setup_functions: Dict[Callable, Dict[str, float]] = {}

#     selected_setups, required_indicators = get_selected_setups(setup_type  = category,
#                                                                module_path = path_to_setups_module,
#                                                                config      = configs)
    
#     # Extract setup functions
#     for setup in selected_setups:
#         setup_func: Callable = selected_setups[setup]['function']
#         properties: dict     = selected_setups[setup]['properties']

#         declared_setup_functions[setup_func] = properties
#         logging.info(f'Setup "{setup}" has been added to "declared_setup_functions".')

#     # Extract indicators
#     for value in required_indicators.values():
#             for item in value:
#                 if item not in declared_indicators:
#                     declared_indicators.add(item)
#                     logging.info(f'Indicator {item} has been added to "declared_indicators".')

#     return declared_setup_functions, declared_indicators
# # ________________________________________________________________________________ . . .


# # =================================================================================================



# # =================================================================================================
# class SignalChief:
#     def declare_setups(self, path_to_setups_module: str, configs: dict):
#         """
#         Declares chosen strategy setups.
#         """
#         self.declared_setup_functions: dict[Callable, dict[str, float]] = {}

#         selected_setups, _ = get_selected_setups('entry_signal_setups', path_to_setups_module, configs)

#         for setup in selected_setups:
#             setup_func: Callable = selected_setups[setup]['function']
#             properties: dict     = selected_setups[setup]['properties']

#             self.declared_setup_functions[setup_func] = properties

#             logging.info(f'Setup "{setup}" has been added to "declared_setup_functions".')
#     # ____________________________________________________________________________ . . .


#     async def generate_signals(self, kline_df: pd.DataFrame, indicator_df: pd.DataFrame):
#         """
#         Executes setup functions asynchronously to return generated signals as a dataframe.
#         """
#         tasks = []
#         for function in self.declared_setup_functions:
#             tasks.append(function(kline_df=kline_df,
#                                   indicator_df=indicator_df,
#                                   properties=self.declared_setup_functions[function]))

#         try:
#             results: list[pd.DataFrame] = await asyncio.gather(*tasks)
#         except asyncio.CancelledError as err:
#             logging.error(f"A task got cancelled in generate_signals() of SignalChief: {err}")
#             raise
#         except Exception as err:
#             logging.error(f'Inside generate_signals() method of SignalChief: {err}')

#         signal_df = pd.DataFrame(index=kline_df.index)

#         for result in results:
#             if not result.empty:
#                 signal_df = signal_df.merge(
#                     result, left_index=True, right_index=True, how='left'
#                 )

#         return signal_df
# =================================================================================================



# if __name__ == '__main__':