import pandas as pd
from get_pinnacle_matches import fetch_tennis_matches
from model import EloModel

def compute_value_bets(elo_file: str, min_value_threshold: float = 0.05) -> pd.DataFrame:
    model = EloModel(elo_file)
    matches_df = fetch_tennis_matches()

    rows = []
    for _, row in matches_df.iterrows():
        p1 = row["player1"]
        p2 = row["player2"]
        surface = row["surface"]

        elo1 = model.get_elo(p1, surface)
        elo2 = model.get_elo(p2, surface)

        if elo1 is None or elo2 is None:
            continue

        # Probabilité selon Elo
        p_elo = 1 / (1 + 10 ** ((elo2 - elo1) / 400))

        # Probabilité implicite selon les cotes Pinnacle
        odds1 = row["odds1"]
        odds2 = row["odds2"]
        p_cotes = 1 / odds1
        margin = 1 / odds1 + 1 / odds2
        p_cotes = p_cotes / margin  # retrait de la marge

        value = p_elo - p_cotes

        if value >= min_value_threshold:
            rows.append({
                "match": f"{p1} vs {p2}",
                "player1": p1,
                "player2": p2,
                "surface": surface,
                "elo1": round(elo1),
                "elo2": round(elo2),
                "prob_elo": round(p_elo * 100, 1),
                "prob_cotes": round(p_cotes * 100, 1),
                "value": round(value * 100, 1),
                "cote_pinnacle": odds1,
                "tournament": row.get("tournament", ""),
                "start_time": row.get("starts", "")
            })

    return pd.DataFrame(rows)
