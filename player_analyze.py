"""This file will get the point data for every player to analyze it.
    1. Get all player ids for every team.
    2. Get the player data for every player.
    3. Analyze. """

from auth import login
import requests
import json
from time import sleep
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
user = login()

def get_player_ids(token: str) -> list[dict]:
    """Get all player ids for every team. If file is present, it will not fetch the data again.
    """
    if os.path.exists("teams.json"):
        logging.info("Teams data already exists. Loading from file.")
        with open("teams.json", "r") as f:
            all_teams = json.load(f)
            return all_teams
    
    logging.info("Fetching teams data from API.")
    url = "https://api.kickbase.com/v4/competitions/1/teams/{team_id}/teamprofile"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"kkstrauth={token};",
    }
    all_teams = []
    for team_id in range(2, 150):
        logging.info(f"Fetching data for team {team_id}")
        try:
            response = requests.get(url.format(team_id=team_id), headers=headers)
            response.raise_for_status()
            if response.content:
                logging.info(f"Data for team {team_id} fetched successfully.")
                team_data = response.json()
            else:
                team_data = {}
        except requests.exceptions.RequestException as e:
            logging.info(f"Error fetching data for team {team_id}: {e}")
            continue
        if team_data["it"]:
            all_teams.append(
                {
                    "team_id": team_data["tid"],
                    "team_name": team_data["tn"],
                    "players": team_data["it"]
                }
            )
        sleep(1)
    with open("teams.json", "w") as f:
        json.dump(all_teams, f, indent=4)
    logging.info(f"Found {len(all_teams)} teams with players.")
    return all_teams

def get_player_data(player_id: int, token: str) -> list[tuple]:
    """Get the player data for every player."""
    points_per_minute = []
    url = f"https://api.kickbase.com/v4/competitions/1/players/{player_id}/performance"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": f"kkstrauth={token};",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        performance_data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data for player {player_id}: {e}")
        return []
    if performance_data:
        for league in performance_data["it"]: # Iterate through all years
            for match in league["ph"]:
                if match.get("p") and match.get("mp"):
                    points_per_minute.append((float(match["p"]),float(match["mp"].replace("'", ""))))
    else:
        logging.warning(f"No performance data found for player {player_id}.")
    return points_per_minute

def analyze_players():
    """Analyze the players and get the points per minute."""
    all_teams = get_player_ids(user.token)
    player_points = {}
    for team in all_teams:
        for player in team["players"]:
            player_id = player["i"]
            logging.info(f"Analyzing player {player_id} from team {team['team_name']}")
            points_per_minute = get_player_data(player_id, user.token)
            player_points[player_id] = {
                "name": player["n"],
                "status": player["st"],
                "points_and_minutes": points_per_minute,
                "market_value": player["mv"],
                "position": player["pos"],
                "team": team["team_name"]
            }
            logging.info(f"Completed analysis for player {player_id}.")
            logging.info(f"{player_points[player_id]}")
    with open("player_analysis.json", "w") as f:
        json.dump(player_points, f, indent=4)
    logging.info("Player analysis completed and saved to player_analysis.json.")
analyze_players()