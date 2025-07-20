import requests
import pandas as pd

# 🔧 Clés API Pinnacle
PINNACLE_HEADERS = {
    "X-RapidAPI-Key": "1df93a4239msh5776d5f2c3b3a91p147a3ejsnea4c93adaca3",
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
    response = requests.get(url, headers=PINNACLE_HEADERS, params={"sport_id": 2})
    data = response.json()

    matches = []

    for event in data.get("events", []):
        league = event.get("league_name", "").lower()
        if "atp" not in league:
            continue
        if "challenger" in league or "doubles" in league or "125" in league:
            continue

        player1 = event.get("home", "")
        player2 = event.get("away", "")
        tournament = event.get("league_name", "")
        surface = "Hard"  # valeur par défaut (si besoin on raffinera)

        # Récupération des cotes
        periods = event.get("periods", {})
        match_period = periods.get("num_0", {})
        money_line = match_period.get("money_line")

        if not isinstance(money_line, dict):
            continue

        odds1 = money_line.get("home")
        odds2 = money_line.get("away")

        if odds1 is None or odds2 is None:
            continue

        matches.append({
            "player1": normalize_name_excel_format(player1),
            "player2": normalize_name_excel_format(player2),
            "odds1": odds1,
            "odds2": odds2,
            "surface": surface,
            "tournament": tournament
        })

    return pd.DataFrame(matches)
