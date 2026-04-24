class GameStatusDisplay:
    
    @staticmethod
    def show_dashboard(gambler_name: str, current_stake: float, lower_limit: float, upper_limit: float, games_played: int):
        print("\n" + "="*50)
        print(f" LIVE TABLE: {gambler_name.upper()} ")
        print("="*50)
        
        # Calculate progress to limits
        dist_to_loss = current_stake - lower_limit
        dist_to_win = upper_limit - current_stake
        
        print(f"Current Balance:   ${current_stake:.2f}")
        print("-" * 50)
        print(f"Loss Limit (Stop): ${lower_limit:.2f}  [Buffer: ${dist_to_loss:.2f}]")
        print(f"Win Goal (Target): ${upper_limit:.2f}  [Remaining: ${dist_to_win:.2f}]")
        print("-" * 50)
        print(f"Games Played: {games_played}")
        print("="*50)

    @staticmethod
    def show_outcome(outcome: str, amount: float, new_balance: float):
        print("\n" + "-"*30)
        if outcome == "WIN":
            print(f"WINNER! Payout: +${amount:.2f}")
        elif outcome == "LOSS":
            print(f"LOSS. Deducted: -${amount:.2f}")
        else:
            print("PUSH. Stake returned.")
            
        print(f"Updated Balance: ${new_balance:.2f}")
        print("-" * 30 + "\n")