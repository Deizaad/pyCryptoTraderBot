

def wait_time(interval: float, current_time: float, last_fetch: float) -> float:
    """
    Calculates required wait time before next subsequent request for constant API calls .

    Parameters:
        interval (float): Maximum accepted call interval (gained by deviding the "RatePeriod" to "RateLimit").
        current_time (float): Current timestamp.
        last_fetch (float): last request's timestamp.

    Returns: 
        wait_time (float): Value of wait time.
    """
    wait_time = max(0, (interval - (current_time - last_fetch)))
    return wait_time
# ____________________________________________________________________________ . . .