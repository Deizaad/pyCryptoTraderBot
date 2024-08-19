class Event:
    """
    This class contains constant attributes for Event channels that are used in the project.
    """
    END_ACTIVITY   = 'active time is ended'
    SUCCESS_FETCH  = 'successfully fetched data'
    START_ACTIVITY = 'active time is started'
    NEW_KLINE_DATA = 'new kline data arrived'
    VALID_TP_SIGNAL   = 'there is a valid tp signal'
    VALID_SL_SIGNAL   = 'there is a valid sl signal'
    MARKET_IS_VALID   = 'market is valid'
    TRADE_GOT_CLOSED  = 'current trade got closed'
    THERE_IS_NO_TRADE = 'there is no open trade'
    VALID_ENTRY_SIGNAL   = 'there is a valid entry signal'
    VALID_TP_SL_SIGNAL   = 'there is a valid combo tp_sl signal'
    NEW_TRADING_SIGNAL   = 'there are new trading signals available'
    LATE_TRADING_SIGNAL  = 'there are late trading signals available'
    NEW_INDICATORS_DATA  = 'new indicators data arrived'
    OPEN_POSITIONS_EXIST = 'there are open positions available'
    NEW_VALIDATION_INDICATOR_DATA   = 'there are new data available for validation indicators'
    RECOVERY_MECHANISM_ACCOMPLISHED = 'recovery mechanism is done successfully'