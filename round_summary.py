import tkinter as tk
from tkinter import messagebox
import sqlite3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from round_setup import round_info

# --- COLORS ---
BG_COLOR = "#121a24"
CARD_BG = "#1f2b3a"
TEXT_COLOR = "#e5e5e5"
GREEN_TEXT = "#00B050"
RED_TEXT = "#FF5C5C"
DB_PATH = "shots_gained.db"
# --- Microsoft Azure Dark Palette ---
BG_PRIMARY   = "#0E1726"
CARD_BG2      = "#1E293B"
TEXT_COLOR2   = "#F3F2F1"
SUBTEXT_COLOR= "#B3B0AD"
ACCENT       = "#0078D4"
ACCENT_HOVER = "#005A9E"
FIELD_BG     = "#2A3448"
FIELD_BORDER = "#2D3E55"

def center_window(win, w, h):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def open_summary_screen(shots):
    window = tk.Tk()
    window.title("Round Summary")
    window.configure(bg=BG_COLOR)
    window.resizable(False, False)
    center_window(window, 900, 700)

    # --- Aggregate Round Data ---
    total_strokes = 0
    total_par = 0
    fairways_hit = 0
    greens_hit = 0
    total_sg = 0


    holes = {}
    for shot in shots:
        hole = shot["Hole"]
        holes.setdefault(hole, []).append(shot)

    for hole, shots_list in holes.items():
        if not shots_list:
            continue

        if shots_list:
            par = int(shots_list[0].get("Par", 0) or 0)
            total_par += par
            strokes = len(shots_list) + sum(s.get("Penalty", 0) for s in shots_list)
            total_strokes += strokes
            total_sg += sum(s.get("StrokesGained", 0) or 0 for s in shots_list)

        # --- Fairway Hit Logic ---
        first = shots_list[0]
        if first.get("Category") == "Driving" and not first.get("Penalty"):
            if par >= 4 and first.get("SurfaceEnd") in ("Fairway", "Green","Hole"):
                fairways_hit += 1

        # --- Green in Regulation Logic ---
        strokes_to_green = next((i + 1 for i, s in enumerate(shots_list)
                                 if s.get("SurfaceEnd") in ( "Green","Hole")), None)
        if strokes_to_green and strokes_to_green <= (par - 2):
            greens_hit += 1

    # --- Totals ---
    if total_strokes - total_par > 0:
        score_vs_par = f"+{total_strokes-total_par}"
    elif total_strokes - total_par < 0:
        score_vs_par = f"-{total_par-total_strokes}"
    else:
        score_vs_par = "E"

    holes_played = len(holes)
    gir_pct = (greens_hit / holes_played * 100) if holes_played else 0
    fir_eligible = sum(1 for h, s in holes.items() if s and s[0].get("Par", 0) >= 4)
    fir_pct = (fairways_hit / fir_eligible * 100) if fir_eligible else 0

    gir_display = f"{greens_hit}/{holes_played} ({gir_pct:.0f}%)"
    fir_display = f"{fairways_hit}/{fir_eligible} ({fir_pct:.0f}%)"

    # --- KPI Section ---
    kpi_frame = tk.Frame(window, bg=BG_COLOR)
    kpi_frame.pack(pady=25)

    def kpi_chip(parent, label, value):
        card = tk.Frame(parent, bg=CARD_BG, padx=20, pady=10)
        card.pack(side="left", padx=15)
        tk.Label(card, text=label, bg=CARD_BG, fg=TEXT_COLOR,
                 font=("Segoe UI", 12, "bold")).pack()
        val_label = tk.Label(card, text=value, bg=CARD_BG, fg=TEXT_COLOR,
                             font=("Segoe UI", 16, "bold"))
        val_label.pack()
        return val_label

    lbl_total_sg = kpi_chip(kpi_frame, "Total SG", f"{total_sg:+.2f}")
    lbl_score_par = kpi_chip(kpi_frame, "Score vs Par", f"{score_vs_par}")
    kpi_chip(kpi_frame, "Fairways Hit", fir_display)
    kpi_chip(kpi_frame, "Greens in Reg", gir_display)

    # --- Color Code KPIs ---
    score_color = RED_TEXT if total_strokes < total_par else "#0077FF" if total_strokes > total_par  else TEXT_COLOR
    lbl_score_par.config(fg=score_color)
    sg_color = GREEN_TEXT if total_sg > 0 else RED_TEXT if total_sg < 0 else TEXT_COLOR
    lbl_total_sg.config(fg=sg_color)

    # --- SG by Category Chart ---
    categories = ["Driving", "Approach", "Short Game", "Putting"]
    sg_by_cat = {cat: 0 for cat in categories}
    for s in shots:
        cat = s.get("Category")
        if cat in sg_by_cat and s["StrokesGained"] is not None:
            sg_by_cat[cat] += s["StrokesGained"]

    fig, ax = plt.subplots(figsize=(7, 4), facecolor=BG_COLOR)
    values = list(sg_by_cat.values())
    bars = ax.barh(categories, list(sg_by_cat.values()),
                   color=[GREEN_TEXT if v > 0 else RED_TEXT if v < 0 else TEXT_COLOR
                          for v in sg_by_cat.values()])
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR)
    ax.spines[:].set_color(TEXT_COLOR)
    ax.set_xlabel("Strokes Gained", color=TEXT_COLOR, fontsize=11)
    ax.margins(x=0.15)  # adds space left/right so labels don’t get clipped
    plt.subplots_adjust(left=0.25, right=0.95, top=0.92, bottom=0.15)  # fine-tuned padding

    ax.axvline(0, color=TEXT_COLOR, linestyle="--", linewidth=1, alpha=0.6)

    # --- White numeric labels on bars ---
    for bar, val in zip(bars, values):
        xpos = bar.get_width()
        ax.text(
            xpos + (0.05 if xpos >= 0 else -0.05),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.2f}",
            va="center",
            ha="left" if xpos >= 0 else "right",
            color="white",
            fontsize=10,
            fontweight="bold"
        )

    chart_frame = tk.Frame(window, bg=BG_COLOR)
    chart_frame.pack(pady=15)
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    # --- Save Function ---
    def save_round():
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            # Save DimRound if not already in DB
            c.execute("""
                INSERT INTO DimRound (PlayerID, CoursePlayed, RoundDate, HolesPlayed, TeePreference)
                VALUES (?, ?, date('now'), ?, 'Tips')
            """, (shots[0]["PlayerID"], round_info["CoursePlayed"], len(holes)))
            round_id = c.lastrowid

            for s in shots:
                c.execute("""
                    INSERT INTO FactShots
                    (PlayerID, RoundID, Hole, Par, HoleResult, Category, SurfaceStart, DistanceStart,
                     SurfaceEnd, DistanceEnd, ClubUsed, ShotShape, Penalty, StrokesGained)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s["PlayerID"], round_id, s["Hole"], s.get("Par"), s.get("HoleResult"),
                      s["Category"], s["SurfaceStart"], s["DistanceStart"], s["SurfaceEnd"],
                      s["DistanceEnd"], s["ClubUsed"], s["ShotShape"], s["Penalty"], s["StrokesGained"]))
            conn.commit()
            conn.close()

            messagebox.showinfo("Round Saved", "✅ Round successfully saved to database!")
            window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Database save failed:\n{e}")

    # --- Save Button ---
    save_btn = tk.Button(
        window,
        text="Save Round",
        font=("Segoe UI", 11, "bold"),
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=18,
        pady=8,
        cursor="hand2",
        command=save_round
    )
    save_btn.pack(pady=25)

    window.mainloop()
