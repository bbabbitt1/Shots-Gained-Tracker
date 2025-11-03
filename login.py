# python
import tkinter as tk
from tkinter import messagebox
import sqlite3

# Palette colors
primary_teal = "#016B61"
teal_mid = "#70B2B2"
teal_light = "#9ECFD4"
pale_sage = "#E5E9C5"
navy = "#032B44"
soft_red = "#D66A5B"
dark_bg = "#0B1220"
dark_surface = "#1A2632"

def center_window(win, w, h):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def on_press(event):
    btn = event.widget
    # store original config once
    if not hasattr(btn, "_orig_cfg"):
        btn._orig_cfg = {
            "bg": btn["bg"],
            "fg": btn["fg"],
            "font": btn["font"],
            "relief": btn["relief"],
            "padx": btn.cget("padx"),
            "pady": btn.cget("pady"),
        }
    btn.config(bg=pale_sage, fg=dark_bg, font=("Arial", 13, "bold"), relief="sunken", padx=14, pady=8)

def on_release(event):
    btn = event.widget
    # perform login action
    login_action()
    # brief visual hold, then restore
    def restore():
        if hasattr(btn, "_orig_cfg"):
            btn.config(
                bg=btn._orig_cfg["bg"],
                fg=btn._orig_cfg["fg"],
                font=btn._orig_cfg["font"],
                relief=btn._orig_cfg["relief"],
                padx=btn._orig_cfg["padx"],
                pady=btn._orig_cfg["pady"],
            )
    btn.after(120, restore)

def login_action():
    global logged_in_player
    pid = player_id.get().strip()
    if not pid:
        messagebox.showwarning("Login", "Please enter a Player ID.")
        return

    try:
        conn = sqlite3.connect("shots_gained.db")
        cursor = conn.cursor()

        cursor.execute("SELECT PlayerName FROM DimPlayer WHERE PlayerID = ?", (pid,))
        result = cursor.fetchone()

        if result:
            player_name = result[0]
            logged_in_player = {
                "PlayerID": pid,
                "PlayerName": player_name
            }
            messagebox.showinfo("Login", f"Welcome, {player_name}!")
            window.destroy()  # <-- Close the window after successful login
        else:
            messagebox.showerror("Login", "Player ID not found. Please try again.")

    except Exception as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        conn.close()

# Build UI
window = tk.Tk()
window.title("Strokes Gained - Login")
window.configure(bg=teal_light)
window.resizable(False, False)
center_window(window, 380, 180)

container = tk.Frame(window, bg=teal_light)
container.pack(expand=True)

player_id_label = tk.Label(container, text="Enter Player ID:", bg=teal_light, fg=dark_bg, font=("Arial", 12, "bold"))
player_id_label.pack(pady=(10, 6))

player_id = tk.Entry(container, width=28, font=("Arial", 12, "bold"))
player_id.pack(pady=(0, 12))
player_id.focus_set()

login_button = tk.Button(
    container,
    text="Login",
    bg=dark_bg,
    fg=pale_sage,
    activebackground=pale_sage,
    activeforeground=dark_bg,
    font=("Arial", 12),
    bd=0,
    padx=12,
    pady=6,
)
login_button.pack()

# Bind press/release to get the enlarge + sage effect
login_button.bind("<ButtonPress-1>", on_press)
login_button.bind("<ButtonRelease-1>", on_release)

window.mainloop()

