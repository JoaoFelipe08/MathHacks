import nflreadpy as nfl
import polars as pl
import random
import tkinter as tk
from tkinter import ttk


# ===========================
# Projection multiplier with risk
# ===========================
def projection_multiplier(position, age, risk_factor=1.0):
    position = position.upper()
    if position == "QB":
        factor = 1.0 - max(0, (age - 30) * 0.03 * risk_factor)
    elif position == "RB":
        factor = 1.0 - max(0, (age - 27) * 0.05 * risk_factor)
    elif position == "WR":
        factor = 1.0 - max(0, (age - 28) * 0.04 * risk_factor)
    elif position == "TE":
        factor = 1.0 - max(0, (age - 28) * 0.03 * risk_factor)
    else:
        factor = 1.0
    # Rising star boost
    if position == "QB" and age <= 25:
        factor *= 1.08
    elif position in ["RB", "WR"] and age <= 23:
        factor *= 1.10
    elif position == "TE" and age <= 24:
        factor *= 1.05
    return factor


# ===========================
# Group players
# ===========================
def group_and_aggregate(df):
    return (
        df.group_by(["player_id", "player_name", "position"])
        .agg([pl.col("fantasy_points").sum().alias("fantasy_points")])
    )


# ===========================
# Add projected points with risk
# ===========================
def add_projected_points(df, risk_factor=1.0):
    return df.with_columns(
        (
            pl.col("fantasy_points")
            * pl.struct(["position"]).map_elements(
                lambda x: projection_multiplier(x["position"], random.uniform(20, 35), risk_factor),
                return_dtype=pl.Float64
            )
        ).round(2).alias("projected_points")
    )


# ===========================
# Snake order generator
# ===========================
def generate_snake_order(num_teams, rounds):
    order = []
    for r in range(rounds):
        if r % 2 == 0:
            order.extend(range(1, num_teams + 1))
        else:
            order.extend(range(num_teams, 0, -1))
    return order


# ===========================
# Snake draft simulation
# Returns full draft and user roster
# ===========================
def simulate_snake_draft(player_pool, num_teams, rounds, user_team):
    ROSTER_REQUIREMENTS = {"QB":1,"RB":2,"WR":2,"TE":1}
    team_rosters = {team:{pos:0 for pos in ROSTER_REQUIREMENTS} for team in range(1,num_teams+1)}
    user_roster = []
    available = player_pool.sort("projected_points", descending=True)
    order = generate_snake_order(num_teams, rounds)
    full_draft = []


    for pick_number, team in enumerate(order, start=1):
        roster = team_rosters[team]
        needed_positions = [pos for pos in ROSTER_REQUIREMENTS if roster[pos]<ROSTER_REQUIREMENTS[pos]]
        pool = available.filter(pl.col("position").is_in(needed_positions)) if needed_positions else available
        if pool.height == 0:
            pool = available
        player = pool.head(1).to_dicts()[0]
        team_rosters[team][player["position"]] += 1


        full_draft.append({
            "round": (pick_number-1)//num_teams + 1,
            "team": team,
            "player": player["player_name"],
            "position": player["position"],
            "projected_points": player["projected_points"],
            "is_user": team == user_team
        })


        if team == user_team:
            user_roster.append(player)


        available = available.filter(pl.col("player_id") != player["player_id"])


    return full_draft, user_roster


