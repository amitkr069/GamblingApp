from services.game_session_manager import GameSessionManager
from models.session_models import SessionParameters
from utils.input_validator import InputValidator
from config.database import get_db_connection

def game_session_manager():
    manager = GameSessionManager()
    validator = InputValidator()
    
    try:
        g_id = int(input("\nEnter Gambler ID for Session Management: "))
    except ValueError:
        print("Invalid ID.")
        return

    print(f"Bound to Gambler ID: {g_id}")
    current_session_id = None
    
    while True:
        print(f"\n=== Session Management [Active Session: {current_session_id or 'None'}] ===")
        print("1. Start New Session")
        print("2. Pause Session")
        print("3. Resume Session")
        print("4. End Session")
        print("5. Check Boundaries (Auto-End Test)")
        print("6. View Session Summary")
        print("7. Return to Main Menu")
        choice = input("Select operation: ")
        
        if choice == '1':
            try:
                print("\n--- Session Configurations ---")
                lower = float(input("Lower Limit (Loss Stop): "))
                upper = float(input("Upper Limit (Win Stop): "))
                min_bet = float(input("Min Bet: "))
                max_bet = float(input("Max Bet: "))
                max_games = int(input("Max Games (0 for no limit): "))
                
                # Active Validation setup
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s", (g_id,))
                current_stake = float(cursor.fetchone()['current_stake'])
                cursor.close()
                conn.close()

                # Run Validations
                limit_val = validator.validate_limits(lower, upper, current_stake, gambler_id=g_id)
                if not limit_val.is_valid:
                    print("\nSession Parameter Validation Failed:")
                    for msg in limit_val.messages: print(f"  -> {msg.severity}: {msg.message}")
                    continue

                params = SessionParameters(lower_limit=lower, upper_limit=upper, min_bet=min_bet, max_bet=max_bet)
                current_session_id = manager.start_session(g_id, max_games if max_games > 0 else None, params)
                print(f"Session Started! [Session ID: {current_session_id}]")
            except ValueError:
                print("Invalid numeric input.")
            except Exception as e:
                print(f"Error: {e}")
                
        # ... Options 2 through 7 remain unchanged ...
        elif choice == '2':
            if not current_session_id: print("Start a session first."); continue
            try:
                reason = input("Enter pause reason: ")
                manager.pause_session(current_session_id, reason)
                print("Session Paused.")
            except Exception as e: print(f"Error: {e}")
                
        elif choice == '3':
            if not current_session_id: print("Start a session first."); continue
            try:
                manager.resume_session(current_session_id)
                print("Session Resumed.")
            except Exception as e: print(f"Error: {e}")
                
        elif choice == '4':
            if not current_session_id: print("Start a session first."); continue
            try:
                final_bal = manager.end_session(current_session_id, "MANUAL")
                print(f"Session Ended Manually. Final Balance: ${final_bal}")
                current_session_id = None
            except Exception as e: print(f"Error: {e}")
                
        elif choice == '5':
            if not current_session_id: print("Start a session first."); continue
            try:
                status = manager.check_boundaries(current_session_id)
                if status == "OK":
                    print("Session is within boundaries.")
                else:
                    print(f"Boundaries breached! Reason: {status}. Session auto-ended.")
                    current_session_id = None
            except Exception as e: print(f"Error: {e}")
                
        elif choice == '6':
            target_id = current_session_id or int(input("Enter past Session ID to view: "))
            try:
                summary = manager.get_session_summary(target_id)
                if not summary: print("Session not found."); continue
                
                s = summary['session']
                print(f"\n=== Session Summary ===\nStatus: {s['status']}\nNet Profit: ${summary['net_profit']}")
            except Exception as e: print(f"Error: {e}")

        elif choice == '7':
            break