import os
import sys
import unittest
import pandas as pd
from dotenv import load_dotenv
from persiantools.jdatetime import JalaliDateTime    # type: ignore

load_dotenv('project_path.env')
path = os.getenv('PYTHONPATH')
if path:
    sys.path.append(path)

from Application.data.validator import is_consistent, is_unique, is_sorted, is_consequtive, turn_Jalali_to_gregorian    # noqa: E402

class TestValidatorModule(unittest.TestCase):

    def setUp(self):
        # Create some sample data
        self.dataframe = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            'value': [1, 2, 3]
        }).set_index('date')

        self.jalali_dates = pd.Series([
            JalaliDateTime(1401, 1, 1),
            JalaliDateTime(1401, 1, 2),
            JalaliDateTime(1401, 1, 3)
        ])

        self.gregorian_dates = pd.Series([
            pd.Timestamp('2022-03-21'),
            pd.Timestamp('2022-03-22'),
            pd.Timestamp('2022-03-23')
        ])

    def test_is_unique(self):
        unique_series = pd.Series([1, 2, 3, 4, 5])
        non_unique_series = pd.Series([1, 2, 2, 4, 5])
        self.assertTrue(is_unique(unique_series))
        self.assertFalse(is_unique(non_unique_series))

    def test_is_sorted(self):
        sorted_series = pd.Series([1, 2, 3, 4, 5])
        unsorted_series = pd.Series([1, 3, 2, 4, 5])
        self.assertTrue(is_sorted(sorted_series))
        self.assertFalse(is_sorted(unsorted_series))

    def test_is_consequtive(self):
        consecutive_dates = pd.date_range(start='2023-01-01', periods=3, freq='D')
        non_consecutive_dates = pd.to_datetime(['2023-01-01', '2023-01-03', '2023-01-04'])

        self.assertTrue(is_consequtive(pd.Series(consecutive_dates), 'D'))
        self.assertFalse(is_consequtive(pd.Series(non_consecutive_dates), 'D'))

    def test_turn_Jalali_to_gregorian(self):
        converted_dates = turn_Jalali_to_gregorian(self.jalali_dates)
        pd.testing.assert_series_equal(converted_dates, self.gregorian_dates)

    def test_is_consistent(self):
        self.assertTrue(is_consistent(self.dataframe, 'D'))

        # Create a DataFrame with non-consecutive dates
        non_consecutive_df = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-03', '2023-01-04']),
            'value': [1, 2, 3]
        }).set_index('date')

        self.assertFalse(is_consistent(non_consecutive_df, 'D'))

if __name__ == '__main__':
    unittest.main()
