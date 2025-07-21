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

st.sidebar.markdown("---")
st.sidebar.subheader("📜 Historique des Value Bets")
log_file = "historique_value_bets.csv"
if os.path.exists(log_file):
    if st.sidebar.button("📂 Voir l'historique complet"):
        df_hist = pd.read_csv(log_file)
        st.subheader("📜 Historique complet")
        st.dataframe(df_hist, use_container_width=True)

    with open(log_file, "rb") as f:
        st.sidebar.download_button(
            label="📥 Télécharger l'historique",
            data=f,
            file_name="historique_value_bets.csv",
            mime="text/csv"
        )
else:
    st.sidebar.info("Aucun historique encore généré.")

# Tabs : deux approches
onglet_a, onglet_b = st.tabs([
    "📈 Méthode A : Value > Seuil",
    "🏆 Méthode B : Top % Value Bets"
])

with onglet_a:
    seuil = st.slider("🔧 Seuil minimum de value (%)", 0.0, 10.0, 5.0, 0.1) / 100
    with st.spinner("Calcul des value bets en cours..."):
        df = compute_value_bets("elo_probs.csv", min_value_threshold=seuil)

    if df.empty:
        st.warning(f"Aucun value bet détecté avec un seuil de {seuil*100:.1f}%.")
        st.subheader("🔍 Mode debug : analyse sans seuil")
        df_debug = compute_value_bets("elo_probs.csv", min_value_threshold=0.0)
        if not df_debug.empty:
            df_debug = df_debug.sort_values(by="value", ascending=False)
            st.dataframe(df_debug, use_container_width=True)
        else:
            st.info("Aucun match n'a pu être analysé (API vide ou noms non matchés).")
    else:
        st.success(f"{len(df)} value bet(s) détecté(s) avec un seuil de {seuil*100:.1f}% :")
        df = df.sort_values(by="value", ascending=False)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Télécharger les bets en CSV",
            data=csv,
            file_name=f"value_bets_{datetime.now().date()}.csv",
            mime="text/csv"
        )

        # 🔐 Historique auto
        df["log_date"] = datetime.now().strftime("%Y-%m-%d")
        if not os.path.exists(log_file):
            df.to_csv(log_file, index=False, mode="w")
        else:
            df.to_csv(log_file, mode="a", index=False, header=False)

with onglet_b:
    top_pct = st.slider("🏆 Top % des meilleurs value bets", 1, 100, 10)
    df_all = compute_value_bets("elo_probs.csv", min_value_threshold=0.0)

    if df_all.empty:
        st.warning("Aucun match analysé.")
    else:
        df_all = df_all.sort_values(by="value", ascending=False)
        top_n = int(len(df_all) * top_pct / 100)
        df_top = df_all.head(top_n)

        st.success(f"{top_n} value bet(s) affiché(s) parmi le Top {top_pct}% triés par value.")
        st.dataframe(df_top, use_container_width=True)

        csv_top = df_top.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Télécharger les bets (Top %)",
            data=csv_top,
            file_name=f"top_value_bets_{datetime.now().date()}.csv",
            mime="text/csv"
        )
 
