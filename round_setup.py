import tkinter as tk
from tkinter import messagebox
from datetime import date

# --- Azure Dark Palette (consistent with login.py) ---
BG_PRIMARY   = "#0E1726"
CARD_BG      = "#1E293B"
TEXT_COLOR   = "#F3F2F1"
SUBTEXT_COLOR= "#B3B0AD"
ACCENT       = "#0078D4"
ACCENT_HOVER = "#005A9E"
FIELD_BG     = "#2A3448"
FIELD_BORDER = "#2D3E55"

# --- Global Cache for Round Info ---
round_info = {}

def center_window(win, w, h):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def open_round_setup(logged_in_player):
    """Launch the round setup UI. Caches round info locally, no DB write yet."""

    def cache_round():
        course = course_entry.get().strip()
        round_date = date_entry.get().strip()
        holes = holes_entry.get().strip()
        tees = tees_entry.get().strip()

        if not course or not round_date or not holes or not tees:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        # Cache info only (no DB write)
        global round_info
        round_info = {
            "RoundID": None,  # to be assigned at the end
            "PlayerID": logged_in_player["PlayerID"],
            "PlayerName": logged_in_player["PlayerName"],
            "CoursePlayed": course,
            "RoundDate": round_date,
            "HolesPlayed": holes,
            "TeePreference": tees
        }

        messagebox.showinfo(
            "Round Cached",
            f"Round setup saved for {logged_in_player['PlayerName']} at {course}.\n\n"
            "You can now begin entering shots."
        )

        print("✅ Cached round info:", round_info)
        window.destroy()  # close setup window

    # --- Build UI ---
    global window
    window = tk.Tk()
    window.title("Strokes Gained - Round Setup")
    window.configure(bg=BG_PRIMARY)
    window.resizable(False, False)
    center_window(window, 460, 380)

    # Outer wrapper for centering
    outer = tk.Frame(window, bg=BG_PRIMARY)
    outer.pack(expand=True, fill="both")

    # Card container
    card = tk.Frame(
        outer, bg=CARD_BG, padx=40, pady=34,
        highlightbackground=FIELD_BORDER, highlightthickness=1
    )
    card.pack(expand=True)

    # --- Title Area ---
    title = tk.Label(
        card, text="Round Setup", bg=CARD_BG, fg=TEXT_COLOR,
        font=("Segoe UI", 15, "bold")
    )
    title.pack(pady=(0, 2))

    subtitle = tk.Label(
        card, text=f"Welcome, {logged_in_player['PlayerName']}",
        bg=CARD_BG, fg=SUBTEXT_COLOR, font=("Segoe UI", 10)
    )
    subtitle.pack(pady=(0, 14))

    # --- Form Fields ---
    form = tk.Frame(card, bg=CARD_BG)
    form.pack(pady=(0, 12))

    def add_field(label_text, default_value=None):
        row = tk.Frame(form, bg=CARD_BG)
        row.pack(anchor="w", pady=6)
        tk.Label(row, text=label_text, bg=CARD_BG, fg=TEXT_COLOR,
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 10))
        entry = tk.Entry(
            row, width=26, font=("Segoe UI", 11),
            bg=FIELD_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
            relief="flat", highlightthickness=1,
            highlightbackground=FIELD_BORDER, highlightcolor=ACCENT
        )
        entry.pack(side="left", ipady=4)
        if default_value:
            entry.insert(0, default_value)
        return entry

    course_entry = add_field("Course Played:")
    date_entry = add_field("Date (YYYY-MM-DD):", str(date.today()))
    holes_entry = add_field("Holes Played:", "18")
    tees_entry = add_field("Tee Preference:", "Tips")

    # --- Save Button ---
    def on_hover(e): e.widget.config(bg=ACCENT_HOVER)
    def off_hover(e): e.widget.config(bg=ACCENT)

    save_btn = tk.Button(
        card, text="Start Round", font=("Segoe UI", 11, "bold"),
        bg=ACCENT, fg="white",
        activebackground=ACCENT_HOVER, activeforeground="white",
        relief="flat", bd=0,
        padx=18, pady=8, cursor="hand2",
        command=cache_round
    )
    save_btn.pack(pady=(8, 10))
    save_btn.bind("<Enter>", on_hover)
    save_btn.bind("<Leave>", off_hover)

    # --- Footer ---
    footer = tk.Label(
        card, text="© 2025 GreensideData", bg=CARD_BG,
        fg=SUBTEXT_COLOR, font=("Segoe UI", 8)
    )
    footer.pack(pady=(10, 0))

    window.mainloop()
