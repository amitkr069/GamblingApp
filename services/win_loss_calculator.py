from config.database import get_db_connection

class WinLossCalculator:

    def update_running_totals(self, session_id: int, game_id: int):
        """
        Calculates session statistics up to the current game, updates streaks, 
        and creates an immutable snapshot of the running totals.
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()

            # 1. Fetch current game details and session starting stake
            cursor.execute("""
                SELECT g.outcome, g.payout_amount, g.loss_amount, g.net_change, s.starting_stake 
                FROM GAME_RECORDS g
                JOIN SESSIONS s ON g.session_id = s.session_id
                WHERE g.game_id = %s FOR UPDATE
            """, (game_id,))
            game = cursor.fetchone()
            
            if not game:
                raise ValueError("Game record not found.")

            # 2. Fetch the most recent snapshot for this session
            cursor.execute("""
                SELECT * FROM RUNNING_TOTALS_SNAPSHOTS 
                WHERE session_id = %s AND game_id < %s 
                ORDER BY game_id DESC LIMIT 1 FOR UPDATE
            """, (session_id, game_id))
            prev = cursor.fetchone()

            # 3. Initialize or carry over previous totals
            totals = prev if prev else {
                'total_games': 0, 'total_wins': 0, 'total_losses': 0, 'total_pushes': 0,
                'total_winnings': 0.0, 'total_losses_amount': 0.0, 'net_profit': 0.0,
                'longest_win_streak': 0, 'longest_loss_streak': 0,
                'current_win_streak': 0, 'current_loss_streak': 0  # Temporary trackers
            }

            # Retrieve current streaks from the last game record if a previous snapshot exists
            curr_w_streak = 0
            curr_l_streak = 0
            if prev:
                cursor.execute("SELECT consecutive_win_streak, consecutive_loss_streak FROM GAME_RECORDS WHERE game_id = %s", (prev['game_id'],))
                last_game = cursor.fetchone()
                curr_w_streak = last_game['consecutive_win_streak'] if last_game else 0
                curr_l_streak = last_game['consecutive_loss_streak'] if last_game else 0

            # 4. Calculate New Values
            totals['total_games'] += 1
            totals['net_profit'] += float(game['net_change'])
            
            if game['outcome'] == 'WIN':
                totals['total_wins'] += 1
                totals['total_winnings'] += float(game['payout_amount'])
                curr_w_streak += 1
                curr_l_streak = 0
            elif game['outcome'] == 'LOSS':
                totals['total_losses'] += 1
                totals['total_losses_amount'] += float(game['loss_amount'])
                curr_l_streak += 1
                curr_w_streak = 0
            else: # PUSH
                totals['total_pushes'] += 1
                curr_w_streak = 0
                curr_l_streak = 0

            # Update longest streaks
            longest_w = max(totals['longest_win_streak'], curr_w_streak)
            longest_l = max(totals['longest_loss_streak'], curr_l_streak)

            # Advanced Metrics
            win_rate = totals['total_wins'] / totals['total_games'] if totals['total_games'] > 0 else 0.0
            
            # Profit Factor = Gross Winning / Gross Loss
            if totals['total_losses_amount'] > 0:
                profit_factor = totals['total_winnings'] / totals['total_losses_amount']
            else:
                profit_factor = totals['total_winnings'] if totals['total_winnings'] > 0 else 0.0

            # ROI = Net Profit / Starting Stake
            roi = totals['net_profit'] / float(game['starting_stake']) if float(game['starting_stake']) > 0 else 0.0

            # 5. Update the Game Record with current streaks
            cursor.execute("""
                UPDATE GAME_RECORDS 
                SET consecutive_win_streak = %s, consecutive_loss_streak = %s 
                WHERE game_id = %s
            """, (curr_w_streak, curr_l_streak, game_id))

            # 6. Insert new Snapshot
            cursor.execute("""
                INSERT INTO RUNNING_TOTALS_SNAPSHOTS (
                    session_id, game_id, total_games, total_wins, total_losses, total_pushes,
                    total_winnings, total_losses_amount, net_profit, win_rate, profit_factor, 
                    roi, longest_win_streak, longest_loss_streak
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id, game_id, totals['total_games'], totals['total_wins'], totals['total_losses'], 
                totals['total_pushes'], totals['total_winnings'], totals['total_losses_amount'], 
                totals['net_profit'], win_rate, profit_factor, roi, longest_w, longest_l
            ))

            conn.commit()
            return cursor.lastrowid

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()