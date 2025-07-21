# test_debug.py

import pandas as pd
from model import EloModel
from get_pinnacle_matches import fetch_tennis_matches
import os

print("🔍 DIAGNOSTIC COMPLET")
print("=" * 50)

# Test 1: Fichier Elo
print("1️⃣ TEST FICHIER ELO")
elo_file = "elo_probs.csv"
if not os.path.exists(elo_file):
    print("❌ Fichier elo_probs.csv manquant")
    print("👉 Lancez: python prepare_elo_csv.py")
else:
    try:
        model = EloModel(elo_file)
        print(f"✅ {len(model.df)} joueurs chargés")
        print(f"📊 Colonnes: {model.df.columns.tolist()}")
        print(f"🎾 Exemple: {model.df.head(3)}")
        
        # Test joueur spécifique
        test_elo = model.get_elo("Djokovic N.", "Hard")
        print(f"🏆 Test Djokovic: {test_elo}")
        
    except Exception as e:
        print(f"❌ Erreur Elo: {e}")

print("\n" + "=" * 50)

# Test 2: API Pinnacle
print("2️⃣ TEST API PINNACLE")
try:
    matches = fetch_tennis_matches()
    print(f"✅ {len(matches)} matchs récupérés")
    
    if not matches.empty:
        print(f"📊 Colonnes: {matches.columns.tolist()}")
        print("🎾 Matchs:")
        for _, match in matches.head(3).iterrows():
            print(f"   {match['player1']} vs {match['player2']} ({match['odds1']}/{match['odds2']})")
    else:
        print("⚠️ Aucun match trouvé")
        
except Exception as e:
    print(f"❌ Erreur API: {e}")

print("\n" + "=" * 50)

# Test 3: Calcul value bets
print("3️⃣ TEST VALUE BETS")
try:
    from value_bets import compute_value_bets
    df = compute_value_bets(elo_file, 0.0)
    print(f"✅ {len(df)} value bets calculés")
    if not df.empty:
        print(df.head())
except Exception as e:
    print(f"❌ Erreur value bets: {e}")