# ===========================
# Draft IQ GUI with remove & drag
# ===========================
class DraftIQ:
    DARK_BG = "#1e1e1e"
    DARK_FRAME = "#2e2e2e"
    LIGHT_TEXT = "#f5f5f5"
    ACCENT = "#4caf50"


    def __init__(self, master):
        self.master = master
        master.title("Draft IQ")
        master.state('zoomed')
        master.configure(bg=self.DARK_BG)


        # Header
        header = tk.Label(master, text="Draft IQ", font=("Helvetica", 22, "bold"),
                          bg=self.DARK_BG, fg=self.ACCENT)
        header.pack(pady=15)


        # Input Frame
        input_frame = tk.Frame(master, bg=self.DARK_FRAME, padx=10, pady=10)
        input_frame.pack(fill=tk.X, padx=15, pady=5)


        tk.Label(input_frame, text="Number of Teams:", font=("Arial", 11), bg=self.DARK_FRAME, fg=self.LIGHT_TEXT).grid(row=0, column=0, sticky="w", pady=5)
        self.num_teams_entry = tk.Entry(input_frame, width=10, bg="#3e3e3e", fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        self.num_teams_entry.grid(row=0, column=1, padx=10, pady=5)
        self.num_teams_entry.insert(0, "10")


        tk.Label(input_frame, text="Your Draft Position:", font=("Arial", 11), bg=self.DARK_FRAME, fg=self.LIGHT_TEXT).grid(row=1, column=0, sticky="w", pady=5)
        self.user_team_entry = tk.Entry(input_frame, width=10, bg="#3e3e3e", fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        self.user_team_entry.grid(row=1, column=1, padx=10, pady=5)
        self.user_team_entry.insert(0, "1")


        tk.Label(input_frame, text="Risk Factor:", font=("Arial", 11), bg=self.DARK_FRAME, fg=self.LIGHT_TEXT).grid(row=2, column=0, sticky="w", pady=5)
        self.risk_scale = tk.Scale(input_frame, from_=0.8, to=1.2, resolution=0.01, orient=tk.HORIZONTAL,
                                   bg=self.DARK_FRAME, fg=self.LIGHT_TEXT, highlightbackground=self.DARK_FRAME,
                                   troughcolor="#3e3e3e", length=200)
        self.risk_scale.set(1.0)
        self.risk_scale.grid(row=2, column=1, padx=10, pady=5)


        self.run_button = tk.Button(input_frame, text="Run Draft", command=self.run_draft,
                                    bg=self.ACCENT, fg=self.LIGHT_TEXT, font=("Arial", 11, "bold"))
        self.run_button.grid(row=3, column=0, columnspan=2, pady=10)


        # Treeview Frame
        tree_frame = tk.Frame(master, bg=self.DARK_FRAME)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)


        columns = ("Round", "Team", "Player", "Position", "Projected Points", "Remove")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=self.DARK_BG,
                        foreground=self.LIGHT_TEXT,
                        fieldbackground=self.DARK_BG,
                        font=("Arial", 10))
        style.configure("Treeview.Heading",
                        background=self.DARK_FRAME,
                        foreground=self.ACCENT,
                        font=("Arial", 11, "bold"))
        style.map("Treeview", background=[('selected', '#555555')])


        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns[:-1]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180, anchor="center")
        self.tree.heading("Remove", text="Remove")
        self.tree.column("Remove", width=80, anchor="center")


        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill=tk.BOTH, expand=True)


        # Total projected points
        self.total_label = tk.Label(master, text="Total Projected Points: 0", font=("Arial", 12, "bold"),
                                    fg=self.LIGHT_TEXT, bg=self.DARK_BG)
        self.total_label.pack(pady=5)


        self.load_players()
        self.dragging_item = None


        # Bindings for clicks and drag
        self.tree.bind('<ButtonPress-1>', self.on_start_drag)
        self.tree.bind('<ButtonRelease-1>', self.on_drop)
        self.tree.bind('<B1-Motion>', self.on_drag_motion)
        self.tree.bind('<Button-1>', self.on_click)


    def load_players(self):
        stats = nfl.load_player_stats(2024)
        stats = stats.fill_nan(0)
        stats = stats.filter(pl.col("position").is_in(["QB","RB","WR","TE"]))
        players = group_and_aggregate(stats)
        self.players = add_projected_points(players)
        self.players = self.players.sort("projected_points", descending=True)


    def run_draft(self):
        self.full_draft, self.user_roster = [], []
        for row in self.tree.get_children():
            self.tree.delete(row)


        try:
            num_teams = int(self.num_teams_entry.get())
            user_team = int(self.user_team_entry.get())
        except ValueError:
            return


        risk_factor = self.risk_scale.get()
        self.players = add_projected_points(self.players, risk_factor=risk_factor)
        self.players = self.players.sort("projected_points", descending=True)
        rounds = sum({"QB":1,"RB":2,"WR":2,"TE":1}.values())
        self.full_draft, self.user_roster = simulate_snake_draft(self.players, num_teams, rounds, user_team)
        self.refresh_treeview()


    def refresh_treeview(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        total_points = 0
        num_teams = int(self.num_teams_entry.get())
        for i, p in enumerate(self.full_draft):
            p["round"] = i // num_teams + 1
            p["team"] = (i % num_teams) + 1
            tag_name = f"user_{p['round']}_{p['team']}" if p["is_user"] else ""
            self.tree.insert("", tk.END, iid=i, values=(p["round"], p["team"], p["player"], p["position"], round(p["projected_points"],2), "❌"), tags=(tag_name,))
            if p["is_user"]:
                self.tree.tag_configure(tag_name, background="#4caf50", foreground="#000000")
                total_points += p["projected_points"]
        self.total_label.config(text=f"Total Projected Points: {round(total_points,2)}")


    # ===========================
    # Drag-and-drop
    # ===========================
    def on_start_drag(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.dragging_item = item


    def on_drag_motion(self, event):
        if self.dragging_item:
            target = self.tree.identify_row(event.y)
            if target and target != self.dragging_item:
                dragging_index = int(self.dragging_item)
                target_index = int(target)
                self.full_draft[dragging_index], self.full_draft[target_index] = self.full_draft[target_index], self.full_draft[dragging_index]
                self.dragging_item = str(target_index)
                self.refresh_treeview()


    def on_drop(self, event):
        self.dragging_item = None


    # ===========================
    # Click remove
    # ===========================
    def on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        if col != "#6":  # Only last column is Remove
            return
        row = self.tree.identify_row(event.y)
        if row:
            index = int(row)
            del self.full_draft[index]
            self.refresh_treeview()


if __name__=="__main__":
    root = tk.Tk()
    DraftIQ(root)
    root.mainloop()

