import pandas as pd

# -------------------------------
# Step 1: Load FantasyPros ADP
# -------------------------------
def get_fantasypros_adp():
    url = "https://www.fantasypros.com/nfl/adp/overall.php"

    # Read tables from the page
    tables = pd.read_html(url)
    df = tables[0]

    # Rename columns
    df = df.rename(columns={"Player Team (Bye)": "player", "AVG": "adp"})

    # Keep only relevant columns
    df = df[["player", "POS", "adp"]]

    # Clean player names
    df["player"] = df["player"].str.split("(").str[0].str.strip()

    # Clean POS column
    df["POS"] = df["POS"].str.split().str[0].str.upper()

    # Convert ADP to float
    df["adp"] = df["adp"].astype(float)

    # Sort by ADP (lowest ADP = best pick)
    df = df.sort_values("adp").reset_index(drop=True)

    return df

# -------------------------------
# Step 2: Generate snake draft order
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
        current = roster.get(pos, 0)
        if current < req:
            needs[pos] = req - current
    return needs

# -------------------------------
# Step 4: ADP-based snake draft
# -------------------------------
def simulate_draft(adp_df, num_teams, rounds, user_team):
    available = adp_df.copy().reset_index(drop=True)
    order = generate_snake_order(num_teams, rounds)
    draft = []
    user_roster = {}

    for pick_number, team in enumerate(order, start=1):

        # User team picks based on roster needs and ADP
        if team == user_team:
            needs = get_needed_positions(user_roster)
            if needs:
                filtered = available[available["POS"].isin(needs.keys())]
                chosen_index = filtered["adp"].idxmin() if not filtered.empty else available["adp"].idxmin()
            else:
                chosen_index = available["adp"].idxmin()
        else:
            # Other teams: just pick next best ADP
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

        # Update user roster
        if team == user_team:
            pos = player["player"]
            user_roster[pos] = user_roster.get(pos, 0) + 1

        # Remove picked player
        available = available.drop(chosen_index).reset_index(drop=True)

    return pd.DataFrame(draft), user_roster

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

    draft, roster = simulate_draft(adp_df, num_teams, rounds, user_team)

    print("\nFULL DRAFT RESULTS:\n")
    print(draft)

    print("\nYOUR FINAL ROSTER:\n")
    print(roster)

if __name__ == "__main__":
    main()