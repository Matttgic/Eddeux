# app.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from value_bets import compute_value_bets

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

elo_file = "elo_probs.csv"
log_file = "historique_value_bets.csv"

# 📅 Sidebar : bouton de mise à jour manuelle du fichier 2025.xlsx
st.sidebar.header("📅 Données")
def update_2025_file():
    import requests
    url = "http://www.tennis-data.co.uk/2025/2025.xlsx"
    dest_folder = "Données"
    dest_file = os.path.join(dest_folder, "2025.xlsx")
    os.makedirs(dest_folder, exist_ok=True)
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(dest_file, "wb") as f:
            f.write(response.content)
        return True, "✅ Fichier 2025.xlsx mis à jour avec succès."
    except Exception as e:
        return False, f"❌ Erreur : {e}"

if st.sidebar.button("🔄 Mettre à jour 2025.xlsx"):
    success, msg = update_2025_file()
    st.sidebar.success(msg) if success else st.sidebar.error(msg)

# 🔀 Tabs pour les deux stratégies
tab1, tab2 = st.tabs(["📊 Méthode A – Seuil fixe", "📈 Méthode B – Top % value bets"])

with tab1:
    seuil = st.slider("🔧 Seuil minimum de value (%)", 0.0, 10.0, 5.0, 0.1) / 100
    df = compute_value_bets(elo_file, min_value_threshold=seuil)

    if df.empty:
        st.warning("Aucun value bet détecté avec ce seuil.")
        st.subheader("🔍 Mode debug : tous les matchs analysés")
        df_debug = compute_value_bets(elo_file, min_value_threshold=0.0)
        if not df_debug.empty:
            st.dataframe(df_debug, use_container_width=True)
    else:
        st.success(f"{len(df)} value bet(s) détecté(s)")
        st.dataframe(df, use_container_width=True)

        # ROI global
        df["ROI"] = df["cote_pinnacle"] * df["prob_elo"]/100 - 1
        roi_moyen = df["ROI"].mean() * 100
        st.markdown(f"📈 **ROI moyen** : `{roi_moyen:.2f}%`")

        # ROI par tranches
        st.markdown("📊 **ROI par tranches de value** :")
        tranches = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stats = []
        for v in tranches:
            bets = df[df["value"] >= v]
            if not bets.empty:
                roi = bets["ROI"].mean() * 100
                stats.append((f"> {v}%", len(bets), f"{roi:.1f}%"))
        st.table(pd.DataFrame(stats, columns=["Seuil", "Bets", "ROI"]))

        # Log historique
        df_log = df.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        # Télécharger CSV
        st.download_button(
            "📥 Télécharger les bets (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"value_bets_seuil_{datetime.now().date()}.csv"
        )

with tab2:
    percent = st.slider("🎯 Top % des meilleurs bets", 1, 100, 10)
    df_all = compute_value_bets(elo_file, min_value_threshold=0.0)

    if df_all.empty:
        st.warning("Aucun match analysé.")
    else:
        df_sorted = df_all.sort_values(by="value", ascending=False)
        cutoff = int(len(df_sorted) * percent / 100)
        df_top = df_sorted.head(cutoff)

        st.success(f"{cutoff} meilleurs bets affichés (Top {percent}%)")
        st.dataframe(df_top, use_container_width=True)

        # ROI
        df_top["ROI"] = df_top["cote_pinnacle"] * df_top["prob_elo"]/100 - 1
        roi_top = df_top["ROI"].mean() * 100
        st.markdown(f"📈 **ROI moyen (Top {percent}%)** : `{roi_top:.2f}%`")

        # Log historique
        df_top["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_top.to_csv(log_file, index=False)
        else:
            df_top.to_csv(log_file, mode="a", header=False, index=False)

        st.download_button(
            "📥 Télécharger les bets (CSV)",
            data=df_top.to_csv(index=False).encode("utf-8"),
            file_name=f"value_bets_top{percent}_{datetime.now().date()}.csv"
        )

# 🕘 Historique
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
