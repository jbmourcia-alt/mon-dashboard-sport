import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import date, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Dashboard Entraînement (DÉMO)", page_icon="🧪", layout="wide")

# --- GÉNÉRATEUR DE DONNÉES FICTIVES ---
def generer_donnees_fictives():
    """Génère des données réalistes pour la démo sans connexion API."""
    data = []
    
    # 1. GÉNÉRATION DE L'HISTORIQUE (30 derniers jours)
    today = date.today()
    for i in range(30):
        current_date = today - timedelta(days=i)
        
        # On simule une activité tous les 2 jours environ (probabilité 50%)
        if np.random.rand() > 0.5:
            r = np.random.rand()
            if r < 0.4:
                # Course à pied
                type_act = "running"
                dist = round(np.random.uniform(5, 15), 2)
                duree = round(dist * np.random.uniform(5.0, 6.5), 2) # entre 5 et 6.5 min/km
            elif r < 0.7:
                # Vélo
                type_act = "cycling"
                dist = round(np.random.uniform(30, 60), 2)
                duree = round(dist / np.random.uniform(20, 30) * 60, 2)
            elif r < 0.9:
                # Muscu
                type_act = "strength_training"
                dist = 0
                duree = 60
            else:
                # Sortie Spéciale
                type_act = "Sortie avec Emma ❤️"
                dist = round(np.random.uniform(5, 12), 2)
                duree = round(dist * 12, 2) # Balade tranquille
            
            data.append({
                "Date": pd.to_datetime(current_date),
                "Type": type_act,
                "Distance (km)": dist,
                "Durée (min)": int(duree),
                "Source": "Réalisé (Garmin)",
                "Notes": "Importé automatiquement"
            })

    # 2. GÉNÉRATION DU PLANNING (7 prochains jours)
    for i in range(1, 8):
        future_date = today + timedelta(days=i)
        if np.random.rand() > 0.4: # Quelques jours de repos
            type_plan = np.random.choice(["running", "cycling", "Sortie avec Emma ❤️"])
            dist_plan = 10 if type_plan == "running" else (40 if type_plan == "cycling" else 8)
            
            data.append({
                "Date": pd.to_datetime(future_date),
                "Type": type_plan,
                "Distance (km)": dist_plan,
                "Durée (min)": 0, # On ne connait pas encore la durée
                "Source": "Prévu",
                "Notes": "Objectif semaine"
            })

    df = pd.DataFrame(data)
    return df.sort_values(by="Date", ascending=False)

# --- GESTION DE L'ÉTAT (SESSION) ---
# Cela permet de garder les données en mémoire même si tu cliques sur un bouton
if 'df_data' not in st.session_state:
    st.session_state.df_data = generer_donnees_fictives()

# --- SIDEBAR : ACTION ---
with st.sidebar:
    st.header("🎮 Mode Simulation")
    st.info("Aucune connexion Garmin requise. Les données sont inventées pour tester l'interface.")
    
    if st.button("🎲 Régénérer de nouvelles données"):
        st.session_state.df_data = generer_donnees_fictives()
        st.rerun()

    st.divider()
    
    st.header("📅 Ajouter au planning")
    with st.form("add_plan"):
        p_date = st.date_input("Date", date.today() + timedelta(days=1))
        p_type = st.selectbox("Sport", ["running", "cycling", "swimming", "Sortie avec Emma ❤️"])
        p_dist = st.number_input("Objectif km", value=10.0)
        
        if st.form_submit_button("Ajouter"):
            new_row = {
                "Date": pd.to_datetime(p_date),
                "Type": p_type,
                "Distance (km)": p_dist,
                "Durée (min)": 0,
                "Source": "Prévu",
                "Notes": "Ajout manuel"
            }
            # Ajout au dataframe en mémoire
            st.session_state.df_data = pd.concat([pd.DataFrame([new_row]), st.session_state.df_data], ignore_index=True)
            st.success("Séance ajoutée !")
            st.rerun()

# --- MAIN DASHBOARD ---
df = st.session_state.df_data

st.title("🏃‍♂️ Dashboard Entraînement (Simulation)")

# KPI Semaine en cours
today = pd.to_datetime(date.today())
start_week = today - timedelta(days=today.weekday())
mask_week = df["Date"] >= start_week

col1, col2, col3 = st.columns(3)
vol_realise = df[(df["Source"] == "Réalisé (Garmin)") & mask_week]["Distance (km)"].sum()
vol_prevu = df[(df["Source"] == "Prévu") & mask_week]["Distance (km)"].sum()

col1.metric("Km Réalisés (Semaine)", f"{vol_realise:.1f} km")
col2.metric("Objectif (Semaine)", f"{vol_prevu:.1f} km", delta=f"{vol_realise - vol_prevu:.1f}")

# Prochaine activité prévue
next_activity = df[(df["Source"] == "Prévu") & (df["Date"] >= today)].sort_values(by="Date")
if not next_activity.empty:
    act = next_activity.iloc[0]
    col3.success(f"🔜 **Prochain :** {act['Type']} ({act['Distance (km)']} km) le {act['Date'].strftime('%d/%m')}")
else:
    col3.info("Rien de prévu prochainement.")

# --- GRAPHIQUE ---
st.subheader("📊 Analyse : Prévu vs Réalisé")
df['Semaine'] = df['Date'].dt.isocalendar().week

# On agrège les données pour le graphique
df_chart = df.groupby(['Semaine', 'Source'])['Distance (km)'].sum().reset_index()

fig = px.bar(
    df_chart, 
    x="Semaine", 
    y="Distance (km)", 
    color="Source", 
    barmode="group",
    color_discrete_map={"Prévu": "#CBD5E0", "Réalisé (Garmin)": "#38B2AC"},
    title="Volume Hebdomadaire"
)
st.plotly_chart(fig, use_container_width=True)

# --- TABLEAU DES DONNÉES ---
st.subheader("📝 Détail des activités")

# Filtres rapides
filtre = st.radio("Afficher :", ["Tout", "Seulement Réalisé", "Seulement Prévu", "Sorties Emma ❤️"], horizontal=True)

if filtre == "Seulement Réalisé":
    df_show = df[df["Source"] == "Réalisé (Garmin)"]
elif filtre == "Seulement Prévu":
    df_show = df[df["Source"] == "Prévu"]
elif filtre == "Sorties Emma ❤️":
    df_show = df[df["Type"] == "Sortie avec Emma ❤️"]
else:
    df_show = df

# Mise en forme du tableau
st.dataframe(
    df_show[["Date", "Type", "Distance (km)", "Durée (min)", "Source", "Notes"]],
    use_container_width=True,
    hide_index=True
)
