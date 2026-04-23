# Import the separated menu functions from our new cli module
from cli.gambler_profile_management import gambler_profile


def main():
    while True:
        print("\n===========================================")
        print("       Gambling Simulation System          ")
        print("===========================================")
        print("1. Gambler Profile Management")
        # print("2. Stake Management Operations")
        print("2. Exit Application")
        
        main_choice = input("\nSelect a module to launch: ")
        
        if main_choice == '1':
            gambler_profile()
        
        elif main_choice == '2':
            print("Shutting down... Goodbye!")
            break
        else:
            print("Invalid selection. Please enter 1 or 2.")

if __name__ == "__main__":
    main()