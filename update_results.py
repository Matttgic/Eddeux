# update_results.py
import pandas as pd

def calculate_profits_and_capital():
    """Calcule automatiquement profit et capital basé sur les résultats"""
    
    try:
        df = pd.read_csv("historique_strategy_A.csv")
        
        capital_current = 200  # Capital initial
        
        for i, row in df.iterrows():
            if row['resultat'] in ['G', 'P'] and pd.isna(row['profit']):
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
                
                # Met à jour les colonnes
                df.at[i, 'profit'] = profit
                df.at[i, 'capital'] = round(capital_current, 2)
        
        # Sauvegarde
        df.to_csv("historique_strategy_A.csv", index=False)
        print("✅ Calculs automatisés mis à jour")
        
        # Affiche le résumé
        total_profit = df[df['resultat'].isin(['G', 'P'])]['profit'].sum()
        nb_gagne = len(df[df['resultat'] == 'G'])
        nb_perdu = len(df[df['resultat'] == 'P'])
        
        print(f"📊 Résumé: {nb_gagne}G/{nb_perdu}P | Profit total: {total_profit:.2f}€ | Capital: {capital_current:.2f}€")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    calculate_profits_and_capital()
