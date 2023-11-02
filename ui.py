import requests
import json
import os
from sleeperpy import Leagues, User

from data_classes import (
    FinalOutput,
    Player,
    Team
)   

from sleeper.api.unofficial import UPlayerAPIClient

from maxPF import (
    get_current_max_pf,
    get_remaining_max_pf,
    get_player_projections_for_remaining_weeks,
    get_roster_positions
)

from sleeper.enum import Sport


score_settings_dict = {}

PROJECTION_URL = "https://api.sleeper.app/projections/nfl/player/{player_id}?season_type=regular&season=2023&grouping=week"
STATS_URL = "https://api.sleeper.app/stats/nfl/regular/{year}/{week}"

def main_menu():
    print("Welcome to Projected MaxPF!")
    username = 'matttoppi1'

    # Load all player details from the JSON file
    with open("players_data.json", "r") as file:
        players = json.load(file)

    # Call the sleeper API to get the user's ID
    account = User.get_user(username)
    if not account:
        print(f"No account found for username: {username}")
        return

    user_id = account['user_id']

    # Call the sleeper API to get the user's leagues
    leagues = get_leagues(user_id)
    if not leagues:
        print("No leagues found for user: " + username)
        return

    # Create a map from league name to league id
    league_map = {league['name']: league['league_id'] for league in leagues}
        
    # Print the leagues
    print("Leagues:")
    for idx, league in enumerate(leagues, 1):
        print(f"{idx}. {league['name']}")

    # Ask the user to select a league by number
    league_number = int(input("Please select a league: ")) - 1
    league_id = league_map[leagues[league_number]['name']]
    
    #clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(leagues[league_number]['name'])
        
    # Fetch the league users to get owner names
    users = get_league_users(league_id)
    user_dict = {user['user_id']: user['display_name'] for user in users}

    
    score_settings_dict = load_scoring_settings(league_id)
    # print(score_settings_dict)
        
    # Call the sleeper API to get the league's rosters
    rosters = Leagues.get_rosters(league_id)
    
    roster_positions = get_roster_positions(league_id)
    # print(roster_positions) 
    
    # get the current week
    current_week = get_current_week()
    print("\n\nCurrent Week: " + str(current_week))  

    final_res = FinalOutput()
    
    print("\nRosters:")
    for roster in rosters:
        owner_name = user_dict.get(roster['owner_id'], "Unknown")
        print(owner_name)
        
    
    input("\nPress Enter to start analysis...") # Pause the program to allow the user to read the output
    os.system('cls' if os.name == 'nt' else 'clear')
    
    standings = []

    for roster in rosters:
        
        team = Team()
        standings.append(team)
        
        print("\n")
             
        # Replace the hardcoded owner name with the one fetched from users data
        owner_name = user_dict.get(roster['owner_id'], "Unknown")
        
        team.name = owner_name
        team.owner_id = roster['owner_id']
        team.wins = roster['settings']['wins']
        team.losses = roster['settings']['losses']
        team.ties = roster['settings']['ties']
        team.points_for = roster['settings']['fpts']
        team.points_against = roster['settings']['fpts_against']
        
        print("--------------")
        
        
        print("Owner: " + team.name)
        
        
        print("\n----\n\nTEAM STATS:\n")
        
        print("Wins: " + str(team.wins))
        print("Losses: " + str(team.losses))
        print("Ties: " + str(team.ties))
        print("Points For: " + str(team.points_for))
        print("Points Against: " + str(team.points_against))
        print("\n")
        
        
        
        
        for player_id in roster['players']: # for each player on the roster
            p = Player(players[player_id]['first_name'] + " " + players[player_id]['last_name'],  # name
                       players[player_id]['position'],  # position
                       player_id,  # id
                       players[player_id]['team'], # team
                       None, # projections
                       owner_name, # owner name
                       score_settings_dict) # scoring settings
            team.players.append(p)
            
        
        
        
        print("Players: ")
        # print all players
        for p in team.players:
            print("| " + p.name)
            
            projections_for_remaining_weeks = get_player_projections_for_remaining_weeks(p.id)
            for week, projection in projections_for_remaining_weeks.items():
                if projection is not None:  # Check if projection is not None
                    p.update_projections(week, projection)
        
        #calculate the max pf for so far this season
        team.current_max_pf = get_current_max_pf(team, current_week -1, score_settings_dict, roster_positions)
                
        
        print("\nCurrent MaxPF: " + str(team.current_max_pf))
        
        
        team.remaining_max_pf = get_remaining_max_pf(team, current_week, score_settings_dict, roster_positions)
        print("\nProjected Remaining MaxPF: " + str(team.remaining_max_pf))
        
        
        team.total_max_pf = team.current_max_pf + team.remaining_max_pf
        
        final_res.total_max_pf[team.name] = team.total_max_pf
        
        print(f"\n---\nTotal MaxPF: {team.total_max_pf.__round__(2)}\n---\n")
    
        print("--------------")
        
        # input("\nPress Enter to continue...") # Pause the program to allow the user to read the output
        os.system('cls' if os.name == 'nt' else 'clear')
        
     
    os.system('cls' if os.name == 'nt' else 'clear')   
    sorted_max_pf = sorted(final_res.total_max_pf.items(), key=lambda x: x[1], reverse=True)
    final_res.predicted_playoff_teams = sorted_max_pf[:6]
    
    
    
    print("Projected MaxPF (Draft Order):")

    # Find the width for the longest team name
    width = max(len(team[0]) for team in sorted_max_pf) + 4

    for team in sorted_max_pf:
        # Left align the team name and right align the MaxPF using the determined width
        print(team[0].ljust(width) + ": " + str(round(team[1], 2)).rjust(5))
        
        
        
    # create a scoring system that has the best team as 100 and the worst team as 0
    for team in sorted_max_pf:
        score = (team[1] - sorted_max_pf[-1][1]) / (sorted_max_pf[0][1] - sorted_max_pf[-1][1]) * 100
        print(team[0] + ": " + str(round(score, 2)))
        
        
    # Standings
    standings = calculate_standings(standings)
    
    print("\n\nStandings:")
    for team in standings:
        print(f"{team.name}: {team.wins}-{team.losses}-{team.ties}")
        
        
    champ_odds = calculate_championship_odds(final_res.total_max_pf, standings)
    
    print("\n\nChampionship Odds:")
    for team, odds in champ_odds.items():
        print(f"{team}: {odds.__round__(2)}")    

    print("\n\n")

