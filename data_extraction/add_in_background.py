import pandas as pd
from datetime import date, timedelta
import nba_api.stats.endpoints as endpoints
from nba_api.live.nba.endpoints import boxscore, scoreboard
import sys
import time
from modules import *
import sqlalchemy
from sqlalchemy import create_engine
import os
from sqlalchemy.exc import SQLAlchemyError
import warnings
import random
import sqlalchemy.exc as sa_exc

assert os.path.exists(".env"), "Please create a .env file in the Oracle-Arena directory."

#Get all env vars in .env file, no libraries needed for this

env_vars = {}
with open(".env") as f:
    for line in f:
        key, value = line.strip().split('=', 1)
        env_vars[key] = value

host = env_vars.get("POSTGRES_HOST", "localhost")
port = env_vars.get("POSTGRES_PORT", "5432")
db_name = env_vars.get("POSTGRES_DB", "oracle_arena")
user = env_vars.get("POSTGRES_USER", "postgres")
password = env_vars.get("POSTGRES_PASSWORD", "password")

#If any are defaults, print a warning
if password == "password":
    print("Warning: password is set to default value. Please change it in the .env file.")


def safe_row_insert(df, table_name, engine):
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=sa_exc.SAWarning)
        # Suppress all warnings
        # Set the warning filter to ignore all warnings
        # This will suppress any warnings that occur during the execution of the code block

        # Create a connection to the database
        with engine.connect() as connection:
            #Suppress ALL warnings and errors!


            for i, row in df.iterrows():
                try:
                    row_df = row.to_frame().T  # Convert row Series to a DataFrame
                    row_df.to_sql(table_name, con=connection, if_exists='append', index=False)
                except SQLAlchemyError as e:
                    print(f"Skipping row {i} in '{table_name}': {e}")

# Initialize DataFrames
teams_df = pd.DataFrame(columns=['team_id', 'season_year', 'team_location', 'team_name', 'team_abbreviation'])
players_df = pd.DataFrame(columns=['player_id', 'player_first_name', 'player_last_name'])
games_df = pd.DataFrame(columns=['game_id', 'season_year', 'game_date', 'home_team_id', 'away_team_id', 'game_time'])
player_game_stats_df = pd.DataFrame(columns=['game_id', 'player_id', 'team_id', 'player_game_stats'])

DATABASE_URL = get_database_url(host, password, user, port, db_name)

days = [date.today() - timedelta(days=i) for i in range(-6, 6, 1)] #Do 5 days back, 6 days forward

