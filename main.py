from cli.gambler_profile_management import gambler_profile
from cli.stake_management import stake_management
from cli.betting_management import betting_management
from cli.game_session_manager import game_session_manager
from cli.win_loss_calculation import win_loss_calculation
from cli.interactive_gameplay import interactive_gameplay

def main():
    while True:
        print("\n===========================================")
        print("       Gambling Simulation System          ")
        print("===========================================")
        print("1. Gambler Profile Management")
        print("2. Stake Management Operations")
        print("3. Betting Mechanism")
        print("4. Game Session Management")
        print("5. Win/Loss Calculation Analytics")

        print("6. Exit Application")
        
        main_choice = input("\nSelect a module to launch: ")
        
        if main_choice == '1':
            gambler_profile()
        elif main_choice == '2':
            stake_management()
        elif main_choice == '3':
            betting_management()
        elif main_choice == '4':
            game_session_manager()
        elif main_choice == '5':
            win_loss_calculation()

        elif main_choice == '6':
            print("Shutting down... Goodbye!")
            break
        else:
            print("Invalid selection")

if __name__ == "__main__":
    main()
