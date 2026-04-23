from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class BettingPreferences:
    min_bet: float
    max_bet: float
    preferred_game_type: str = 'ALL'
    auto_play_enabled: bool = False
    auto_play_max_games: int = 0
    session_loss_limit: Optional[float] = None
    session_win_target: Optional[float] = None
    preference_id: Optional[int] = None
    gambler_id: Optional[int] = None
    updated_at: Optional[datetime] = None

@dataclass
class GamblerProfile:
    username: str
    initial_stake: float
    win_threshold: float
    loss_threshold: float
    min_required_stake: float
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    current_stake: Optional[float] = None
    gambler_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None