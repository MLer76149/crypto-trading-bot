"""
bot/risk.py
Position sizing, stop-loss and take-profit calculations.
"""


class RiskManager:
    def __init__(self, config: dict):
        self.max_position_size = config["max_position_size"]
        self.stop_loss_pct = config["stop_loss_pct"]
        self.take_profit_pct = config["take_profit_pct"]

    def position_size(self, capital: float, price: float) -> float:
        """Units to buy given available capital."""
        return (capital * self.max_position_size) / price

    def stop_loss_price(self, entry_price: float, side: str) -> float:
        if side == "buy":
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    def take_profit_price(self, entry_price: float, side: str) -> float:
        if side == "buy":
            return entry_price * (1 + self.take_profit_pct)
        return entry_price * (1 - self.take_profit_pct)
