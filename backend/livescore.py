import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
API_TOKEN = "yw1FZog8TY4W8uBULxkFddtHKTNKVFWLLcSXvclVmSRtHOKsNZhDgv3dOipe"
BASE_URL = "https://api.sportmonks.com/v3/football"

def get_live_match_stats(team_name):
    """
    Récupère les statistiques en direct d'un match pour une équipe donnée
    """
    
    # 1. Recherche de l'équipe
    print(f"🔍 Recherche de l'équipe '{team_name}'...")
    search_url = f"{BASE_URL}/teams/search/{team_name}"
    resp = requests.get(search_url, params={"api_token": API_TOKEN})
    
    if not resp.json().get('data'):
        return " Équipe introuvable."
    
    team_id = resp.json()['data'][0]['id']
    team_name_official = resp.json()['data'][0]['name']
    print(f" Équipe trouvée : {team_name_official} (ID: {team_id})")
    
    # 2. Chercher dans /livescores/inplay
    print(f"\n Recherche de matchs en direct...")
    
    livescores_url = f"{BASE_URL}/livescores/inplay"
    params = {
        "api_token": API_TOKEN,
        "include": "participants;scores;state;statistics.type;events"
    }
    
    resp_live = requests.get(livescores_url, params=params)
    live_data = resp_live.json()
    
    if 'data' not in live_data:
        print(f" Erreur API: {live_data}")
        return None
    
    live_matches = live_data.get('data', [])
    print(f"📋 {len(live_matches)} match(s) en cours trouvé(s)")
    
    # Debug: afficher les matchs trouvés
    if live_matches:
        print(f"\n Analyse des matchs en cours...")
        for i, match in enumerate(live_matches, 1):
            participants = match.get('participants', [])
            if len(participants) >= 2:
                team1 = participants[0].get('name', 'N/A')
                team2 = participants[1].get('name', 'N/A')
                print(f"   {i}. {team1} vs {team2}")
                print(f"      IDs: {participants[0].get('id')} vs {participants[1].get('id')}")
    
    # 3. Chercher le match de notre équipe
    match_found = None
    
    for match in live_matches:
        participants = match.get('participants', [])
        for participant in participants:
            if participant.get('id') == team_id:
                match_found = match
                print(f"\n Match de {team_name_official} trouvé !")
                break
        if match_found:
            break
    
    # 4. Si pas trouvé dans inplay, chercher dans les matchs d'aujourd'hui
    if not match_found:
        print(f"\n  {team_name_official} ne joue pas dans les matchs en direct trouvés")
        print(f" Recherche dans les matchs d'aujourd'hui...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        fixtures_url = f"{BASE_URL}/fixtures/date/{today}"
        params_today = {
            "api_token": API_TOKEN,
            "include": "participants;scores;state;statistics.type;events",
            "filters": f"participantSearch:{team_name_official}"
        }
        
        resp_today = requests.get(fixtures_url, params=params_today)
        today_data = resp_today.json()
        
        if 'data' not in today_data:
            print(f" Erreur API: {today_data}")
            return None
        
        fixtures = today_data.get('data', [])
        print(f"📋 {len(fixtures)} match(s) trouvé(s) aujourd'hui pour {team_name_official}")
        
        # Chercher un match en cours (state_id: 2=LIVE, 3=HT, etc.)
        live_states = [2, 3, 8, 9, 10, 11, 12, 13, 14]
        
        for fixture in fixtures:
            state = fixture.get('state', {})
            state_id = state.get('id')
            state_name = state.get('state', 'UNKNOWN')
            
            print(f"   Match: {fixture.get('name')} | State: {state_name} (ID: {state_id})")
            
            if state_id in live_states:
                match_found = fixture
                print(f"    Match EN COURS trouvé !")
                break
    
    # 5. Option manuelle
    if not match_found:
        print(f"\n Aucun match en direct trouvé")
        print(f"\n Voulez-vous chercher par ID de fixture ?")
        fixture_id = input(f"   Entrez l'ID (ou Entrée pour annuler): ")
        
        if fixture_id.strip():
            fixture_url = f"{BASE_URL}/fixtures/{fixture_id.strip()}"
            params_id = {
                "api_token": API_TOKEN,
                "include": "participants;scores;state;statistics.type;events"
            }
            
            try:
                resp_id = requests.get(fixture_url, params=params_id)
                fixture_data = resp_id.json()
                
                if 'data' in fixture_data:
                    match_found = fixture_data['data']
                    print(f" Match trouvé par ID !")
                else:
                    print(f" Erreur: {fixture_data}")
            except Exception as e:
                print(f" Erreur: {e}")
        
        if not match_found:
            return None
    
    # 6. Extraction des informations
    print(f"\n{'='*70}")
    print(f" MATCH EN DIRECT")
    print(f"{'='*70}")
    
    # Participants
    participants = match_found.get('participants', [])
    if len(participants) < 2:
        print(" Erreur: participants manquants")
        return None
    
    home_team = participants[0].get('name', 'N/A')
    away_team = participants[1].get('name', 'N/A')
    home_id = participants[0].get('id')
    away_id = participants[1].get('id')
    
    is_home = (home_id == team_id)
    
    # Score avec détails
    scores = match_found.get('scores', [])
    home_score = 0
    away_score = 0
    halftime_home = None
    halftime_away = None
    
    for score in scores:
        desc = score.get('description', '').upper()
        score_data = score.get('score', {})
        participant_id = score.get('participant_id')
        
        if 'CURRENT' in desc:
            if participant_id == home_id:
                home_score = score_data.get('participant', 0) or 0
            elif participant_id == away_id:
                away_score = score_data.get('participant', 0) or 0
        elif 'HALFTIME' in desc or 'HT' in desc:
            if participant_id == home_id:
                halftime_home = score_data.get('participant', 0) or 0
            elif participant_id == away_id:
                halftime_away = score_data.get('participant', 0) or 0
    
    # État
    state = match_found.get('state', {})
    minute = state.get('minute', 'N/A')
    status = state.get('state', 'N/A')
    
    print(f"  {home_team} {home_score} - {away_score} {away_team}")
    if halftime_home is not None and halftime_away is not None:
        print(f"    (Mi-temps: {halftime_home} - {halftime_away})")
    print(f"  Minute: {minute}' | Statut: {status}")
    print(f" {team_name_official}: {'DOMICILE ' if is_home else 'EXTÉRIEUR '}")
    print(f"{'='*70}")
    
    # 7. Statistiques - UTILISATION DU CHAMP TYPE
    statistics = match_found.get('statistics', [])
    team_stats = {}
    opponent_stats = {}
    
    print(f"\n🔍 Statistiques disponibles: {len(statistics)} statistique(s)")
    
    # Extraction avec le nom du type
    for stat in statistics:
        try:
            participant_id = stat.get('participant_id')
            data = stat.get('data', {})
            value = data.get('value')
            
            # Récupérer le nom depuis le champ 'type'
            type_obj = stat.get('type', {})
            stat_name = type_obj.get('name', 'Inconnu')
            
            # Déterminer si c'est notre équipe ou l'adversaire
            is_our_team = (participant_id == team_id)
            target_dict = team_stats if is_our_team else opponent_stats
            
            if value is not None and stat_name != 'Inconnu':
                target_dict[stat_name] = value
                
        except Exception as e:
            print(f"    Erreur extraction stat: {e}")
            pass
    
    print(f"    Stats extraites: {len(team_stats)} pour votre équipe, {len(opponent_stats)} pour l'adversaire")
    
    # 8. Événements
    events = match_found.get('events', [])
    team_events = {
        'Buts': [],
        'Cartons Jaunes': [],
        'Cartons Rouges': [],
        'Remplacements': []
    }
    
    for event in events:
        if event.get('participant_id') == team_id:
            type_id = event.get('type_id')
            minute_ev = event.get('minute', 'N/A')
            player_name = event.get('player_name', 'Inconnu')
            
            # Types d'événements courants
            if type_id in [13, 14, 15, 16, 17, 18]:  # Buts
                team_events['Buts'].append(f"{player_name} ({minute_ev}')")
            elif type_id == 84:  # Carton jaune
                team_events['Cartons Jaunes'].append(f"{player_name} ({minute_ev}')")
            elif type_id == 83:  # Carton rouge
                team_events['Cartons Rouges'].append(f"{player_name} ({minute_ev}')")
            elif type_id in [18, 19]:  # Remplacements
                team_events['Remplacements'].append(f"{player_name} ({minute_ev}')")
    
    # 9. Affichage amélioré
    print(f"\n{'='*70}")
    print(f" STATISTIQUES - {team_name_official.upper()}")
    print(f"{'='*70}")
    
    if team_stats:
        # Stats principales en premier
        priority = ['Possession %', 'Tirs totaux', 'Tirs cadrés', 'Tirs non cadrés', 
                   'Corners', 'Fautes', 'Cartons jaunes', 'Cartons rouges']
        
        print("\n Statistiques principales:")
        for stat in priority:
            if stat in team_stats:
                print(f"   {stat}: {team_stats[stat]}")
        
        # Autres stats
        other_stats = {k: v for k, v in team_stats.items() if k not in priority}
        if other_stats:
            print("\n Statistiques détaillées:")
            for stat_name, stat_value in sorted(other_stats.items()):
                print(f"   {stat_name}: {stat_value}")
    else:
        print("  Aucune statistique disponible")
    
    print(f"\n{'='*70}")
    print(f"📊 STATISTIQUES - ADVERSAIRE ({home_team if not is_home else away_team})")
    print(f"{'='*70}")
    
    if opponent_stats:
        print("\n Statistiques principales:")
        for stat in priority:
            if stat in opponent_stats:
                print(f"   {stat}: {opponent_stats[stat]}")
        
        other_opponent = {k: v for k, v in opponent_stats.items() if k not in priority}
        if other_opponent:
            print("\n Statistiques détaillées:")
            for stat_name, stat_value in sorted(other_opponent.items()):
                print(f"   {stat_name}: {stat_value}")
    else:
        print("  Aucune statistique disponible")
    
    print(f"\n{'='*70}")
    print(f" ÉVÉNEMENTS - {team_name_official.upper()}")
    print(f"{'='*70}")
    
    has_events = False
    for event_type, events_list in team_events.items():
        if events_list:
            has_events = True
            print(f"\n{event_type}:")
            for event in events_list:
                print(f"  • {event}")
    
    if not has_events:
        print("\n  Aucun événement")
    
    print(f"\n{'='*70}\n")
    
    return {
        'match_info': {
            'home_team': home_team,
            'away_team': away_team,
            'score': f"{home_score} - {away_score}",
            'minute': minute,
            'status': status
        },
        'team_stats': team_stats,
        'opponent_stats': opponent_stats,
        'events': team_events
    }

# --- EXÉCUTION ---
if __name__ == "__main__":
    club = input(" Entrez le nom du club : ")
    result = get_live_match_stats(club)
    
    if result and isinstance(result, dict):
        print(" Données extraites avec succès!")
    else:
        print("  Impossible de récupérer les données")
