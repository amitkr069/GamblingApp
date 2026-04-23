from .base_strategy import BettingStrategy

class FixedStrategy(BettingStrategy):
    def calculate_next_bet(self, base_amount: float, history: list) -> float:
        """Always bets the same fixed amount."""
        return base_amount