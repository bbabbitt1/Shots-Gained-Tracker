import tkinter as tk
from tkinter import messagebox
import sqlite3

# --- Microsoft Azure Dark Palette ---
BG_PRIMARY   = "#0E1726"
CARD_BG      = "#1E293B"
TEXT_COLOR   = "#F3F2F1"
SUBTEXT_COLOR= "#B3B0AD"
ACCENT       = "#0078D4"
ACCENT_HOVER = "#005A9E"
FIELD_BG     = "#2A3448"
FIELD_BORDER = "#2D3E55"

def center_window(win, w, h):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def login_action():
    global logged_in_player
    pid = player_id.get().strip()
    if not pid:
        messagebox.showwarning("Login", "Please enter a Player ID.")
        return
    try:
        conn = sqlite3.connect("shots_gained.db")
        cur = conn.cursor()
        cur.execute("SELECT PlayerName FROM DimPlayer WHERE PlayerID=?", (pid,))
        row = cur.fetchone()
        if row:
            logged_in_player = {"PlayerID": pid, "PlayerName": row[0]}
            messagebox.showinfo("Login", f"Welcome, {row[0]}!")
            window.destroy()
        else:
            messagebox.showerror("Login", "Player ID not found.")
    except Exception as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        conn.close()

def on_hover(e): e.widget.config(bg=ACCENT_HOVER)
def off_hover(e): e.widget.config(bg=ACCENT)

# --- Build UI ---
window = tk.Tk()
window.title("Strokes Gained - Login")
window.configure(bg=BG_PRIMARY)
window.resizable(False, False)
center_window(window, 460, 300)

# Outer frame for centering card
outer = tk.Frame(window, bg=BG_PRIMARY)
outer.pack(expand=True, fill="both")

# Card frame
card = tk.Frame(outer, bg=CARD_BG, padx=40, pady=32,
                highlightbackground=FIELD_BORDER, highlightthickness=1)
card.pack(expand=True)

# --- Title area ---
title = tk.Label(card, text="Strokes Gained Tracker",
                 bg=CARD_BG, fg=TEXT_COLOR, font=("Segoe UI", 15, "bold"))
title.pack(pady=(0, 2))

subtitle = tk.Label(card, text="Sign in with your Player ID",
                    bg=CARD_BG, fg=SUBTEXT_COLOR, font=("Segoe UI", 10))
subtitle.pack(pady=(0, 14))

# --- Player ID row ---
row = tk.Frame(card, bg=CARD_BG)
row.pack(pady=(0, 14))

player_id_label = tk.Label(row, text="Player ID:",
                           bg=CARD_BG, fg=TEXT_COLOR, font=("Segoe UI", 11, "bold"))
player_id_label.pack(side="left", padx=(0, 10))

player_id = tk.Entry(row, width=5, font=("Segoe UI", 11,"bold"),
                     bg=FIELD_BG, fg=TEXT_COLOR, insertbackground=TEXT_COLOR,
                     relief="flat", highlightthickness=1,
                     highlightbackground=FIELD_BORDER, highlightcolor=ACCENT)
player_id.pack(side="left", ipady=4)
player_id.focus_set()

# --- Login button ---
login_btn = tk.Button(card, text="Login", font=("Segoe UI", 11, "bold"),
                      bg=ACCENT, fg="white",
                      activebackground=ACCENT_HOVER, activeforeground="white",
                      relief="flat", bd=0,
                      padx=18, pady=8, cursor="hand2",
                      command=login_action)
login_btn.pack(pady=(0, 12))
login_btn.bind("<Enter>", on_hover)
login_btn.bind("<Leave>", off_hover)

# --- Footer ---
footer = tk.Label(card, text="© 2025 GreensideData",
                  bg=CARD_BG, fg=SUBTEXT_COLOR, font=("Segoe UI", 8))
footer.pack(pady=(8, 0))

window.mainloop()
