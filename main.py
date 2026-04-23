# Import the separated menu functions from our new cli module
from cli.gambler_profile_management import gambler_profile
from cli.stake_management import stake_management
from cli.betting_management import betting_management

def main():
    while True:
        print("\n===========================================")
        print("       Gambling Simulation System          ")
        print("===========================================")
        print("1. Gambler Profile Management")
        print("2. Stake Management Operations")
        print("3. Betting Mechanism")
        print("4. Exit Application")
        
        main_choice = input("\nSelect a module to launch: ")
        
        if main_choice == '1':
            gambler_profile()
        elif main_choice == '2':
            stake_management()
        elif main_choice == '3':
            betting_management()
        elif main_choice == '4':
            print("Shutting down... Goodbye!")
            break
        else:
            print("Invalid selection. Please enter 1, 2, 3 or 4.")

if __name__ == "__main__":
    main()
