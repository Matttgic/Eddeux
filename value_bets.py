# value_bets.py

import pandas as pd
from get_pinnacle_matches import fetch_tennis_matches
from model import EloModel

def compute_value_bets(elo_file: str, min_value_threshold: float = 0.05) -> pd.DataFrame:
    try:
        # Chargement modèle Elo
        model = EloModel(elo_file)
        print(f"✅ Modèle Elo chargé")
        
        # Récupération matchs API
        matches_df = fetch_tennis_matches()
        
        if matches_df.empty:
            print("❌ Aucun match récupéré de l'API")
            return pd.DataFrame()
            
        print(f"🎾 {len(matches_df)} matchs à analyser")
        
    except Exception as e:
        print(f"❌ Erreur initialisation : {e}")
        return pd.DataFrame()

    rows = []
    matches_analyzed = 0
    matches_with_elo = 0
    
    for _, row in matches_df.iterrows():
        p1 = row["player1"]
        p2 = row["player2"]
        surface = row["surface"]

        # Récupération Elo
        elo1 = model.get_elo(p1, surface)
        elo2 = model.get_elo(p2, surface)
        
        matches_analyzed += 1

        if elo1 is None or elo2 is None:
            print(f"⚠️ Elo manquant : {p1} vs {p2}")
            continue
            
        matches_with_elo += 1

        # Probabilité selon Elo
        p_elo = 1 / (1 + 10 ** ((elo2 - elo1) / 400))

        # Probabilité implicite selon les cotes Pinnacle
        odds1 = float(row["odds1"])
        odds2 = float(row["odds2"])
        
        # Retrait de la marge bookmaker
        p_cotes = 1 / odds1
        margin = 1 / odds1 + 1 / odds2
        p_cotes = p_cotes / margin

        # Calcul value
        value = p_elo - p_cotes

        print(f"📊 {p1} vs {p2}: Elo={p_elo:.3f}, Cotes={p_cotes:.3f}, Value={value:.3f}")

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
                "starts": row.get("starts", "")  # ✅ CORRECTION : "starts" au lieu de "start_time"
            })

    print(f"📈 Résumé : {matches_analyzed} analysés, {matches_with_elo} avec Elo, {len(rows)} value bets")
    return pd.DataFrame(rows)

# Test
if __name__ == "__main__":
    df = compute_value_bets("elo_probs.csv", 0.0)
    print(df)
