# 🎾 Value Bets Tennis – Elo vs Cotes Pinnacle

Ce projet permet de détecter des paris de tennis rentables en comparant un modèle **Elo dynamique** (calculé à partir des matchs historiques ATP depuis 2000) avec les **cotes Pinnacle** en temps réel.

---

## 🧠 Objectif

> Battre les bookmakers en détectant automatiquement les **value bets** : des matchs où la probabilité de victoire estimée par le modèle est **plus élevée** que celle implicite dans les cotes.

---

## 📁 Structure du projet

```
📦 Projet
🔺 app.py                  # Interface Streamlit avec affichage des bets
🔺 prepare_elo_csv.py      # Création du fichier elo_probs.csv depuis les fichiers Excel tennis
🔺 model.py                # Lecture du fichier Elo et calcul des probabilités
🔺 get_pinnacle_matches.py # Requête API pour récupérer les cotes des matchs ATP
🔺 value_bets.py           # Détection des value bets (Elo vs cotes)
🔺 top_value_bets.py       # (optionnel) Analyse de la rentabilité des meilleurs value bets
🔺 elo_probs.csv           # Résultat du calcul Elo pour chaque joueur
🔺 Data/                   # Tous les fichiers .xlsx de tennis-data.co.uk (2000–2025)
```

---

## ⚙️ Fonctionnement

### 1. **Préparer le fichier Elo**

Lancer :

```bash
python prepare_elo_csv.py
```

Cela va :

* Lire tous les fichiers tennis dans `Data/`
* Calculer l’Elo pour chaque joueur (Hard, Clay, Grass)
* Générer un fichier `elo_probs.csv`

---

### 2. **Calcul des value bets**

Le cœur de l’analyse se fait dans `value_bets.py`, qui :

* Récupère les cotes via l’API Pinnacle
* Estime les probabilités avec ton Elo
* Compare les deux pour estimer la **value**
* Garde les paris où la value dépasse un seuil (ex: 5%)

---

### 3. **Interface Streamlit**

Lancer :

```bash
streamlit run app.py
```

Tu verras :

* Les value bets du jour (s’il y en a)
* Un mode debug si aucun match n’est détecté
* Un bouton pour exporter les bets en CSV

---

## 🌟 Stratégies de paris

### 🔹 Option A – Seuil fixe (value > X%)

On joue **tous les bets** avec une value supérieure à un seuil donné (ex: 5%).

| Seuil de Value | Nombre de Bets | ROI moyen |
| -------------- | -------------- | --------- |
| > 0%           | 4298           | 9.8%      |
| > 1%           | 3823           | 11.2%     |
| > 2%           | 3262           | 13.1%     |
| > 3%           | 2732           | 15.6%     |
| > 4%           | 2223           | 18.6%     |
| > 5%           | 1742           | 21.6%     |
| > 6%           | 1364           | 24.7%     |
| > 7%           | 1062           | 27.6%     |
| > 8%           | 828            | 29.9%     |
| > 9%           | 659            | 31.9%     |
| > 10%          | 510            | 33.9%     |

🔸 Bon compromis entre volume et rentabilité
🔸 Plus tu montes le seuil, plus le ROI augmente (mais tu as moins de paris)

---

### 🔹 Option B – Top X% des meilleurs value bets

On trie tous les matchs par leur value décroissante et on garde seulement les meilleurs X% :

| % des meilleurs bets | ROI moyen |
| -------------------- | --------- |
| Top 5%               | **\~70%** |
| Top 10%              | \~50%     |
| Top 20%              | \~35%     |

🔹 Très fort ROI sur une petite sélection
🔹 Utile pour stratégie ultra-sélective ou automatisée

---

## 📌 Bonus

Si tu veux analyser les performances de ton historique ou tester des seuils différents :

* Utilise `top_value_bets.py` pour tester les top bets
* Ou crée un `backtest.py` avec les résultats réels (`match_results.csv`) pour vérifier si ton modèle est toujours performant

---

## 📞 API utilisée

* [Pinnacle Odds API via RapidAPI](https://rapidapi.com/tipsters/api/pinnacle-odds/)
  Clé : fournie dans le code (`get_pinnacle_matches.py`)

---

## ✅ Statut actuel

* [x] Données ATP historiques 2000–2025
* [x] Calcul Elo par surface
* [x] Détection de value bets
* [x] Interface Streamlit avec CSV export
* [ ] Ajout de WTA (optionnel)
* [ ] Backtest automatique avec `match_results.csv` (bientôt)

---

**🔐 Tu peux maintenant utiliser cette stratégie pour parier intelligemment sur le tennis ATP en détectant des erreurs dans les cotes !**
 
