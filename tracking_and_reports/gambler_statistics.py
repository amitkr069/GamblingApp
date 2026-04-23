from config.database import get_db_connection

class GamblerStatistics:
    
    @staticmethod
    def get_financial_status(gambler_id: int) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT current_stake, initial_stake, win_threshold, loss_threshold 
                FROM GAMBLERS WHERE gambler_id = %s
            """, (gambler_id,))
            status = cursor.fetchone()
            
            if status:
                status['net_profit'] = status['current_stake'] - status['initial_stake']
                status['distance_to_win'] = status['win_threshold'] - status['current_stake']
                status['distance_to_loss'] = status['current_stake'] - status['loss_threshold']
            
            return status
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_profile_summary(gambler_id: int) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM GAMBLERS WHERE gambler_id = %s", (gambler_id,))
            gambler = cursor.fetchone()
            
            cursor.execute("SELECT * FROM BETTING_PREFERENCES WHERE gambler_id = %s", (gambler_id,))
            prefs = cursor.fetchone()
            
            return {"gambler": gambler, "preferences": prefs}
        finally:
            cursor.close()
            conn.close()

