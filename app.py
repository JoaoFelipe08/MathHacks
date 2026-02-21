from flask import Flask, jsonify, request, render_template
import pandas as pd
import nflreadpy as nfl
import polars as pl
import random

app = Flask(__name__)

data_store_fan = {}
data_store_real = {} 

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    league_size = int(data["leagueSize"])
    draft_type = data["draftType"]
    current_round = int(data["currentRound"])
    draft_position = int(data["draftPosition"])

    print("Received:", league_size, draft_type, current_round, draft_position)

    # Temporary fake calculation
    players = [
        {"name": "Player A", "score": 20 + current_round},
        {"name": "Player B", "score": 18 + draft_position},
        {"name": "Player C", "score": 15 + league_size}
    ]

    return jsonify({"players": players})


if __name__ == "__main__":
    app.run(debug=True)


# Draft Generator Based on Projected Points

# =====================================================
# Projection multiplier function
# =====================================================

def projection_multiplier(position, age):

    position = position.upper()

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

    # Rising star boost
    if position == "QB" and age <= 25:
        factor *= 1.08

    elif position == "RB" and age <= 23:
        factor *= 1.10

    elif position == "WR" and age <= 23:
        factor *= 1.10

    elif position == "TE" and age <= 24:
        factor *= 1.05

    return factor


# =====================================================
# Group so each player appears once
# =====================================================

def group_and_aggregate(df):

    return (
        df.group_by(["player_id", "player_name", "position"])
        .agg([
            pl.col("fantasy_points").sum().alias("fantasy_points")
        ])
    )


# =====================================================
# Add projected points
# =====================================================

def add_projected_points(df):

    return df.with_columns(

        (
            pl.col("fantasy_points")

            *

            pl.struct(["position"]).map_elements(

                lambda x: projection_multiplier(
                    x["position"],
                    random.uniform(20, 35)   # replace with real age later
                ),

                return_dtype=pl.Float64

            )

        )

        .round(2)

        .alias("projected_points")

    )


# =====================================================
# Snake order generator
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
# Snake draft simulation with roster limits
# =====================================================

def simulate_snake_draft_pts(player_pool, num_teams, rounds, user_team):

    ROSTER_REQUIREMENTS = {

        "QB": 1,
        "RB": 2,
        "WR": 2,
        "TE": 1

    }

    # Track each team's roster
    team_rosters = {

        team: {pos: 0 for pos in ROSTER_REQUIREMENTS}

        for team in range(1, num_teams + 1)

    }

    user_roster = []

    available = player_pool.sort(
        "projected_points",
        descending=True
    )

    order = generate_snake_order(num_teams, rounds)

    for pick_number, team in enumerate(order, start=1):

        roster = team_rosters[team]

        # Find needed positions
        needed_positions = [

            pos for pos in ROSTER_REQUIREMENTS

            if roster[pos] < ROSTER_REQUIREMENTS[pos]

        ]

        # Filter to needed positions
        if needed_positions:

            filtered = available.filter(

                pl.col("position").is_in(needed_positions)

            )

            if filtered.height == 0:

                filtered = available

        else:

            filtered = available

        # Select best player
        player = filtered.head(1).to_dicts()[0]

        # Update roster counts
        team_rosters[team][player["position"]] += 1

        # Save user's players
        if team == user_team:

            user_roster.append({

                "round": (pick_number - 1) // num_teams + 1,
                "player": player["player_name"],
                "position": player["position"],
                "projected_points": player["projected_points"]

            })

        # Remove drafted player
        available = available.filter(

            pl.col("player_id") != player["player_id"]

        )

    return user_roster


# =====================================================
# MAIN PROGRAM
# =====================================================

print("Loading NFL data...")

stats = nfl.load_player_stats(2024)

stats = stats.fill_nan(0)

# Only skill positions
stats = stats.filter(

    pl.col("position").is_in(

        ["QB", "RB", "WR", "TE"]

    )

)

# Group players
players = group_and_aggregate(stats)

# Add projections
players = add_projected_points(players)

# Sort players
players = players.sort(

    "projected_points",
    descending=True

)

# Show top players
print("\nTop 20 Players:")

print(

    players.select(

        ["player_name", "position", "projected_points"]

    ).head(20)

)


# =====================================================
# Run snake draft
# =====================================================

num_teams = int(input("\nNumber of teams: "))

rounds = int(input("Number of rounds: "))

user_team = int(input("Your draft position: "))


user_roster = simulate_snake_draft_pts(

    players,
    num_teams,
    rounds,
    user_team

)


# =====================================================
# Print your roster
# =====================================================

print("\nYOUR TEAM:\n")

for player in user_roster:

    print(

        f"Round {player['round']} | "
        f"{player['player']} | "
        f"{player['position']} | "
        f"{player['projected_points']} pts"

    )