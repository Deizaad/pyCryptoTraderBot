import os
import sys
import pandas as pd
from dotenv import load_dotenv
from typing import Coroutine, Callable

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

import Application.trading.analysis.indicator_functions as indicators    # noqa: E402
from Application.trading.analysis.indicator_classes import Supertrend    # noqa: E402



# =================================================================================================
def supertrend_task(item: Supertrend, kline_df: pd.DataFrame) -> Coroutine:
    window = item.params[0]
    factor = item.params[1]
    properties = {'window': window, 'factor': factor}

    task = indicators.pandas_supertrend(kline_df.copy(), **properties)
    return task
    # ____________________________________________________________________________ . . .


# Task function definition for other indicators ...
# =================================================================================================



# =================================================================================================
coroutines_map: dict[type, Callable] = {Supertrend: supertrend_task,
                                        }    # function mappingfor other indicators ...
# =================================================================================================