# model.py

import pandas as pd

class EloModel:
    def __init__(self, filepath: str):
        self.df = pd.read_csv(filepath)
        self.df['player'] = self.df['player'].apply(self.normalize_name)

    def normalize_name(self, name: str) -> str:
        parts = name.strip().split(" ")
        if len(parts) == 1:
            return name
        return f"{parts[0][0]}. {' '.join(parts[1:])}"  # e.g. "Novak Djokovic" -> "N. Djokovic"

    def get_elo(self, player: str, surface: str) -> float:
        player = self.normalize_name(player)
        row = self.df[self.df['player'] == player]
        if row.empty:
            return None
        if surface in row.columns:
            return float(row[surface].values[0])
        return float(row['elo'].values[0])  # fallback to general elo

    def get_probability(self, player1: str, player2: str, surface: str) -> float:
        elo1 = self.get_elo(player1, surface)
        elo2 = self.get_elo(player2, surface)

        if elo1 is None or elo2 is None:
            return None

        diff = elo1 - elo2
        prob = 1 / (1 + 10 ** (-diff / 400))
        return prob
