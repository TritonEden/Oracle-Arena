import pandas as pd
from datetime import date, timedelta
import nba_api.stats.endpoints as endpoints
from nba_api.live.nba.endpoints import boxscore
from nba_api.stats.endpoints import boxscoresummaryv2
import json
import time
import math
import sqlalchemy

def get_home_away_team(game_id):
    """
    Retrieves the home and away team IDs for a given NBA game.

    Parameters:
    game_id (str): The unique identifier for the game.

    Returns:
    tuple: A pair of integers representing the home team ID and away team ID.
    """

    boxscore = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
    game_data = boxscore.get_data_frames()[0]  # Game summary data

    home_team_id = game_data['HOME_TEAM_ID'].iloc[0]  # Extract home team ID
    away_team_id = game_data['VISITOR_TEAM_ID'].iloc[0]  # Extract away team ID

    return home_team_id, away_team_id

def get_season(game_id):
    """
    Determines the NBA season based on the given game_id.

    The game_id follows a pattern where:
    - A game_id starting with '00246' to '00299' corresponds to seasons from 1946-47 to 1999-00.
    - A game_id starting with '00200' to '00224' corresponds to seasons from 2000-01 to 2024-25.

    Logic:
    - Extract the 4th and 5th digits of game_id (game_year).
    - If game_year is between 46 and 99, it belongs to the 1900s (1946-47 to 1999-00).
    - Otherwise, it belongs to the 2000s (2000-01 onward).
    - The output is formatted as "YYYY-YY", where YY represents the last two digits of the next year.

    Parameters:
    game_id (str): The unique identifier for the game.

    Returns:
    string: The NBA season in the format 'YYYY-YY' (e.g., '1999-00').
    """

    game_year = int(game_id[3:5])  # Extracts the season identifier
    if 46 <= game_year <= 99:
        start_year = game_year + 1900
    else:
        start_year = game_year + 2000

    end_year_short = (start_year + 1) % 100  # Get last two digits of the next year
    return f"{start_year}-{end_year_short:02d}"

def fill_teams_df(game_id, team_stats, teams_df):

    season_year = get_season(game_id)
    team_ids = team_stats['TEAM_ID'].unique()

    # Get home team data
    team_one_row = team_stats[team_stats['TEAM_ID'] == team_ids[0]].iloc[0]
    team_one_location = team_one_row['TEAM_CITY']
    team_one_name = team_one_row['TEAM_NAME']
    team_one_abbrev = team_one_row['TEAM_ABBREVIATION']

    # Get away team data
    team_two_row = team_stats[team_stats['TEAM_ID'] == team_ids[1]].iloc[0]
    team_two_location = team_two_row['TEAM_CITY']
    team_two_name = team_two_row['TEAM_NAME']
    team_two_abbrev = team_two_row['TEAM_ABBREVIATION']

    # Convert the data to a data frame and concatenate it with the existing teams_df
    new_rows = pd.DataFrame([
        {'team_id': team_ids[0], 'season_year': season_year,
        'team_location': team_one_location, 'team_name': team_one_name,
        'team_abbreviation': team_one_abbrev},

        {'team_id': team_ids[1], 'season_year': season_year,
        'team_location': team_two_location, 'team_name': team_two_name,
        'team_abbreviation': team_two_abbrev}
    ])

    # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
    existing_keys = set(zip(teams_df['team_id'], teams_df['season_year']))
    new_rows_filtered = new_rows[~new_rows.apply(lambda row: (row['team_id'], row['season_year']) in existing_keys, axis=1)]

    # Concatenate only if new unique rows exist
    if not new_rows_filtered.empty:
        teams_df = pd.concat([teams_df, new_rows_filtered], ignore_index=True)

    return teams_df

def fill_players_df(player_stats, players_df):

    player_ids = player_stats['PLAYER_ID'].unique()

    for player_id in player_ids:
        # Get the player data
        player_row = player_stats[player_stats['PLAYER_ID'] == player_id].iloc[0]
        full_name = player_row['PLAYER_NAME']
        name_parts = full_name.split(" ", 1)  # Split at the first space
        player_first_name = name_parts[0]  # First name (everything before the first space)
        player_last_name = name_parts[1] if len(name_parts) > 1 else ""  # Last name (everything after), or empty if no space

        # Convert the data to a data frame and concatenate it with the existing players_df
        new_row = pd.DataFrame([
            {'player_id': player_id,
            'player_first_name': player_first_name, 'player_last_name': player_last_name
            },
        ])

        # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
        existing_keys = set(zip(players_df['player_id']))
        new_rows_filtered = new_row[~new_row.apply(lambda row: (row['player_id']) in existing_keys, axis=1)]

        # Concatenate only if new unique rows exist
        if not new_rows_filtered.empty:
            players_df = pd.concat([players_df, new_rows_filtered], ignore_index=True)

    return players_df

