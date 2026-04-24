from dataclasses import dataclass
from typing import List, Optional
import math
from config.database import get_db_connection

@dataclass
class ValidationMessage:
    severity: str  # 'WARNING' or 'CRITICAL'
    message: str

@dataclass
class ValidationResult:
    is_valid: bool
    messages: List[ValidationMessage]

class InputValidator:
    
    def _log_event(self, error_type: str, severity: str, message: str, 
                   field_name: str = None, attempted_value: str = None, 
                   session_id: int = None, gambler_id: int = None):
        """Persists the validation event to the database for auditing."""
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO VALIDATION_EVENTS (session_id, gambler_id, error_type, severity, field_name, attempted_value, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (session_id, gambler_id, error_type, severity, field_name, str(attempted_value)[:255], message))
            conn.commit()
        except Exception as e:
            print(f"[System Log] Failed to record validation event: {e}")
        finally:
            cursor.close()
            conn.close()

    def validate_stake(self, stake: float, gambler_id: int = None) -> ValidationResult:
        messages = []
        is_valid = True
        
        if stake is None or math.isnan(stake) or math.isinf(stake):
            msg = "Stake must be a valid finite number."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("STAKE_ERROR", "CRITICAL", msg, "stake", str(stake), gambler_id=gambler_id)
            is_valid = False
            return ValidationResult(is_valid, messages)

        if stake < 0:
            msg = "Stake cannot be negative."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("STAKE_ERROR", "CRITICAL", msg, "stake", str(stake), gambler_id=gambler_id)
            is_valid = False
            
        elif stake == 0:
            messages.append(ValidationMessage("WARNING", "Stake is exactly zero. Account is effectively empty."))

        return ValidationResult(is_valid, messages)

    def validate_bet(self, bet_amount: float, current_stake: float, min_bet: float, max_bet: float, 
                     gambler_id: int = None, session_id: int = None) -> ValidationResult:
        messages = []
        is_valid = True

        if bet_amount <= 0:
            msg = "Bet amount must be greater than zero."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("BET_ERROR", "CRITICAL", msg, "bet_amount", str(bet_amount), session_id, gambler_id)
            is_valid = False
            
        if bet_amount > current_stake:
            msg = f"Insufficient funds. Attempted to bet ${bet_amount} with only ${current_stake} available."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("BET_ERROR", "CRITICAL", msg, "bet_amount", str(bet_amount), session_id, gambler_id)
            is_valid = False
            
        if bet_amount < min_bet or bet_amount > max_bet:
            msg = f"Bet amount must be between ${min_bet} and ${max_bet}."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("LIMIT_ERROR", "CRITICAL", msg, "bet_amount", str(bet_amount), session_id, gambler_id)
            is_valid = False

        if is_valid and bet_amount >= (current_stake * 0.5):
             messages.append(ValidationMessage("WARNING", "High risk bet: You are betting 50% or more of your current stake."))

        return ValidationResult(is_valid, messages)

    def validate_limits(self, lower_limit: float, upper_limit: float, initial_stake: float, gambler_id: int = None) -> ValidationResult:
        messages = []
        is_valid = True

        if lower_limit < 0:
            msg = "Lower limit cannot be negative."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("LIMIT_ERROR", "CRITICAL", msg, "lower_limit", str(lower_limit), gambler_id=gambler_id)
            is_valid = False
            
        if upper_limit <= lower_limit:
            msg = "Upper limit must be strictly greater than lower limit."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("LIMIT_ERROR", "CRITICAL", msg, "upper_limit", str(upper_limit), gambler_id=gambler_id)
            is_valid = False
            
        if initial_stake <= lower_limit or initial_stake >= upper_limit:
            msg = f"Initial stake (${initial_stake}) must be between the lower (${lower_limit}) and upper (${upper_limit}) limits."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("LIMIT_ERROR", "CRITICAL", msg, "initial_stake", str(initial_stake), gambler_id=gambler_id)
            is_valid = False

        return ValidationResult(is_valid, messages)

    def validate_probability(self, prob: float, gambler_id: int = None) -> ValidationResult:
        messages = []
        is_valid = True

        if prob < 0.0 or prob > 1.0:
            msg = "Probability must be a value between 0.0 and 1.0."
            messages.append(ValidationMessage("CRITICAL", msg))
            self._log_event("LIMIT_ERROR", "CRITICAL", msg, "win_probability", str(prob), gambler_id=gambler_id)
            is_valid = False

        return ValidationResult(is_valid, messages)