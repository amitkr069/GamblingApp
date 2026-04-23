from config.database import get_db_connection

class StakeManagementService:

    def process_transaction(self, gambler_id: int, transaction_type: str, amount: float, 
                            session_id: int = None, bet_id: int = None, game_id: int = None, 
                            ref: str = None) -> float:
        """
        Executes a financial transaction, updates the gambler's current stake,
        logs the transaction immutably, and updates session peaks if applicable.
        """
        if amount < 0 and transaction_type not in ['BET_LOSS', 'BET_PLACED', 'WITHDRAWAL']:
            raise ValueError("Amount cannot be negative for this transaction type.")

        conn = get_db_connection()
        if not conn:
            raise Exception("Database connection failed.")
            
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()

            # 1. Lock the Gambler row and get current balance
            cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s FOR UPDATE", (gambler_id,))
            gambler = cursor.fetchone()
            if not gambler:
                raise ValueError("Gambler not found.")
                
            balance_before = float(gambler['current_stake'])
            
            # Calculate new balance based on transaction type
            if transaction_type in ['BET_PLACED', 'WITHDRAWAL', 'BET_LOSS']:
                balance_after = balance_before - abs(amount)
            else: # DEPOSIT, BET_WIN, ADJUSTMENT
                balance_after = balance_before + abs(amount)

            if balance_after < 0:
                raise ValueError(f"Insufficient funds. Current balance: {balance_before}")

            # 2. Update Gambler Balance
            cursor.execute("""
                UPDATE GAMBLERS SET current_stake = %s WHERE gambler_id = %s
            """, (balance_after, gambler_id))

            # 3. Log the Stake Transaction
            cursor.execute("""
                INSERT INTO STAKE_TRANSACTIONS 
                (gambler_id, session_id, bet_id, game_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (gambler_id, session_id, bet_id, game_id, transaction_type, abs(amount), balance_before, balance_after, ref))

            # 4. Monitor & Update Session Extremes (Peak/Lowest)
            if session_id:
                cursor.execute("""
                    SELECT peak_stake, lowest_stake FROM SESSIONS WHERE session_id = %s FOR UPDATE
                """, (session_id,))
                session = cursor.fetchone()
                
                if session:
                    new_peak = max(balance_after, float(session['peak_stake'] or balance_after))
                    new_lowest = min(balance_after, float(session['lowest_stake'] or balance_after))
                    
                    cursor.execute("""
                        UPDATE SESSIONS SET peak_stake = %s, lowest_stake = %s WHERE session_id = %s
                    """, (new_peak, new_lowest, session_id))

            conn.commit()
            return balance_after
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_real_time_balance(self, gambler_id: int) -> float:
        """Fetches the immediate current balance."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            result = cursor.fetchone()
            return float(result['current_stake']) if result else 0.0
        finally:
            cursor.close()
            conn.close()

    def validate_boundaries(self, gambler_id: int, current_balance: float) -> dict:
        """
        Validates if the current balance has breached the gambler's global upper/lower limits.
        (Session-specific limits would be checked here too once UC-4 is built).
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT win_threshold, loss_threshold FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            limits = cursor.fetchone()
            
            if not limits:
                raise ValueError("Gambler not found.")
                
            status = {
                "upper_limit_reached": current_balance >= float(limits['win_threshold']),
                "lower_limit_reached": current_balance <= float(limits['loss_threshold']),
                "current_balance": current_balance,
                "win_threshold": float(limits['win_threshold']),
                "loss_threshold": float(limits['loss_threshold'])
            }
            return status
        finally:
            cursor.close()
            conn.close()

