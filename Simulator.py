import requests
import pandas as pd

def get_fantasypros_adp():
    url = "https://www.fantasypros.com/nfl/adp/overall.php"

    tables = pd.read_html(url)

    # First table contains ADP data
    df = tables[0]

    # Clean columns
    df = df.rename(columns={
        "Player Team (Bye)": "player",
        "AVG": "adp"
    })

    # Keep only what we need
    df = df[["Rank", "player", "POS", "AVG"]]
    df = df.rename(columns={"AVG": "adp"})

    # Remove team info from player name
    df["player"] = df["player"].str.split("(").str[0].str.strip()

    # Convert ADP to probability weight
    # Lower ADP = higher probability
    df["weight"] = 1 / df["adp"]

    return df