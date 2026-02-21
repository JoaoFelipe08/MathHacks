import requests
import pandas as pd

def ageFactor(player_name, userFactor):
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
    
    # Get age info
    age = player.iloc[0]['age']
    
    # Handle players with missing age data
    if pd.isna(age):
        return effectedFactor
    
    # Adjust factor based on age
    if age < 25:
        return effectedFactor * (userFactor + 1)
    elif age > 30:
        return effectedFactor * userFactor
    else:
        return effectedFactor 
print(ageFactor("Patrick Mahomes",0.9))
    