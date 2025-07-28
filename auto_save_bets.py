# auto_save_bets.py
import pandas as pd
from datetime import datetime
from value_bets import compute_value_bets
import os

def calculate_kelly_bet(prob_elo, odds, capital=200, kelly_fraction=0.25, max_percent=0.20):
    """Calcule la mise Kelly avec plafond"""
    # Kelly = (p*b - q) / b où p=prob, b=gain_net, q=1-p
    p = prob_elo / 100  # Convertir en décimal
    b = odds - 1  # Gain net
    q = 1 - p
    
    kelly_percent = (p * b - q) / b
    kelly_percent = max(0, kelly_percent)  # Pas de mise négative
    
    # Appliquer fraction Kelly (25%)
    kelly_bet = capital * kelly_percent * kelly_fraction
    
    # Plafond à 20% du capital
    max_bet = capital * max_percent
    
    return min(kelly_bet, max_bet)

def save_daily_bets():
    """Sauvegarde automatique des value bets quotidiens"""
    
    # Paramètres configurables
    SEUIL_A = 0.05  # 5% pour stratégie A
    TOP_PERCENT_B = 30  # Top 30% pour stratégie B
    CAPITAL_BASE = 200  # €
    
    try:
        # Récupère tous les matchs
        df_all = compute_value_bets("elo_probs.csv", 0.0)
        
        if df_all.empty:
            print("❌ Aucun match trouvé")
            return
            
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Stratégie A - Seuil fixe
        df_a = df_all[df_all['value'] >= SEUIL_A * 100].copy()
        if not df_a.empty:
            df_a['date'] = date_str
            df_a['strategie'] = 'A_seuil_5pct'
            
            # Calcul mise Kelly
            df_a['mise_kelly'] = df_a.apply(
                lambda row: round(calculate_kelly_bet(
                    row['prob_elo'], 
                    row['cote_pinnacle'], 
                    CAPITAL_BASE
                ), 2), axis=1
            )
            
            # Colonnes résultat à remplir manuellement
            df_a['resultat'] = ''  # 'G' ou 'P' à remplir
            df_a['profit'] = ''    # À calculer après résultat
            df_a['capital'] = ''   # Capital mis à jour
            
            append_to_csv(df_a, "historique_strategy_A.csv")
            print(f"✅ {len(df_a)} bets stratégie A sauvés")
        
        # Stratégie B - Top %
        df_sorted = df_all.sort_values('value', ascending=False)
        nb_top = max(1, int(len(df_sorted) * TOP_PERCENT_B / 100))
        df_b = df_sorted.head(nb_top).copy()
        if not df_b.empty:
            df_b['date'] = date_str
            df_b['strategie'] = 'B_top_30pct'
            
            # Calcul mise Kelly
            df_b['mise_kelly'] = df_b.apply(
                lambda row: round(calculate_kelly_bet(
                    row['prob_elo'], 
                    row['cote_pinnacle'], 
                    CAPITAL_BASE
                ), 2), axis=1
            )
            
            # Colonnes résultat à remplir manuellement
            df_b['resultat'] = ''
            df_b['profit'] = ''
            df_b['capital'] = ''
            
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
