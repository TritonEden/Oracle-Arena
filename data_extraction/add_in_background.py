import pandas as pd
from datetime import date, timedelta
import nba_api.stats.endpoints as endpoints
from nba_api.live.nba.endpoints import boxscore
import sys
import time
from modules import *
import sqlalchemy
from sqlalchemy import create_engine
import os

with open("../backend/.env", "r") as f:
    password = f.readlines()[0].strip()
assert os.path.exists("../backend/.env"), "Please create a .env file in the backend directory."

# Initialize DataFrames
teams_df = pd.DataFrame(columns=['team_id', 'season_year', 'team_location', 'team_name', 'team_abbreviation'])
players_df = pd.DataFrame(columns=['player_id', 'player_first_name', 'player_last_name'])
games_df = pd.DataFrame(columns=['game_id', 'season_year', 'game_date', 'home_team_id', 'away_team_id'])
player_game_stats_df = pd.DataFrame(columns=['game_id', 'player_id', 'team_id', 'player_game_stats'])

days = []

for i in range(1, 8):
    days.append(date.today() - timedelta(days=i))

for current_date in days:

    print(f"Processing games for {current_date}...")

    # Fetch the games data with retry and exponential backoff
    games = fetch_with_retry(endpoints.scoreboardv2.ScoreboardV2, game_date=current_date)

    print("Obtained games: ", games)

    try:
        games_data = games.get_data_frames()[0]
        game_ids = games_data['GAME_ID']
        if len(game_ids) > 0:
            current_highest_season = get_season(game_ids[0])  # Assuming get_season is defined somewhere
        else:
            print(f"No games found for {current_date}")
    except Exception as e:
        print(f"Error processing games for {current_date}: {e}. Skipping")
        sys.exit(1)

    # Loop through all the game IDs and fetch the box score data
    for game_id in game_ids:
        # Get all stats using BoxScoreTraditionalV2 with retry and exponential backoff
        boxscore = fetch_with_retry(endpoints.boxscoretraditionalv2.BoxScoreTraditionalV2, game_id=game_id)
        
        if boxscore is None:
            print(f"Error fetching stats for game {game_id}. Skipping.")
            sys.exit(1)

        try:
            player_stats = boxscore.get_data_frames()[0]
            team_stats = boxscore.get_data_frames()[1]
            
            teams_df = fill_teams_df(game_id, team_stats, teams_df)
            players_df = fill_players_df(player_stats, players_df)
            games_df = fill_games_df(game_id, current_date, games_df)
            player_game_stats_df = get_player_game_stats(game_id, player_stats, player_game_stats_df)

            DATABASE_URL = f"postgresql://rgutkeecsoraclearenaadmin:{password}@rg-utk-eecs-oracle-arena-postgresql-db.postgres.database.azure.com:5432/postgres"

            engine = create_engine(DATABASE_URL)


        except Exception as e:
            print(f"Error processing stats for game {game_id}: {e}. Skipping.")
            sys.exit(1)

# Save the DataFrames to the database
try:
    teams_df.to_sql('teams', engine, if_exists='append', index=False)
except Exception as e:
    print(f"Error saving teams data. Skipping.")

try:
    players_df.to_sql('players', engine, if_exists='append', index=False)
except Exception as e:
    print(f"Error saving players data. Skipping.")

try:
    games_df.to_sql('games', engine, if_exists='append', index=False)
except Exception as e:
    print(f"Error saving games data.")
    sys.exit(1)

try:
    player_game_stats_df.to_sql('playergamestats', engine, if_exists='append', index=False)
except Exception as e:
    print(f"Error saving player game stats data.")
    sys.exit(1)


print(teams_df)
print('\n')
print(players_df)
print('\n')
print(games_df)
print('\n')
print(player_game_stats_df)