def fill_games_df(game_id, game_date, games_df):
    season_year = get_season(game_id)
    home_team_id, away_team_id = get_home_away_team(game_id)

    # Convert the data to a data frame and concatenate it with the existing games_df
    new_row = pd.DataFrame([
        {'game_id': game_id, 'season_year': season_year, 'game_date': game_date,
        'home_team_id': home_team_id, 'away_team_id': away_team_id, 'game_time': 'Final'}
    ])

    # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
    existing_keys = set(zip(games_df['game_id'], games_df['season_year']))
    new_rows_filtered = new_row[~new_row.apply(lambda row: (row['game_id'], row['season_year']) in existing_keys, axis=1)]

    # Concatenate only if new unique rows exist
    if not new_rows_filtered.empty:
        games_df = pd.concat([games_df, new_rows_filtered], ignore_index=True)

    return games_df

def get_player_game_stats(game_id, player_stats, player_game_stats_df):
    player_ids = player_stats['PLAYER_ID'].unique()

    columns_to_keep = [
        "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", 
        "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", 
        "BLK", "TO", "PF", "PTS", "PLUS_MINUS"
    ]

    for player_id in player_ids:
        player_row = player_stats[player_stats['PLAYER_ID'] == player_id].iloc[0]

        # Get the player stats in JSON format
        player_stats_json = player_row.to_dict()

        # Filter the data
        player_stats_json = {key: player_stats_json[key] for key in columns_to_keep if key in player_stats_json} 
        player_stats_json = json.dumps(player_stats_json)  # Convert to JSON string

        

        # Convert the data to a data frame and concatenate it with the existing player_game_stats_df
        new_row = pd.DataFrame([
            {'game_id': game_id, 'player_id': player_id, 'team_id': player_row['TEAM_ID'], 
            'player_game_stats': player_stats_json}
        ])

        # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
        existing_keys = set(zip(player_game_stats_df['game_id'], player_game_stats_df['player_id']))
        new_rows_filtered = new_row[~new_row.apply(lambda row: (row['game_id'], row['player_id']) in existing_keys, axis=1)]

        # Concatenate only if new unique rows exist
        if not new_rows_filtered.empty:
            player_game_stats_df = pd.concat([player_game_stats_df, new_rows_filtered], ignore_index=True)

    return player_game_stats_df


# Function to simulate an API request with retries and exponential backoff
def fetch_with_retry(func, *args, **kwargs):
    retries = 20  # Number of retries
    delay = 1  # Initial delay time in seconds
    for attempt in range(retries):
        try:
            # Call the original function with passed arguments and keyword arguments
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                print(f"Error inside retry fn: {e}. Retrying in {delay}s...")
                #print the current time
                print(time.strftime('%X %x %Z'))
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"Failed after {retries} attempts: {e}")
                return None
            
def check_dfs(dfs: list):
    """
    Check if the dataframes are empty or have missing values. Does not check for duplicates or mismatched ids
    """
    for df in dfs:
        if df.isnull().values.any():
            print(f"Missing values in {df.columns[df.isnull().any()].tolist()}")
            #Print the rows where these values are missing
            print(df[df.isnull().any(axis=1)])
            return False
    return True

