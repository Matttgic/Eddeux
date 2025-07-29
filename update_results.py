# update_results.py
import pandas as pd

def calculate_profits_and_capital(filename, capital_initial=200):
    """Calcule automatiquement profit et capital basé sur les résultats"""
    
    try:
        df = pd.read_csv(filename)
        
        capital_current = capital_initial
        
        for i, row in df.iterrows():
            if row['resultat'] in ['G', 'P', 'A'] and (pd.isna(row['profit']) or row['profit'] == ''):
                mise = row['mise_kelly']
                cote = row['cote_pinnacle']
                
                if row['resultat'] == 'G':
                    # Gain = mise * (cote - 1)
                    profit = round(mise * (cote - 1), 2)
                    capital_current += profit
                elif row['resultat'] == 'P':
                    # Perte = -mise
                    profit = -mise
                    capital_current += profit
                elif row['resultat'] == 'A':
                    # Annulé = 0
                    profit = 0
                
                # Met à jour les colonnes
                df.at[i, 'profit'] = profit
                df.at[i, 'capital'] = round(capital_current, 2)
        
        # Sauvegarde
        df.to_csv(filename, index=False)
        
        # Calcule résumé
        df_with_results = df[df['resultat'].isin(['G', 'P', 'A'])]
        if not df_with_results.empty:
            total_profit = df_with_results['profit'].sum()
            nb_gagne = len(df[df['resultat'] == 'G'])
            nb_perdu = len(df[df['resultat'] == 'P'])
            nb_annule = len(df[df['resultat'] == 'A'])
            
            strategy_name = "A" if "strategy_A" in filename else "B"
            print(f"✅ Stratégie {strategy_name}: {nb_gagne}G/{nb_perdu}P/{nb_annule}A | Profit: {total_profit:.2f}€ | Capital: {capital_current:.2f}€")
        
        return capital_current
        
    except FileNotFoundError:
        print(f"❌ Fichier {filename} non trouvé")
        return capital_initial
    except Exception as e:
        print(f"❌ Erreur {filename}: {e}")
        return capital_initial

def update_both_strategies():
    """Met à jour les deux stratégies"""
    print("🔄 Mise à jour des calculs automatiques...")
    
    # Stratégie A
    capital_a = calculate_profits_and_capital("historique_strategy_A.csv", 200)
    
    # Stratégie B
    capital_b = calculate_profits_and_capital("historique_strategy_B.csv", 200)
    
    print(f"\n📈 Capital final - Stratégie A: {capital_a:.2f}€ | Stratégie B: {capital_b:.2f}€")

if __name__ == "__main__":
    update_both_strategies()
