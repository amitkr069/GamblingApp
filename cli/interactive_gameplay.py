from ui.interactive_menu import InteractiveGameplay
from services.game_session_manager import GameSessionManager
from models.session_models import SessionParameters

def interactive_gameplay():
    """Sub-menu for UC-07: Interactive Gameplay"""
    game_ui = InteractiveGameplay()
    manager = GameSessionManager()
    
    while True:
        print("\n=== Interactive Casino Table ===")
        print("1. Sit at Table (Start New Session & Play)")
        print("2. Resume Suspended Session")
        print("3. Return to Main Menu")
        choice = input("Select operation: ")
        
        if choice == '1':
            try:
                g_id = int(input("Enter Gambler ID: "))
                
                # Fast-track session setup
                lower = float(input("Enter Loss Stop (Lower Limit): "))
                upper = float(input("Enter Win Target (Upper Limit): "))
                
                params = SessionParameters(lower_limit=lower, upper_limit=upper, min_bet=5, max_bet=500)
                s_id = manager.start_session(g_id, max_games=100, params=params)
                
                # Launch the interactive game loop
                game_ui.run_table(g_id, s_id)
                
            except Exception as e:
                print(f"Error setting up table: {e}")
                
        elif choice == '2':
            try:
                s_id = int(input("Enter paused Session ID to resume: "))
                g_id = int(input("Enter Gambler ID: "))
                
                manager.resume_session(s_id)
                game_ui.run_table(g_id, s_id)
            except Exception as e:
                 print(f"Cannot resume: {e}")

        elif choice == '3':
            break
        else:
            print("Invalid selection.")