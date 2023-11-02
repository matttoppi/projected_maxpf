import requests
import json
import os
import time

from update_players import fetch_players, save_players_locally, update_env_file
from ui import main_menu

def main():
    update_players_data()
    main_menu()    

def update_players_data():
    last_update_time = get_last_update_time()

    if not last_update_time or (int(time.time()) - last_update_time) > (3 * 24 * 60 * 60):
        players_data = fetch_players()
        if players_data:
            save_players_locally(players_data)
            update_env_file()
            print("Players data updated locally as 'players_data.json'.")
            print(".env file updated with the time of the last player update.")
        else:
            print("Could not fetch players data.")

def get_last_update_time():
    env_file_path = '.env'
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.startswith("TIME_OF_LAST_PLAYER_UPDATE"):
                    try:
                        return int(line.split("=")[1].strip())
                    except ValueError:
                        return None
    return None

if __name__ == "__main__":
    main()
