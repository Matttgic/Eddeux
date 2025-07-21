import streamlit as st
from value_bets import compute_value_bets
import pandas as pd
from datetime import datetime
import os
import requests

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

log_file = "historique_value_bets.csv"
elo_file = "elo_probs.csv"

# 📅 Sidebar : bouton de mise à jour manuelle
st.sidebar.header("📅 Données")

def update_2025_file():
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

if st.sidebar.button("🔄 Mettre à jour le fichier 2025.xlsx"):
    success, msg = update_2025_file()
    if success:
        st.sidebar.success(msg)
    else:
        st.sidebar.error(msg)

# 📂 Tabs pour les deux stratégies
tab1, tab2 = st.tabs(["📊 Méthode A - Seuil fixe", "📈 Méthode B - Top %"])

# -------------------------------
# 🟦 MÉTHODE A : Seuil de value
# -------------------------------
with tab1:
    seuil = st.slider(
        "🔧 Seuil minimum de value (%)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.1,
        help="Affiche les matchs dont la value est supérieure à ce pourcentage"
    ) / 100

    with st.spinner("Calcul des value bets en cours..."):
        df = compute_value_bets(elo_file, min_value_threshold=seuil)

    if df.empty:
        st.warning("Aucun value bet détecté avec ce seuil.")
        st.subheader("🔍 Mode debug : analyse sans seuil")
        df_debug = compute_value_bets(elo_file, min_value_threshold=0.0)
        if not df_debug.empty:
            st.dataframe(df_debug.sort_values(by="value", ascending=False), use_container_width=True)
        else:
            st.info("Aucun match analysé.")
    else:
        st.success(f"{len(df)} value bet(s) détecté(s) avec un seuil de {seuil*100:.1f}% :")
        df = df.sort_values(by="value", ascending=False)
        st.dataframe(df, use_container_width=True)

        # Logging
        df_log = df.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        # Téléchargement CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger les bets (CSV)", csv, file_name=f"value_bets_{datetime.now().date()}.csv")

# -------------------------------
# 🟩 MÉTHODE B : Top X%
# -------------------------------
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

        # Logging
        df_log = df_top.copy()
        df_log["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df_log.to_csv(log_file, index=False)
        else:
            df_log.to_csv(log_file, mode="a", header=False, index=False)

        # Téléchargement CSV
        csv = df_top.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger les bets (CSV)", csv, file_name=f"value_bets_top{percent}_{datetime.now().date()}.csv")

# -------------------------------
# 📜 Historique dans la sidebar
# -------------------------------
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
