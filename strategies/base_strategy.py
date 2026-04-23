from abc import ABC, abstractmethod

class BettingStrategy(ABC):
    @abstractmethod
    def calculate_next_bet(self, base_amount: float, history: list) -> float:
        """Calculates the bet amount for the next game based on previous outcomes."""
        pass