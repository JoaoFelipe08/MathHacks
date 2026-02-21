import pandas as pd
import random


############################################################
# LOAD FANTASYPROS ADP
############################################################

def get_fantasypros_adp():

    url = "https://www.fantasypros.com/nfl/adp/overall.php"
    df = pd.read_html(url)[0]

    df = df.rename(columns={
        "Player Team (Bye)": "player",
        "AVG": "adp"
    })

    df = df[["player", "POS", "adp"]]

    df["player"] = df["player"].str.split("(").str[0].str.strip()

    df["adp"] = df["adp"].astype(float)

    df["weight"] = 1 / df["adp"]

    return df


############################################################
# GENERATE SNAKE ORDER
############################################################

def generate_snake_order(num_teams, rounds):

    order = []

    for r in range(rounds):

        if r % 2 == 0:
            order.extend(range(1, num_teams+1))
        else:
            order.extend(range(num_teams, 0, -1))

    return order


############################################################
# USER TEAM POSITION NEEDS
############################################################

REQUIRED_POSITIONS = {
    "QB": 1,
    "WR": 2,
    "RB": 1,
    "TE": 1
}


############################################################
# CHECK WHAT USER TEAM STILL NEEDS
############################################################

def get_needed_positions(team_roster):

    needs = {}

    for pos, required in REQUIRED_POSITIONS.items():

        current = team_roster.get(pos, 0)

        if current < required:
            needs[pos] = required - current

    return needs


############################################################
# SIMULATE DRAFT WITH USER STRATEGY
############################################################

def simulate_snake_draft(adp_df, num_teams, rounds, user_team):

    available = adp_df.copy().reset_index(drop=True)

    order = generate_snake_order(num_teams, rounds)

    draft = []

    # Track user's roster
    user_roster = {}

    for pick_number, team in enumerate(order, start=1):

        # USER TEAM PICK
        # USER TEAM PICK
        if team == user_team:

            needs = get_needed_positions(user_roster)

            if needs:
                 # Filter only needed positions
                filtered = available[available["POS"].isin(needs.keys())]

                if not filtered.empty:
                    # Choose best ADP (lowest number)
                    chosen_index = filtered["adp"].idxmin()
                else:
                    # If no players left in needed positions, pick best overall
                    chosen_index = available["adp"].idxmin()
        else:
            # Choose best overall ADP
            chosen_index = available["adp"].idxmin()
            # second part 
        if team == user_team:

            needs = get_needed_positions(user_roster)

            if needs:
                # Filter only needed positions
                filtered = available[available["POS"].isin(needs.keys())]

                # Choose best ADP (lowest number)
                chosen_index = filtered["adp"].idxmin()
            else:
                # Choose best overall ADP
                chosen_index = available["adp"].idxmin()

        else:
            # OTHER TEAMS: weighted random
            weights = available["weight"]

            chosen_index = random.choices(
                available.index,
                weights=weights,
                k=1
            )[0]

        player = available.loc[chosen_index]

        draft.append({
            "pick": pick_number,
            "team": team,
            "player": player["player"],
            "pos": player["POS"],
            "adp": player["adp"]
        })

        # Update user roster
        if team == user_team:

            pos = player["POS"]

            user_roster[pos] = user_roster.get(pos, 0) + 1

        available = available.drop(chosen_index).reset_index(drop=True)

    return pd.DataFrame(draft), user_roster


############################################################
# RUN
############################################################

adp = get_fantasypros_adp()

draft, roster = simulate_snake_draft(
    adp_df=adp,
    num_teams=10,
    rounds=8,
    user_team=5
)

print("\nFULL DRAFT:")
print(draft)

print("\nYOUR FINAL ROSTER:")
print(roster)