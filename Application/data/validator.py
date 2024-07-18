"""
This module contains functionalities to validate all kind of datas that are going to be imported in
data_processor module.
"""
import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.utils.exchange.nobitex import resolution_map  # noqa: E402
from Application.data.data_tools import turn_Jalali_to_gregorian  # noqa: E402


def is_consistent(dataframe: pd.DataFrame, resolution: str):
    """
    Checks a DataFrame's index for being sorted, consequtive, and uniqunue.
    """
    cond1, cond2, cond3 = False, False, False
    
    if is_consequtive(dataframe.index.to_series(), resolution):
        cond1 = True
    if is_sorted(dataframe.index.to_series()):
        cond2 = True
    if is_unique(dataframe.index.to_series()):
        cond3 = True

    if cond1 and cond2 and cond3:
        logging.info('VALIDATOR:\n\tdataframe being "consistent": Validated')
        return True
    else:
        logging.info('VALIDATOR:\n\tdataframe being "consistent": Invalidated')
        return False
# ____________________________________________________________________________ . . .


def is_unique(series: pd.Series):
    """
    Checks if a series has unique values.
    """
    if series.is_unique:
        logging.info('VALIDATOR:\n\tdata being unique: Validated')
        return True
    else:
        logging.info('VALIDATOR:\n\tdata being unique: Inalidated')
        return False
# ____________________________________________________________________________ . . .


def is_sorted(series: pd.Series):
    """
    Checks if a series has sorted values.
    """
    if series.is_monotonic_increasing:
        logging.info('VALIDATOR:\n\tdata being sorted: Validated')
        return True
    else:
        logging.info('VALIDATOR:\n\tdata being sorted: Invalidated')
        return False
# ____________________________________________________________________________ . . .


def is_consequtive(series: pd.Series, resolution: str):
    """
    Checks if a series of datetime values is consequtive (there are no missing values).
    """
    gregorian_index = turn_Jalali_to_gregorian(series)

    freq = resolution_map(resolution)

    complete_date_range = pd.date_range(start=gregorian_index.min(),
                                        end=gregorian_index.max(),
                                        freq=freq)

    cond1 = gregorian_index.isin(complete_date_range).all()
    cond2 = len(complete_date_range) == len(gregorian_index)

    if cond1 and cond2:
        logging.info('VALIDATOR:\n\tdata being consequtive: Validated')
        return True
    else:
        logging.info('VALIDATOR:\n\tdata being consequtive: Invalidated')
        return False
# ____________________________________________________________________________ . . .