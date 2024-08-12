class Event:
    """
    This class contains constant attributes for Event channels that are used in the project.
    """
    START_ACTIVITY  = 'active time is started'
    END_ACTIVITY    = 'active time is ended'
    SUCCESS_FETCH   = 'successfully fetched data'
    NEW_KLINE_DATA  = 'new kline data arrived'
    MARKET_IS_VALID = 'market is valid'
    OPEN_POSITIONS_EXIST    = 'there are open positions available'
    RECOVERY_MECHANISM_ACCOMPLISHED = 'recovery mechanism is done successfully'
    NEW_VALIDATION_INDICATOR_DATA   = 'there are new data available for validation indicators'