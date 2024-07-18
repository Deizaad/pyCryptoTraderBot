import logging


def resolution_map(resolution: str) -> str:
    """
    Maps resolution string to proper frequency and period that are used in 
    "data.validator.is_consequtive()" function.
    """
    resolution_dict: dict = {
        '1'  : 'min',
        '5'  : '5min',
        '15' : '15min',
        '30' : '30min',
        '60' : '60min',
        '180': '180min',
        '240': '240min',
        '360': '360min',
        '720': '720min',
        'D'  : 'D' ,
        '2D' : '2D',
        '3D' : '3D',
    }
    try:
        if resolution not in resolution_dict.keys():
            raise ValueError(f'Provided resolution (timeframe) {resolution} is not in \
                             Nobitex\'s approved resolutions or has wrong data type of \
                             {type(resolution)}, str is only accepted.')
        else:
            frequency: str = resolution_dict.get(resolution, '0')

        return frequency
    except ValueError as err:
        logging.error(f'Inside "resolution_map()" function of "utils.exchange.nobitex.py" module: {err}')
        return '0'
    # ____________________________________________________________________________ . . .