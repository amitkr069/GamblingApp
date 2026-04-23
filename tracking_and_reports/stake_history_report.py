from config.database import get_db_connection

class StakeHistoryReport:

    @staticmethod
    def get_transaction_history(gambler_id: int, limit: int = 50) -> list:
        """Retrieves the chronological audit trail of stake changes."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT transaction_id, transaction_type, amount, balance_before, balance_after, transaction_ref, created_at 
                FROM STAKE_TRANSACTIONS 
                WHERE gambler_id = %s 
                ORDER BY created_at DESC LIMIT %s
            """, (gambler_id, limit))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_volatility_summary(gambler_id: int, session_id: int = None) -> dict:
        """Calculates stake volatility and groups transaction summaries."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # 1. Get Transaction Groupings (Total won, total lost, deposits)
            query = """
                SELECT transaction_type, COUNT(*) as count, SUM(amount) as total_volume 
                FROM STAKE_TRANSACTIONS 
                WHERE gambler_id = %s 
            """
            params = [gambler_id]
            if session_id:
                query += " AND session_id = %s "
                params.append(session_id)
                
            query += " GROUP BY transaction_type"
            cursor.execute(query, tuple(params))
            transactions_summary = cursor.fetchall()

            # 2. Get Global Volatility (Max ever vs Min ever) if no session provided
            if not session_id:
                cursor.execute("""
                    SELECT MAX(balance_after) as global_peak, MIN(balance_after) as global_lowest 
                    FROM STAKE_TRANSACTIONS WHERE gambler_id = %s
                """, (gambler_id,))
                extremes = cursor.fetchone()
            else:
                # If session provided, pull from the SESSIONS table cache
                cursor.execute("""
                    SELECT starting_stake, peak_stake, lowest_stake 
                    FROM SESSIONS WHERE session_id = %s
                """, (session_id,))
                session_data = cursor.fetchone()
                extremes = {
                    "global_peak": session_data['peak_stake'] if session_data else 0.0,
                    "global_lowest": session_data['lowest_stake'] if session_data else 0.0
                }

            peak = float(extremes['global_peak'] or 0.0)
            lowest = float(extremes['global_lowest'] or 0.0)
            volatility_spread = peak - lowest

            return {
                "transaction_breakdown": transactions_summary,
                "peak_stake": peak,
                "lowest_stake": lowest,
                "volatility_spread": volatility_spread
            }
        finally:
            cursor.close()
            conn.close()

