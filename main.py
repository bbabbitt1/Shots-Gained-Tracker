# main.py
"""
Main entry point for the Strokes Gained Golf App.
Handles the full flow:
1. Login → 2. Round Setup → 3. Shot Entry → 4. Summary Screen
"""

def main():
    # Step 1: Login
    import login
    login.window.mainloop()  # Blocks until login window closes

    # If login was successful, a global variable will exist
    if not hasattr(login, "logged_in_player"):
        print("❌ Login not completed. Exiting.")
        return

    player = login.logged_in_player
    print(f"✅ Logged in as {player['PlayerName']} (PlayerID: {player['PlayerID']})")

    # Step 2: Round setup
    from round_setup import open_round_setup, round_info
    open_round_setup(player)

    # If round setup completed, a global variable round_info should exist
    if not hasattr(round_info, "get"):
        print("❌ Round setup not completed. Exiting.")
        return

    # Step 3: Shot entry
    from shot_entry import open_shot_entry, cached_shots
    open_shot_entry()
    # Step 4: After summary screen executes, cached_shots will have been saved
    from round_summary import open_summary_screen
    open_summary_screen(cached_shots)

    print("✅ App flow completed successfully.")

if __name__ == "__main__":
    main()
