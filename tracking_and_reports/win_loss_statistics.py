from config.database import get_db_connection

class WinLossStatistics:

    @staticmethod
    def get_latest_session_stats(session_id: int) -> dict:
        """Retrieves the most recent statistical snapshot for a session."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM RUNNING_TOTALS_SNAPSHOTS 
                WHERE session_id = %s 
                ORDER BY game_id DESC LIMIT 1
            """, (session_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_running_totals_timeline(session_id: int, limit: int = 20) -> list:
        """Fetches the game-by-game progression of the session's financials."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT r.*, g.outcome, g.net_change 
                FROM RUNNING_TOTALS_SNAPSHOTS r
                JOIN GAME_RECORDS g ON r.game_id = g.game_id
                WHERE r.session_id = %s 
                ORDER BY r.game_id ASC LIMIT %s
            """, (session_id, limit))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()