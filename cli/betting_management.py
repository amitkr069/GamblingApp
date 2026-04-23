from services.betting_service import BettingService
from strategies.fixed_strategy import FixedStrategy
from strategies.martingale_strategy import MartingaleStrategy

def betting_management():
    """Sub-menu for UC-03: Betting Mechanism"""
    service = BettingService()
    
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
                
                bet_id = service.place_bet(g_id, amt, prob, odds)
                print(f"Bet placed successfully! [Bet ID: {bet_id}]")
                print("Remember to Resolve this bet using Option 2!")
            except Exception as e:
                print(f"Error: {e}")
                
        elif choice == '2':
            try:
                bet_id = int(input("Enter Bet ID to resolve: "))
                force = input("Force outcome? (W for Win, L for Loss, Enter for Random): ").upper()
                
                outcome = 'WIN' if force == 'W' else ('LOSS' if force == 'L' else None)
                
                result = service.resolve_bet(bet_id, forced_outcome=outcome)
                print("\n--- BET SETTLED ---")
                print(f"Outcome: {result['outcome']}")
                print(f"Payout: ${result['payout']}")
                print(f"New Balance: ${result['new_balance']}")
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
                    # Calculate amount using the selected strategy
                    current_bet = strategy.calculate_next_bet(base_amt, history)
                    print(f"Round {i+1}: Attempting to bet ${current_bet:.2f}...")
                    
                    # Place & Resolve instantly
                    bet_id = service.place_bet(g_id, current_bet, 0.48, 2.0) # 48% chance, 2.0 odds
                    res = service.resolve_bet(bet_id)
                    
                    # Store result so the strategy can calculate the NEXT bet
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
                print(f"{'Bet ID':<8} | {'Amount':<8} | {'Status':<10} | {'Outcome':<8} | {'Payout'}")
                print("-" * 55)
                for b in history:
                    status = "Settled" if b['is_settled'] else "Pending"
                    outcome = b['outcome'] or "N/A"
                    payout = f"${b['payout_amount']}" if b['payout_amount'] is not None else "N/A"
                    print(f"{b['bet_id']:<8} | ${b['bet_amount']:<7} | {status:<10} | {outcome:<8} | {payout}")
            except Exception as e:
                 print(f"Error: {e}")

        elif choice == '5':
            break
        else:
            print("Invalid selection.")