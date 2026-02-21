import nflreadpy as nfl
import polars as pl
import random

# -----------------------------------
# Projection multiplier function
# -----------------------------------
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
        raise ValueError(f"Unknown position: {position}")

    if position == "QB" and age <= 25:
        factor *= 1.08
    elif position == "RB" and age <= 23:
        factor *= 1.10
    elif position == "WR" and age <= 23:
        factor *= 1.10
    elif position == "TE" and age <= 24:
        factor *= 1.05

    return factor


# -----------------------------------
# Group players so each appears once
# -----------------------------------
def group_and_aggregate(df):
    return (
        df.group_by(['player_id', 'player_name', 'position'])
        .agg([
            pl.col('fantasy_points').sum().alias('fantasy_points'),
        ])
    )


# -----------------------------------
# Add projected points column
# -----------------------------------
def add_projected_points(df):
    return df.with_columns(
        (
            pl.col("fantasy_points") *
            pl.struct(["position"]).map_elements(
                lambda x: projection_multiplier(
                    x["position"],
                    random.uniform(20, 40)
                ),
                return_dtype=pl.Float64,
            )
        ).round(2).alias("projected_points")
    )


# -----------------------------------
# Snake draft order generator
# -----------------------------------
def generate_snake_order(num_teams, rounds):

    order = []

    for r in range(rounds):

        if r % 2 == 0:
            order.extend(range(1, num_teams + 1))
        else:
            order.extend(range(num_teams, 0, -1))

    return order


# -----------------------------------
# Snake draft simulation
# -----------------------------------
def simulate_snake_draft(player_pool, num_teams, rounds):

    available = player_pool.sort("projected_points", descending=True)

    order = generate_snake_order(num_teams, rounds)

    draft_results = []

    for pick_number, team in enumerate(order, start=1):

        # pick best available player
        player = available.row(0, named=True)

        draft_results.append({
            "pick": pick_number,
            "round": (pick_number - 1) // num_teams + 1,
            "team": team,
            "player": player["player_name"],
            "position": player["position"],
            "projected_points": player["projected_points"]
        })

        # remove drafted player
        available = available.slice(1)

    return draft_results


# -----------------------------------
# Load data
# -----------------------------------
stats = nfl.load_player_stats(2024)
stats = stats.fill_nan(0)

qb_df = stats.filter(pl.col('position') == 'QB')
rb_df = stats.filter(pl.col('position') == 'RB')
wr_df = stats.filter(pl.col('position') == 'WR')
te_df = stats.filter(pl.col('position') == 'TE')

qb_df = add_projected_points(group_and_aggregate(qb_df))
rb_df = add_projected_points(group_and_aggregate(rb_df))
wr_df = add_projected_points(group_and_aggregate(wr_df))
te_df = add_projected_points(group_and_aggregate(te_df))

# -----------------------------------
# Combine ALL players into one pool
# -----------------------------------
all_players = pl.concat([qb_df, rb_df, wr_df, te_df])

all_players = all_players.sort("projected_points", descending=True)

print("\nTop 20 Overall Players:")
print(all_players.select([
    "player_name",
    "position",
    "projected_points"
]).head(20))


# -----------------------------------
# Run snake draft
# -----------------------------------
num_teams = int(input("\nNumber of teams: "))
rounds = int(input("Number of rounds: "))

draft = simulate_snake_draft(all_players, num_teams, rounds)

print("\nSNAKE DRAFT RESULTS:\n")

for pick in draft:
    print(
        f"Pick {pick['pick']} | "
        f"Round {pick['round']} | "
        f"Team {pick['team']} | "
        f"{pick['player']} ({pick['position']}) | "
        f"{pick['projected_points']} pts"
    )