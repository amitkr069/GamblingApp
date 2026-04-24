from services.betting_service import BettingService
from strategies.fixed_strategy import FixedStrategy
from strategies.martingale_strategy import MartingaleStrategy
from utils.input_validator import InputValidator
from config.database import get_db_connection

def betting_management():
    service = BettingService()
    validator = InputValidator()
    
    try:
        g_id = int(input("\nEnter Gambler ID to bind for betting: "))
    except ValueError:
        print("Invalid ID.")
        return

    print(f"Bound to Gambler ID: {g_id}")
    
    while True:
        print("\n=== UC-03: Betting Mechanism ===")
        print("1. Place a Single Bet")
        print("2. Resolve an Unsettled Bet")
        print("3. Auto-Play (Simulate 5 Rounds with Strategy)")
        print("4. View Recent Bet History")
        print("5. Return to Main Menu")
        choice = input("Select operation: ")
        
        if choice == '1':
            try:
                amt = float(input("Bet Amount: "))
                prob = float(input("Win Probability (e.g., 0.50 for 50%): "))
                odds = float(input("Decimal Odds (e.g., 2.0 for double payout): "))
                
                # Active Validation Setup
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT current_stake FROM GAMBLERS WHERE gambler_id = %s", (g_id,))
                current_stake = cursor.fetchone()['current_stake']
                cursor.close()
                conn.close()

                # Run Validations
                bet_val = validator.validate_bet(amt, float(current_stake), min_bet=1, max_bet=100000, gambler_id=g_id)
                prob_val = validator.validate_probability(prob, gambler_id=g_id)
                
                if not bet_val.is_valid or not prob_val.is_valid:
                    print("\nBet Validation Failed:")
                    for msg in bet_val.messages + prob_val.messages:
                        print(f"  -> {msg.severity}: {msg.message}")
                    continue

                bet_id = service.place_bet(g_id, amt, prob, odds)
                print(f"Bet placed successfully! [Bet ID: {bet_id}]")
            except ValueError:
                print("Invalid numeric input.")
            except Exception as e:
                print(f"Error: {e}")
                
        # ... Options 2, 3, 4, and 5 remain unchanged ...
        elif choice == '2':
            try:
                bet_id = int(input("Enter Bet ID to resolve: "))
                force = input("Force outcome? (W for Win, L for Loss, Enter for Random): ").upper()
                outcome = 'WIN' if force == 'W' else ('LOSS' if force == 'L' else None)
                
                result = service.resolve_bet(bet_id, forced_outcome=outcome)
                print("\n--- BET SETTLED ---")
                print(f"Outcome: {result['outcome']} | Payout: ${result['payout']} | New Balance: ${result['new_balance']}")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '3':
            try:
                base_amt = float(input("Enter Base Bet Amount: "))
                print("Select Strategy:\n1. Fixed\n2. Martingale")
                strat_choice = input("Choice: ")
                strategy = MartingaleStrategy() if strat_choice == '2' else FixedStrategy()
                history = []
                
                print("\n--- Starting Auto-Play (5 Rounds) ---")
                for i in range(5):
                    current_bet = strategy.calculate_next_bet(base_amt, history)
                    print(f"Round {i+1}: Attempting to bet ${current_bet:.2f}...")
                    bet_id = service.place_bet(g_id, current_bet, 0.48, 2.0)
                    res = service.resolve_bet(bet_id)
                    history.append({'bet_amount': current_bet, 'outcome': res['outcome']})
                    print(f"   -> Result: {res['outcome']} | New Balance: ${res['new_balance']:.2f}")
            except Exception as e:
                print(f"Auto-Play Halted: {e}")

        elif choice == '4':
            try:
                history = service.get_bet_history(g_id)
                if not history:
                    print("No bets found.")
                    continue
                print("\n--- Recent Bets ---")
                for b in history:
                    print(f"ID: {b['bet_id']} | ${b['bet_amount']} | {b['outcome'] or 'Pending'} | Payout: {b['payout_amount']}")
            except Exception as e:
                 print(f"Error: {e}")

        elif choice == '5':
            break