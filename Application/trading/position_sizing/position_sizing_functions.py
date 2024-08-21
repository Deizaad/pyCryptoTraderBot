



def risk_adjusted_kelly_margin_sizing(capital               : float,
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
    print(position_size_by_risk)

    # Calculating position size by kelly fraction
    kelly_fraction = max(0, (win_rate - ((1 - win_rate) / win_loss_ratio)))
    kelly_position_size = round((kelly_fraction * capital * leverage), 2)
    print(kelly_position_size)

    # chosing final position size
    final_position_size = min(position_size_by_risk, kelly_position_size)
    return final_position_size


def risk_adjusted_with_kelly_criterion_margin_sizing():
    """
    
    """
    pass


if __name__ == '__main__':
    position_size = risk_adjusted_kelly_margin_sizing(capital               = 100000,
                                                      risk_per_trade_pct    = 0.02,
                                                      leverage              = 2,
                                                      win_rate              = 0.55,
                                                      win_loss_ratio        = 2.5,
                                                      stop_loss_pct         = 0.03,
                                                      probable_slippage_pct = 0.005)
    
    print(position_size)