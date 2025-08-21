import matplotlib.pyplot as plt
import json
from collections import defaultdict
import numpy as np
with open("player_analysis.json", "r") as f:
    player_data = json.load(f)

def plot_all_player_performance():
    """Plot the performance of all players based on their points per minute."""
    all_players_ppm = defaultdict(list)
    all_players_points = []
    all_players_minutes = []
    for player_id in player_data.keys():
        player_info = player_data.get(str(player_id))

        if not player_info:
            print(f"No data found for player ID {player_id}.")
            continue

        points_per_minute = player_info.get("points_and_minutes", [])

        if not points_per_minute:
            print(f"No performance data available for player ID {player_id}.")
            continue

        # Unzip the points and minutes
        points, minutes = zip(*points_per_minute)

        ppm = [p / m if m > 0 else 0 for p, m in zip(points, minutes)]

        all_players_ppm[player_info["team"]].extend(ppm)
        all_players_minutes.extend(minutes)
        all_players_points.extend(points)

    plt.figure(figsize=(10, 5))
    for team in all_players_ppm:
        plt.hist(all_players_ppm[team], bins=50, alpha=0.7, label=team)
        # Plot mean as line 
        plt.axvline(float(np.mean(all_players_ppm[team])), linestyle='dashed', linewidth=1, label=f"{team} Mean PPM")
    #plt.scatter(all_players_minutes, all_players_points, marker='o', linestyle='-', color='b')
    plt.title("Player Performance: Points per Minute (All Players)")
    plt.xlabel("Minutes Played")
    plt.legend()
    plt.ylabel("Points Scored")
    plt.grid()
    plt.show()
plot_all_player_performance()
