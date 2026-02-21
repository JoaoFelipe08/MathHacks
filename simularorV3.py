import pandas as pd

############################################################
# STEP 1: GET FANTASYPROS ADP
############################################################
def get_fantasypros_adp():
    """
    Pulls FantasyPros ADP (Average Draft Position) data from the website.
    Returns a DataFrame sorted by ADP (lowest = highest pick).
    """
    url = "https://www.fantasypros.com/nfl/adp/overall.php"
    df = pd.read_html(url)[0]

    # Rename columns for convenience
    df = df.rename(columns={
        "Player Team (Bye)": "player",
        "AVG": "adp"
    })

    # Keep only the relevant columns
    df = df[["player", "POS", "adp"]]

    # Clean player names (remove team and bye info)
    df["player"] = df["player"].str.split("(").str[0].str.strip()

    # Convert ADP to float
    df["adp"] = df["adp"].astype(float)

    # Sort by ADP (lowest = most picked by fans)
    df = df.sort_values("adp").reset_index(drop=True)

    return df

############################################################
# STEP 2: PICK TEAM BASED ON POSITION NEEDS
############################################################
def pick_team(adp_df):
    """
    Picks a fantasy team based on your roster requirements:
    1 QB, 1 RB, 2 WR, 1 TE
    """
    # Define roster requirements
    required_positions = {
        "QB": 1,
        "RB": 1,
        "WR": 2,
        "TE": 1
    }

    team = []  # Store selected players
    remaining = required_positions.copy()
    
    # Iterate through ADP list
    for idx, row in adp_df.iterrows():
        pos = row["POS"]
        if pos in remaining and remaining[pos] > 0:
            team.append({
                "player": row["player"],
                "position": pos,
                "adp": row["adp"]
            })
            remaining[pos] -= 1

        # Stop when all roster spots are filled
        if sum(remaining.values()) == 0:
            break

    return pd.DataFrame(team)

############################################################
# STEP 3: MAIN PROGRAM
############################################################
def main():
    print("Loading FantasyPros ADP data...")
    adp = get_fantasypros_adp()
    print(f"Loaded {len(adp)} players.\n")

    # Pick your team based on fan ADP
    team = pick_team(adp)

    print("YOUR TEAM BASED ON FAN AVERAGE PICKS:\n")
    print(team)

############################################################
# RUN PROGRAM
############################################################
if __name__ == "__main__":
    main()