from services.stake_management_service import StakeManagementService
from tracking_and_reports.stake_history_report import StakeHistoryReport
from utils.input_validator import InputValidator

def stake_management():
    service = StakeManagementService()
    report = StakeHistoryReport()
    validator = InputValidator()
    
    try:
        g_id = int(input("\nEnter Gambler ID to bind for this session: "))
    except ValueError:
        print("Invalid ID. Returning to Main Menu.")
        return

    print(f"Testing Environment Active -> Bound to Gambler ID: {g_id}")
    
    while True:
        print("\n=== UC-02: Stake Management Operations ===")
        print("1. View Real-Time Balance")
        print("2. Process Deposit")
        print("3. Process Simulated Bet (Win/Loss)")
        print("4. Validate Boundary Conditions")
        print("5. View Transaction History")
        print("6. View Volatility Summary")
        print("7. Return to Main Menu")
        choice = input("Select operation: ")
        
        if choice == '1':
            try:
                balance = service.get_real_time_balance(g_id)
                print(f"Real-Time Balance: ${balance:.2f}")
            except Exception as e:
                print(f"Error: {e}")
            
        elif choice == '2':
            try:
                amt = float(input("Enter deposit amount: "))
                
                # Active Validation
                stake_val = validator.validate_stake(amt, gambler_id=g_id)
                if not stake_val.is_valid:
                     print("\nInvalid Deposit:")
                     for msg in stake_val.messages: print(f"  -> {msg.message}")
                     continue

                new_bal = service.process_transaction(g_id, 'DEPOSIT', amt, ref="Manual Deposit")
                print(f"Deposit successful. New Balance: ${new_bal:.2f}")
            except ValueError:
                print("Invalid numeric input.")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '3':
            try:
                type_map = {'1': 'BET_WIN', '2': 'BET_LOSS'}
                print("1. Win\n2. Loss")
                t_choice = input("Select Outcome: ")
                
                if t_choice not in type_map:
                    print("Invalid outcome.")
                    continue
                    
                amt = float(input("Enter amount won/lost: "))
                current_bal = service.get_real_time_balance(g_id)
                
                # Active Validation for Loss Simulation
                if t_choice == '2':
                    bet_val = validator.validate_bet(amt, current_bal, min_bet=0, max_bet=current_bal, gambler_id=g_id)
                    if not bet_val.is_valid:
                         print("\nInvalid Simulated Bet:")
                         for msg in bet_val.messages: print(f"  -> {msg.message}")
                         continue

                new_bal = service.process_transaction(g_id, type_map[t_choice], amt, ref="Simulated Bet")
                print(f"Transaction processed. New Balance: ${new_bal:.2f}")
            except ValueError:
                print("Invalid numeric input.")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '4':
            try:
                current_bal = service.get_real_time_balance(g_id)
                status = service.validate_boundaries(g_id, current_bal)
                print("\n--- Boundary Status ---")
                print(f"Current Balance: ${status['current_balance']}")
                print(f"Win Threshold ({status['win_threshold']}) Reached: {'YES' if status['upper_limit_reached'] else 'No'}")
                print(f"Loss Threshold ({status['loss_threshold']}) Reached: {'YES' if status['lower_limit_reached'] else 'No'}")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '5':
            try:
                history = report.get_transaction_history(g_id, limit=10)
                if not history:
                    print("No transactions found.")
                    continue
                print("\n--- Last 10 Transactions ---")
                for t in history:
                    print(f"{t['transaction_type']:<15} | ${t['amount']:<9.2f} | {t['transaction_ref']}")
            except Exception as e:
                 print(f"Error: {e}")
                
        elif choice == '6':
            try:
                summary = report.get_volatility_summary(g_id)
                print(f"\n--- Volatility Summary ---\nAll-Time Peak: ${summary['peak_stake']}")
                print(f"Total Volatility Spread: ${summary['volatility_spread']}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '7':
            break
