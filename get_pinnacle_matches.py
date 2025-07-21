# get_pinnacle_matches.py

import requests
import pandas as pd

# 🔧 Clés API Pinnacle
PINNACLE_HEADERS = {
    "X-RapidAPI-Key": "e1e76b8e3emsh2445ffb97db0128p158afdjsnb3175ce8d916",
    "X-RapidAPI-Host": "pinnacle-odds.p.rapidapi.com"
}

# ✅ Convertit un nom complet ("Carlos Alcaraz") en "Alcaraz C."
def normalize_name_excel_format(full_name: str) -> str:
    parts = full_name.strip().split()
    if len(parts) < 2:
        return full_name
    first = parts[0]
    last = " ".join(parts[1:])
    return f"{last} {first[0]}."

# 📥 Récupère les matchs ATP à venir depuis l'API Pinnacle
def fetch_tennis_matches():
    url = "https://pinnacle-odds.p.rapidapi.com/kit/v1/markets"
    params = {"sport_id": 2}  # Tennis uniquement
    
    try:
        response = requests.get(url, headers=PINNACLE_HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur API : {e}")
        return pd.DataFrame()

    matches = []

    # ✅ Structure correcte : events (pas data)
    events = data.get("events", [])
    print(f"🔍 {len(events)} événements trouvés")

    for event in events:
        league = event.get("league_name", "").lower()
        
        # Filtrage ATP/WTA seulement
        if not ("atp" in league or "wta" in league):
            continue
        if "challenger" in league or "125" in league or "double" in league:
            continue

        player1 = event.get("home", "")
        player2 = event.get("away", "")
        tournament = event.get("league_name", "")
        surface = "Hard"  # par défaut
        start_time = event.get("starts", None)

        # ✅ STRUCTURE PINNACLE SPÉCIFIQUE
        periods = event.get("periods", {})
        match_period = periods.get("num_0", {})
        money_line = match_period.get("money_line", {})

        if not money_line:
            print(f"⚠️ Pas de money_line pour {player1} vs {player2}")
            continue

        odds1 = money_line.get("home")
        odds2 = money_line.get("away")

        if odds1 is None or odds2 is None:
            print(f"⚠️ Cotes manquantes : {player1} vs {player2}")
            continue

        print(f"✅ Match trouvé : {player1} vs {player2} - Cotes: {odds1}/{odds2}")

        matches.append({
            "player1": normalize_name_excel_format(player1),
            "player2": normalize_name_excel_format(player2),
            "odds1": odds1,
            "odds2": odds2,
            "surface": surface,
            "tournament": tournament,
            "starts": start_time
        })

    print(f"🎾 {len(matches)} matchs ATP/WTA récupérés")
    return pd.DataFrame(matches)

# Test direct
if __name__ == "__main__":
    df = fetch_tennis_matches()
    print(df) 
