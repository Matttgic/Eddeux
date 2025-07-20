from value_bets import compute_value_bets
import pandas as pd

# Réduction du seuil de value bet pour tester
df = compute_value_bets("elo_probs.csv", min_value_threshold=0.01)

if df.empty:
    print("❌ Aucun value bet détecté.\n")
else:
    print(f"✅ {len(df)} value bet(s) détecté(s) :\n")
    print(df.to_string(index=False))
