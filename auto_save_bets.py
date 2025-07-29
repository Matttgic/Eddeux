# auto_save_bets.py
import pandas as pd
from datetime import datetime, timezone, timedelta
from value_bets import compute_value_bets
import os

def get_current_capital(strategy):
    """Récupère le capital actuel depuis le dernier résultat"""
    filename = f"historique_strategy_{strategy}.csv"
    try:
        df = pd.read_csv(filename)
        if not df.empty:
            for i in range(len(df)-1, -1, -1):
                if pd.notna(df.iloc[i]['capital']) and df.iloc[i]['capital'] != '':
                    return float(df.iloc[i]['capital'])
    except:
        pass
    return 200

def calculate_kelly_bet(prob_elo, odds, capital, kelly_fraction=0.25, max_percent=0.20):
    """Calcule la mise Kelly avec plafond"""
    p = prob_elo / 100
    b = odds - 1
    q = 1 - p
    
    kelly_percent = (p * b - q) / b
    kelly_percent = max(0, kelly_percent)
    
    kelly_bet = capital * kelly_percent * kelly_fraction
    max_bet = capital * max_percent
    
    return min(kelly_bet, max_bet)

def is_today_match(start_time_str):
    """Vérifie si le match est aujourd'hui avant 11h heure française"""
    try:
        # Parse la date du match
        match_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        
        # Convertir en heure française (UTC+1 ou UTC+2)
        france_tz = timezone(timedelta(hours=2))  # UTC+2 en été
        match_time_france = match_time.astimezone(france_tz)
        
        # Date actuelle en France
        now_france = datetime.now(france_tz)
        today_france = now_france.date()
        
        # Le match est "d'aujourd'hui" s'il commence:
        # - Aujourd'hui avant 11h
        # - Ou demain (car on lance le script à 11h pour les matchs du soir)
        match_date = match_time_france.date()
        
        if match_date == today_france:
            return True
        elif match_date == today_france + timedelta(days=1):
            return True
        else:
            return False
            
    except:
        return True  # En cas d'erreur, on garde le match

def save_daily_bets():
    """Sauvegarde automatique des value bets quotidiens"""
    
    SEUIL_A = 0.05
    TOP_PERCENT_B = 30
    
    try:
        df_all = compute_value_bets("elo_probs.csv", 0.0)
        
        if df_all.empty:
            print("❌ Aucun match trouvé")
            return
        
        # Filtrer les matchs d'aujourd'hui/demain seulement
        if 'starts' in df_all.columns:
            df_all['is_today'] = df_all['starts'].apply(is_today_match)
            df_filtered = df_all[df_all['is_today']].copy()
            df_filtered = df_filtered.drop('is_today', axis=1)
        else:
            df_filtered = df_all.copy()  # Prend tous les matchs si pas de colonne starts
            print("⚠️ Pas de colonne 'starts', prend tous les matchs")
        
        if df_filtered.empty:
            print("❌ Aucun match aujourd'hui/demain")
            return
            
        date_str = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 Sauvegarde pour le {date_str}")
        
        # Stratégie A
        current_capital_a = get_current_capital("A")
        print(f"💰 Capital actuel Stratégie A: {current_capital_a:.2f}€")
        
        df_a = df_filtered[df_filtered['value'] >= SEUIL_A * 100].copy()
        if not df_a.empty:
            df_a['date'] = date_str
            df_a['strategie'] = 'A_seuil_5pct'
            
            df_a['mise_kelly'] = df_a.apply(
                lambda row: round(calculate_kelly_bet(
                    row['prob_elo'], 
                    row['cote_pinnacle'], 
                    current_capital_a
                ), 2), axis=1
            )
            
            df_a['resultat'] = ''
            df_a['profit'] = ''
            df_a['capital'] = ''
            
            append_to_csv(df_a, "historique_strategy_A.csv")
            print(f"✅ {len(df_a)} bets stratégie A sauvés")
        
        # Stratégie B
        current_capital_b = get_current_capital("B")
        print(f"💰 Capital actuel Stratégie B: {current_capital_b:.2f}€")
        
        df_sorted = df_filtered.sort_values('value', ascending=False)
        nb_top = max(1, int(len(df_sorted) * TOP_PERCENT_B / 100))
        df_b = df_sorted.head(nb_top).copy()
        if not df_b.empty:
            df_b['date'] = date_str
            df_b['strategie'] = 'B_top_30pct'
            
            df_b['mise_kelly'] = df_b.apply(
                lambda row: round(calculate_kelly_bet(
                    row['prob_elo'], 
                    row['cote_pinnacle'], 
                    current_capital_b
                ), 2), axis=1
            )
            
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
        combined = combined.drop_duplicates(subset=['date', 'player1', 'player2'], keep='first')
        combined.to_csv(filename, index=False)
    else:
        df.to_csv(filename, index=False)

if __name__ == "__main__":
    save_daily_bets()
