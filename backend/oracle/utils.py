import csv
import ast
from django.conf import settings

CSV_FILE_PATH_STATS = settings.BASE_DIR / "../data_extraction/player_game_stats-full.csv"

def get_player_stats_from_csv(player_id):
    stats = []
    try:
        with open(CSV_FILE_PATH_STATS, newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                if int(row["player_id"]) == player_id:
                    # Convert string to list of dictionaries
                    player_stats = ast.literal_eval(row["player_game_stats"])
                    stats.append({
                        "game_id": row["game_id"],
                        "team_id": row["team_id"],
                        "stats": player_stats
                    })
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return stats

CSV_FILE_PATH_PLAYER = settings.BASE_DIR / "../data_extraction/players-full.csv"

def get_players_from_csv():
    players = []
    try:
        with open(CSV_FILE_PATH_PLAYER, newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                players.append({
                    "player_id": int(row["player_id"]),
                    "player_first_name": row["player_first_name"],
                    "player_last_name": row["player_last_name"],
                })
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return players
