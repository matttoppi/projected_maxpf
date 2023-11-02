import requests
import json
import os
import time

def fetch_players():
    # Fetch players from the Sleeper API
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch players with status code: {response.status_code}")
        return None

def save_players_locally(players_data):
    # Check if the file already exists
    if os.path.exists('players_data.json'):
        print("'players_data.json' already exists. Overwriting...")

    # Save the players data as a JSON file
    with open('players_data.json', 'w', encoding='utf-8') as f:
        json.dump(players_data, f, ensure_ascii=False, indent=4)

def update_env_file():
    env_file_path = '.env'
    current_time = int(time.time())  # Current timestamp

    # Check if .env file exists
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as file:
            lines = file.readlines()

        # Find and replace the line with the time update
        for i, line in enumerate(lines):
            if line.startswith("TIME_OF_LAST_PLAYER_UPDATE"):
                lines[i] = f"TIME_OF_LAST_PLAYER_UPDATE={current_time}\n"
                break
        else:
            # If the variable doesn't exist in the .env, append it
            lines.append(f"TIME_OF_LAST_PLAYER_UPDATE={current_time}\n")

        with open(env_file_path, 'w') as file:
            file.writelines(lines)

    else:
        # If .env doesn't exist, create it with the variable
        with open(env_file_path, 'w') as file:
            file.write(f"TIME_OF_LAST_PLAYER_UPDATE={current_time}\n")

def main():
    players_data = fetch_players()
    if players_data:
        save_players_locally(players_data)
        update_env_file()
        print("Players data saved locally as 'players_data.json'.")
        print(".env file updated with the time of the last player update.")
    else:
        print("Could not fetch players data.")

if __name__ == "__main__":
    main()
