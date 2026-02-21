import requests
import pandas as pd
import random


############################################################
# STEP 1: GET ADP DATA FROM FANTASYPROS
############################################################

def get_fantasypros_adp():

    url = "https://www.fantasypros.com/nfl/adp/overall.php"

    # Read table from website
    tables = pd.read_html(url)
    df = tables[0]

    # Rename columns
    df = df.rename(columns={
        "Player Team (Bye)": "player",
        "AVG": "adp"
    })

    # Keep needed columns
    df = df[["Rank", "player", "POS", "adp"]]

    # Clean player names (remove team and bye info)
    df["player"] = df["player"].str.split("(").str[0].str.strip()

    # Convert ADP to float
    df["adp"] = df["adp"].astype(float)

    # Create weight (lower ADP = higher probability)
    df["weight"] = 1 / df["adp"]

    return df


############################################################
# STEP 2: GENERATE SNAKE ORDER
############################################################

def generate_snake_order(num_teams, rounds):

    order = []

    for round_num in range(1, rounds + 1):

        if round_num % 2 == 1:
            round_order = list(range(1, num_teams + 1))
        else:
            round_order = list(range(num_teams, 0, -1))

        order.extend(round_order)

    return order


############################################################
# STEP 3: SIMULATE DRAFT
############################################################

def simulate_snake_draft(adp_df, num_teams, rounds):

    available_players = adp_df.copy().reset_index(drop=True)

    snake_order = generate_snake_order(num_teams, rounds)

    results = []

    for pick_number, team in enumerate(snake_order, start=1):

        weights = available_players["weight"]

        chosen_index = random.choices(
            available_players.index,
            weights=weights,
            k=1
        )[0]

        player = available_players.loc[chosen_index]

        results.append({
            "pick": pick_number,
            "round": (pick_number - 1) // num_teams + 1,
            "team": team,
            "player": player["player"],
            "position": player["POS"],
            "adp": player["adp"]
        })

        # Remove drafted player
        available_players = available_players.drop(chosen_index).reset_index(drop=True)

    return pd.DataFrame(results)


############################################################
# STEP 4: GET YOUR TEAM PICKS
############################################################

def get_user_team(draft_df, user_team):

    return draft_df[draft_df["team"] == user_team]


############################################################
# STEP 5: MAIN PROGRAM
############################################################

def main():

    print("Loading FantasyPros ADP data...")
    adp_df = get_fantasypros_adp()

    print("Loaded", len(adp_df), "players")

    num_teams = int(input("Enter number of teams: "))
    rounds = int(input("Enter number of rounds: "))
    user_team = int(input("Enter your draft position (team number): "))

    draft = simulate_snake_draft(adp_df, num_teams, rounds)

    print("\nFULL DRAFT RESULTS:\n")
    print(draft)

    print("\nYOUR TEAM PICKS:\n")
    print(get_user_team(draft, user_team))


############################################################
# RUN PROGRAM
############################################################

if __name__ == "__main__":
    main()