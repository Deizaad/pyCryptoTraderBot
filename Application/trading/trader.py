import pandas as pd
import numpy as np

from Application.api.nb_api.order import Order


# =================================================================================================
class TradeSupervisor:
    """
    TradeSupervisor class monitors for signals and performs trading jobs.
    """
    def __init__(self, signal_df: pd.DataFrame, interval: float = 1.0):
        self.signal_df = signal_df
        self.interval = interval
        self.setups = []
        self.filters = []
    # ____________________________________________________________________________ . . .


    def job(self):
        """
        Sets trading jobs to call the order class.
        """
        pass
    # ____________________________________________________________________________ . . .


    def involve(self):
        """
        Involves setups and filters from config base on mode to the job method.
        """
        pass
    # ____________________________________________________________________________ . . .


    def _monitor(self) -> tuple[bool, dict[str, list[str]]]:
        """
        This function checks the last row of Signal DataFrame for the presence of the strings 
            'bull' or 'bear'. It returns a boolean indicating if any matches were found, andv a 
            dictionary with the strings as keys and lists of column labels as values.

        Returns: Tuple with a boolean and a dictionary. The boolean is True if any matches were 
            found, otherwise False.. The dictionary has 'bull' and 'bear' as keys and lists of 
            column labels as values.
        """
        if self.signal_df.empty:
            return False, {}
        
        last_row = self.signal_df.iloc[-1].to_numpy()
        
        columns = self.signal_df.columns.to_numpy()

        result: dict[str, list[str]] = {'bull': [], 'bear': []}

        bull_indices = np.where(last_row == 'bull')[0]
        bear_indices = np.where(last_row == 'bear')[0]

        result['bull'] = columns[bull_indices].tolist()
        result['bear'] = columns[bear_indices].tolist()

        has_match = bool(result['bull']) or bool(result['bear'])

        return has_match, result
    # ____________________________________________________________________________ . . .

    
    async def perform(self):
        """
        Performs monitor and jobs asynchronously.
        """
        pass
# =================================================================================================


data = {
    'A': [1, 2, 3, 'bull'],
    'B': [4, 5, 6, 'bear'],
    'C': [8, 'bear', 10, 'bull']
}
df = pd.DataFrame(data)
trade = TradeSupervisor(df)
trade._monitor()