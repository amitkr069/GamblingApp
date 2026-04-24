class SessionSummaryDisplay:

    @staticmethod
    def print_final_report(session_data: dict, stats_data: dict):
        print("\n" + "*"*50)
        print(" "*10 + "FINAL SESSION REPORT")
        print("*"*50)
        
        s = session_data['session']
        
        print(f"\n[ Session Details ]")
        print(f"Status:       {s['status']}")
        print(f"End Reason:   {s['end_reason']}")
        print(f"Duration:     {session_data['active_duration_sec']} sec (Paused: {session_data['paused_duration_sec']} sec)")
        
        print(f"\n[ Financials ]")
        print(f"Starting Stake:  ${s['starting_stake']:.2f}")
        print(f"Ending Stake:    ${s['ending_stake']:.2f}")
        print(f"Peak Stake:      ${s['peak_stake']:.2f}")
        print(f"Lowest Stake:    ${s['lowest_stake']:.2f}")
        
        net_profit = session_data['net_profit']
        profit_str = f"+${net_profit:.2f}" if net_profit > 0 else f"-${abs(net_profit):.2f}"
        print(f"Net Profit:      {profit_str}")
        
        if stats_data:
            print(f"\n[ Advanced Metrics ]")
            print(f"Total Games:   {stats_data['total_games']} (W:{stats_data['total_wins']} / L:{stats_data['total_losses']})")
            print(f"Win Rate:      {stats_data['win_rate'] * 100:.1f}%")
            print(f"Profit Factor: {stats_data['profit_factor']:.2f}x")
            print(f"ROI:           {stats_data['roi'] * 100:.1f}%")
            print(f"Longest Win Streak:  {stats_data['longest_win_streak']}")
            print(f"Longest Loss Streak: {stats_data['longest_loss_streak']}")
            
        print("*"*50 + "\n")