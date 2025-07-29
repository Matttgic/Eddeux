# migrate_csv.py
import pandas as pd
import os

def migrate_strategy_files():
    """Migre start_time vers starts et nettoie les fichiers historiques"""
    
    files_to_migrate = [
        "historique_strategy_A.csv",
        "historique_strategy_B.csv"
    ]
    
    for filename in files_to_migrate:
        if not os.path.exists(filename):
            print(f"⚠️ Fichier {filename} non trouvé")
            continue
            
        try:
            # Charger le CSV
            df = pd.read_csv(filename)
            print(f"\n📂 {filename}")
            print(f"   Avant: {len(df)} lignes, colonnes: {list(df.columns)}")
            
            # Vérifier les colonnes
            has_start_time = 'start_time' in df.columns
            has_starts = 'starts' in df.columns
            
            if has_start_time and has_starts:
                print("   🔄 Migration start_time → starts")
                
                # Compter les valeurs avant migration
                starts_empty = df['starts'].isna().sum()
                start_time_filled = df['start_time'].notna().sum()
                
                print(f"   📊 starts vides: {starts_empty}, start_time remplis: {start_time_filled}")
                
                # Migrer: utiliser start_time quand starts est vide
                df['starts'] = df['starts'].fillna(df['start_time'])
                
                # Supprimer start_time
                df = df.drop('start_time', axis=1)
                
                print("   ✅ Migration terminée - colonne start_time supprimée")
                
            elif has_start_time and not has_starts:
                print("   🔄 Renommage start_time → starts")
                df = df.rename(columns={'start_time': 'starts'})
                print("   ✅ Colonne start_time renommée en starts")
                
            elif has_starts and not has_start_time:
                print("   ℹ️ Déjà bon - seulement colonne starts")
                
            else:
                print("   ⚠️ Aucune colonne de date trouvée")
                continue
            
            # Vérifier le résultat
            starts_filled = df['starts'].notna().sum()
            print(f"   📊 Résultat: {starts_filled} dates dans colonne starts")
            print(f"   📊 Nouvelles colonnes: {list(df.columns)}")
            
            # Sauvegarder
            df.to_csv(filename, index=False)
            print(f"   💾 {filename} sauvegardé")
                
        except Exception as e:
            print(f"❌ Erreur avec {filename}: {e}")
    
    print("\n🎯 Migration terminée ! Filtrage 11h-11h opérationnel sur tout l'historique.")

if __name__ == "__main__":
    migrate_strategy_files()
