import pandas as pd

# -------------------------------
# Step 1: Load FantasyPros ADP
# -------------------------------
def get_fantasypros_adp():
    url = "https://www.fantasypros.com/nfl/adp/overall.php"
    tables = pd.read_html(url)
    df = tables[0]

    df = df.rename(columns={"Player Team (Bye)": "player", "AVG": "adp"})
    df = df[["player", "POS", "adp"]]

    df["player"] = df["player"].str.split("(").str[0].str.strip()
    df["POS"] = df["POS"].str.split().str[0].str.upper()
    df["adp"] = df["adp"].astype(float)

    df = df.sort_values("adp").reset_index(drop=True)
    return df

# -------------------------------
# Step 2: Snake draft order
# -------------------------------
def generate_snake_order(num_teams, rounds):
    order = []
    for r in range(rounds):
        if r % 2 == 0:
            order.extend(range(1, num_teams + 1))
        else:
            order.extend(range(num_teams, 0, -1))
    return order

# -------------------------------
# Step 3: Roster requirements
# -------------------------------
REQUIRED_POSITIONS = {"QB":1, "RB":1, "WR":2, "TE":1}

def get_needed_positions(roster):
    needs = {}
    for pos, req in REQUIRED_POSITIONS.items():
        current = len(roster.get(pos, []))
        if current < req:
            needs[pos] = req - current
    return needs

# -------------------------------
# Step 4: ADP-based draft
# -------------------------------
def simulate_draft(adp_df, num_teams, rounds, user_team):
    available = adp_df.copy().reset_index(drop=True)
    order = generate_snake_order(num_teams, rounds)
    draft = []

    # Store actual players picked for user team
    user_roster = {pos: [] for pos in REQUIRED_POSITIONS}

    for pick_number, team in enumerate(order, start=1):
        # User team picks
        if team == user_team:
            needs = get_needed_positions(user_roster)
            if needs:
                filtered = available[available["POS"].isin(needs.keys())]
                chosen_index = filtered["adp"].idxmin() if not filtered.empty else available["adp"].idxmin()
            else:
                chosen_index = available["adp"].idxmin()
        else:
            # Other teams pick next best ADP
            chosen_index = available["adp"].idxmin()

        player = available.loc[chosen_index]

        draft.append({
            "pick": pick_number,
            "round": (pick_number-1)//num_teams + 1,
            "team": team,
            "player": player["player"],
            "position": player["POS"],
            "adp": player["adp"]
        })

        # Add player to user roster if it's your pick
        if team == user_team:
            pos = player["POS"]
            if pos in user_roster:
                user_roster[pos].append(player["player"])

        # Remove picked player
        available = available.drop(chosen_index).reset_index(drop=True)

    # Convert user roster to DataFrame for display
    user_team_df = []
    for pos, players in user_roster.items():
        for p in players:
            user_team_df.append({"player": p, "position": pos})
    user_team_df = pd.DataFrame(user_team_df)

    return pd.DataFrame(draft), user_team_df

# -------------------------------
# Step 5: Main
# -------------------------------
def main():
    print("Loading FantasyPros ADP data...")
    adp_df = get_fantasypros_adp()
    print(f"Loaded {len(adp_df)} players.\n")

    num_teams = int(input("Enter number of teams: "))
    rounds = int(input("Enter number of rounds: "))
    user_team = int(input("Enter your draft position (team number): "))

    draft, user_roster_df = simulate_draft(adp_df, num_teams, rounds, user_team)

    print("\nFULL DRAFT RESULTS:\n")
    print(draft)

    print("\nYOUR FINAL ROSTER:\n")
    print(user_roster_df)

if __name__ == "__main__":
    main()