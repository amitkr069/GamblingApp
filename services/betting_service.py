import random
from config.database import get_db_connection

class BettingService:
    
    def _ensure_active_session(self, gambler_id: int, cursor) -> int:
        """Helper to guarantee a session exists to satisfy the Foreign Key constraint."""
        cursor.execute("SELECT session_id FROM SESSIONS WHERE gambler_id = %s AND status = 'ACTIVE'", (gambler_id,))
        session = cursor.fetchone()
        if session:
            return session['session_id']
            
        # Create a dummy session for testing UC-3
        cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
        stake = cursor.fetchone()['current_stake']
        cursor.execute("""
            INSERT INTO SESSIONS (gambler_id, status, starting_stake, peak_stake, lowest_stake) 
            VALUES (%s, 'ACTIVE', %s, %s, %s)
        """, (gambler_id, stake, stake, stake))
        return cursor.lastrowid

    def place_bet(self, gambler_id: int, bet_amount: float, win_probability: float, odds_value: float) -> int:
        """Deducts the stake and registers an unsettled bet."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            # 1. Lock Gambler & Validate Balance
            cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s FOR UPDATE", (gambler_id,))
            gambler = cursor.fetchone()
            if not gambler or gambler['current_stake'] < bet_amount:
                raise ValueError("Insufficient balance to place bet.")
                
            session_id = self._ensure_active_session(gambler_id, cursor)
            stake_before = float(gambler['current_stake'])
            stake_after = stake_before - bet_amount
            potential_win = bet_amount * odds_value
            
            # 2. Deduct Balance
            cursor.execute("UPDATE GAMBLERS SET current_stake = %s WHERE gambler_id = %s", (stake_after, gambler_id))
            
            # 3. Determine Game Index
            cursor.execute("SELECT COUNT(*) as c FROM BETS WHERE session_id = %s", (session_id,))
            game_idx = cursor.fetchone()['c'] + 1
            
            # 4. Insert Bet
            cursor.execute("""
                INSERT INTO BETS (session_id, gambler_id, game_index, bet_amount, win_probability, 
                                  odds_type, odds_value, potential_win, stake_before, stake_after, is_settled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, gambler_id, game_idx, bet_amount, win_probability, 'DECIMAL', odds_value, potential_win, stake_before, stake_after, False))
            
            bet_id = cursor.lastrowid
            
            # 5. Log Transaction
            cursor.execute("""
                INSERT INTO STAKE_TRANSACTIONS (session_id, gambler_id, bet_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, gambler_id, bet_id, 'BET_PLACED', bet_amount, stake_before, stake_after, f"Game {game_idx} placed"))
            
            conn.commit()
            return bet_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_bet(self, bet_id: int, forced_outcome: str = None) -> dict:
        """Resolves an unsettled bet, calculates payouts, and creates the Game Record."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            # 1. Fetch the Unsettled Bet
            cursor.execute("SELECT * FROM BETS WHERE bet_id = %s FOR UPDATE", (bet_id,))
            bet = cursor.fetchone()
            if not bet or bet['is_settled']:
                raise ValueError("Bet is invalid or already settled.")
                
            gambler_id = bet['gambler_id']
            session_id = bet['session_id']
            
            # 2. Determine Outcome
            if forced_outcome:
                outcome = forced_outcome.upper()
            else:
                roll = random.uniform(0, 1)
                outcome = 'WIN' if roll <= float(bet['win_probability']) else 'LOSS'
                
            # 3. Calculate Financials
            cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s FOR UPDATE", (gambler_id,))
            stake_before = float(cursor.fetchone()['current_stake'])
            
            payout = float(bet['potential_win']) if outcome == 'WIN' else 0.0
            loss_amount = float(bet['bet_amount']) if outcome == 'LOSS' else 0.0
            net_change = payout - float(bet['bet_amount']) # Total net movement of wealth
            stake_after = stake_before + payout
            
            # 4. Update Gambler & Bet
            cursor.execute("UPDATE GAMBLERS SET current_stake = %s WHERE gambler_id = %s", (stake_after, gambler_id))
            cursor.execute("UPDATE BETS SET is_settled = TRUE WHERE bet_id = %s", (bet_id,))
            
            # 5. Create Game Record
            cursor.execute("""
                INSERT INTO GAME_RECORDS (session_id, bet_id, outcome, payout_amount, loss_amount, net_change, stake_before, stake_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, bet_id, outcome, payout, loss_amount, net_change, stake_before, stake_after))
            game_id = cursor.lastrowid
            
            # 6. Log Settlement Transaction (If Win, record the payout)
            if outcome == 'WIN':
                cursor.execute("""
                    INSERT INTO STAKE_TRANSACTIONS (session_id, gambler_id, bet_id, game_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (session_id, gambler_id, bet_id, game_id, 'BET_WIN', payout, stake_before, stake_after, "Bet Settlement"))
            else:
                cursor.execute("""
                    INSERT INTO STAKE_TRANSACTIONS (session_id, gambler_id, bet_id, game_id, transaction_type, amount, balance_before, balance_after, transaction_ref)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (session_id, gambler_id, bet_id, game_id, 'BET_LOSS', 0.0, stake_before, stake_after, "Bet Settlement (Loss)"))

            conn.commit()
            return {"bet_id": bet_id, "outcome": outcome, "payout": payout, "new_balance": stake_after}
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def get_bet_history(self, gambler_id: int) -> list:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT b.bet_id, b.bet_amount, b.is_settled, g.outcome, g.payout_amount 
                FROM BETS b
                LEFT JOIN GAME_RECORDS g ON b.bet_id = g.bet_id
                WHERE b.gambler_id = %s ORDER BY b.placed_at DESC LIMIT 10
            """, (gambler_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()