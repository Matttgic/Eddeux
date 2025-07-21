import pandas as pd
import os
from glob import glob

# 🌍 Dossier contenant les fichiers Excel tennis-data
DATA_DIR = "Données"
OUTPUT_FILE = "elo_probs.csv"

# 🟩 Conversion surface → colonne Elo
SURFACE_MAP = {
    "Hard": "elo_hard",
    "Clay": "elo_clay",
    "Grass": "elo_grass"
}

# 📥 Lecture et fusion de tous les fichiers tennis-data
files = glob(os.path.join(DATA_DIR, "*.xls*"))
print(f"🔎 {len(files)} fichiers trouvés dans {DATA_DIR}/")

df_list = []
for file in files:
    try:
        df = pd.read_excel(file)
        print(f"✅ Chargé : {os.path.basename(file)} ({len(df)} lignes)")
        df_list.append(df)
    except Exception as e:
        print(f"❌ Erreur chargement {file} : {e}")

if not df_list:
    print("❌ Aucun fichier Excel n’a pu être lu. Arrêt.")
    exit()

raw = pd.concat(df_list, ignore_index=True)
print(f"📊 Total fusionné : {raw.shape[0]} lignes")

# 🔧 Nettoyage et filtrage
raw = raw.rename(columns=lambda x: x.strip())
raw = raw[raw['Surface'].isin(SURFACE_MAP.keys())]
raw = raw.dropna(subset=['Winner', 'Loser'])

# 🛠️ Initialisation Elo
base_elo = 1500
elos = {}

# 🔁 Mise à jour Elo surface par surface
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

# 🧱 Construction du DataFrame final
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

# 📈 Résumé
print(f"✅ Fichier {OUTPUT_FILE} généré avec {len(final_df)} joueurs uniques.") 
