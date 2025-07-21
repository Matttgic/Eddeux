# app.py

import streamlit as st
from value_bets import compute_value_bets
import pandas as pd
from datetime import datetime
import os
import requests

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

# 📅 Sidebar
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

# Vérification fichier Elo
elo_file = "elo_probs.csv"
if not os.path.exists(elo_file):
    st.error(f"❌ Fichier {elo_file} introuvable. Lancez d'abord 'python prepare_elo_csv.py'")
    st.stop()

# 📊 Onglets stratégies
tab1, tab2 = st.tabs(["🎯 Stratégie A: Seuil fixe", "🏆 Stratégie B: Top %"])

with tab1:
    st.header("🔹 Stratégie A : Seuil fixe (value > X%)")
    st.info("On joue **tous les bets** avec une value supérieure à un seuil donné")
    
    seuil = st.slider(
        "🔧 Seuil minimum de value (%)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.1,
        help="Affiche les matchs dont la value est supérieure à ce pourcentage"
    ) / 100

    with st.spinner("Calcul des value bets en cours..."):
        try:
            df = compute_value_bets(elo_file, min_value_threshold=seuil)
        except Exception as e:
            st.error(f"❌ Erreur lors du calcul : {e}")
            df = pd.DataFrame()

    if df.empty:
        st.warning(f"Aucun value bet détecté avec un seuil de {seuil*100:.1f}%.")
        
        # Mode debug
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

        # CSV export
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📅 Télécharger les bets en CSV",
            data=csv,
            file_name=f"value_bets_seuil_{datetime.now().date()}.csv",
            mime="text/csv"
        )

with tab2:
    st.header("🔹 Stratégie B : Top X% des meilleurs value bets")
    st.info("On trie tous les matchs par value décroissante et garde les meilleurs X%")
    
    pourcentage = st.slider(
        "📊 Pourcentage des meilleurs bets à garder",
        min_value=1,
        max_value=50,
        value=10,
        step=1,
        help="Garde seulement les X% meilleurs value bets"
    )

    with st.spinner("Calcul des top value bets..."):
        try:
            df_all = compute_value_bets(elo_file, min_value_threshold=0.0)
        except Exception as e:
            st.error(f"❌ Erreur lors du calcul : {e}")
            df_all = pd.DataFrame()

    if df_all.empty:
        st.warning("Aucun match analysé.")
    else:
        # Tri par value décroissante
        df_sorted = df_all.sort_values(by="value", ascending=False)
        
        # Calcul du nombre de matchs à garder
        nb_total = len(df_sorted)
        nb_a_garder = max(1, int(nb_total * pourcentage / 100))
        
        # Sélection des top X%
        df_top = df_sorted.head(nb_a_garder)
        
        st.success(f"Top {pourcentage}% : {nb_a_garder} matchs sur {nb_total} total")
        
        # Métriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Value moyenne", f"{df_top['value'].mean():.1f}%")
        with col2:
            st.metric("Value minimale", f"{df_top['value'].min():.1f}%")
        with col3:
            st.metric("Value maximale", f"{df_top['value'].max():.1f}%")
        
        st.dataframe(df_top, use_container_width=True)

        # CSV export
        csv_top = df_top.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📊 Télécharger Top {pourcentage}% en CSV",
            data=csv_top,
            file_name=f"top_{pourcentage}pct_bets_{datetime.now().date()}.csv",
            mime="text/csv"
        )

# 📈 Tableau des ROI théoriques
st.header("📈 ROI Théoriques des Stratégies")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 Stratégie A : Seuil fixe")
    roi_data_a = {
        "Seuil": [">0%", ">1%", ">2%", ">3%", ">4%", ">5%", ">6%", ">7%", ">8%", ">9%", ">10%"],
        "Nb Bets": [4298, 3823, 3262, 2732, 2223, 1742, 1364, 1062, 828, 659, 510],
        "ROI": ["9.8%", "11.2%", "13.1%", "15.6%", "18.6%", "21.6%", "24.7%", "27.6%", "29.9%", "31.9%", "33.9%"]
    }
    st.dataframe(pd.DataFrame(roi_data_a), use_container_width=True)

with col2:
    st.subheader("🏆 Stratégie B : Top X%")
    roi_data_b = {
        "Top": ["5%", "10%", "20%"],
        "ROI": ["~70%", "~50%", "~35%"]
    }
    st.dataframe(pd.DataFrame(roi_data_b), use_container_width=True)
