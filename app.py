import streamlit as st
import pandas as pd
import os
from datetime import datetime
from value_bets import compute_value_bets

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

# Fichier de log historique
log_file = "historique_value_bets.csv"
elo_file = "elo_probs.csv"

# Tabs pour les 2 méthodes
tab1, tab2 = st.tabs(["📊 Méthode A - Seuil fixe", "📈 Méthode B - Top %"])

with tab1:
    seuil = st.slider("🔧 Seuil minimum de value (%)", 0.0, 10.0, 5.0, 0.1) / 100
    df = compute_value_bets(elo_file, min_value_threshold=seuil)

    if df.empty:
        st.warning("Aucun value bet détecté avec ce seuil.")
    else:
        st.success(f"{len(df)} value bet(s) détecté(s) avec un seuil de {seuil*100:.1f}%")
        st.dataframe(df, use_container_width=True)

        # Log automatique
        df_log = df.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        # Téléchargement
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger les bets (CSV)", csv, file_name=f"value_bets_{datetime.now().date()}.csv")

with tab2:
    percent = st.slider("🎯 Top % des meilleurs bets", 1, 100, 10)
    df_all = compute_value_bets(elo_file, min_value_threshold=0.0)

    if df_all.empty:
        st.warning("Aucun match analysé.")
    else:
        df_sorted = df_all.sort_values(by="value", ascending=False)
        cutoff = int(len(df_sorted) * percent / 100)
        df_top = df_sorted.iloc[:cutoff]
        st.success(f"{cutoff} meilleurs bets affichés (Top {percent}%)")
        st.dataframe(df_top, use_container_width=True)

        # Log automatique
        df_log = df_top.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        # Téléchargement
        csv = df_top.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger les bets (CSV)", csv, file_name=f"value_bets_top{percent}_{datetime.now().date()}.csv")

# Sidebar : historique
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Historique des Value Bets")
if os.path.exists(log_file):
    if st.sidebar.button("📂 Voir l'historique complet"):
        df_hist = pd.read_csv(log_file)
        st.subheader("📜 Historique complet")
        st.dataframe(df_hist, use_container_width=True)

    with open(log_file, "rb") as f:
        st.sidebar.download_button("📥 Télécharger l'historique", f, file_name="historique_value_bets.csv")
else:
    st.sidebar.info("Aucun historique encore disponible.")
