from .base_strategy import BettingStrategy

class MartingaleStrategy(BettingStrategy):
    def calculate_next_bet(self, base_amount: float, history: list) -> float:
        """Doubles the bet after a loss, resets to base after a win."""
        if not history:
            return base_amount
            
        last_outcome = history[-1]['outcome']
        last_bet = history[-1]['bet_amount']
        
        if last_outcome == 'LOSS':
            return last_bet * 2
        return base_amount