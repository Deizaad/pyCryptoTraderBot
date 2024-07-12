""" TODO comment-tags:    -> DONE

DONE NO-001 configure 'os.getenv' to return "Token is not configured" in case of None.
            issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                  to: me
                  on: 2024-04-17
            perform by: me
                    on: 2024-04-19

DONE NO-002 configure Printing size of OHLC dataframe.
            issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                  to: me
                  on: 2024-04-21
            perform by: me
                    on: 2024-04-30
"""
##################################################################################################

""" FIXME comment-tags:    -> FIXED

FIXED NO-001 fix time values in trades-df should drop three zeros 000 from end.
             issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                   to: me
                   on: 2024-04-19
             perform by: me
                     on: 2024-04-20

FIXME NO-002 fix the progress bar prints again after each print in console.
             issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                   to: me
                   on: 2024-04-21

FIXME NO-003 fix update_trades() function that collects duplicate trades data.
             issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                   to: me
                   on: 2024-04-30

FIXME NO-004 fix supertrend function not reaturning values for bearish direction.
             issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                   to: me
                    on: 2024-05-20

FIXME NO-005 fix indicator dataframe populates late.
             issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                   to: me
                   on: 2024-05-26

# FIXME NO-006 there is a bug in the 'update_kline()' or 'populate_kline()' and '_last_timestamp()'
               methods of 'nobitex_api.Market' class which has been caused to fetch dissordered 
               kline data. It's recommended to refactor how 'data_processor.py' initiates and 
               streams kline data in an approach that all steps perform on data frames.
             issue by: Deizaad -> 166605426+Deizaad@users.noreply.github.com
                   to: me
                   on: 2024-07-12
""" 
##################################################################################################
