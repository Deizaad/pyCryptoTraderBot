import asyncio


# =================================================================================================
async def risk_adjusted_kelly_margin_sizing(capital               : float,
                                            risk_per_trade_pct    : float,
                                            leverage              : float,
                                            win_rate              : float,
                                            win_loss_ratio        : float,
                                            stop_loss_pct         : float,
                                            probable_slippage_pct : float) -> float:
    """
    Calculate the position size based on Kelly Criterion and max loss per trade.
    Ensures that position size does not exceed max allowable risk.

    Parameters:
        capital (float): Total capital available for trading.
        risk_per_trade_pct (float): Maximum percentage of capital to risk on a single trade.
        leverage (float): Leverage used in the trade.
        win_rate (float): Historical win rate of the trading strategy (0-1).
        win_loss_ratio (float): Ratio of average win to average loss.
        stop_loss_pct (float): Initial stop loss percentage for the trade.
        probable_slippage_pct (float): Expected slippage percentage for stop-loss orders.

    Returns:
        position_size (float):
    """
    # Calculate the position size by risk
    max_loss_per_trade_value = risk_per_trade_pct * capital
    adjusted_stop_loss = stop_loss_pct + probable_slippage_pct
    position_size_by_risk = round((max_loss_per_trade_value / (adjusted_stop_loss * leverage)), 2)
    # print(position_size_by_risk)

    # Calculating position size by kelly fraction
    kelly_fraction = max(0, (win_rate - ((1 - win_rate) / win_loss_ratio)))
    kelly_position_size = round((kelly_fraction * capital * leverage), 2)
    # print(kelly_position_size)

    # chosing final position size
    final_position_size = min(position_size_by_risk, kelly_position_size)
    return final_position_size
# ________________________________________________________________________________ . . .


def risk_adjusted_with_kelly_criterion_margin_sizing():
    """
    
    """

    pass
# ________________________________________________________________________________ . . .


async def risk_adjusted_position_sizing(portfolio_balance  : float,
                                        risk_per_trade_pct : float,
                                        entry_price        : float,
                                        stop_loss_price    : float,
                                        slippage_pct       : float,
                                        maker_fee          : float,
                                        taker_fee          : float,
                                        src_currency       : str,
                                        dst_currency       : str,
                                        funding_rate_fee   : float | None = None):
    """
    Calculates position size in a way that the total risk dosn't exceed the pre defined resk per
    trade value.

    Parameters:

    Returns:
        position_size (float): 
    """
    max_risk_per_trade_value = risk_per_trade_pct * portfolio_balance
    fee_factors = (maker_fee * entry_price) + (taker_fee * stop_loss_price)
    stop_loss_distance = abs(entry_price - stop_loss_price) + (slippage_pct * stop_loss_price)

    position_size_by_risk = max_risk_per_trade_value / (stop_loss_distance + fee_factors)

    # Define the minimum position size for pair
    min_position_size = 5

    # Define the maximum position size for pair
    max_position_size = 50
    
    if min_position_size < position_size_by_risk < max_position_size:
        position_size = position_size_by_risk
    elif position_size_by_risk <= min_position_size:
        position_size = min_position_size
    else:
        position_size = max_position_size

    return position_size
# ________________________________________________________________________________ . . .


def _min_position_size(src_currency: str, dst_currency: str):
    """
    Returns the minimum profitable position size for src_currency. This value accounts for the
    minimum position size for src_currency accepted by exchange, minimum size that is still
    profitable when counting trading costs, and ...

    This function should execute once at the start of activity times or once a day to compute the
    value and return this same value every time being called in that trading session without 
    computing it again.
    """
    return 5
# ________________________________________________________________________________ . . .


def _max_position_size(src_currency: str, dst_currency: str):
    """
    Returns the maximum position size for trading pair that is still profitable while not impacting
    on market price, and ...
    """
    return 50
# ________________________________________________________________________________ . . .


def monte_carlo_position_sizing():
    """
    Uses statistical modeling to simulate a range of outcomes based on win-rate and win-to-loss
    ratio.
    """
    pass
# ________________________________________________________________________________ . . .


def volatility_based_position_sizing():
    """
    Adjusts position size based on the volatility of the trading pair and aims to normalize the 
    risk per trade regardless of the pair's volatility.
    """
    pass
# ________________________________________________________________________________ . . .


# =================================================================================================


if __name__ == '__main__':
    # position_size = asyncio.run(risk_adjusted_kelly_margin_sizing(
    #     capital               = 100000,
    #     risk_per_trade_pct    = 0.02,
    #     leverage              = 2,
    #     win_rate              = 0.55,
    #     win_loss_ratio        = 2.5,
    #     stop_loss_pct         = 0.03,
    #     probable_slippage_pct = 0.005)
    # )
    
    position_size = asyncio.run(risk_adjusted_position_sizing(portfolio_balance  = 10000.0,
                                                              risk_per_trade_pct = 0.02,
                                                              entry_price        = 256,
                                                              stop_loss_price    = 250,
                                                              slippage_pct       = 0.002,
                                                              maker_fee          = 0.001,
                                                              taker_fee          = 0.0013,
                                                              src_currency       = 'usdt',
                                                              dst_currency       = 'rls'))

    print(position_size)