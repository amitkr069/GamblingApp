from config.database import get_db_connection
from models.session_models import GameSession, SessionParameters

class GameSessionManager:

    def start_session(self, gambler_id: int, max_games: int, params: SessionParameters) -> int:
        """Initializes a new ACTIVE session if the gambler doesn't already have one."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            # 1. Prevent duplicate active sessions
            cursor.execute("""
                SELECT session_id FROM SESSIONS 
                WHERE gambler_id = %s AND status IN ('ACTIVE', 'PAUSED')
            """, (gambler_id,))
            if cursor.fetchone():
                raise ValueError("Gambler already has an active or paused session.")

            # 2. Get current stake for initialization
            cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s FOR UPDATE", (gambler_id,))
            gambler = cursor.fetchone()
            if not gambler:
                raise ValueError("Gambler not found.")
                
            starting_stake = float(gambler['current_stake'])
            
            if starting_stake < params.lower_limit or starting_stake > params.upper_limit:
                 raise ValueError(f"Starting stake ({starting_stake}) must be between limits ({params.lower_limit} - {params.upper_limit})")

            # 3. Create Session
            cursor.execute("""
                INSERT INTO SESSIONS (gambler_id, status, starting_stake, peak_stake, lowest_stake, max_games)
                VALUES (%s, 'ACTIVE', %s, %s, %s, %s)
            """, (gambler_id, starting_stake, starting_stake, starting_stake, max_games))
            session_id = cursor.lastrowid

            # 4. Save Session Parameters
            cursor.execute("""
                INSERT INTO SESSION_PARAMETERS (session_id, lower_limit, upper_limit, min_bet, max_bet, default_win_probability, max_session_minutes, strict_mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session_id, params.lower_limit, params.upper_limit, params.min_bet, params.max_bet, params.default_win_probability, params.max_session_minutes, params.strict_mode))

            conn.commit()
            return session_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def pause_session(self, session_id: int, reason: str = "Manual Pause"):
        """Pauses an active session and starts the pause timer."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            cursor.execute("SELECT status FROM SESSIONS WHERE session_id = %s FOR UPDATE", (session_id,))
            session = cursor.fetchone()
            
            if not session or session['status'] != 'ACTIVE':
                raise ValueError("Only ACTIVE sessions can be paused.")

            cursor.execute("UPDATE SESSIONS SET status = 'PAUSED' WHERE session_id = %s", (session_id,))
            
            cursor.execute("""
                INSERT INTO PAUSE_RECORDS (session_id, pause_reason, paused_at)
                VALUES (%s, %s, NOW())
            """, (session_id, reason))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def resume_session(self, session_id: int):
        """Resumes a paused session and calculates accumulated pause seconds."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            cursor.execute("SELECT status FROM SESSIONS WHERE session_id = %s FOR UPDATE", (session_id,))
            session = cursor.fetchone()
            
            if not session or session['status'] != 'PAUSED':
                raise ValueError("Only PAUSED sessions can be resumed.")

            # Find open pause record
            cursor.execute("""
                SELECT pause_id, TIMESTAMPDIFF(SECOND, paused_at, NOW()) as seconds 
                FROM PAUSE_RECORDS 
                WHERE session_id = %s AND resumed_at IS NULL 
                ORDER BY paused_at DESC LIMIT 1 FOR UPDATE
            """, (session_id,))
            pause = cursor.fetchone()

            if pause:
                pause_sec = pause['seconds']
                cursor.execute("""
                    UPDATE PAUSE_RECORDS SET resumed_at = NOW(), pause_seconds = %s WHERE pause_id = %s
                """, (pause_sec, pause['pause_id']))
                
                # Add to session total pause time
                cursor.execute("""
                    UPDATE SESSIONS SET status = 'ACTIVE', total_pause_seconds = total_pause_seconds + %s 
                    WHERE session_id = %s
                """, (pause_sec, session_id))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def end_session(self, session_id: int, end_reason: str = "MANUAL"):
        """Ends the session, closes open pauses, and records final financials."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            
            # Fetch current balance
            cursor.execute("""
                SELECT s.gambler_id, s.status, g.current_stake 
                FROM SESSIONS s JOIN GAMBLERS g ON s.gambler_id = g.gambler_id 
                WHERE s.session_id = %s FOR UPDATE
            """, (session_id,))
            data = cursor.fetchone()
            
            if not data or data['status'] in ('COMPLETED', 'TERMINATED'):
                raise ValueError("Session is already ended.")

            # If ending while paused, resolve the pause record first
            if data['status'] == 'PAUSED':
                cursor.execute("""
                    SELECT pause_id, TIMESTAMPDIFF(SECOND, paused_at, NOW()) as seconds 
                    FROM PAUSE_RECORDS WHERE session_id = %s AND resumed_at IS NULL LIMIT 1 FOR UPDATE
                """, (session_id,))
                pause = cursor.fetchone()
                if pause:
                    cursor.execute("""
                        UPDATE PAUSE_RECORDS SET resumed_at = NOW(), pause_seconds = %s WHERE pause_id = %s
                    """, (pause['seconds'], pause['pause_id']))
                    cursor.execute("UPDATE SESSIONS SET total_pause_seconds = total_pause_seconds + %s WHERE session_id = %s", (pause['seconds'], session_id))

            # Mark Session as Ended
            cursor.execute("""
                UPDATE SESSIONS 
                SET status = 'COMPLETED', end_reason = %s, ended_at = NOW(), ending_stake = %s
                WHERE session_id = %s
            """, (end_reason, data['current_stake'], session_id))

            conn.commit()
            return data['current_stake']
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def check_boundaries(self, session_id: int):
        """Actively checks if a session has breached its limits. Ends it if true."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT s.gambler_id, s.games_played, s.max_games, p.upper_limit, p.lower_limit, g.current_stake
                FROM SESSIONS s
                JOIN SESSION_PARAMETERS p ON s.session_id = p.session_id
                JOIN GAMBLERS g ON s.gambler_id = g.gambler_id
                WHERE s.session_id = %s AND s.status = 'ACTIVE'
            """, (session_id,))
            data = cursor.fetchone()
            
            if not data:
                return None # Session not active or doesn't exist
                
            current = float(data['current_stake'])
            
            if current >= float(data['upper_limit']):
                self.end_session(session_id, "WIN_LIMIT")
                return "WIN_LIMIT"
            elif current <= float(data['lower_limit']):
                self.end_session(session_id, "LOSS_LIMIT")
                return "LOSS_LIMIT"
            elif data['max_games'] and data['games_played'] >= data['max_games']:
                 self.end_session(session_id, "MANUAL") # Treat game limit as manual/natural end
                 return "GAMES_LIMIT"
                 
            return "OK"
        finally:
            cursor.close()
            conn.close()

    def get_session_summary(self, session_id: int) -> dict:
        """Retrieves session metadata, durations, and metrics."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT s.*, p.upper_limit, p.lower_limit,
                TIMESTAMPDIFF(SECOND, s.started_at, IFNULL(s.ended_at, NOW())) as total_duration_sec
                FROM SESSIONS s
                JOIN SESSION_PARAMETERS p ON s.session_id = p.session_id
                WHERE s.session_id = %s
            """, (session_id,))
            session = cursor.fetchone()
            if not session:
                return None
                
            active_sec = session['total_duration_sec'] - (session['total_pause_seconds'] or 0)
            
            # Calculate PnL
            start_stake = float(session['starting_stake'])
            end_stake = float(session['ending_stake']) if session['ending_stake'] else float(session['peak_stake']) # rough approx if not ended
            net_profit = end_stake - start_stake

            return {
                "session": session,
                "active_duration_sec": active_sec,
                "paused_duration_sec": session['total_pause_seconds'],
                "net_profit": net_profit
            }
        finally:
            cursor.close()
            conn.close()