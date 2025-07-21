import pandas as pd
import os
from glob import glob

SURFACE_MAP = {
    "Hard": "elo_hard",
    "Clay": "elo_clay",
    "Grass": "elo_grass"
}

DATA_DIR = "Données"
OUTPUT_FILE = "elo_probs.csv"

# Lecture et fusion de tous les fichiers tennis-data
files = glob(os.path.join(DATA_DIR, "*.xls*"))
df_list = []
for file in files:
    try:
        df = pd.read_excel(file)
        df_list.append(df)
    except Exception:
        continue

raw = pd.concat(df_list, ignore_index=True)

# Normalisation colonnes
raw = raw.rename(columns=lambda x: x.strip())
raw = raw[raw['Surface'].isin(SURFACE_MAP.keys())]
raw = raw.dropna(subset=['Winner', 'Loser'])

# 👉 On garde les noms des joueurs tels quels (format complet)

# Initialisation Elo
base_elo = 1500
elos = {}

# Mise à jour Elo par surface
for surface_label, colname in SURFACE_MAP.items():
    elos[colname] = {}

    data = raw[raw['Surface'] == surface_label].sort_values("Date")

    for _, row in data.iterrows():
        w, l = row['Winner'], row['Loser']
        K = 32

        ew = elos[colname].get(w, base_elo)
        el = elos[colname].get(l, base_elo)

        prob_w = 1 / (1 + 10 ** ((el - ew) / 400))
        ew_new = ew + K * (1 - prob_w)
        el_new = el + K * (0 - (1 - prob_w))

        elos[colname][w] = ew_new
        elos[colname][l] = el_new

# Agrégation dans un seul DataFrame
players = set()
for d in elos.values():
    players.update(d.keys())

rows = []
for player in players:
    row = {"player": player}
    for colname in SURFACE_MAP.values():
        row[colname] = elos[colname].get(player, base_elo)
    row["elo"] = sum(row[s] for s in SURFACE_MAP.values()) / 3
    rows.append(row)

final_df = pd.DataFrame(rows)
final_df.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Fichier {OUTPUT_FILE} généré avec {len(final_df)} joueurs.")
