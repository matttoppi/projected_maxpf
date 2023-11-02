
import requests
from ui import UPlayerAPIClient


def get_current_max_pf(team, weeks_played, scoring_settings_dict, roster_positions):
    max_pf = 0

    print("\nPrevious Weeks MaxPF:")
    for week in range(1, weeks_played + 1):
        weekly_scores = {}
        used_players = set()  # Track players already counted for MaxPF

        # Fetch stats for the week
        week_stats = get_player_stats(2023, week)  # Assuming year is 2023

        for player_stat in week_stats:
            player_id = player_stat.player_id
            if player_stat.stats and any(player.id == player_id for player in team.players):  
                # Check if the player has stats for the week and is on the team
                player_weekly_stats = player_stat.stats
                weekly_scores[player_id] = calculate_fpts_from_stats(player_weekly_stats.__dict__, scoring_settings_dict)

        weekly_max_pf = 0  # track the max pf for this week
        for pos in roster_positions:
            eligible_positions = [pos]
            if pos == 'FLEX':
                eligible_positions = ['WR', 'RB', 'TE']

            best_player_id = max((pid for pid in weekly_scores if any(player.id == pid and player.position in eligible_positions for player in team.players)),
                                 key=weekly_scores.get, default=None)
            
            if best_player_id and best_player_id not in used_players:
                weekly_max_pf += weekly_scores[best_player_id]
                used_players.add(best_player_id)
                del weekly_scores[best_player_id]

        max_pf += weekly_max_pf
        print(f"- Week {week} MaxPF: {weekly_max_pf}")  # print the max pf for this week
    return max_pf

def get_remaining_max_pf(team, current_week, scoring_settings_dict, roster_positions):
    total_max_pf = 0
    
    print("\n")
    
    for week in range(current_week, 19):
        weekly_scores = {}
        used_players = set()  # Track players already counted for MaxPF

        for player in team.players:
            # Print player name for debugging
            # print(f"Player: {player.name}")

            # Check if the player has projections for this week
            if (week - 1) < len(player.projections):
                player_weekly_projection = player.projections[week - 1]
            else:
                print(f"No projections for {player.name} for week {week}")
                continue

            # # Debug print
            # print(player_weekly_projection)
            # input("Press Enter to continue...")

            if not player_weekly_projection:
                print(f"No projections for {player.name} for week {week}")
                continue

            populated_stats = {k: v for (k, v) in player_weekly_projection.items() if v is not None}
            
            # print(populated_stats)
            
            projection_fpts = calculate_fpts_from_projections(populated_stats, scoring_settings_dict)
            # print(f"Projection for {player.name} for week {week}: {projection_fpts}")  # Debug print
            weekly_scores[player.id] = projection_fpts
        
        weekly_max_pf = 0  # track the max pf for this week
        
        for pos in roster_positions:
            eligible_positions = [pos]
            if pos == 'FLEX':
                eligible_positions = ['WR', 'RB', 'TE']

            best_player_id = max(
                (pid for pid in weekly_scores 
                 if any(player.id == pid and player.position in eligible_positions for player in team.players)),
                key=weekly_scores.get, default=None)
            
            if best_player_id and best_player_id not in used_players:
                weekly_max_pf += weekly_scores[best_player_id]
                used_players.add(best_player_id)
                del weekly_scores[best_player_id]

        total_max_pf += weekly_max_pf
        print(f"- Week {week} MaxPF: {weekly_max_pf}")  # print the max pf for this week
    return total_max_pf

def calculate_fpts_from_stats(projections, scoring_settings_dict):
    fpts = 0
    for stat, value in projections.items():
        if stat in scoring_settings_dict and value is not None:
            fpts += value * scoring_settings_dict[stat]

    
    # print("FPTS: " + str(fpts))
    return fpts

def get_roster_positions(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        response_json = response.json()
        starting_positions = [pos for pos in response_json['roster_positions'] if pos != 'BN']
        return starting_positions  # Always return the result
        
    else:
        print(f"Failed to fetch users for league {league_id} with status code: {response.status_code}")
        return []  # Return an empty list in case of failure
    
def get_player_projections_for_remaining_weeks(player_id):
    
    BASE_URL = "https://api.sleeper.com"

    season = 2023
    
    try:
        # Fetch Weekly Projections using the provided endpoint
        response = requests.get(f"{BASE_URL}/projections/nfl/player/{player_id}?season_type=regular&season={season}&grouping=week")
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code

        weekly_projections = response.json()
        
        # print(weekly_projections)

        return weekly_projections

    except requests.RequestException as e:  # Catching a more general exception to handle any request-related error
        print(f"Failed to get projections for player ID {player_id} for season {season}: {str(e)}")
        return None
    

