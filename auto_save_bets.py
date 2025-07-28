# auto_save_bets.py
import pandas as pd
from datetime import datetime
from value_bets import compute_value_bets
import os

def save_daily_bets():
    """Sauvegarde automatique des value bets quotidiens"""
    
    # Paramètres configurables
    SEUIL_A = 0.05  # 5% pour stratégie A
    TOP_PERCENT_B = 20  # Top 20% pour stratégie B
    
    try:
        # Récupère tous les matchs
        df_all = compute_value_bets("elo_probs.csv", 0.0)
        
        if df_all.empty:
            print("❌ Aucun match trouvé")
            return
            
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Stratégie A - Seuil fixe
        df_a = df_all[df_all['value'] >= SEUIL_A * 100]
        if not df_a.empty:
            df_a['date'] = date_str
            df_a['strategie'] = 'A_seuil_5pct'
            append_to_csv(df_a, "historique_strategy_A.csv")
            print(f"✅ {len(df_a)} bets stratégie A sauvés")
        
        # Stratégie B - Top %
        df_sorted = df_all.sort_values('value', ascending=False)
        nb_top = max(1, int(len(df_sorted) * TOP_PERCENT_B / 100))
        df_b = df_sorted.head(nb_top)
        if not df_b.empty:
            df_b['date'] = date_str
            df_b['strategie'] = 'B_top_30pct'
            append_to_csv(df_b, "historique_strategy_B.csv")
            print(f"✅ {len(df_b)} bets stratégie B sauvés")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

def append_to_csv(df, filename):
    """Ajoute les données au CSV existant"""
    if os.path.exists(filename):
        existing = pd.read_csv(filename)
        combined = pd.concat([existing, df], ignore_index=True)
        # Supprime doublons (même match + même date)
        combined = combined.drop_duplicates(subset=['date', 'player1', 'player2'], keep='first')
        combined.to_csv(filename, index=False)
    else:
        df.to_csv(filename, index=False)

if __name__ == "__main__":
    save_daily_bets()