def get_leagues(user_id):
    return Leagues.get_all_leagues(user_id, "nfl", 2023)

if __name__ == "__main__":
    main_menu()

def load_scoring_settings(league_id):
    response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}")
    league_details = response.json()
    scoring_settings_dict = league_details.get("scoring_settings", {})
    return scoring_settings_dict
    
def get_current_week():
    """Fetch the current NFL week from the Sleeper API."""
    url = "https://api.sleeper.app/v1/state/nfl"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("week", 1)  # Default to week 1 if 'week' key is missing
    else:
        print(f"Failed to get current week. HTTP Status Code: {response.status_code}")
        return 1

def get_league_users(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch users for league {league_id} with status code: {response.status_code}")
        return []
      
def get_player_stats(year, week):
    try:
        stats_data = UPlayerAPIClient.get_all_player_stats(sport=Sport.NFL, season=str(year), week=week)
        return stats_data
    except ValueError as e:
        print(f"Failed to fetch stats for year {year} week {week} with error: {str(e)}")
        return []

def get_all_players_projections():
    all_projections_data = UPlayerAPIClient.get_all_player_projections(
        sport=Sport.NFL, season="2023"
    )
    return all_projections_data

def calculate_fpts_from_projections(projections, scoring_settings_dict):
    fpts = 0
    
    # Ensure the 'stats' key exists in projections
    if 'stats' not in projections:
        # print(f"Missing 'stats' in projections for player {projections.get('player_id', 'Unknown')}.")
        return 0

    # Extract the stats dictionary from projections
    stats = projections['stats']

    # Calculate fantasy points for each stat
    for stat, value in stats.items():
        if stat in scoring_settings_dict and value is not None:
            fpts += value * scoring_settings_dict[stat]

    return fpts

def calculate_standings(teams):
    standings = []
    for team in teams:
        # sort by wins
        standings.append(team)
        
    standings = sorted(standings, key=lambda x: x.wins, reverse=True)
    print(standings)
    return standings

def calculate_median(values):
    sorted_values = sorted(values)
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return sorted_values[mid]
    else:
        return (sorted_values[mid - 1] + sorted_values[mid]) / 2

def odds_adjustment(relative_advantage):
    # Calculate the scaling factor based on the relative advantage/disadvantage
    # if a team has a maxPF that is 10% higher than the average, they have a relative advantage of 0.1
    # 0.1 is the scaling factor for a relative advantage of 0
    # 1.1 is the scaling factor for a relative advantage of 1
    # if someone has a relative advantage of 3, they have a scaling factor of 3.1 which is a 310% increase in odds
    # that gets multiplied by the baseline odds
    return max(0.1, 1 + (0.1 * relative_advantage))

def record_weight(current_wins, total_games):
    return current_wins / total_games

def historical_weight(rank):
    # Weights based on historical rank
    rank_weights = {
        1: 0.25,
        2: 0.20,
        3: 0.18,
        4: 0.15,
        5: 0.12,
        6: 0.10,
        7: 0.05,
        8: 0.03,
        9: 0.025,
        10: 0.02,
        11: 0.02,
        12: 0.01
    }
    return rank_weights.get(rank, 0.01)  # Default to 0.01 if rank is not in the dictionary

def calculate_championship_odds(maxPFs, standings):
    avg_maxPF = sum(maxPFs.values()) / len(maxPFs)  # Calculate the average maxPF
    median_maxPF = sorted(maxPFs.values())[len(maxPFs) // 2]  # Calculate the median maxPF
    
    # Calculate the relative advantage/disadvantage based on average
    relative_advantages_avg = {team: (maxPF - avg_maxPF) / 65 for team, maxPF in maxPFs.items()} 
    
    # Calculate the relative advantage/disadvantage based on median
    relative_advantages_median = {team: (maxPF - median_maxPF) / 65 for team, maxPF in maxPFs.items()}
    
    baseline_odds = {team: (maxPF**0.5) for team, maxPF in maxPFs.items()} # Calculate the baseline odds based on the square root of the maxPF
    total_maxPF_sqrt = sum(baseline_odds.values()) # this is the sum of the square roots of the maxPFs
    baseline_odds = {team: odds/total_maxPF_sqrt for team, odds in baseline_odds.items()} # this means that the sum of the odds is 1

    # print(f"\nAverage MaxPF: {avg_maxPF.__round__(2)}")
    # print(f"Median MaxPF: {median_maxPF.__round__(2)}\n")
    
    # print("\nRelative Advantages (Average):")
    # for team, advantage in relative_advantages_avg.items():
    #     print(f"{team}: {advantage.__round__(2)}")
    
    # print("\nRelative Advantages (Median):")
    # for team, advantage in relative_advantages_median.items():
    #     print(f"{team}: {advantage.__round__(2)}")
        
    # print("\nBaseline Odds (Adjusted):")
    # for team, odds in baseline_odds.items():
    #     print(f"{team}: {odds.__round__(2)}")
    
    playoff_boost = 1.35 # 25% boost for playoff teams

    adjusted_odds = {}
    for team_obj in standings:
        team = team_obj.name
        combined_weight = 0.40 * record_weight(team_obj.wins, team_obj.wins + team_obj.losses + team_obj.ties)  # 40% weight for record
        rank = standings.index(team_obj) + 1
        combined_weight += 0.25 * historical_weight(rank)  # 25% weight for historical rank
        
        # Check if the team is in the top 6 and apply the playoff boost
        if rank <= 6:
            combined_weight *= playoff_boost
        
        # Adjust the odds based on both the average and median relative advantages
        # For simplicity, we'll average the adjustments. This can be modified if necessary.
        adjusted_odds[team] = baseline_odds[team] * (odds_adjustment(relative_advantages_avg[team]) + odds_adjustment(relative_advantages_median[team])) / 2 * combined_weight

    total_adjusted_odds = sum(adjusted_odds.values())
    normalized_odds = {team: odds/total_adjusted_odds for team, odds in adjusted_odds.items()}

    # Convert odds to percentages
    final_odds = {team: odds * 100 for team, odds in normalized_odds.items()}
    final_odds = {team: odds.__round__(2) for team, odds in final_odds.items()}
    final_odds = {team: odds for team, odds in sorted(final_odds.items(), key=lambda x: x[1], reverse=True)}
    
    return final_odds


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
    

