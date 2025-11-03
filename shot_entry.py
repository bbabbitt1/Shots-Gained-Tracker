import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3

# --- COLORS ---
teal_light = "#9ECFD4"
pale_sage = "#E5E9C5"
dark_bg = "#0B1220"
dark_text = "#0B1220"
green_text = "#017a39"
red_text = "#b10000"

# --- DATABASE CONFIG ---
DB_PATH = "shots_gained.db"

# --- IMPORT round_info from setup ---
from round_setup import round_info

# Global cache for all shots this round
cached_shots = []

def center_window(win, w, h):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def open_shot_entry():
    """Dynamic shot entry window — with table view, memory, and 'Hole' handling."""
    hole_num = 1
    shots_this_hole = []
    last_surface = None
    last_distance = None

    def calculate_strokes_gained():
        """Auto-calculates strokes gained using DimAvg, including 'Hole' handling."""
        try:
            surface_start = surface_start_dd.get()
            surface_end = surface_end_dd.get()
            dist_start = float(distance_start_entry.get())
        except ValueError:
            sg_label.config(text="Strokes Gained: --", fg=dark_text)
            return

        if not surface_start or not surface_end:
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get starting expected strokes
            cursor.execute("""
                SELECT TourAvg FROM DimAvg
                WHERE Surface = ? AND Distance = ?
            """, (surface_start, int(dist_start)))
            start_avg = cursor.fetchone()
            if not start_avg:
                sg_label.config(text="Start Avg Missing", fg=red_text)
                conn.close()
                return

            # Determine ending expected strokes
            if surface_end == "Hole":
                end_avg_val = 0.0
            else:
                try:
                    dist_end = float(distance_end_entry.get())
                except ValueError:
                    sg_label.config(text="End distance required", fg=red_text)
                    conn.close()
                    return

                cursor.execute("""
                    SELECT TourAvg FROM DimAvg
                    WHERE Surface = ? AND Distance = ?
                """, (surface_end, int(dist_end)))
                end_avg = cursor.fetchone()
                if not end_avg:
                    sg_label.config(text="End Avg Missing", fg=red_text)
                    conn.close()
                    return
                end_avg_val = end_avg[0]

            conn.close()

            # Compute strokes gained
            sg_value = start_avg[0] - (1 + end_avg_val)
            if penalty_var.get():
                sg_value -= 1

            color = green_text if sg_value > 0 else red_text if sg_value < 0 else dark_text
            sg_label.config(text=f"Strokes Gained: {sg_value:+.2f}", fg=color)
            sg_label.sg_value = sg_value

        except Exception as e:
            sg_label.config(text=f"Error: {e}", fg=red_text)

    def toggle_distance_end_state(event=None):
        """Disable DistanceEnd when 'Hole' selected."""
        if surface_end_dd.get() == "Hole":
            distance_end_entry.delete(0, tk.END)
            distance_end_entry.config(state="disabled")
        else:
            distance_end_entry.config(state="normal")

    def add_shot():
        """Add one shot to table + memory."""
        nonlocal last_surface, last_distance
        try:
            sg_value = getattr(sg_label, "sg_value", None)
            if sg_value is None:
                messagebox.showwarning("Warning", "Please complete shot details first.")
                return

            par_value = int(par_dd.get()) if par_dd.get() else None

            shot = {
                "PlayerID": round_info["PlayerID"],
                "RoundID": round_info["RoundID"],
                "Hole": hole_num,
                "Par": par_value,
                "HoleResult": None,
                "Category": category_dd.get(),
                "SurfaceStart": surface_start_dd.get(),
                "DistanceStart": float(distance_start_entry.get()) if distance_start_entry.get() else None,
                "SurfaceEnd": surface_end_dd.get(),
                "DistanceEnd": None if surface_end_dd.get() == "Hole" else float(distance_end_entry.get()),
                "ClubUsed": club_entry.get().strip(),
                "ShotShape": shape_entry.get().strip(),
                "Penalty": 1 if penalty_var.get() else 0,
                "StrokesGained": sg_value
            }

            # Cache and display
            shots_this_hole.append(shot)
            tree.insert("", "end", values=(
                shot["Category"], shot["SurfaceStart"], shot["DistanceStart"] or "",
                shot["SurfaceEnd"], shot["DistanceEnd"] or "", shot["Penalty"], f"{sg_value:+.2f}"
            ))

            # Update memory for next shot
            last_surface = surface_end_dd.get()
            last_distance = distance_end_entry.get()

            clear_fields(preserve_last=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_fields(preserve_last=False):
        """Reset inputs for next shot, optionally reusing previous end data."""
        category_dd.set("")
        surface_start_dd.set("")
        surface_end_dd.set("")
        distance_start_entry.delete(0, tk.END)
        distance_end_entry.delete(0, tk.END)
        club_entry.delete(0, tk.END)
        shape_entry.delete(0, tk.END)
        penalty_var.set(False)
        sg_label.config(text="Strokes Gained: --", fg=dark_text)
        distance_end_entry.config(state="normal")

        # Auto-fill start with memory
        if preserve_last and last_surface and last_distance:
            surface_start_dd.set(last_surface)
            if last_surface != "Hole":
                distance_start_entry.insert(0, last_distance)

    def determine_hole_result(par, num_shots, total_penalties):
        strokes = num_shots + total_penalties
        relative = strokes - par
        if relative <= -2:
            return "Eagle"
        elif relative == -1:
            return "Birdie"
        elif relative == 0:
            return "Par"
        elif relative == 1:
            return "Bogey"
        elif relative == 2:
            return "Double Bogey"
        else:
            return f"Other (+{relative})"

    def save_hole():
        """Cache all shots for this hole, compute hole result."""
        nonlocal last_surface, last_distance
        if not shots_this_hole:
            messagebox.showwarning("No Shots", "Please add at least one shot.")
            return
        if not par_dd.get():
            messagebox.showwarning("Missing Par", "Please select a Par value for this hole.")
            return

        par_value = int(par_dd.get())
        total_penalties = sum(shot["Penalty"] for shot in shots_this_hole)
        num_shots = len(shots_this_hole)
        hole_result = determine_hole_result(par_value, num_shots, total_penalties)

        hole_result_label.config(text=f"Hole Result: {hole_result}", fg=dark_text)

        # Cache all shots
        for shot in shots_this_hole:
            shot["HoleResult"] = hole_result
            cached_shots.append(shot)

        shots_this_hole.clear()
        tree.delete(*tree.get_children())  # clear table
        last_surface = None
        last_distance = None
        messagebox.showinfo("Hole Saved", f"Hole {hole_num} saved as {hole_result}")
        next_hole()

    def next_hole():
        """Advance to next hole or finish round."""
        nonlocal hole_num, last_surface, last_distance
        if hole_num < int(round_info["HolesPlayed"]):
            hole_num += 1
            hole_label.config(text=f"Hole {hole_num}")
            par_dd.set("")
            hole_result_label.config(text="Hole Result: --")
            last_surface = None
            last_distance = None

            # Reset to tee
            surface_start_dd.set("Tee")
            distance_start_entry.delete(0, tk.END)
            distance_end_entry.config(state="normal")
        else:
            messagebox.showinfo("Round Complete", "All holes recorded. Generating summary...")
            window.destroy()
            from summary_screen import open_summary_screen
            open_summary_screen(cached_shots)

    # --- UI SETUP ---
    global window
    window = tk.Tk()
    window.title(f"Strokes Gained - {round_info['CoursePlayed']}")
    window.configure(bg=teal_light)
    window.resizable(False, False)
    center_window(window, 1000, 750)

    hole_label = tk.Label(window, text=f"Hole {hole_num}", bg=teal_light, fg=dark_bg, font=("Arial", 16, "bold"))
    hole_label.pack(pady=10)

    # Top bar
    top_frame = tk.Frame(window, bg=teal_light)
    top_frame.pack(pady=(5, 15))

    tk.Label(top_frame, text="Par:", bg=teal_light, fg=dark_text, font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5)
    par_dd = ttk.Combobox(top_frame, values=[3, 4, 5], width=5, state="readonly")
    par_dd.grid(row=0, column=1, padx=5)

    hole_result_label = tk.Label(top_frame, text="Hole Result: --", bg=teal_light, fg=dark_text, font=("Arial", 11, "bold"))
    hole_result_label.grid(row=0, column=2, padx=15)

    # Form fields
    form = tk.Frame(window, bg=teal_light)
    form.pack(pady=10)

    tk.Label(form, text="Category:", bg=teal_light, fg=dark_text).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    category_dd = ttk.Combobox(form, values=["Driving", "Approach", "Short Game", "Putting"], width=17, state="readonly")
    category_dd.grid(row=0, column=1, pady=5)

    tk.Label(form, text="Surface Start:", bg=teal_light, fg=dark_text).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    surface_start_dd = ttk.Combobox(form, values=["Tee", "Fairway", "Rough", "Sand", "Green", "Penalty"], width=17, state="readonly")
    surface_start_dd.grid(row=1, column=1, pady=5)
    surface_start_dd.set("Tee")

    tk.Label(form, text="Distance Start (yds):", bg=teal_light, fg=dark_text).grid(row=2, column=0, sticky="e", padx=5, pady=5)
    distance_start_entry = tk.Entry(form, width=20)
    distance_start_entry.grid(row=2, column=1, pady=5)

    tk.Label(form, text="Surface End:", bg=teal_light, fg=dark_text).grid(row=3, column=0, sticky="e", padx=5, pady=5)
    surface_end_dd = ttk.Combobox(form, values=["Tee", "Fairway", "Rough", "Sand", "Green", "Penalty", "Hole"], width=17, state="readonly")
    surface_end_dd.grid(row=3, column=1, pady=5)
    surface_end_dd.bind("<<ComboboxSelected>>", toggle_distance_end_state)

    tk.Label(form, text="Distance End (yds):", bg=teal_light, fg=dark_text).grid(row=4, column=0, sticky="e", padx=5, pady=5)
    distance_end_entry = tk.Entry(form, width=20)
    distance_end_entry.grid(row=4, column=1, pady=5)

    tk.Label(form, text="Club Used:", bg=teal_light, fg=dark_text).grid(row=5, column=0, sticky="e", padx=5, pady=5)
    club_entry = tk.Entry(form, width=20)
    club_entry.grid(row=5, column=1, pady=5)

    tk.Label(form, text="Shot Shape:", bg=teal_light, fg=dark_text).grid(row=6, column=0, sticky="e", padx=5, pady=5)
    shape_entry = tk.Entry(form, width=20)
    shape_entry.grid(row=6, column=1, pady=5)

    penalty_var = tk.BooleanVar()
    penalty_cb = tk.Checkbutton(form, text="Penalty", bg=teal_light, fg=dark_text, variable=penalty_var, command=calculate_strokes_gained)
    penalty_cb.grid(row=7, column=1, sticky="w", pady=5)

    sg_label = tk.Label(window, text="Strokes Gained: --", bg=teal_light, fg=dark_text, font=("Arial", 13, "bold"))
    sg_label.pack(pady=8)

    # --- Shot table ---
    columns = ("Category", "Start", "DistStart", "End", "DistEnd", "Penalty", "SG")
    tree = ttk.Treeview(window, columns=columns, show="headings", height=8)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")
    tree.pack(pady=10)

    scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.place(relx=0.97, rely=0.38, relheight=0.35)

    btn_frame = tk.Frame(window, bg=teal_light)
    btn_frame.pack(pady=20)

    tk.Button(btn_frame, text="Add Shot", bg=dark_bg, fg=pale_sage, font=("Arial", 11, "bold"), command=add_shot).grid(row=0, column=0, padx=15)
    tk.Button(btn_frame, text="Save Hole", bg=dark_bg, fg=pale_sage, font=("Arial", 11, "bold"), command=save_hole).grid(row=0, column=1, padx=15)

    for widget in [surface_start_dd, surface_end_dd, distance_start_entry, distance_end_entry]:
        widget.bind("<FocusOut>", lambda e: calculate_strokes_gained())
        widget.bind("<KeyRelease>", lambda e: calculate_strokes_gained())

    window.mainloop()
