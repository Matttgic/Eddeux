# model.py

import pandas as pd

class EloModel:
    def __init__(self, filepath: str):
        try:
            self.df = pd.read_csv(filepath)
            self.df['player'] = self.df['player'].apply(self.normalize_name)
            print(f"✅ {len(self.df)} joueurs chargés depuis {filepath}")
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Fichier {filepath} introuvable")
        except Exception as e:
            raise Exception(f"❌ Erreur lecture CSV : {e}")

    def normalize_name(self, name: str) -> str:
        if pd.isna(name):
            return ""
        parts = name.strip().split()
        if len(parts) == 1:
            return name
        return f"{parts[0][0]}. {' '.join(parts[1:])}"

    def get_elo(self, player: str, surface: str) -> float:
        player_norm = self.normalize_name(player)
        row = self.df[self.df['player'] == player_norm]

        if row.empty:
            print(f"❌ Joueur non trouvé : '{player_norm}'")
            return None

        # Mapping surface vers colonne
        surface_map = {
            "Hard": "elo_hard",
            "Clay": "elo_clay", 
            "Grass": "elo_grass"
        }
        
        col = surface_map.get(surface, "elo")
        
        if col in self.df.columns:
            return float(row[col].values[0])
        elif "elo" in self.df.columns:
            return float(row["elo"].values[0])
        else:
            raise ValueError(f"❌ Colonnes Elo manquantes dans le CSV")

    def get_probability(self, player1: str, player2: str, surface: str) -> float:
        elo1 = self.get_elo(player1, surface)
        elo2 = self.get_elo(player2, surface)

        if elo1 is None or elo2 is None:
            return None

        diff = elo1 - elo2
        prob = 1 / (1 + 10 ** (-diff / 400))
        return prob

# Test
if __name__ == "__main__":
    try:
        model = EloModel("elo_probs.csv")
        print(model.df.columns.tolist())
        print(model.df.head())
    except Exception as e:
        print(f"Erreur : {e}")
