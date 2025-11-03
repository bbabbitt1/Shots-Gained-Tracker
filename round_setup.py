import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import date

# --- COLORS (reuse palette for consistency) ---
teal_light = "#9ECFD4"
pale_sage = "#E5E9C5"
dark_bg = "#0B1220"
dark_surface = "#1A2632"
dark_text = "#0B1220"

# global variable to store round info
round_info = {}

def center_window(win, w, h):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def open_round_setup(logged_in_player):
    """Launches the round setup window with cached player info."""
    def save_round():
        course = course_entry.get().strip()
        round_date = date_entry.get().strip()
        holes = holes_entry.get().strip()
        tees = tees_entry.get().strip()

        if not course or not round_date or not holes or not tees:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        try:
            conn = sqlite3.connect("shots_gained.db")
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO DimRound (PlayerID, CoursePlayed, RoundDate, HolesPlayed, TeePreference)
                VALUES (?, ?, ?, ?, ?)
            """, (logged_in_player["PlayerID"], course, round_date, holes, tees))

            conn.commit()
            round_id = cursor.lastrowid
            conn.close()

            # cache the round info globally
            global round_info
            round_info = {
                "RoundID": round_id,
                "PlayerID": logged_in_player["PlayerID"],
                "PlayerName": logged_in_player["PlayerName"],
                "CoursePlayed": course,
                "RoundDate": round_date,
                "HolesPlayed": holes,
                "TeePreference": tees
            }

            messagebox.showinfo("Round Created", f"Round #{round_id} created for {logged_in_player['PlayerName']}!")
            window.destroy()  # close setup window

            print("✅ Cached round info:", round_info)

        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")

    # --- BUILD UI ---
    global window
    window = tk.Tk()
    window.title("Strokes Gained - Round Setup")
    window.configure(bg=teal_light)
    window.resizable(False, False)
    center_window(window, 420, 320)

    tk.Label(window, text=f"Welcome, {logged_in_player['PlayerName']}",
             bg=teal_light, fg=dark_text, font=("Arial", 14, "bold")).pack(pady=(10, 10))

    # Form fields
    form = tk.Frame(window, bg=teal_light)
    form.pack(pady=10)

    tk.Label(form, text="Course Played:", bg=teal_light, fg=dark_text, font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=5)
    course_entry = tk.Entry(form, width=30)
    course_entry.grid(row=0, column=1, pady=5)

    tk.Label(form, text="Date (YYYY-MM-DD):", bg=teal_light, fg=dark_text, font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", pady=5)
    date_entry = tk.Entry(form, width=30)
    date_entry.insert(0, str(date.today()))
    date_entry.grid(row=1, column=1, pady=5)

    tk.Label(form, text="Holes Played:", bg=teal_light, fg=dark_text, font=("Arial", 11, "bold")).grid(row=2, column=0, sticky="w", pady=5)
    holes_entry = tk.Entry(form, width=30)
    holes_entry.insert(0, "18")
    holes_entry.grid(row=2, column=1, pady=5)

    tk.Label(form, text="Tees:", bg=teal_light, fg=dark_text, font=("Arial", 11, "bold")).grid(row=3, column=0, sticky="w", pady=5)
    tees_entry = tk.Entry(form, width=30)
    tees_entry.insert(0, "Tips")
    tees_entry.grid(row=3, column=1, pady=5)

    # Save button
    save_btn = tk.Button(window, text="Start Round", bg=dark_bg, fg=pale_sage, font=("Arial", 12, "bold"), command=save_round)
    save_btn.pack(pady=20)

    window.mainloop()
