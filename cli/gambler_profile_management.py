from models.gambler_profile import GamblerProfile, BettingPreferences
from services.gambler_profile_service import GamblerProfileService
from tracking_and_reports.gambler_statistics import GamblerStatistics

def gambler_profile():
    """Sub-menu for UC-01: Gambler Profile Management"""
    service = GamblerProfileService()
    stats = GamblerStatistics()
    
    while True:
        print("\n=== UC-01: Gambler Profile Management ===")
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
                win_th = float(input("Win Threshold: "))
                loss_th = float(input("Loss Threshold: "))
                min_req = float(input("Min Required Stake: "))
                
                min_bet = float(input("Min Bet: "))
                max_bet = float(input("Max Bet: "))
                
                profile = GamblerProfile(username=username, full_name=full_name, initial_stake=initial, 
                                         win_threshold=win_th, loss_threshold=loss_th, min_required_stake=min_req)
                prefs = BettingPreferences(min_bet=min_bet, max_bet=max_bet)
                
                g_id = service.create_profile(profile, prefs)
                print(f"Profile created. ID: {g_id}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '2':
            try:
                g_id = int(input("Gambler ID: "))
                name = input("New Full Name: ")
                w_th = float(input("New Win Threshold: "))
                l_th = float(input("New Loss Threshold: "))
                service.update_profile(g_id, name, w_th, l_th)
                print("Profile updated.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '3':
            try:
                g_id = int(input("Gambler ID: "))
                summary = stats.get_profile_summary(g_id)
                finances = stats.get_financial_status(g_id)
                
                if summary['gambler']:
                    print("\n--- Summary ---")
                    print(f"Name: {summary['gambler']['full_name']} (@{summary['gambler']['username']})")
                    print(f"Active: {summary['gambler']['is_active']}")
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
                print(f"Eligibility: {'Valid for Session' if is_eligible else 'Insufficient Funds/Inactive'}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '5':
            try:
                g_id = int(input("Gambler ID: "))
                n_init, n_win, n_loss = service.reset_profile(g_id)
                print(f"Profile Reset. New Baseline: {n_init} (Win Limit: {n_win}, Loss Limit: {n_loss})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == '6':
            break
        else:
            print("Invalid selection.")