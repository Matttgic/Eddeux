# get_pinnacle_matches.py

import requests
import pandas as pd
from datetime import datetime

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

    matches = []
    for event in data.get("leagues", []):
        for match in event.get("events", []):
            try:
                if "doubles" in match["home"]['name'].lower():
                    continue
                if match['status'] != 'not_started':
                    continue

                home = match['home']['name']
                away = match['away']['name']

                odds = match.get("main", {}).get("odds", [])
                if len(odds) != 2:
                    continue

                matches.append({
                    "player1": home,
                    "player2": away,
                    "odds1": float(odds[0]['value']),
                    "odds2": float(odds[1]['value']),
                    "surface": detect_surface(match.get("league", {}).get("name", "")),
                    "match_id": match['id'],
                    "starts": match.get("start_time")
                })
            except Exception:
                continue

    return pd.DataFrame(matches)


def detect_surface(league_name: str) -> str:
    name = league_name.lower()
    if any(surface in name for surface in ["clay", "roland"]):
        return "elo_clay"
    elif any(surface in name for surface in ["hard", "australian", "us open"]):
        return "elo_hard"
    elif "grass" in name or "wimbledon" in name:
        return "elo_grass"
    return "elo"  # default surface
