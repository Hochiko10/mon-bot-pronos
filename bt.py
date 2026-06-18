import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# ─── CONFIGURATION DE TES CLÉS ──────────────────────────────────────
ODDS_API_KEY = "35a8ad1ecd88bf09e0d9a778d0d8da9e"
SPORT = "soccer_fifa_world_cup" 
OPENROUTER_API_KEY = "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"
MODEL_NAME = "openai/gpt-oss-120b:free"
# ────────────────────────────────────────────────────────────────────

# Configuration de la page de ton site
st.set_page_config(page_title="AI Expert Pronos", page_icon="⚽", layout="centered")

def analyser_avec_openrouter(match_name, type_pari, choix_pari, cote):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Tu es un expert en football. Analyse en 2 phrases max si ce pari est safe : {match_name}, {type_pari}, {choix_pari}, Cote: {cote}. Réponds avec [STATUS] RECOMMANDÉ ou PIÈGE suivi de ton [AVIS]."
    data = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200: 
            return response.json()['choices'][0]['message']['content'].strip()
    except: 
        return "[STATUS] ERREUR\n[AVIS] IA indisponible."
    return "[STATUS] ERREUR\n[AVIS] Erreur de réponse de l'IA."

def recuperer_les_matchs():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal"}
    response = requests.get(url, params=params)
    if response.status_code != 200: return []
    
    paris_safes = []
    maintenant = datetime.now(timezone.utc)
    limite_temps = maintenant + timedelta(days=3)

    for match in response.json():
        match_time = datetime.fromisoformat(match.get("commence_time").replace("Z", "+00:00"))
        if match_time > limite_temps: continue
        if not match.get("bookmakers"): continue
            
        for market in match["bookmakers"][0]["markets"]:
            for outcome in market.get("outcomes"):
                cote = outcome["price"]
                if 1.15 <= cote <= 1.45:
                    date_aff = match_time.strftime("%d/%m à %H:%M")
                    if market.get("key") == "h2h":
                        type_pari, choix = "Victoire Directe", f"Victoire de {outcome['name']}"
                    else:
                        type_pari = "Nombre de buts"
                        terme = "Plus de" if outcome['name'].lower() == "over" else "Moins de"
                        choix = f"{terme} {outcome.get('point')} buts"
                    
                    paris_safes.append({"match": f"{match['home_team']} vs {match['away_team']}", "type": type_pari, "choix": choix, "cote": cote, "date": date_aff})
    return sorted(paris_safes, key=lambda x: x["cote"])

# ─── DESIGN DE L'INTERFACE WEB STREAMLIT ───────────────────────────
st.title("🏆 Dashboard Multi-Paris & IA Expert")
st.write("Bienvenue sur ton application d'analyse algorithmique pour la Coupe du Monde 2026.")

# Un gros bouton pour lancer l'analyse sur le site
if st.button("🚀 Lancer l'analyse en temps réel", type="primary"):
    with st.spinner("L'API scanne les matchs et l'IA d'OpenRouter rédige les rapports..."):
        resultats = recuperer_les_matchs()
        
        if not resultats:
            st.warning("Aucun match safe trouvé pour les 3 prochains jours.")
        else:
            st.success(f"Analyse terminée ! {len(resultats[:3])} opportunités détectées.")
            st.divider()
            
            # Affichage des résultats sous forme de "Cartes" esthétiques
            for prono in resultats[:3]:
                with st.container():
                    st.subheader(f"🏟️ {prono['match']}")
                    st.caption(f"📅 Date du match : {prono['date']}")
                    
                    # Colonnes pour afficher proprement le type de pari et la cote
                    col1, col2 = st.columns(2)
                    col1.metric(label="Type de Pari", value=prono['type'])
                    col2.metric(label="Option & Cote", value=f"{prono['choix']} @ {prono['cote']}")
                    
                    # Appel de l'IA pour l'affichage web
                    analyse_ia = analyser_avec_openrouter(prono['match'], prono['type'], prono['choix'], prono['cote'])
                    
                    if "RECOMMANDÉ" in analyse_ia:
                        st.success("🟢 **Verdict de l'IA :** Recommandé")
                    else:
                        st.error("🔴 **Verdict de l'IA :** Attention Match Piège")
                        
                    st.info(f"🧠 **Note de l'Expert AI :** {analyse_ia.replace('[STATUS] RECOMMANDÉ', '').replace('[STATUS] PIÈGE', '').replace('[AVIS]', '').strip()}")
                    st.divider()