import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from round_setup import round_info

# --- Azure Dark Palette ---
BG_PRIMARY   = "#0E1726"
CARD_BG      = "#1E293B"
ENTRY_BG     = "#CED8E9"
TEXT_COLOR   = "#F3F2F1"
SUBTEXT_COLOR= "#B3B0AD"
ACCENT       = "#0078D4"
ACCENT_HOVER = "#005A9E"
FIELD_BG     = "#2A3448"
FIELD_BORDER = "#2D3E55"
GREEN_TEXT   = "#13A10E"
RED_TEXT     = "#C50F1F"

DB_PATH = "shots_gained.db"
cached_shots = []

def center_window(win, w, h):
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (sw - w) // 2, (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def open_shot_entry():
    """Shot entry window, Azure dark with grid layout and cached data only."""
    hole_num = 1
    shots_this_hole = []
    last_surface, last_distance = None, None

    # --- FUNCTIONS ---
    def calculate_strokes_gained():
        """Compute SG live (no DB write)."""
        try:
            surf_start = surface_start_dd.get()
            surf_end = surface_end_dd.get()
            if not surf_start or not surf_end:
                return
            dist_start = float(distance_start_entry.get())
        except ValueError:
            sg_label.config(text="Strokes Gained: --", fg=TEXT_COLOR)
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT TourAvg FROM DimAvg WHERE Surface=? AND Distance=?", (surf_start, int(dist_start)))
            start_row = c.fetchone()
            if not start_row:
                sg_label.config(text="Start Avg Missing", fg=RED_TEXT)
                return
            if surf_end == "Hole":
                end_val = 0
            else:
                dist_end = float(distance_end_entry.get())
                c.execute("SELECT TourAvg FROM DimAvg WHERE Surface=? AND Distance=?", (surf_end, int(dist_end)))
                end_row = c.fetchone()
                if not end_row:
                    sg_label.config(text="End Avg Missing", fg=RED_TEXT)
                    return
                end_val = end_row[0]
            sg_val = start_row[0] - (1 + end_val)
            if penalty_var.get():
                sg_val -= 1
            color = GREEN_TEXT if sg_val > 0 else RED_TEXT if sg_val < 0 else TEXT_COLOR
            sg_label.config(text=f"Strokes Gained: {sg_val:+.2f}", bg = "#2D3E55", fg=color)
            sg_label.sg_value = sg_val
        except Exception as e:
            sg_label.config(text=f"Error: {e}", fg=RED_TEXT)
        finally:
            conn.close()

    def toggle_end_state(event=None):
        if surface_end_dd.get() == "Hole":
            distance_end_entry.delete(0, tk.END)
            distance_end_entry.config(state="disabled")
        else:
            distance_end_entry.config(state="normal")

    def add_shot():
        nonlocal last_surface, last_distance
        sg_val = getattr(sg_label, "sg_value", None)
        if sg_val is None:
            messagebox.showwarning("Warning", "Please complete shot details first.")
            return

        shot = {
            "PlayerID": round_info["PlayerID"],
            "RoundID": round_info["RoundID"],
            "Hole": hole_num,
            "Par": int(par_dd.get()) if par_dd.get() else None,
            "Category": category_dd.get(),
            "SurfaceStart": surface_start_dd.get(),
            "DistanceStart": float(distance_start_entry.get()),
            "SurfaceEnd": surface_end_dd.get(),
            "DistanceEnd": None if surface_end_dd.get() == "Hole" else float(distance_end_entry.get()),
            "ClubUsed": club_entry.get().strip(),
            "ShotShape": shape_entry.get().strip(),
            "Penalty": 1 if penalty_var.get() else 0,
            "StrokesGained": sg_val
        }

        # Append and display
        shots_this_hole.append(shot)
        tree.insert("", "end", values=(
            shot["Category"],
            shot["SurfaceStart"],
            shot["DistanceStart"],
            shot["SurfaceEnd"],
            shot["DistanceEnd"] or "",
            shot["Penalty"],
            f"{sg_val:+.2f}"
        ))

        # Update memory for next shot
        last_surface, last_distance = surface_end_dd.get(), distance_end_entry.get()

        # ✅ Fix: call with correct argument name
        clear_fields(preserve_last=True)

    def previous_shot():
        """Load the last shot entered for editing."""
        nonlocal last_surface, last_distance
        if not shots_this_hole:
            messagebox.showinfo("No Previous Shot", "No previous shots to edit.")
            return

        last_shot = shots_this_hole.pop()
        clear_fields()
        category_dd.set(last_shot["Category"])
        surface_start_dd.set(last_shot["SurfaceStart"])
        distance_start_entry.insert(0, last_shot["DistanceStart"])
        surface_end_dd.set(last_shot["SurfaceEnd"])
        if last_shot["SurfaceEnd"] != "Hole":
            distance_end_entry.insert(0, last_shot["DistanceEnd"])
        club_entry.insert(0, last_shot["ClubUsed"])
        shape_entry.insert(0, last_shot["ShotShape"])
        penalty_var.set(bool(last_shot["Penalty"]))
        sg_label.config(text=f"Editing Shot | SG: {last_shot['StrokesGained']:+.2f}", fg=ACCENT)

        # remove last row from table
        for row in tree.get_children():
            tree.delete(row)
        for s in shots_this_hole:
            tree.insert("", "end", values=(
                s["Category"], s["SurfaceStart"], s["DistanceStart"],
                s["SurfaceEnd"], s["DistanceEnd"] or "", s["Penalty"], f"{s['StrokesGained']:+.2f}"
            ))

    def clear_fields(preserve_last=False):
        """Reset inputs for next shot, with smart auto-population based on previous shot."""
        category_dd.set("")
        surface_start_dd.set("")
        surface_end_dd.set("")
        distance_start_entry.delete(0, tk.END)
        distance_end_entry.delete(0, tk.END)
        club_entry.delete(0, tk.END)
        shape_entry.delete(0, tk.END)
        penalty_var.set(False)
        sg_label.config(text="Strokes Gained: --", fg=TEXT_COLOR)
        distance_end_entry.config(state="normal")

        # --- carry over last shot context if applicable ---
        if preserve_last and last_surface and last_distance:
            surface_start_dd.set(last_surface)
            if last_surface != "Hole":
                distance_start_entry.insert(0, last_distance)

        # ✅ if last shot ended on Green → next shot category = Putting
        if last_surface == "Green":
            category_dd.set("Putting")

        # ✅ if last shot ended on Tee (re-tee after OB) → next shot category = Driving
        elif last_surface == "Tee":
            category_dd.set("Driving")

    def determine_hole_result(par, num, penalties):
        total = num + penalties
        diff = total - par
        return (
            "Eagle" if diff <= -2 else
            "Birdie" if diff == -1 else
            "Par" if diff == 0 else
            "Bogey" if diff == 1 else
            "Double Bogey" if diff == 2 else
            f"Other (+{diff})"
        )

    def save_hole():
        if not shots_this_hole:
            messagebox.showwarning("No Shots", "Please add at least one shot.")
            return
        if not par_dd.get():
            messagebox.showwarning("Missing Par", "Select par value.")
            return
        par = int(par_dd.get())
        total_pen = sum(s["Penalty"] for s in shots_this_hole)
        res = determine_hole_result(par, len(shots_this_hole), total_pen)
        for s in shots_this_hole:
            s["HoleResult"] = res
            cached_shots.append(s)
        shots_this_hole.clear()
        tree.delete(*tree.get_children())
        messagebox.showinfo("Hole Saved", f"Hole {hole_num} saved as {res}")
        next_hole()


    def next_hole():
        nonlocal hole_num, last_surface, last_distance
        if hole_num < int(round_info["HolesPlayed"]):
            hole_num += 1
            hole_label.config(text=f"Hole {hole_num}")
            par_dd.set("")
            last_surface, last_distance = None, None
            surface_start_dd.set("Tee")
            distance_start_entry.delete(0, tk.END)
            distance_end_entry.config(state="normal")
        else:
            messagebox.showinfo("Round Complete", "All holes recorded.")
            window.destroy()
            from round_summary import open_summary_screen
            open_summary_screen(cached_shots)

    # --- UI BUILD ---
    global window
    window = tk.Tk()
    window.title(f"Strokes Gained - {round_info.get('CoursePlayed','Round')}")
    window.configure(bg=BG_PRIMARY)
    window.resizable(False, False)
    center_window(window, 1000, 850)

    card = tk.Frame(window, bg=CARD_BG, padx=40, pady=30, highlightbackground=FIELD_BORDER, highlightthickness=1)
    card.pack(expand=True, pady=25)

    hole_label = tk.Label(card, text=f"Hole {hole_num}", bg=CARD_BG, fg=TEXT_COLOR, font=("Segoe UI", 15, "bold"))
    hole_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

    tk.Label(card, text="Par:", bg=CARD_BG, fg=TEXT_COLOR, font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="e", pady=6, padx=(0, 10))
    par_dd = ttk.Combobox(card, values=[3, 4, 5], width=5, state="readonly")
    par_dd.grid(row=1, column=1, sticky="w", pady=6)

    # --- Auto-set Category when Par changes ---
    def on_par_change(event=None):
        selected_par = par_dd.get()
        if selected_par == "3":
            category_dd.set("Approach")
        elif selected_par in ("4", "5"):
            category_dd.set("Driving")
        else:
            category_dd.set("")  # clear if user resets or removes value

    par_dd.bind("<<ComboboxSelected>>", on_par_change)

    # Form fields (clean grid alignment)
    row_labels = [
        ("Category:", ["Driving", "Approach", "Short Game", "Putting"]),
        ("Surface Start:", ["Tee", "Fairway", "Rough", "Sand", "Green", "Penalty"]),
        ("Distance Start (yds/ft):", None),
        ("Surface End:", ["Tee", "Fairway", "Rough", "Sand", "Green", "Penalty", "Hole"]),
        ("Distance End (yds):", None),
        ("Club Used*:", None),
        ("Shot Shape*:", None)
    ]
    widgets = []
    for idx, (label, options) in enumerate(row_labels, start=2):
        tk.Label(card, text=label, bg=CARD_BG, fg=TEXT_COLOR, font=("Segoe UI", 11, "bold")).grid(row=idx, column=0, sticky="e", pady=5, padx=(0, 10))
        if options:
            w = ttk.Combobox(card, values=options, width=18, state="readonly")
        else:
            w = tk.Entry(card, width=20, bg=ENTRY_BG, relief="flat")
        w.grid(row=idx, column=1, sticky="w", pady=5)
        widgets.append(w)

    category_dd, surface_start_dd, distance_start_entry, surface_end_dd, distance_end_entry, club_entry, shape_entry = widgets
    surface_end_dd.bind("<<ComboboxSelected>>", toggle_end_state)

    penalty_var = tk.BooleanVar()
    penalty_cb = tk.Checkbutton(card, text="Penalty", bg=CARD_BG, fg=TEXT_COLOR, variable=penalty_var, command=calculate_strokes_gained)
    penalty_cb.grid(row=len(row_labels)+2, column=1, sticky="w", pady=5)

    sg_label = tk.Label(card, text="Strokes Gained: --", bg=CARD_BG, fg=TEXT_COLOR, font=("Segoe UI", 12, "bold"))
    sg_label.grid(row=len(row_labels)+3, column=0, columnspan=2, pady=(10, 8))

    # Treeview
    columns = ("Category","Start","DistStart","End","DistEnd","Penalty","SG")
    tree = ttk.Treeview(card, columns=columns, show="headings", height=8)
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview", background="#1E293B", fieldbackground="#1E293B",
                    foreground=TEXT_COLOR, font=("Segoe UI", 10))
    style.map("Treeview", background=[("selected", "#324057")])
    style.configure("Treeview.Heading", background="#2A3A55", foreground=TEXT_COLOR,
                    font=("Segoe UI", 10, "bold"))
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")
    tree.tag_configure("odd", background="#1E293B")
    tree.tag_configure("even", background="#24344C")
    tree.grid(row=len(row_labels)+4, column=0, columnspan=2, pady=(10, 10))

    # Buttons
    def on_hover(e): e.widget.config(bg=ACCENT_HOVER)
    def off_hover(e): e.widget.config(bg=ACCENT)

    btn_frame = tk.Frame(card, bg=CARD_BG)
    btn_frame.grid(row=len(row_labels)+5, column=0, columnspan=2, pady=(20, 20))
    for text, cmd in [("Add Shot", add_shot), ("Save Hole", save_hole), ("Previous Shot", previous_shot), ("Clear Fields", clear_fields)]:
        b = tk.Button(btn_frame, text=text, bg=ACCENT, fg="white", font=("Segoe UI", 11, "bold"),
                      relief="flat", bd=0, padx=18, pady=12, cursor="hand2", command=cmd)
        b.pack(side="left", padx=10)
        b.bind("<Enter>", on_hover)
        b.bind("<Leave>", off_hover)

    # Live SG recalculation
    for w in [surface_start_dd, surface_end_dd, distance_start_entry, distance_end_entry]:
        w.bind("<FocusOut>", lambda e: calculate_strokes_gained())
        w.bind("<KeyRelease>", lambda e: calculate_strokes_gained())

    window.mainloop()
