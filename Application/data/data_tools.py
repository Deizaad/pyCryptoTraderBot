import pytz
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from persiantools.jdatetime import JalaliDateTime    # type: ignore


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
# ____________________________________________________________________________ . . .


def join_raw_kline(current_data, data_piece, join_method):
    """
    This function attaches pieces of kline data to current data and returns a dictionary.
    """
    keys = ['t', 'o', 'h', 'l', 'c', 'v']

    match join_method:
        case 'PREPEND':
            # Convert lists to numpy arrays for efficient operations
            for key in keys:
                current_data[key] = np.array(current_data[key])
                data_piece[key] = np.array(data_piece[key])
            
            # Prepend new data to current data using numpy
            for key in keys:
                current_data[key] = np.concatenate((data_piece[key], current_data[key]))

            # Convert numpy arrays back to lists
            for key in keys:
                current_data[key] = current_data[key].tolist()
            
            return current_data
        
        case 'APPEND':
            raise NotImplementedError('The APPEND join_method in join_raw_kline function has no code!')
        
        case _:
            logging.error(f'Wrong join_method provided to join_raw_kline function: {join_method}')
            return {}
# ____________________________________________________________________________ . . .


def Tehran_timestamp():
    """
    This function returns the timestamp for current time in 'Asia/Tehran' timezone.
    """
    timezone = pytz.timezone('Asia/Tehran')
    time = datetime.now(timezone)
    print(time)
    timestamp = int(time.timestamp())

    return timestamp
# ____________________________________________________________________________ . . .


if __name__ == '__main__':
    raw_data = {'s': 'ok', 't': [1719228600, 1719228660, 1719228720, 1719228780, 1719228840, 
                                 1719228900, 1719228960, 1719229020, 1719229080, 1719229140, 
                                 1719229200, 1719229260, 1719229320, 1719229380, 1719229440, 
                                 1719229500, 1719229560, 1719229620, 1719229680, 1719229740], 
                                 'o': [60985.0, 60985.0, 60985.0, 60951.0, 60952.0, 
                                 60955.0, 60982.0, 60996.0, 60983.0, 60995.0, 60995.0, 60997.0, 
                                 60961.0, 60961.0, 60966.0, 60990.0, 60991.0, 60996.0, 60990.0, 
                                 60989.0], 'h': [60985.0, 60989.0, 60987.0, 60996.0, 60983.0, 
                                 60982.0, 60996.0, 60996.0, 60996.0, 60996.0, 60997.0, 60998.0, 
                                 60961.0, 60999.0, 60997.0, 60996.0, 60996.0, 60996.0, 60990.0, 
                                 60996.0], 'l': [60950.0, 60950.0, 60951.0, 60950.0, 60951.0, 
                                 60955.0, 60956.0, 60956.0, 60983.0, 60982.0, 60994.0, 60960.0, 
                                 60957.0, 60957.0, 60961.0, 60961.0, 60962.0, 60964.0, 60970.0, 
                                 60970.0], 'c': [60950.0, 60950.0, 60955.0, 60955.0, 60955.0, 
                                 60956.0, 60996.0, 60983.0, 60995.0, 60995.0, 60997.0, 60961.0, 
                                 60958.0, 60997.0, 60995.0, 60991.0, 60996.0, 60990.0, 60989.0, 
                                 60990.0], 'v': [5503.55443304, 6298.7836152988, 1880.542894261, 
                                 20501.8400133588, 2967.0603120826, 8466.2199580257, 
                                 4407.032887752, 6731.5128804735, 4086.24595, 5328.4879254301, 
                                 6609.4729541354, 5970.5679817479, 5051.3518966021, 
                                 11347.9331739157, 1435.6668853334, 1516.49, 5088.56, 
                                 4292.6875235137, 3889.6737491196, 1834.2927355984]}
    
    kline_df = parse_kline_to_df(raw_data)
    print(kline_df)