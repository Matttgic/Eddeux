# update_2025_file.py

import requests
import os

def main():
    url = "http://www.tennis-data.co.uk/2025/2025.xlsx"
    dest_folder = "Données"
    dest_file = os.path.join(dest_folder, "2025.xlsx")

    os.makedirs(dest_folder, exist_ok=True)

    try:
        print(f"📥 Téléchargement de {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(dest_file, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Fichier 2025.xlsx mis à jour ({len(response.content)} bytes)")
        
    except Exception as e:
        print(f"❌ Erreur de téléchargement : {e}")
        exit(1)

if __name__ == "__main__":
    main()
