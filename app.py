# app.py

import streamlit as st
from value_bets import compute_value_bets
import pandas as pd
from datetime import datetime
import os
import requests

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

# 📅 Sidebar : bouton de mise à jour manuelle du fichier 2025.xlsx
st.sidebar.header("📅 Données")

def update_2025_file():
    url = "http://www.tennis-data.co.uk/2025/2025.xlsx"
    dest_folder = "Données"
    dest_file = os.path.join(dest_folder, "2025.xlsx")
    os.makedirs(dest_folder, exist_ok=True)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(dest_file, "wb") as f:
            f.write(response.content)
        return True, "✅ Fichier 2025.xlsx mis à jour avec succès."
    except Exception as e:
        return False, f"❌ Erreur : {e}"

if st.sidebar.button("🔄 Mettre à jour le fichier 2025.xlsx"):
    success, msg = update_2025_file()
    if success:
        st.sidebar.success(msg)
    else:
        st.sidebar.error(msg)

# 📊 Slider pour seuil de value bet (%)
seuil = st.slider(
    "🔧 Seuil minimum de value (%)",
    min_value=0.0,
    max_value=10.0,
    value=5.0,
    step=0.1,
    help="Affiche les matchs dont la value est supérieure à ce pourcentage"
) / 100

# Chargement des Elo
elo_file = "elo_probs.csv"

# Vérification de l'existence du fichier Elo
if not os.path.exists(elo_file):
    st.error(f"❌ Fichier {elo_file} introuvable. Lancez d'abord 'python prepare_elo_csv.py'")
    st.stop()

with st.spinner("Calcul des value bets en cours..."):
    try:
        df = compute_value_bets(elo_file, min_value_threshold=seuil)
    except Exception as e:
        st.error(f"❌ Erreur lors du calcul : {e}")
        df = pd.DataFrame()

if df.empty:
    st.warning(f"Aucun value bet détecté avec un seuil de {seuil*100:.1f}%.")

    # Mode debug : tout afficher si aucun bet filtré
    st.subheader("🔍 Mode debug : analyse sans seuil")
    try:
        df_debug = compute_value_bets(elo_file, min_value_threshold=0.0)
        if not df_debug.empty:
            df_debug = df_debug.sort_values(by="value", ascending=False)
            st.dataframe(df_debug, use_container_width=True)
        else:
            st.info("Aucun match n'a pu être analysé (API vide ou noms non matchés).")
    except Exception as e:
        st.error(f"❌ Erreur mode debug : {e}")
else:
    st.success(f"{len(df)} value bet(s) détecté(s) avec un seuil de {seuil*100:.1f}% :")
    df = df.sort_values(by="value", ascending=False)
    st.dataframe(df, use_container_width=True)

    # Bouton de téléchargement CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📅 Télécharger les bets en CSV",
        data=csv,
        file_name=f"value_bets_{datetime.now().date()}.csv",
        mime="text/csv"
    )
