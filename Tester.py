import random
import pandas as pd

from Simulator import get_fantasypros_adp
def simulate_snake_draft(adp_df, num_teams, rounds):

    available = adp_df.copy().reset_index(drop=True)

    draft = []
    pick_number = 1

    for round_num in range(1, rounds + 1):

        # Snake order
        if round_num % 2 == 1:
            order = list(range(1, num_teams + 1))
        else:
            order = list(range(num_teams, 0, -1))

        for team in order:

            weights = available["weight"]

            chosen_index = random.choices(
                available.index,
                weights=weights,
                k=1
            )[0]

            player = available.loc[chosen_index]

            draft.append({
                "pick": pick_number,
                "round": round_num,
                "team": team,
                "player": player["player"],
                "pos": player["POS"],
                "adp": player["adp"]
            })

            available = available.drop(chosen_index).reset_index(drop=True)

            pick_number += 1

    return pd.DataFrame(draft)

adp = get_fantasypros_adp()

draft = simulate_snake_draft(
    adp_df=adp,
    num_teams=10,
    rounds=5
)

print(draft)