for current_date in days:

    #If we are processing the current date, we do not have stats -- so let's just get the teams and games
    if current_date > date.today():
        print(f"Adding future date: {current_date}.")
        # Get the schedule for that day
        games = endpoints.scoreboardv2.ScoreboardV2(game_date=current_date)

        if games is None:
            print(f"Error fetching future date's games: 100. Skipping.")
            continue

        games = games.game_header.get_data_frame()

                
        df_games = fill_games_df_future(games, games_df)

        df_games = df_games.drop_duplicates()

        if not check_dfs([df_games]):
            print("DataFrames have null values. Skipping")
            continue

        df_games = df_games.astype({"game_id": str})
        df_games["game_id"] = df_games["game_id"].apply(lambda x: f"00{x}" if len(x) == 2 else x)

        print("Saving future date's teams and games to the database...")

        engine = create_engine(DATABASE_URL)
        print("Engine created")
        # Save the DataFrames to the database row by row

        #Change the name of some columns for the players and change it to new_players_df
        safe_row_insert(df_games, 'games', engine)
        
        #If a date is/was in the future, we may have to go ahead and update it to what we know now
        print("Updating the dates...")
        insert_date_in_db(df_games, engine)
        
        continue
    if current_date == date.today():
        print("Fetching today's games and teams...")
        games = fetch_with_retry(scoreboard.ScoreBoard)
        if games is None:
            print(f"Error fetching today's games: 100. Skipping.")
            continue
        df_teams = fill_teams_df_v1(games, teams_df)
        df_games = fill_games_df_v1(games, games_df)

        df_games = df_games.drop_duplicates()
        df_teams = df_teams.drop_duplicates()

        assert check_dfs([df_games, df_teams]), "DataFrames have null values"

        df_games = df_games.astype({"game_id": str})
        df_games["game_id"] = df_games["game_id"].apply(lambda x: f"00{x}" if len(x) == 2 else x)

        print("Saving today's teams and games to the database...")

        engine = create_engine(DATABASE_URL)
        print("Engine created")
        # Save the DataFrames to the database row by row

        #Change the name of some columns for the players and change it to new_players_df
        safe_row_insert(df_teams, 'teams', engine)
        safe_row_insert(df_games, 'games', engine)

        #If a date is/was in the future, we may have to go ahead and update it to what we know now
        print("Updating the dates...")
        insert_date_in_db(df_games, engine)
        continue
    print(f"Fetching games for {current_date}...")

    # Fetch the games data with retry and exponential backoff
    games = fetch_with_retry(endpoints.scoreboardv2.ScoreboardV2, game_date=current_date)

    try:
        games_data = games.get_data_frames()[0]
        game_ids = games_data['GAME_ID']
        if len(game_ids) > 0:
            current_highest_season = get_season(game_ids[0])  # Assuming get_season is defined somewhere
        else:
            print(f"No games found for {current_date}")
    except Exception as e:
        print(f"Error processing games for {current_date}: {e}: 100. Skipping")
        continue

    # Loop through all the game IDs and fetch the box score data
    for game_id in game_ids:
        # Get all stats using BoxScoreTraditionalV2 with retry and exponential backoff -- do this for not today
        boxscore = fetch_with_retry(endpoints.boxscoretraditionalv2.BoxScoreTraditionalV2, game_id=game_id)
        
        if boxscore is None:
            print(f"Error fetching stats for game {game_id}: 101. Skipping.")
            continue

        try:
            player_stats = boxscore.get_data_frames()[0]
            team_stats = boxscore.get_data_frames()[1]

            if player_stats.empty or team_stats.empty:
                boxscore = fetch_with_retry(endpoints.boxscoretraditionalv3.BoxScoreTraditionalV3, game_id=game_id)
                print("Fetching BoxScoreTraditionalV3")
                player_stats = boxscore.get_data_frames()[0]
                team_stats = boxscore.get_data_frames()[1]
                #Rename the columns to match the old ones
                player_stats["PLAYER_NAME"] = player_stats["firstName"] + " " + player_stats["familyName"]
                player_stats = player_stats.rename(columns={
                    "gameId": "GAME_ID",
                    "personId": "PLAYER_ID",
                    "teamId": "TEAM_ID",
                    "teamCity": "TEAM_CITY",
                    "teamName": "TEAM_NAME",
                    "teamTricode": "TEAM_ABBREVIATION",
                    "minutes": "MIN",
                    "fieldGoalsMade": "FGM",
                    "fieldGoalsAttempted": "FGA",
                    "fieldGoalsPercentage": "FG_PCT",
                    "threePointersMade": "FG3M",
                    "threePointersAttempted": "FG3A",
                    "threePointersPercentage": "FG3_PCT",
                    "freeThrowsMade": "FTM",
                    "freeThrowsAttempted": "FTA",
                    "freeThrowsPercentage": "FT_PCT",
                    "reboundsOffensive": "OREB",
                    "reboundsDefensive": "DREB",
                    "reboundsTotal": "REB",
                    "assists": "AST",
                    "steals": "STL",
                    "blocks": "BLK",
                    "turnovers": "TO",
                    "foulsPersonal": "PF",
                    "points": "PTS",
                    "plusMinusPoints": "PLUS_MINUS"
                })

                team_stats = team_stats.rename(columns={
                    "gameId": "GAME_ID",
                    "teamId": "TEAM_ID",
                    "teamCity": "TEAM_CITY",
                    "teamName": "TEAM_NAME",
                    "teamTricode": "TEAM_ABBREVIATION",
                    "minutes": "MIN",
                    "fieldGoalsMade": "FGM",
                    "fieldGoalsAttempted": "FGA",
                    "fieldGoalsPercentage": "FG_PCT",
                    "threePointersMade": "FG3M",
                    "threePointersAttempted": "FG3A",
                    "threePointersPercentage": "FG3_PCT",
                    "freeThrowsMade": "FTM",
                    "freeThrowsAttempted": "FTA",
                    "freeThrowsPercentage": "FT_PCT",
                    "reboundsOffensive": "OREB",
                    "reboundsDefensive": "DREB",
                    "reboundsTotal": "REB",
                    "assists": "AST",
                    "steals": "STL",
                    "blocks": "BLK",
                    "turnovers": "TO",
                    "foulsPersonal": "PF",
                    "points": "PTS"
                })

                #For player_stats, if MIN is an empty string, set it to null and then all of the other stats to null
                player_stats.loc[player_stats["MIN"] == "", "MIN"] = None

                for i, row in player_stats.iterrows():
                    if row["MIN"] is None:
                        player_stats.at[i, "FGM"] = None
                        player_stats.at[i, "FGA"] = None
                        player_stats.at[i, "FG_PCT"] = None
                        player_stats.at[i, "FG3M"] = None
                        player_stats.at[i, "FG3A"] = None
                        player_stats.at[i, "FG3_PCT"] = None
                        player_stats.at[i, "FTM"] = None
                        player_stats.at[i, "FTA"] = None
                        player_stats.at[i, "FT_PCT"] = None
                        player_stats.at[i, "OREB"] = None
                        player_stats.at[i, "DREB"] = None
                        player_stats.at[i, "REB"] = None
                        player_stats.at[i, "AST"] = None
                        player_stats.at[i, "STL"] = None
                        player_stats.at[i, "BLK"] = None
                        player_stats.at[i, "TO"] = None
                        player_stats.at[i, "PF"] = None
                        player_stats.at[i, "PTS"] = None
                        player_stats.at[i, "PLUS_MINUS"] = None

            teams_df = fill_teams_df(game_id, team_stats, teams_df)
            print("Got teams_df")
            players_df = fill_players_df(player_stats, players_df)
            print("Got players_df")
            games_df = fill_games_df(game_id, current_date, games_df)
            print("Got games_df")
            player_game_stats_df = get_player_game_stats(game_id, player_stats, player_game_stats_df)
            print("Got player_game_stats_df")

            #Go thru the player_game_stats_df and all the jsons. In those jsons, replace any Nans to None
            player_game_stats_df = json_fix(player_game_stats_df)
            print("Got player_game_stats_df with json fix")

            # Save the DataFrames to CSV files
            teams_df.to_csv("teams-tmp.csv", index=False)
            players_df.to_csv("players-tmp.csv", index=False)
            games_df.to_csv("games-tmp.csv", index=False)
            player_game_stats_df.to_csv("player_game_stats-tmp.csv", index=False)

            df_stats = pd.read_csv("player_game_stats-tmp.csv")
            df_games = pd.read_csv("games-tmp.csv")
            df_players = pd.read_csv("players-tmp.csv")
            df_teams = pd.read_csv("teams-tmp.csv")

            #Check the validity of the df's -- YES THIS IS CRAPPY CODE BUT IT WORKS FOR NOW
            df_stats = df_stats.drop_duplicates()
            df_games = df_games.drop_duplicates()
            df_players = df_players.drop_duplicates()
            df_teams = df_teams.drop_duplicates()
            df_players = df_players.rename(columns={"player_first_name": "first_name", "player_last_name": "last_name"})
            assert check_dfs([df_stats, df_games, df_players, df_teams]), "DataFrames have null values"
            assert df_stats.player_id.nunique() == df_players.player_id.nunique(), "Player IDs do not match between stats and players dataframes."
            assert df_stats.team_id.nunique() == df_teams.team_id.nunique(), "Team IDs do not match between stats and teams dataframes."
            assert df_stats.game_id.nunique() == df_games.game_id.nunique(), "Game IDs do not match between stats and games dataframes."
            df_games = df_games.astype({"game_id": str})
            df_stats = df_stats.astype({"game_id": str})
            df_games["game_id"] = df_games["game_id"].apply(lambda x: f"00{x}" if len(x) == 2 else x)
            df_stats["game_id"] = df_stats["game_id"].apply(lambda x: f"00{x}" if len(x) == 2 else x)

            print("Saving stats to the database...")
            
            engine = create_engine(DATABASE_URL)
            print("Engine created")
            # Save the DataFrames to the database row by row

            #Change the name of some columns for the players and change it to new_players_df
            safe_row_insert(df_teams, 'teams', engine)
            safe_row_insert(df_players, 'players', engine)
            safe_row_insert(df_games, 'games', engine)
            safe_row_insert(df_stats, 'player_game_stats', engine)

            print("Updating the dates...")
            insert_date_in_db(df_games, engine)

            teams_df = pd.DataFrame(columns=['team_id', 'season_year', 'team_location', 'team_name', 'team_abbreviation'])
            players_df = pd.DataFrame(columns=['player_id', 'player_first_name', 'player_last_name'])
            games_df = pd.DataFrame(columns=['game_id', 'season_year', 'game_date', 'home_team_id', 'away_team_id', 'game_time'])
            player_game_stats_df = pd.DataFrame(columns=['game_id', 'player_id', 'team_id', 'player_game_stats'])


        except Exception as e:
            print(f"Error processing stats for game {game_id}: {e}: 102. Skipping.")
            continue

    time.sleep(1+random.uniform(0.5, 2.5))  # Sleep for 1 second to avoid hitting the API too quickly

os.remove("teams-tmp.csv")
os.remove("players-tmp.csv")
os.remove("games-tmp.csv")
os.remove("player_game_stats-tmp.csv")
