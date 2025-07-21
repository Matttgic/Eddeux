# update_2025_file.py

import requests
import os

url = "http://www.tennis-data.co.uk/2025/2025.xlsx"
dest_folder = "tennis_data"
dest_file = os.path.join(dest_folder, "2025.xlsx")

os.makedirs(dest_folder, exist_ok=True)

try:
    response = requests.get(url)
    response.raise_for_status()
    with open(dest_file, "wb") as f:
        f.write(response.content)
    print("✅ Fichier 2025.xlsx mis à jour avec succès.")
except Exception as e:
    print(f"❌ Erreur de téléchargement : {e}")
