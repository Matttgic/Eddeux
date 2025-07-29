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

def is_match_for_today_session(start_time_str):
    """Filtre les matchs pour la session du jour (11h aujourd'hui -> 11h demain)"""
    try:
        if not start_time_str or pd.isna(start_time_str):
            return True  # Garde si pas d'info de temps
            
        # Parse la date du match
        match_time = datetime.fromisoformat(str(start_time_str).replace('Z', '+00:00'))
        
        # Heure française (UTC+2 en été)
        france_tz = timezone(timedelta(hours=2))
        match_time_france = match_time.astimezone(france_tz)
        now_france = datetime.now(france_tz)
        
        # Session = 11h aujourd'hui -> 11h demain
        session_start = now_france.replace(hour=11, minute=0, second=0, microsecond=0)
        session_end = session_start + timedelta(days=1)
        
        # Si on est avant 11h aujourd'hui, on prend la session d'hier 11h -> aujourd'hui 11h
        if now_france.hour < 11:
            session_start = session_start - timedelta(days=1)
            session_end = session_end - timedelta(days=1)
        
        # Le match est dans la session s'il commence entre session_start et session_end
        return session_start <= match_time_france <= session_end
        
    except:
        return True  # En cas d'erreur, garde le match

def sort_csv_by_date(filename):
    """Trie automatiquement le CSV par date après ajout"""
    try:
        df = pd.read_csv(filename)
        
        if 'starts' in df.columns and len(df) > 1:
            # Convertir starts en datetime pour tri
            df['starts_temp'] = df['starts'].fillna('1900-01-01T00:00:00')
            df['starts_temp'] = pd.to_datetime(df['starts_temp'])
            
            # Trier par date
            df_sorted = df.sort_values('starts_temp')
            df_sorted = df_sorted.drop('starts_temp', axis=1)
            
            # Sauvegarder trié
            df_sorted.to_csv(filename, index=False)
            print(f"📅 {filename} trié par date automatiquement")
    except Exception as e:
        print(f"⚠️ Erreur tri {filename}: {e}")

def save_daily_bets():
    """Sauvegarde automatique des value bets quotidiens"""
    
    SEUIL_A = 0.05
    TOP_PERCENT_B = 30
    
    try:
        df_all = compute_value_bets("elo_probs.csv", 0.0)
        
        if df_all.empty:
            print("❌ Aucun match trouvé")
            return
        
        # Filtrer les matchs pour la session 11h-11h
        if 'starts' in df_all.columns:
            df_all['is_session'] = df_all['starts'].apply(is_match_for_today_session)
            df_filtered = df_all[df_all['is_session']].copy()
            df_filtered = df_filtered.drop('is_session', axis=1)
            print(f"📅 Matchs filtrés pour session 11h-11h: {len(df_filtered)}/{len(df_all)}")
        else:
            df_filtered = df_all.copy()  # Prend tous les matchs si pas de colonne starts
            print("⚠️ Pas de colonne 'starts', prend tous les matchs")
        
        if df_filtered.empty:
            print("❌ Aucun match dans la session 11h-11h")
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
    """Ajoute les données au CSV existant et trie par date"""
    if os.path.exists(filename):
        existing = pd.read_csv(filename)
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date', 'player1', 'player2'], keep='first')
        combined.to_csv(filename, index=False)
    else:
        df.to_csv(filename, index=False)
    
    # ✅ TRI AUTOMATIQUE après chaque sauvegarde
    sort_csv_by_date(filename)

if __name__ == "__main__":
    save_daily_bets()
