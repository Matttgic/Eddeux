# get_pinnacle_matches.py

import requests
import pandas as pd

RAPIDAPI_KEY = "1df93a4239msh5776d5f2c3b3a91p147a3ejsnea4c93adaca3"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "pinnacle-odds.p.rapidapi.com"
}

URL = "https://pinnacle-odds.p.rapidapi.com/kit/v1/markets"


def fetch_tennis_matches():
    response = requests.get(URL, headers=HEADERS, params={"sport_id": 2})
    response.raise_for_status()
    data = response.json()

    events = data.get("events", [])
    matches = []

    for event in events:
        league_name = event.get("league_name", "").lower()
        if "atp" not in league_name:
            continue  # ATP only
        if "challenger" in league_name or "125" in league_name or "double" in league_name:
            continue

        player1 = event.get("home")
        player2 = event.get("away")
        if not player1 or not player2:
            continue

        periods = event.get("periods", {})
        match_period = periods.get("num_0", {})
        money_line = match_period.get("money_line")

        if not isinstance(money_line, dict):
            continue  # sécurise l'accès

        odds1 = money_line.get("home")
        odds2 = money_line.get("away")

        if not odds1 or not odds2:
            continue

        matches.append({
            "player1": player1.strip(),
            "player2": player2.strip(),
            "odds1": float(odds1),
            "odds2": float(odds2),
            "surface": detect_surface(league_name),
            "match_id": event.get("id"),
            "starts": event.get("start_time")
        })

    return pd.DataFrame(matches)


def detect_surface(league_name: str) -> str:
    name = league_name.lower()
    if any(surface in name for surface in ["clay", "roland"]):
        return "elo_clay"
    elif any(surface in name for surface in ["hard", "australian", "us open"]):
        return "elo_hard"
    elif "grass" in name or "wimbledon" in name:
        return "elo_grass"
    return "elo"  # fallback
