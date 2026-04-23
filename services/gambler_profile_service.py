from config.database import get_db_connection
from models.gambler_profile import GamblerProfile, BettingPreferences

class GamblerProfileService:

    def create_profile(self, profile: GamblerProfile, prefs: BettingPreferences) -> int:
        if profile.initial_stake <= 0:
            raise ValueError("Initial stake must be > 0.")
        if profile.win_threshold <= profile.initial_stake:
            raise ValueError("Win threshold must be greater than initial stake.")
        if profile.loss_threshold >= profile.initial_stake:
            raise ValueError("Loss threshold must be less than initial stake.")
        if prefs.min_bet <= 0 or prefs.max_bet < prefs.min_bet:
            raise ValueError("Invalid bet limits. Min bet > 0, Max bet >= Min bet.")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            conn.start_transaction()

            # Insert Gambler
            cursor.execute("""
                INSERT INTO GAMBLERS (username, full_name, email, initial_stake, current_stake, win_threshold, loss_threshold, min_required_stake, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (profile.username, profile.full_name, profile.email, profile.initial_stake, 
                  profile.initial_stake, profile.win_threshold, profile.loss_threshold, profile.min_required_stake, profile.is_active))
            
            gambler_id = cursor.lastrowid

            # Insert Preferences
            cursor.execute("""
                INSERT INTO BETTING_PREFERENCES (gambler_id, min_bet, max_bet, preferred_game_type, auto_play_enabled, auto_play_max_games, session_loss_limit, session_win_target)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (gambler_id, prefs.min_bet, prefs.max_bet, prefs.preferred_game_type, 
                  prefs.auto_play_enabled, prefs.auto_play_max_games, prefs.session_loss_limit, prefs.session_win_target))

            # Log Stake Transaction
            cursor.execute("""
                INSERT INTO STAKE_TRANSACTIONS (gambler_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (gambler_id, 'INITIAL_STAKE', profile.initial_stake, 0.00, profile.initial_stake, "Profile Creation"))

            conn.commit()
            return gambler_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def update_profile(self, gambler_id: int, full_name: str, win_threshold: float, loss_threshold: float):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            current = cursor.fetchone()['current_stake']
            
            if win_threshold <= current or loss_threshold >= current:
                raise ValueError(f"Limits invalid based on current stake ({current}).")

            cursor.execute("""
                UPDATE GAMBLERS 
                SET full_name = %s, win_threshold = %s, loss_threshold = %s 
                WHERE gambler_id = %s
            """, (full_name, win_threshold, loss_threshold, gambler_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def reset_profile(self, gambler_id: int):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            cursor.execute("SELECT initial_stake, current_stake, win_threshold, loss_threshold FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            data = cursor.fetchone()

            # Proportional threshold calculation
            win_ratio = data['win_threshold'] / data['initial_stake']
            loss_ratio = data['loss_threshold'] / data['initial_stake']

            new_initial = data['current_stake']
            new_win_target = new_initial * win_ratio
            new_loss_target = new_initial * loss_ratio

            # Update Gambler
            cursor.execute("""
                UPDATE GAMBLERS 
                SET initial_stake = %s, win_threshold = %s, loss_threshold = %s 
                WHERE gambler_id = %s
            """, (new_initial, new_win_target, new_loss_target, gambler_id))

            # Log Transaction
            cursor.execute("""
                INSERT INTO STAKE_TRANSACTIONS (gambler_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (gambler_id, 'RESET', 0.00, new_initial, new_initial, "Session Reset"))

            conn.commit()
            return new_initial, new_win_target, new_loss_target
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def validate_eligibility(self, gambler_id: int) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT current_stake, min_required_stake, is_active FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            result = cursor.fetchone()
            if result and result['is_active']:
                return result['current_stake'] >= result['min_required_stake']
            return False
        finally:
            cursor.close()
            conn.close()