import requests
import pandas as pd

# --- CONFIGURATION ---
API_TOKEN = "yw1FZog8TY4W8uBULxkFddtHKTNKVFWLLcSXvclVmSRtHOKsNZhDgv3dOipe" # Remplacez par votre token
BASE_URL = "https://api.sportmonks.com/v3/football"

def get_full_stats_universal(team_name):
    # 1. Récupération ID Equipe
    print(f"1️  Recherche de l'équipe '{team_name}'...")
    search_url = f"{BASE_URL}/teams/search/{team_name}"
    resp = requests.get(search_url, params={"api_token": API_TOKEN})
    if not resp.json().get('data'): return " Équipe introuvable."
    team_id = resp.json()['data'][0]['id']
    print(f"    ID trouvé : {team_id}")

    # 2. Récupération Saison Active
    print(f"  Recherche de la saison active...")
    team_url = f"{BASE_URL}/teams/{team_id}"
    resp_seasons = requests.get(team_url, params={"api_token": API_TOKEN, "include": "seasons"})
    
    current_season_id = None
    for season in resp_seasons.json()['data']['seasons']:
        if season.get('is_current'):
            current_season_id = season['id']
            break
    if not current_season_id: current_season_id = resp_seasons.json()['data']['seasons'][0]['id']
    print(f"    Saison ID : {current_season_id}")

    # 3. Récupération Classement AVEC TOUS LES DÉTAILS
    print(f"  Extraction brute des données...")
    standings_url = f"{BASE_URL}/standings/seasons/{current_season_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "details.type" # On inclut les définitions des types
    }
    
    resp_standings = requests.get(standings_url, params=params)
    standings_data = resp_standings.json().get('data')

    if not standings_data: return " Pas de données de classement."

    # 4. Extraction "Agnostique" (On prend tout ce qu'on trouve)
    stats_found = {}
    
    for entry in standings_data:
        if entry.get('participant_id') == team_id:
            # Stats de base (toujours présentes à la racine)
            stats_found['Position'] = entry.get('position')
            stats_found['Points'] = entry.get('points')
            
            # On regarde dans le tableau 'details'
            if 'details' in entry:
                print("\n  DÉTAILS TROUVÉS DANS L'API ")
                for detail in entry['details']:
                    # On récupère le NOM LISIBLE (ex: "Matches Played") 
                    # et la VALEUR (ex: 18)
                    try:
                        nom_stat = detail['type']['name'] # Nom humain (ex: Won)
                        valeur = detail['value']
                        print(f"   -> {nom_stat}: {valeur}")
                        
                        # On l'ajoute à notre dictionnaire final
                        stats_found[nom_stat] = valeur
                    except:
                        pass # Ignore les erreurs si un champ manque
            break
            
    return stats_found

# --- EXÉCUTION ---
club = input("Entrez le club : ")
resultat = get_full_stats_universal(club)

# --- AFFICHAGE FINAL ---
if isinstance(resultat, dict) and len(resultat) > 0:
    print("\n  TABLEAU RÉCAPITULATIF ")
    # On convertit le dictionnaire en DataFrame pour une belle lecture
    df = pd.DataFrame([resultat])
    display(df)
else:
    print(" Aucune stat trouvée.")
