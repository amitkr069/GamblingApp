from models.gambler_profile import GamblerProfile, BettingPreferences
from services.gambler_profile_service import GamblerProfileService
from tracking_and_reports.gambler_statistics import GamblerStatistics
from utils.input_validator import InputValidator

def gambler_profile():
    service = GamblerProfileService()
    stats = GamblerStatistics()
    validator = InputValidator()
    
    while True:
        print("\n=== Gambler Profile Management ===")
        print("1. Create Profile")
        print("2. Update Profile")
        print("3. Retrieve Profile & Financial Status")
        print("4. Validate Eligibility")
        print("5. Reset Profile")
        print("6. Return to Main Menu")
        choice = input("Select operation: ")
        
        if choice == '1':
            try:
                username = input("Username: ")
                full_name = input("Full Name: ")
                initial = float(input("Initial Stake: "))
                win_th = float(input("Win Threshold (Upper Limit): "))
                loss_th = float(input("Loss Threshold (Lower Limit): "))
                min_req = float(input("Min Required Stake: "))
                min_bet = float(input("Min Bet: "))
                max_bet = float(input("Max Bet: "))
                
                # Active Validation
                stake_val = validator.validate_stake(initial)
                limit_val = validator.validate_limits(loss_th, win_th, initial)
                
                if not stake_val.is_valid or not limit_val.is_valid:
                    print("\nInput Validation Failed:")
                    for msg in stake_val.messages + limit_val.messages:
                        print(f"  -> {msg.severity}: {msg.message}")
                    continue # Abort creation and restart menu
                
                profile = GamblerProfile(username=username, full_name=full_name, initial_stake=initial, 
                                         win_threshold=win_th, loss_threshold=loss_th, min_required_stake=min_req)
                prefs = BettingPreferences(min_bet=min_bet, max_bet=max_bet)
                
                g_id = service.create_profile(profile, prefs)
                print(f"Profile created. ID: {g_id}")
            except ValueError:
                print("Invalid numeric input. Please enter numbers for stakes and limits.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '2':
            try:
                g_id = int(input("Gambler ID: "))
                name = input("New Full Name: ")
                w_th = float(input("New Win Threshold: "))
                l_th = float(input("New Loss Threshold: "))
                
                # Active Validation (Requires fetching current balance to test limits)
                current_bal = stats.get_financial_status(g_id)['current_stake']
                limit_val = validator.validate_limits(l_th, w_th, current_bal, gambler_id=g_id)
                
                if not limit_val.is_valid:
                    print("\nInput Validation Failed:")
                    for msg in limit_val.messages:
                        print(f"  -> {msg.severity}: {msg.message}")
                    continue

                service.update_profile(g_id, name, w_th, l_th)
                print("Profile updated.")
            except ValueError:
                print("Invalid numeric input.")
            except Exception as e:
                print(f"Error: {e}")

        # ... Options 3, 4, 5, and 6 remain unchanged ...
        elif choice == '3':
            try:
                g_id = int(input("Gambler ID: "))
                summary = stats.get_profile_summary(g_id)
                finances = stats.get_financial_status(g_id)
                if summary['gambler']:
                    print("\n--- Summary ---")
                    print(f"Name: {summary['gambler']['full_name']} (@{summary['gambler']['username']})")
                    print("\n--- Financials ---")
                    for k, v in finances.items():
                        print(f"{k}: {v}")
                else:
                    print("Not found.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '4':
            try:
                g_id = int(input("Gambler ID: "))
                is_eligible = service.validate_eligibility(g_id)
                print(f"Eligibility: {'Valid' if is_eligible else 'Insufficient Funds/Inactive'}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '5':
            try:
                g_id = int(input("Gambler ID: "))
                n_init, n_win, n_loss = service.reset_profile(g_id)
                print(f"Profile Reset. New Baseline: {n_init}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '6':
            break
        else:
            print("Invalid selection.")