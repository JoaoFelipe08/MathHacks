import requests
import pandas as pd

def injuryFactor(player_name, userFactor):
    effectedFactor = 1.0
    url = "https://api.sleeper.app/v1/players/nfl"
    
    # Get player data
    players = requests.get(url).json()
    
    # Convert to DataFrame
    df = pd.DataFrame(players).T
    
    # Find the player (case insensitive)
    player = df[df['full_name'].str.lower() == player_name.lower()]
    
    # Check if player exists
    if player.empty:
        return f"Player '{player_name}' not found."
    
    # Get injury info
    injury_status = player.iloc[0]['injury_status']
    
    # Handle healthy players
    if pd.isna(injury_status):
        return effectedFactor
    
    return effectedFactor*userFactor

print(injuryFactor("Patrick Mahomes",0.9))
