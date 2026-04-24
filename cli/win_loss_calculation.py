from services.win_loss_calculator import WinLossCalculator
from tracking_and_reports.win_loss_statistics import WinLossStatistics
from config.database import get_db_connection

def win_loss_calculation():
    """Sub-menu for UC-05: Win/Loss Calculation"""
    calculator = WinLossCalculator()
    stats = WinLossStatistics()
    
    try:
        s_id = int(input("\nEnter Session ID to analyze: "))
    except ValueError:
        print("Invalid Session ID.")
        return

    print(f"Bound to Session ID: {s_id}")
    
    while True:
        print("\n=== UC-05: Win/Loss Analytics ===")
        print("1. Process Missing Game Snapshots (Sync Totals)")
        print("2. View Latest Session Statistics (Win Rate, ROI, Streaks)")
        print("3. View Running Totals Timeline")
        print("4. Return to Main Menu")
        choice = input("Select operation: ")
        
        if choice == '1':
            # Helper to find games in this session that don't have a snapshot yet
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    SELECT g.game_id FROM GAME_RECORDS g
                    LEFT JOIN RUNNING_TOTALS_SNAPSHOTS r ON g.game_id = r.game_id
                    WHERE g.session_id = %s AND r.snapshot_id IS NULL
                    ORDER BY g.game_id ASC
                """, (s_id,))
                pending_games = cursor.fetchall()
                
                if not pending_games:
                    print("All games are already synced.")
                else:
                    for game in pending_games:
                        calculator.update_running_totals(s_id, game['game_id'])
                        print(f"Processed snapshot for Game ID: {game['game_id']}")
                    print(f"Successfully synced {len(pending_games)} games.")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                cursor.close()
                conn.close()

        elif choice == '2':
            try:
                data = stats.get_latest_session_stats(s_id)
                if not data:
                    print("No statistics found. Play some games and sync first.")
                    continue
                
                print("\n=== Advanced Session Analytics ===")
                print(f"Games Played: {data['total_games']} (W:{data['total_wins']} / L:{data['total_losses']} / P:{data['total_pushes']})")
                print(f"Win Rate: {data['win_rate'] * 100:.2f}%")
                print(f"Net Profit: ${data['net_profit']:.2f}")
                print(f"Gross Winnings: ${data['total_winnings']:.2f} | Gross Losses: ${data['total_losses_amount']:.2f}")
                print(f"Profit Factor: {data['profit_factor']:.2f}x")
                print(f"Return on Investment (ROI): {data['roi'] * 100:.2f}%")
                print(f"Longest Streaks -> Win: {data['longest_win_streak']} | Loss: {data['longest_loss_streak']}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '3':
            try:
                timeline = stats.get_running_totals_timeline(s_id)
                if not timeline:
                    print("No timeline data found.")
                    continue
                
                print("\n=== Running Totals Timeline ===")
                print(f"{'Game':<6} | {'Outcome':<8} | {'Net Change':<12} | {'Total Profit':<12} | {'Win Rate'}")
                print("-" * 60)
                for t in timeline:
                    print(f"#{t['game_id']:<5} | {t['outcome']:<8} | ${t['net_change']:<11.2f} | ${t['net_profit']:<11.2f} | {t['win_rate']*100:.1f}%")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '4':
            break
        else:
            print("Invalid selection.")