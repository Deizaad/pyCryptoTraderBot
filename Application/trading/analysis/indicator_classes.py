class Indicator:
    def __init__(self, name, *params):
        self.name = name
        self.params = params

    def __repr__(self):
        return f"{self.name}({', '.join(map(str, self.params))})"

class SMA(Indicator):
    def __init__(self, period):
        super().__init__('SMA', period)
        if period <= 0:
            raise ValueError("Period must be positive")

class EMA(Indicator):
    def __init__(self, period):
        super().__init__('EMA', period)
        if period <= 0:
            raise ValueError("Period must be positive")

class RSI(Indicator):
    def __init__(self, period):
        super().__init__('RSI', period)
        if period <= 0:
            raise ValueError("Period must be positive")

class BollingerBands(Indicator):
    def __init__(self, period):
        super().__init__('BollingerBands', period)
        if period <= 0:
            raise ValueError("Period must be positive")

class MACD(Indicator):
    def __init__(self, fast, slow, signal):
        super().__init__('MACD', fast, slow, signal)
        if fast <= 0 or slow <= 0 or signal <= 0:
            raise ValueError("All periods must be positive")
        if fast >= slow:
            raise ValueError("Fast period must be less than slow period")

class Supertrend(Indicator):
    def __init__(self, window: int, factor: float):
        """
        Supertrend indicator data class

        parameters:
            window (int): The atr period to calculate supertrend values.
            factor (float): The multiplier to offset the supertrend value from source price.
        """
        super().__init__('Supertrend', window, factor)
        if window <= 0:
            raise ValueError("Window most be positive")

# Example of an indicator without parameters
class Volume(Indicator):
    def __init__(self):
        super().__init__('Volume')
