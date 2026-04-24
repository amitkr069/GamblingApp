from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class SessionParameters:
    lower_limit: float
    upper_limit: float
    min_bet: float
    max_bet: float
    default_win_probability: float = 0.5000
    max_session_minutes: Optional[int] = None
    strict_mode: bool = True
    session_id: Optional[int] = None

@dataclass
class GameSession:
    gambler_id: int
    starting_stake: float
    max_games: Optional[int] = None
    session_id: Optional[int] = None
    status: str = 'ACTIVE'
    peak_stake: Optional[float] = None
    lowest_stake: Optional[float] = None