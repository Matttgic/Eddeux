# value_bets.py

import pandas as pd
from model import EloModel
from get_pinnacle_matches import fetch_tennis_matches


def compute_implied_prob(odds: float) -> float:
    return 1 / odds if odds and odds > 0 else 0


def compute_value_bets(elo_csv_path: str, min_value_threshold: float = 0.05) -> pd.DataFrame:
    model = EloModel(elo_csv_path)
    matches_df = fetch_tennis_matches()

    value_bets = []

    for _, row in matches_df.iterrows():
        player1 = row["player1"]
        player2 = row["player2"]
        surface = row["surface"]

        proba = model.get_probability(player1, player2, surface)
        if proba is None:
            continue

        implied1 = compute_implied_prob(row["odds1"])
        implied2 = compute_implied_prob(row["odds2"])

        value1 = proba - implied1
        value2 = (1 - proba) - implied2

        if value1 >= min_value_threshold:
            value_bets.append({
                "match": f"{player1} vs {player2}",
                "player": player1,
                "cote": row["odds1"],
                "proba": round(proba, 3),
                "value": round(value1, 3),
                "surface": surface,
                "start_time": row["starts"]
            })
        elif value2 >= min_value_threshold:
            value_bets.append({
                "match": f"{player1} vs {player2}",
                "player": player2,
                "cote": row["odds2"],
                "proba": round(1 - proba, 3),
                "value": round(value2, 3),
                "surface": surface,
                "start_time": row["starts"]
            })

    return pd.DataFrame(value_bets)