def json_fix(df):
    # This function will clean the 'player_game_stats' column
    
    # Function to replace NaN with None in nested data structures
    def replace_nan_with_none(data):
        if isinstance(data, dict):
            return {key: replace_nan_with_none(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [replace_nan_with_none(item) for item in data]
        elif isinstance(data, float) and math.isnan(data):
            return None
        else:
            return data

    jsons = []

    # Convert the 'player_game_stats' column to a list
    stats_list = df["player_game_stats"].to_list()

    # Process each row in the list
    for stat in stats_list:
        # Convert the string to a dictionary safely
        try:
            stat_dict = json.loads(stat)  # Safely parse the JSON string into a dictionary
            # Replace NaN values with None recursively
            stat_dict = replace_nan_with_none(stat_dict)
            # Convert back to a JSON string
            stat_dict = json.dumps(stat_dict)
            jsons.append(stat_dict)
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {stat}")
            jsons.append(None)  # In case of an error, append None

    # Drop the old column and add the new one
    df = df.drop(columns=["player_game_stats"])
    df["player_game_stats"] = jsons

    return df


import sys
def fill_games_df_v1(boxscore, games_df):

    games = boxscore.get_dict()

    for game in games['scoreboard']['games']:

        game_id = game['gameId']
        game_date = game['gameEt']
        # Turn 2025-04-10T23:00:00Z into a date object -- truncate time
        game_date = game_date.split("T")[0]
        game_date = date.fromisoformat(game_date)
        game_date = game_date.strftime("%Y-%m-%d")

        game_time = game['gameEt']

        #Convert to just the time -- and am/pm format and remove seconds
        game_time = game_time.split("T")[1]
        game_time = game_time.split(".")[0]
        game_time = game_time.split(":")
        game_time = f"{int(game_time[0]) % 12}:{game_time[1]} {['am', 'pm'][int(game_time[0]) // 12]} ET"

        home_team_id = game['homeTeam']['teamId']
        away_team_id = game['awayTeam']['teamId']

        season_year = get_season(game_id)
        
        new_row = pd.DataFrame([
            {'game_id': game_id, 'season_year': season_year, 'game_date': game_date,
            'home_team_id': home_team_id, 'away_team_id': away_team_id, 'game_time': game_time}
        ])

        # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
        existing_keys = set(zip(games_df['game_id'], games_df['season_year']))
        new_rows_filtered = new_row[~new_row.apply(lambda row: (row['game_id'], row['season_year']) in existing_keys, axis=1)]

        # Concatenate only if new unique rows exist
        if not new_rows_filtered.empty:
            games_df = pd.concat([games_df, new_rows_filtered], ignore_index=True)

    return games_df

def fill_teams_df_v1(boxscore, teams_df):

    games = boxscore.get_dict()

    for game in games['scoreboard']['games']:

        game_id = game['gameId']
        season_year = get_season(game_id)
        home_team = game['homeTeam']
        away_team = game['awayTeam']


        
        # Convert the data to a data frame and concatenate it with the existing teams_df
        new_rows = pd.DataFrame([
            {'team_id': home_team["teamId"], 'season_year': season_year,
            'team_location': home_team["teamCity"], 'team_name': home_team["teamName"],
            'team_abbreviation': home_team["teamTricode"]},

            {'team_id': away_team["teamId"], 'season_year': season_year,
            'team_location': away_team["teamCity"], 'team_name': away_team["teamName"],
            'team_abbreviation': away_team["teamTricode"]},
        ])

        # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
        existing_keys = set(zip(teams_df['team_id'], teams_df['season_year']))
        new_rows_filtered = new_rows[~new_rows.apply(lambda row: (row['team_id'], row['season_year']) in existing_keys, axis=1)]

        # Concatenate only if new unique rows exist
        if not new_rows_filtered.empty:
            teams_df = pd.concat([teams_df, new_rows_filtered], ignore_index=True)
        
    return teams_df

def fill_games_df_future(games, games_df):
    
    for _, game in games.iterrows()   : 
        game_id = game['GAME_ID']
        game_date = game['GAME_DATE_EST']
        # Turn 2025-04-10T23:00:00Z into a date object -- truncate time

        game_date = game_date.split("T")[0]
        game_date = date.fromisoformat(game_date)
        game_date = game_date.strftime("%Y-%m-%d")
        

        game_time = game['GAME_STATUS_TEXT']

        home_team_id = game['HOME_TEAM_ID']
        away_team_id = game['VISITOR_TEAM_ID']
        season_year = get_season(game_id)

        new_row = pd.DataFrame([
            {'game_id': game_id, 'season_year': season_year, 'game_date': game_date,
            'home_team_id': home_team_id, 'away_team_id': away_team_id, 'game_time': game_time}
        ])

        # Ensure uniqueness before concatenation (set lookup is O(1) time complexity)
        existing_keys = set(zip(games_df['game_id'], games_df['season_year']))
        new_rows_filtered = new_row[~new_row.apply(lambda row: (row['game_id'], row['season_year']) in existing_keys, axis=1)]

        # Concatenate only if new unique rows exist
        if not new_rows_filtered.empty:
            games_df = pd.concat([games_df, new_rows_filtered], ignore_index=True)
        
    return games_df


# Since games are already in the database, we may need to update the game_time column like this
def insert_date_in_db(games_df, engine):

    for _, row in games_df.iterrows():

        with engine.connect() as connection:
            #Return the number of rows affected by the query
            ret = connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE games
                    SET game_time = :game_time
                    WHERE game_id = :game_id
                    """
                ),
                {"game_id": row['game_id'], "game_time": row['game_time']}
            )
            connection.commit()

#Literally all this does is return the database url, which we needed in multiple programs
def get_database_url(host, password, user, port=5432, db_name="oracle_db"):
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"