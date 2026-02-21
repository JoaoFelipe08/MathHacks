import nflreadpy as nfl
import polars as pl
import pandas as pd
import random

# =====================================================
# SETTINGS
# =====================================================

ROSTER_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1
}

TOTAL_ROUNDS = sum(ROSTER_REQUIREMENTS.values())

# =====================================================
# AGE‑BASED PROJECTION MULTIPLIER
# =====================================================

def projection_multiplier(position, age):

    if position == "QB":
        factor = 1.0 - max(0, (age - 30) * 0.03)

    elif position == "RB":
        factor = 1.0 - max(0, (age - 27) * 0.05)

    elif position == "WR":
        factor = 1.0 - max(0, (age - 28) * 0.04)

    elif position == "TE":
        factor = 1.0 - max(0, (age - 28) * 0.03)

    else:
        factor = 1.0

    if age <= 23:
        factor *= 1.08

    return factor


# =====================================================
# LOAD YOUR CALCULATED PROJECTIONS
# =====================================================

def load_projections():

    stats = nfl.load_player_stats(2024)

    stats = stats.fill_nan(0)

    stats = stats.filter(
        pl.col("position").is_in(["QB", "RB", "WR", "TE"])
    )

    players = (
        stats.group_by(["player_id", "player_name", "position"])
        .agg([
            pl.col("fantasy_points").sum().alias("fantasy_points")
        ])
    )

    players = players.with_columns(

        (
            pl.col("fantasy_points")
            *
            pl.struct(["position"]).map_elements(
                lambda x: projection_multiplier(
                    x["position"],
                    random.uniform(20, 35)
                ),
                return_dtype=pl.Float64
            )

        ).round(2).alias("projected_points")

    )

    return players.to_pandas().reset_index(drop=True)


# =====================================================
# LOAD FAN ADP DATA
# =====================================================

def load_adp():

    url = "https://www.fantasypros.com/nfl/adp/overall.php"

    df = pd.read_html(url)[0]

    df = df.rename(columns={
        "Player Team (Bye)": "player_name",
        "AVG": "adp",
        "POS": "position"
    })

    df = df[["player_name", "position", "adp"]]

    df["player_name"] = df["player_name"].str.split("(").str[0].str.strip()

    df["position"] = df["position"].str.split().str[0].str.upper()

    df["adp"] = df["adp"].astype(float)

    return df.reset_index(drop=True)


# =====================================================
# SNAKE ORDER
# =====================================================

def generate_snake_order(num_teams, rounds):

    order = []

    for r in range(rounds):

        if r % 2 == 0:
            order.extend(range(1, num_teams + 1))
        else:
            order.extend(range(num_teams, 0, -1))

    return order


# =====================================================
# COMBINED DRAFT LOGIC
# =====================================================

def simulate_draft(adp_df, projections_df, num_teams, user_team):

    # merge datasets
    df = adp_df.merge(
        projections_df[["player_name", "projected_points"]],
        on="player_name",
        how="left"
    )

    df["projected_points"] = df["projected_points"].fillna(0)

    # only keep needed positions
    df = df[df["position"].isin(ROSTER_REQUIREMENTS.keys())]

    df = df.reset_index(drop=True)

    available = df.copy()

    # track rosters
    team_rosters = {
        team: {pos: 0 for pos in ROSTER_REQUIREMENTS}
        for team in range(1, num_teams + 1)
    }

    user_roster = []

    order = generate_snake_order(num_teams, TOTAL_ROUNDS)

    # draft loop
    for pick_number, team in enumerate(order, start=1):

        roster = team_rosters[team]

        needed_positions = [

            pos for pos in ROSTER_REQUIREMENTS
            if roster[pos] < ROSTER_REQUIREMENTS[pos]

        ]

        pool = available[
            available["position"].isin(needed_positions)
        ]

        if pool.empty:
            continue

        # YOUR TEAM → BEST PROJECTED POINTS
        if team == user_team:

            idx = pool["projected_points"].idxmax()

        # OTHER TEAMS → BEST ADP
        else:

            idx = pool["adp"].idxmin()

        player = available.loc[idx]

        # update roster
        team_rosters[team][player["position"]] += 1

        # save your picks
        if team == user_team:

            user_roster.append({

                "round": (pick_number - 1)//num_teams + 1,
                "player": player["player_name"],
                "position": player["position"],
                "projected_points": player["projected_points"],
                "adp": player["adp"]

            })

        # remove player
        available = available.drop(idx).reset_index(drop=True)

    return user_roster


# =====================================================
# MAIN
# =====================================================

print("Loading fan ADP data...")
adp = load_adp()

print("Loading your projections...")
projections = load_projections()

num_teams = int(input("\nNumber of teams: "))
user_team = int(input("Your draft position: "))

user_roster = simulate_draft(
    adp,
    projections,
    num_teams,
    user_team
)

# =====================================================
# PRINT RESULTS
# =====================================================

print("\nYOUR FINAL TEAM:\n")

for p in user_roster:

    print(
        f"Round {p['round']} | "
        f"{p['player']} | "
        f"{p['position']} | "
        f"{round(p['projected_points'],2)} pts | "
        f"ADP {p['adp']}"
    )

# roster summary
print("\nPOSITION COUNTS:")

counts = {}

for p in user_roster:
    counts[p["position"]] = counts.get(p["position"], 0) + 1

print(counts)