# app.py

import streamlit as st
from value_bets import compute_value_bets
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Tennis Value Bets", layout="wide")
st.title("🎾 Value Bets Tennis - Elo vs Cotes Pinnacle")

# Chargement automatique depuis fichier local
elo_file = "elo_probs.csv"

with st.spinner("Calcul des value bets en cours..."):
    df = compute_value_bets(elo_file)

if df.empty:
    st.warning("Aucun value bet détecté avec les données actuelles.")

    # Mode debug si aucun bet trouvé
    st.subheader("🔍 Mode debug : analyse détaillée")
    df_debug = compute_value_bets(elo_file, min_value_threshold=0.0)

    if not df_debug.empty:
        df_debug = df_debug.sort_values(by="value", ascending=False)
        st.dataframe(df_debug, use_container_width=True)
    else:
        st.info("Aucun match n'a pu être analysé (API vide ou noms non matchés).")
else:
    st.success(f"{len(df)} value bet(s) détecté(s) :")
    df = df.sort_values(by="value", ascending=False)
    st.dataframe(df, use_container_width=True)

    # Export CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Télécharger en CSV",
        data=csv,
        file_name=f"value_bets_{datetime.now().date()}.csv",
        mime="text/csv"
    )
