# verify_and_fix.py
import pandas as pd
import os

def force_migration():
    """Force la migration avec vérifications supplémentaires"""
    
    files = ["historique_strategy_A.csv", "historique_strategy_B.csv"]
    
    for filename in files:
        print(f"\n🔍 Vérification {filename}")
        
        if not os.path.exists(filename):
            print(f"❌ Fichier non trouvé")
            continue
            
        # Charger et analyser
        df = pd.read_csv(filename)
        print(f"📊 Colonnes actuelles: {list(df.columns)}")
        
        if 'start_time' in df.columns and 'starts' in df.columns:
            print("🔧 Colonnes en double détectées - migration forcée")
            
            # Sauvegarder backup
            backup_name = f"{filename}.backup"
            df.to_csv(backup_name, index=False)
            print(f"💾 Backup créé: {backup_name}")
            
            # Migration
            df['starts'] = df['starts'].fillna(df['start_time'])
            df = df.drop('start_time', axis=1)
            
            # Force sauvegarde
            try:
                df.to_csv(filename, index=False)
                print(f"✅ {filename} sauvegardé avec succès")
                
                # Vérification
                df_check = pd.read_csv(filename)
                print(f"✅ Vérification: {list(df_check.columns)}")
                
            except Exception as e:
                print(f"❌ Erreur sauvegarde: {e}")
        else:
            print("ℹ️ Pas de migration nécessaire")

if __name__ == "__main__":
    force_migration()
