class Event:
    """
    This class contains constant attributes for Event channels that are used in the project.
    """
    START_ACTIVITY  = 'active time is started'
    END_ACTIVITY    = 'active time is ended'
    SUCCESS_FETCH   = 'successfully fetched data'
    NEW_KLINE_DATA  = 'new kline data arrived'
    OPEN_POSITIONS_EXIST    = 'there are open positions available'
    EXIT_RECOVERY_MECHANISM = 'exiting the recovery mechanism'