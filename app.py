import streamlit as st
import pandas as pd
import os
from datetime import datetime
from value_bets import compute_value_bets

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

# Fichier Elo et log
elo_file = "elo_probs.csv"
log_file = "historique_value_bets.csv"

# Tabs pour les deux stratégies
tab1, tab2 = st.tabs(["📊 Stratégie A - Seuil fixe", "📈 Stratégie B - Top %"])

with tab1:
    seuil = st.slider("🔧 Seuil minimum de value (%)", 0.0, 10.0, 5.0, 0.1) / 100
    df = compute_value_bets(elo_file, min_value_threshold=seuil)

    if df.empty:
        st.warning("Aucun value bet détecté avec ce seuil.")
        st.subheader("🔍 Mode debug : tous les matchs analysés")
        df_debug = compute_value_bets(elo_file, min_value_threshold=0.0)
        if not df_debug.empty:
            df_debug = df_debug.sort_values(by="value", ascending=False)
            st.dataframe(df_debug, use_container_width=True)
        else:
            st.info("Aucun match analysé (problème API ?)")
    else:
        st.success(f"{len(df)} value bet(s) détecté(s) avec un seuil de {seuil*100:.1f}%")
        st.dataframe(df, use_container_width=True)

        # ROI global et par tranches
        df['roi'] = (df['cote_pinnacle'] * (df['prob_elo'] / 100)) - 1
        roi_total = df['roi'].mean() * 100
        st.metric("📈 ROI moyen global", f"{roi_total:.2f}%")

        # ROI par tranches
        df['tranche'] = pd.cut(df['value'], bins=[0,2,4,6,8,10,100], labels=["0-2%","2-4%","4-6%","6-8%","8-10%",">10%"])
        grouped = df.groupby("tranche")["roi"].mean().multiply(100).reset_index()
        st.dataframe(grouped.rename(columns={"roi": "ROI moyen (%)"}), use_container_width=True)

        # Log historique
        df_log = df.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger les bets (CSV)", csv, file_name=f"value_bets_{datetime.now().date()}.csv")

with tab2:
    top_percent = st.slider("🎯 Top % des meilleurs bets", 1, 100, 10)
    df_all = compute_value_bets(elo_file, min_value_threshold=0.0)

    if df_all.empty:
        st.warning("Aucun match analysé.")
    else:
        df_all = df_all.sort_values(by="value", ascending=False)
        cutoff = max(1, int(len(df_all) * top_percent / 100))
        df_top = df_all.head(cutoff)

        st.success(f"{cutoff} bets sélectionnés (Top {top_percent}%)")
        st.dataframe(df_top, use_container_width=True)

        df_top['roi'] = (df_top['cote_pinnacle'] * (df_top['prob_elo'] / 100)) - 1
        roi_total = df_top['roi'].mean() * 100
        st.metric("📈 ROI moyen Top %", f"{roi_total:.2f}%")

        # ROI par tranches
        df_top['tranche'] = pd.cut(df_top['value'], bins=[0,2,4,6,8,10,100], labels=["0-2%","2-4%","4-6%","6-8%","8-10%",">10%"])
        grouped = df_top.groupby("tranche")["roi"].mean().multiply(100).reset_index()
        st.dataframe(grouped.rename(columns={"roi": "ROI moyen (%)"}), use_container_width=True)

        df_log = df_top.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        csv = df_top.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger les bets (CSV)", csv, file_name=f"top_{top_percent}_value_bets_{datetime.now().date()}.csv")

# Historique en sidebar
st.sidebar.header("📜 Historique des Value Bets")
if os.path.exists(log_file):
    if st.sidebar.button("📂 Voir l'historique complet"):
        df_hist = pd.read_csv(log_file)
        st.subheader("📜 Historique complet")
        st.dataframe(df_hist, use_container_width=True)
    with open(log_file, "rb") as f:
        st.sidebar.download_button("📥 Télécharger l'historique", f, file_name="historique_value_bets.csv")
else:
    st.sidebar.info("Aucun historique disponible.")
