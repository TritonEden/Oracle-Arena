import json
import sqlalchemy
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler


def get_data_from_db():
    # Get raw tables from the database

    # If on local machine
    # with open("../.env", "r") as f:
    #     password = f.readlines()[3].strip().split("=")[1].strip() #May need to change the line number, but mine is on line 4
    password = "CS402OAAPass$"

    # If on Docker
    #import os
    #password = os.getenv('PASSWORD', '')

    DATABASE_URL = f"postgresql://rgutkeecsoraclearenaadmin:{password}@rg-utk-eecs-oracle-arena-postgresql-db.postgres.database.azure.com:5432/postgres"

    engine = sqlalchemy.create_engine(DATABASE_URL, echo=True)

    # Get the games, players, teams, and player_game_stats tables from the database -- store them into df's

    with engine.connect() as connection:
        # Read the tables into DataFrames
        games_df = pd.read_sql_table('games', connection)
        players_df = pd.read_sql_table('players', connection)
        teams_df = pd.read_sql_table('teams', connection)
        #With player game stats, we need a CTE first WITH new_player_game_stats as (
                #     SELECT DISTINCT ON (game_id, player_id) *
                #     FROM player_game_stats
                # ),

        player_game_stats_df = pd.read_sql_query("""WITH new_player_game_stats as (
                    SELECT DISTINCT ON (game_id, player_id) *
                    FROM player_game_stats
                ) SELECT * FROM new_player_game_stats""", connection)

    return games_df, player_game_stats_df

def winpred_reg_data(games_df, player_game_stats_df):
    # Load datasets
    games = games_df
    player_stats = player_game_stats_df

    # Filter for regular season games only
    games["game_id"] = games["game_id"].astype(str)
    player_stats["game_id"] = player_stats["game_id"].astype(str)
    games = games[games["game_id"].str.startswith("2")]
    player_stats = player_stats[player_stats["game_id"].str.startswith("2")]

    # Melt games dataframe for team-wise games played
    games_melted = games.melt(id_vars=["game_id", "season_year"], 
                            value_vars=["home_team_id", "away_team_id"],
                            value_name="team_id")

    # Count games played per team per season
    games_played = games_melted.groupby(["season_year", "team_id"])["game_id"].nunique().reset_index()
    games_played.rename(columns={"game_id": "games_played"}, inplace=True)

    # Parse nested player stats
    player_stats['player_game_stats'] = player_stats['player_game_stats'].apply(json.loads)
    player_stats = player_stats.dropna(subset=['player_game_stats']).copy()
    player_stats = pd.concat(
        [player_stats.drop(columns=['player_game_stats']), 
        player_stats['player_game_stats'].apply(pd.Series)], 
        axis=1
    )

    # Merge season info
    player_stats = player_stats.merge(games[['game_id', 'season_year']], on='game_id', how='left')

    # Define stat columns
    stats_columns = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 
                    'OREB', 'DREB', 'AST', 'STL', 'BLK', 
                    'TO', 'PTS']

    # Filter and aggregate player stats
    player_stats = player_stats[['season_year', 'game_id', 'team_id'] + stats_columns]
    team_stats = player_stats.groupby(['game_id', 'team_id'])[stats_columns].sum().reset_index()

    # Merge with games to determine home/away teams
    team_stats = team_stats.merge(
        games[['game_id', 'season_year', 'home_team_id', 'away_team_id']], 
        on='game_id', 
        how='left'
    )

    # Separate home and away stats
    home_stats = team_stats[team_stats['team_id'] == team_stats['home_team_id']]
    away_stats = team_stats[team_stats['team_id'] == team_stats['away_team_id']]

    # Rename columns
    home_stats = home_stats.rename(columns={col: col + "_home" for col in stats_columns}).drop(columns=['team_id'])
    away_stats = away_stats.rename(columns={col: col + "_away" for col in stats_columns}).drop(columns=['team_id'])

    # Merge into one row per game
    game_stats = home_stats.merge(away_stats, on=['game_id', 'season_year', 'home_team_id', 'away_team_id'], how='inner')

    # Compute outcome, 1 if home team wins, 0 otherwise
    game_stats["home_team_win"] = (game_stats["PTS_home"] > game_stats["PTS_away"]).astype(int)

    # Create a dataframe of winners
    winners = pd.DataFrame({
        "game_id": game_stats["game_id"],
        "winner_team_id": game_stats["home_team_id"].where(game_stats["home_team_win"] == 1, game_stats["away_team_id"])
    })

    # Convert to long format for modeling (Home and away team stats for each game on the rows of the model input)
    home_team_stats = game_stats[["game_id", "season_year", "home_team_id"] + [col for col in game_stats.columns if col.endswith("_home")]].copy()
    away_team_stats = game_stats[["game_id", "season_year", "away_team_id"] + [col for col in game_stats.columns if col.endswith("_away")]].copy()

    home_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_home", "") for col in home_team_stats.columns[3:]]
    away_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_away", "") for col in away_team_stats.columns[3:]]

    long_stats = pd.concat([home_team_stats, away_team_stats], axis=0).sort_values(["team_id", "season_year", "game_id"])

    # Sort by game_date in chonological order before calculating rolling averages
    long_stats = long_stats.merge(games[['game_id', 'game_date']], on='game_id', how='left')
    long_stats = long_stats.sort_values('game_date').reset_index(drop=True)

    wl_count = long_stats.copy()

    # Merge the winner lookup table into the long stats df
    wl_count = wl_count.merge(winners, on='game_id', how='left')

    # Calculate wins and losses for each team up to the current game
    wl_count["won_game"] = (wl_count["team_id"] == wl_count["winner_team_id"]).astype(int)
    wl_count["games_so_far"] = (
        wl_count.groupby(['team_id', 'season_year'])
        .cumcount()
    )
    wl_count["wins"] = (
        wl_count.groupby(['team_id', 'season_year'])["won_game"]
        .cumsum() - wl_count["won_game"]
    ).fillna(0).astype(int)
    wl_count["losses"] = (
        wl_count["games_so_far"] - wl_count["wins"]
    ).clip(lower=0).astype(int)

    # Compute number of possessions for each team (from NBA.com)
    long_stats["POSS"] = (
        (long_stats["FGA"] + 0.44 * long_stats["FTA"] - long_stats["OREB"] + long_stats["TO"])
    )
    long_stats["POSS"] = long_stats["POSS"].clip(lower=0)  # Ensure there are no negative possession values

    # Compute per 100 possession stats
    per_100_columns = [stat + "_100" for stat in stats_columns]
    for stat in stats_columns:
        long_stats[stat + "_100"] = 100 * long_stats[stat] / long_stats["POSS"]

    # Add the possession stat to per_100_columns so we can compute rolling averages for it
    per_100_columns.append("POSS")

    # Compute rolling averages of per-100-possession stats
    def compute_rolling_averages(group):
        return group[per_100_columns].shift().expanding().mean()

    long_stats_avg = long_stats.copy()
    long_stats_avg[per_100_columns] = long_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)
    long_stats_avg.drop(columns=stats_columns, inplace=True)

    # Fallback: previous season average per-100 stats
    prev_season_averages = long_stats.groupby(["team_id", "season_year"])[per_100_columns].mean().reset_index()

    def shift_season(season_str):
        start, end = season_str.split("-")
        next_start = str(int(start) + 1)
        next_end = str(int(end[-2:]) + 1).zfill(2)
        return f"{next_start}-{next_end}"

    prev_season_averages["season_year"] = prev_season_averages["season_year"].apply(shift_season)

    long_stats_avg = long_stats_avg.merge(
        prev_season_averages,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback")
    )

    for stat in per_100_columns:
        long_stats_avg[stat] = long_stats_avg[stat].fillna(long_stats_avg[f"{stat}_fallback"])
        long_stats_avg.drop(columns=[f"{stat}_fallback"], inplace=True)

    long_stats_avg.dropna(inplace=True)

    last_5_games = long_stats.merge(wl_count[['game_id', 'team_id', 'wins', 'losses', 'won_game']], 
                              on=['game_id', 'team_id'], how='left')

    # Define which columns to roll over
    rolling_features = per_100_columns  # exclude 'won_game' for mean calculations

    # Rolling mean stats over the last 5 games (using only previous games)
    rolling_means = (
        last_5_games.groupby(['team_id', 'season_year'])[rolling_features]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    rolling_wins = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    rolling_losses = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: (1 - x.shift(1)).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    # Merge based on index (team_id, season_year, original index inside group)
    rolling_5 = pd.concat(
        [
            rolling_means.rename(columns={col: f"rolling_{col}_last5" for col in rolling_means.columns}),
            rolling_wins.rename('rolling_wins_last5'),
            rolling_losses.rename('rolling_losses_last5')
        ],
        axis=1
    )

    # Now merge back safely (indexes match)
    last_5_games = pd.concat([last_5_games, rolling_5], axis=1)

    # Merge previous season averages as fallback
    last_5_games = last_5_games.merge(
        prev_season_averages[['team_id', 'season_year'] + per_100_columns],
        on=['team_id', 'season_year'],
        how='left',
        suffixes=('', '_fallback')
    )

    # Fill rolling columns using fallback columns
    for col in [f"rolling_{stat}_last5" for stat in per_100_columns] + ['rolling_wins_last5', 'rolling_losses_last5']:
        fallback_col = col.replace('rolling_', '').replace('_last5', '') + '_fallback'
        if fallback_col in last_5_games.columns:
            last_5_games[col] = last_5_games[col].fillna(last_5_games[fallback_col])

    # Drop all *_fallback columns
    last_5_games.drop(columns=[c for c in last_5_games.columns if c.endswith('_fallback')], inplace=True)

    opponent_allowed_columns = [stat + "_allowed" for stat in per_100_columns]

    # Create df to store stats from the opposing team
    opponent_stats = long_stats[["game_id", "team_id", "game_date"] + per_100_columns].copy()
    opponent_stats = opponent_stats.rename(columns={col: col + "_allowed" for col in per_100_columns})

    # Pair each team with their opponent in the same game
    team_allowed_stats = long_stats[["game_id", "team_id", "season_year"]].merge(
        opponent_stats, on="game_id", suffixes=("", "_opp")
    )

    # Only keep rows where the opponent is different (i.e., get opponent stats)
    team_allowed_stats = team_allowed_stats[team_allowed_stats["team_id"] != team_allowed_stats["team_id_opp"]]

    # It doesn't matter who the opponenet in each game is so we can drop this column now
    team_allowed_stats.drop("team_id_opp", axis=1, inplace=True)

    def compute_rolling_averages(group):
        return group[opponent_allowed_columns].shift().expanding().mean()

    # Compute rolling averages of per-100-possession allowed stats
    team_allowed_stats[opponent_allowed_columns] = team_allowed_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)

    # Compute season averages of opponent stats allowed
    season_allowed_stats = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .mean()
        .reset_index()
    )

    # Fallback: previous season average per-100 allowed stats
    prev_allowed = season_allowed_stats.copy()
    prev_allowed["season_year"] = prev_allowed["season_year"].apply(shift_season)

    team_allowed_stats = team_allowed_stats.merge(
        prev_allowed,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback"),
    )

    # Fill any missing values in the allowed stats with fallback season averages
    for stat in opponent_allowed_columns:
        team_allowed_stats[stat] = team_allowed_stats[stat].fillna(team_allowed_stats[f"{stat}_fallback"])
        team_allowed_stats.drop(columns=[f"{stat}_fallback"], inplace=True)

    # Drop the first first game from the first season for each team in the database because is has no fallback
    team_allowed_stats.dropna(inplace=True)

    # Calculate rolling means of opponent stats allowed over past 5 games
    rolling_allowed_means = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    # Combine rolling and fallback for each stat
    for stat in per_100_columns:
        col = f"{stat}_allowed"
        rolling_col = f"rolling_{col}_last5"
        
        team_allowed_stats[rolling_col] = rolling_allowed_means[col].fillna(team_allowed_stats[col])

    # Final cleanup: drop any rows that still have NaNs in important rolling stats
    rolling_allowed_cols = [f"rolling_{stat}_allowed_last5" for stat in per_100_columns]
    team_allowed_stats.dropna(subset=rolling_allowed_cols, inplace=True)

    # Drop unneeded columns
    team_allowed_stats.drop(['season_year', 'game_date'], axis=1, inplace=True)

    # Add rolling stats for the last 5 games
    # First select only the rolling columns + game_id and team_id
    rolling_cols = ['game_id', 'team_id'] + [col for col in last_5_games.columns if col.startswith('rolling_')]

    # Pull out the rolling columns
    rolling_features_data = last_5_games[rolling_cols]

    # Merge rolling_features with long_stats_avg df
    long_stats_avg = long_stats_avg.merge(rolling_features_data, on=["game_id", "team_id"], how='left')

    # Add allowed stats to the df
    long_stats_avg = long_stats_avg.merge(team_allowed_stats, on=["game_id", "team_id"], how="left")

    # Drop the columns from the first 5 games for each team in the 2018-19 season
    long_stats_avg.dropna(inplace=True)

    # Home/Away features
    home_features = long_stats_avg.merge(game_stats[['game_id', 'home_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'home_team_id'], how='inner').drop(columns=['home_team_id'])
    away_features = long_stats_avg.merge(game_stats[['game_id', 'away_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'away_team_id'], how='inner').drop(columns=['away_team_id'])

    # Add wins and losses to home and away features
    home_features = home_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')
    away_features = away_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')

    # Rename the columns for home and away features
    exclude = {'game_id', 'season_year', 'team_id', 'game_date'}
    home_features.columns = [
        f"{col}_home" if col not in exclude else col
        for col in home_features.columns
    ]
    away_features.columns = [
        f"{col}_away" if col not in exclude else col
        for col in away_features.columns
    ]

    # Merge features
    ml_df = home_features.merge(away_features, on=["game_id", "game_date"], how="inner").merge(
        game_stats[["game_id", "home_team_win"]],
        on="game_id", how="inner"
    )
    ml_df = ml_df.drop_duplicates('game_id')

    # Clean up
    ml_df = ml_df.drop(columns=["team_id_x", "team_id_y", "season_year_x", "season_year_y"], errors='ignore')
    X = ml_df.drop(columns=["game_id", "home_team_win"])
    y = ml_df[["home_team_win", "game_date"]]
    
    return X, y

def winpred_playoff_data(games_df, player_game_stats_df):
    # Load datasets
    games = games_df
    player_stats = player_game_stats_df

    # Filter for regular season and playoff games
    games["game_id"] = games["game_id"].astype(str)
    player_stats["game_id"] = player_stats["game_id"].astype(str)
    games = games[games["game_id"].str.startswith(("2", "4"))]
    player_stats = player_stats[player_stats["game_id"].str.startswith(("2", "4"))]

    # Melt games dataframe for team-wise games played
    games_melted = games.melt(id_vars=["game_id", "season_year"], 
                            value_vars=["home_team_id", "away_team_id"],
                            value_name="team_id")

    # Count games played per team per season
    games_played = games_melted.groupby(["season_year", "team_id"])["game_id"].nunique().reset_index()
    games_played.rename(columns={"game_id": "games_played"}, inplace=True)

    # Parse nested player stats
    player_stats['player_game_stats'] = player_stats['player_game_stats'].apply(json.loads)
    player_stats = player_stats.dropna(subset=['player_game_stats']).copy()
    player_stats = pd.concat(
        [player_stats.drop(columns=['player_game_stats']), 
        player_stats['player_game_stats'].apply(pd.Series)], 
        axis=1
    )

    # Merge season info
    player_stats = player_stats.merge(games[['game_id', 'season_year']], on='game_id', how='left')

    # Define stat columns
    stats_columns = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 
                    'OREB', 'DREB', 'AST', 'STL', 'BLK', 
                    'TO', 'PTS']

    # Filter and aggregate player stats
    player_stats = player_stats[['season_year', 'game_id', 'team_id'] + stats_columns]
    team_stats = player_stats.groupby(['game_id', 'team_id'])[stats_columns].sum().reset_index()

    # Merge with games to determine home/away teams
    team_stats = team_stats.merge(
        games[['game_id', 'season_year', 'home_team_id', 'away_team_id']], 
        on='game_id', 
        how='left'
    )

    # Separate home and away stats
    home_stats = team_stats[team_stats['team_id'] == team_stats['home_team_id']]
    away_stats = team_stats[team_stats['team_id'] == team_stats['away_team_id']]

    # Rename columns
    home_stats = home_stats.rename(columns={col: col + "_home" for col in stats_columns}).drop(columns=['team_id'])
    away_stats = away_stats.rename(columns={col: col + "_away" for col in stats_columns}).drop(columns=['team_id'])

    # Merge into one row per game
    game_stats = home_stats.merge(away_stats, on=['game_id', 'season_year', 'home_team_id', 'away_team_id'], how='inner')

    # Compute outcome, 1 if home team wins, 0 otherwise
    game_stats["home_team_win"] = (game_stats["PTS_home"] > game_stats["PTS_away"]).astype(int)

    # Create a dataframe of winners
    winners = pd.DataFrame({
        "game_id": game_stats["game_id"],
        "winner_team_id": game_stats["home_team_id"].where(game_stats["home_team_win"] == 1, game_stats["away_team_id"])
    })

    # Convert to long format for modeling (Home and away team stats for each game on the rows of the model input)
    home_team_stats = game_stats[["game_id", "season_year", "home_team_id"] + [col for col in game_stats.columns if col.endswith("_home")]].copy()
    away_team_stats = game_stats[["game_id", "season_year", "away_team_id"] + [col for col in game_stats.columns if col.endswith("_away")]].copy()

    home_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_home", "") for col in home_team_stats.columns[3:]]
    away_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_away", "") for col in away_team_stats.columns[3:]]

    long_stats = pd.concat([home_team_stats, away_team_stats], axis=0).sort_values(["team_id", "season_year", "game_id"])

    # Sort by game_date in chonological order before calculating rolling averages
    long_stats = long_stats.merge(games[['game_id', 'game_date']], on='game_id', how='left')
    long_stats = long_stats.sort_values('game_date').reset_index(drop=True)

    wl_count = long_stats.copy()

    # Merge the winner lookup table into the long stats df
    wl_count = wl_count.merge(winners, on='game_id', how='left')

    # Calculate wins and losses for each team up to the current game
    wl_count["won_game"] = (wl_count["team_id"] == wl_count["winner_team_id"]).astype(int)
    wl_count["games_so_far"] = (
        wl_count.groupby(['team_id', 'season_year'])
        .cumcount()
    )
    wl_count["wins"] = (
        wl_count.groupby(['team_id', 'season_year'])["won_game"]
        .cumsum() - wl_count["won_game"]
    ).fillna(0).astype(int)
    wl_count["losses"] = (
        wl_count["games_so_far"] - wl_count["wins"]
    ).clip(lower=0).astype(int)

    # Compute number of possessions for each team (from NBA.com)
    long_stats["POSS"] = (
        (long_stats["FGA"] + 0.44 * long_stats["FTA"] - long_stats["OREB"] + long_stats["TO"])
    )
    long_stats["POSS"] = long_stats["POSS"].clip(lower=0)  # Ensure there are no negative possession values

    # Compute per 100 possession stats
    per_100_columns = [stat + "_100" for stat in stats_columns]
    for stat in stats_columns:
        long_stats[stat + "_100"] = 100 * long_stats[stat] / long_stats["POSS"]

    # Add the possession stat to per_100_columns so we can compute rolling averages for it
    per_100_columns.append("POSS")

    # Compute rolling averages of per-100-possession stats
    def compute_rolling_averages(group):
        return group[per_100_columns].shift().expanding().mean()

    long_stats_avg = long_stats.copy()
    long_stats_avg[per_100_columns] = long_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)
    long_stats_avg.drop(columns=stats_columns, inplace=True)

    # Fallback: previous season average per-100 stats
    prev_season_averages = long_stats.groupby(["team_id", "season_year"])[per_100_columns].mean().reset_index()

    def shift_season(season_str):
        start, end = season_str.split("-")
        next_start = str(int(start) + 1)
        next_end = str(int(end[-2:]) + 1).zfill(2)
        return f"{next_start}-{next_end}"

    prev_season_averages["season_year"] = prev_season_averages["season_year"].apply(shift_season)

    long_stats_avg = long_stats_avg.merge(
        prev_season_averages,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback")
    )

    for stat in per_100_columns:
        long_stats_avg[stat] = long_stats_avg[stat].fillna(long_stats_avg[f"{stat}_fallback"])
        long_stats_avg.drop(columns=[f"{stat}_fallback"], inplace=True)

    long_stats_avg.dropna(inplace=True)

    last_5_games = long_stats.merge(wl_count[['game_id', 'team_id', 'wins', 'losses', 'won_game']], 
                              on=['game_id', 'team_id'], how='left')

    # Define which columns to roll over
    rolling_features = per_100_columns  # exclude 'won_game' for mean calculations

    # Rolling mean stats over the last 5 games (using only previous games)
    rolling_means = (
        last_5_games.groupby(['team_id', 'season_year'])[rolling_features]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    rolling_wins = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    rolling_losses = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: (1 - x.shift(1)).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    # Merge based on index (team_id, season_year, original index inside group)
    rolling_5 = pd.concat(
        [
            rolling_means.rename(columns={col: f"rolling_{col}_last5" for col in rolling_means.columns}),
            rolling_wins.rename('rolling_wins_last5'),
            rolling_losses.rename('rolling_losses_last5')
        ],
        axis=1
    )

    # Now merge back safely (indexes match)
    last_5_games = pd.concat([last_5_games, rolling_5], axis=1)

    # Merge previous season averages as fallback
    last_5_games = last_5_games.merge(
        prev_season_averages[['team_id', 'season_year'] + per_100_columns],
        on=['team_id', 'season_year'],
        how='left',
        suffixes=('', '_fallback')
    )

    # Fill rolling columns using fallback columns
    for col in [f"rolling_{stat}_last5" for stat in per_100_columns] + ['rolling_wins_last5', 'rolling_losses_last5']:
        fallback_col = col.replace('rolling_', '').replace('_last5', '') + '_fallback'
        if fallback_col in last_5_games.columns:
            last_5_games[col] = last_5_games[col].fillna(last_5_games[fallback_col])

    # Drop all *_fallback columns
    last_5_games.drop(columns=[c for c in last_5_games.columns if c.endswith('_fallback')], inplace=True)

    opponent_allowed_columns = [stat + "_allowed" for stat in per_100_columns]

    # Create df to store stats from the opposing team
    opponent_stats = long_stats[["game_id", "team_id", "game_date"] + per_100_columns].copy()
    opponent_stats = opponent_stats.rename(columns={col: col + "_allowed" for col in per_100_columns})

    # Pair each team with their opponent in the same game
    team_allowed_stats = long_stats[["game_id", "team_id", "season_year"]].merge(
        opponent_stats, on="game_id", suffixes=("", "_opp")
    )

    # Only keep rows where the opponent is different (i.e., get opponent stats)
    team_allowed_stats = team_allowed_stats[team_allowed_stats["team_id"] != team_allowed_stats["team_id_opp"]]

    # It doesn't matter who the opponenet in each game is so we can drop this column now
    team_allowed_stats.drop("team_id_opp", axis=1, inplace=True)

    def compute_rolling_averages(group):
        return group[opponent_allowed_columns].shift().expanding().mean()

    # Compute rolling averages of per-100-possession allowed stats
    team_allowed_stats[opponent_allowed_columns] = team_allowed_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)

    # Compute season averages of opponent stats allowed
    season_allowed_stats = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .mean()
        .reset_index()
    )

    # Fallback: previous season average per-100 allowed stats
    prev_allowed = season_allowed_stats.copy()
    prev_allowed["season_year"] = prev_allowed["season_year"].apply(shift_season)

    team_allowed_stats = team_allowed_stats.merge(
        prev_allowed,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback"),
    )

    # Fill any missing values in the allowed stats with fallback season averages
    for stat in opponent_allowed_columns:
        team_allowed_stats[stat] = team_allowed_stats[stat].fillna(team_allowed_stats[f"{stat}_fallback"])
        team_allowed_stats.drop(columns=[f"{stat}_fallback"], inplace=True)

    # Drop the first first game from the first season for each team in the database because is has no fallback
    team_allowed_stats.dropna(inplace=True)

    # Calculate rolling means of opponent stats allowed over past 5 games
    rolling_allowed_means = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    # Combine rolling and fallback for each stat
    for stat in per_100_columns:
        col = f"{stat}_allowed"
        rolling_col = f"rolling_{col}_last5"
        
        team_allowed_stats[rolling_col] = rolling_allowed_means[col].fillna(team_allowed_stats[col])

    # Final cleanup: drop any rows that still have NaNs in important rolling stats
    rolling_allowed_cols = [f"rolling_{stat}_allowed_last5" for stat in per_100_columns]
    team_allowed_stats.dropna(subset=rolling_allowed_cols, inplace=True)

    # Drop unneeded columns
    team_allowed_stats.drop(['season_year', 'game_date'], axis=1, inplace=True)

    # Add rolling stats for the last 5 games
    # First select only the rolling columns + game_id and team_id
    rolling_cols = ['game_id', 'team_id'] + [col for col in last_5_games.columns if col.startswith('rolling_')]

    # Pull out the rolling columns
    rolling_features_data = last_5_games[rolling_cols]

    # Merge rolling_features with long_stats_avg df
    long_stats_avg = long_stats_avg.merge(rolling_features_data, on=["game_id", "team_id"], how='left')

    # Add allowed stats to the df
    long_stats_avg = long_stats_avg.merge(team_allowed_stats, on=["game_id", "team_id"], how="left")

    # Drop the columns from the first 5 games for each team in the 2018-19 season
    long_stats_avg.dropna(inplace=True)

    # Home/Away features
    home_features = long_stats_avg.merge(game_stats[['game_id', 'home_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'home_team_id'], how='inner').drop(columns=['home_team_id'])
    away_features = long_stats_avg.merge(game_stats[['game_id', 'away_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'away_team_id'], how='inner').drop(columns=['away_team_id'])

    # Add wins and losses to home and away features
    home_features = home_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')
    away_features = away_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')

    # Rename the columns for home and away features
    exclude = {'game_id', 'season_year', 'team_id', 'game_date'}
    home_features.columns = [
        f"{col}_home" if col not in exclude else col
        for col in home_features.columns
    ]
    away_features.columns = [
        f"{col}_away" if col not in exclude else col
        for col in away_features.columns
    ]

    # Merge features
    ml_df = home_features.merge(away_features, on=["game_id", "game_date"], how="inner").merge(
        game_stats[["game_id", "home_team_win"]],
        on="game_id", how="inner"
    )
    ml_df = ml_df.drop_duplicates('game_id')

    # Only include playoff games in the model input
    ml_df = ml_df[ml_df["game_id"].str.startswith("4")]

    # Clean up
    ml_df = ml_df.drop(columns=["team_id_x", "team_id_y", "season_year_x", "season_year_y"], errors='ignore')
    X = ml_df.drop(columns=["game_id", "home_team_win"])
    y = ml_df[["home_team_win", "game_date"]]

    return X, y

def pointspred_reg_data(games_df, player_game_stats_df):
    # Load datasets
    games = games_df
    player_stats = player_game_stats_df

    # Filter for regular season games only
    games["game_id"] = games["game_id"].astype(str)
    player_stats["game_id"] = player_stats["game_id"].astype(str)
    games = games[games["game_id"].str.startswith("2")]
    player_stats = player_stats[player_stats["game_id"].str.startswith("2")]

    # Melt games dataframe for team-wise games played
    games_melted = games.melt(id_vars=["game_id", "season_year"], 
                            value_vars=["home_team_id", "away_team_id"],
                            value_name="team_id")

    # Count games played per team per season
    games_played = games_melted.groupby(["season_year", "team_id"])["game_id"].nunique().reset_index()
    games_played.rename(columns={"game_id": "games_played"}, inplace=True)

    # Parse nested player stats
    player_stats['player_game_stats'] = player_stats['player_game_stats'].apply(json.loads)
    player_stats = player_stats.dropna(subset=['player_game_stats']).copy()
    player_stats = pd.concat(
        [player_stats.drop(columns=['player_game_stats']), 
        player_stats['player_game_stats'].apply(pd.Series)], 
        axis=1
    )

    # Merge season info
    player_stats = player_stats.merge(games[['game_id', 'season_year']], on='game_id', how='left')

    # Define stat columns
    stats_columns = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 
                    'OREB', 'DREB', 'AST', 'STL', 'BLK', 
                    'TO', 'PTS']

    # Filter and aggregate player stats
    player_stats = player_stats[['season_year', 'game_id', 'team_id'] + stats_columns]
    team_stats = player_stats.groupby(['game_id', 'team_id'])[stats_columns].sum().reset_index()

    # Merge with games to determine home/away teams
    team_stats = team_stats.merge(
        games[['game_id', 'season_year', 'home_team_id', 'away_team_id']], 
        on='game_id', 
        how='left'
    )

    # Separate home and away stats
    home_stats = team_stats[team_stats['team_id'] == team_stats['home_team_id']]
    away_stats = team_stats[team_stats['team_id'] == team_stats['away_team_id']]

    # Rename columns
    home_stats = home_stats.rename(columns={col: col + "_home" for col in stats_columns}).drop(columns=['team_id'])
    away_stats = away_stats.rename(columns={col: col + "_away" for col in stats_columns}).drop(columns=['team_id'])

    # Merge into one row per game
    game_stats = home_stats.merge(away_stats, on=['game_id', 'season_year', 'home_team_id', 'away_team_id'], how='inner')

    # Compute outcome, 1 if home team wins, 0 otherwise
    game_stats["home_team_win"] = (game_stats["PTS_home"] > game_stats["PTS_away"]).astype(int)

    # Compute total score
    game_stats["total_score"] = (game_stats["PTS_home"] + game_stats["PTS_away"]).astype(int)

    # Create a dataframe of winners
    winners = pd.DataFrame({
        "game_id": game_stats["game_id"],
        "winner_team_id": game_stats["home_team_id"].where(game_stats["home_team_win"] == 1, game_stats["away_team_id"])
    })

    # Convert to long format for modeling (Home and away team stats for each game on the rows of the model input)
    home_team_stats = game_stats[["game_id", "season_year", "home_team_id"] + [col for col in game_stats.columns if col.endswith("_home")]].copy()
    away_team_stats = game_stats[["game_id", "season_year", "away_team_id"] + [col for col in game_stats.columns if col.endswith("_away")]].copy()

    home_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_home", "") for col in home_team_stats.columns[3:]]
    away_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_away", "") for col in away_team_stats.columns[3:]]

    long_stats = pd.concat([home_team_stats, away_team_stats], axis=0).sort_values(["team_id", "season_year", "game_id"])

    # Sort by game_date in chonological order before calculating rolling averages
    long_stats = long_stats.merge(games[['game_id', 'game_date']], on='game_id', how='left')
    long_stats = long_stats.sort_values('game_date').reset_index(drop=True)

    wl_count = long_stats.copy()

    # Merge the winner lookup table into the long stats df
    wl_count = wl_count.merge(winners, on='game_id', how='left')

    # Calculate wins and losses for each team up to the current game
    wl_count["won_game"] = (wl_count["team_id"] == wl_count["winner_team_id"]).astype(int)
    wl_count["games_so_far"] = (
        wl_count.groupby(['team_id', 'season_year'])
        .cumcount()
    )
    wl_count["wins"] = (
        wl_count.groupby(['team_id', 'season_year'])["won_game"]
        .cumsum() - wl_count["won_game"]
    ).fillna(0).astype(int)
    wl_count["losses"] = (
        wl_count["games_so_far"] - wl_count["wins"]
    ).clip(lower=0).astype(int)

    # Compute number of possessions for each team (from NBA.com)
    long_stats["POSS"] = (
        (long_stats["FGA"] + 0.44 * long_stats["FTA"] - long_stats["OREB"] + long_stats["TO"])
    )
    long_stats["POSS"] = long_stats["POSS"].clip(lower=0)  # Ensure there are no negative possession values

    # Compute per 100 possession stats
    per_100_columns = [stat + "_100" for stat in stats_columns]
    for stat in stats_columns:
        long_stats[stat + "_100"] = 100 * long_stats[stat] / long_stats["POSS"]

    # Add the possession stat to per_100_columns so we can compute rolling averages for it
    per_100_columns.append("POSS")

    # Compute rolling averages of per-100-possession stats
    def compute_rolling_averages(group):
        return group[per_100_columns].shift().expanding().mean()

    long_stats_avg = long_stats.copy()
    long_stats_avg[per_100_columns] = long_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)
    long_stats_avg.drop(columns=stats_columns, inplace=True)

    # Fallback: previous season average per-100 stats
    prev_season_averages = long_stats.groupby(["team_id", "season_year"])[per_100_columns].mean().reset_index()

    def shift_season(season_str):
        start, end = season_str.split("-")
        next_start = str(int(start) + 1)
        next_end = str(int(end[-2:]) + 1).zfill(2)
        return f"{next_start}-{next_end}"

    prev_season_averages["season_year"] = prev_season_averages["season_year"].apply(shift_season)

    long_stats_avg = long_stats_avg.merge(
        prev_season_averages,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback")
    )

    for stat in per_100_columns:
        long_stats_avg[stat] = long_stats_avg[stat].fillna(long_stats_avg[f"{stat}_fallback"])
        long_stats_avg.drop(columns=[f"{stat}_fallback"], inplace=True)

    long_stats_avg.dropna(inplace=True)

    last_5_games = long_stats.merge(wl_count[['game_id', 'team_id', 'wins', 'losses', 'won_game']], 
                              on=['game_id', 'team_id'], how='left')

    # Define which columns to roll over
    rolling_features = per_100_columns  # exclude 'won_game' for mean calculations

    # Rolling mean stats over the last 5 games (using only previous games)
    rolling_means = (
        last_5_games.groupby(['team_id', 'season_year'])[rolling_features]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    rolling_wins = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    rolling_losses = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: (1 - x.shift(1)).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    # Merge based on index (team_id, season_year, original index inside group)
    rolling_5 = pd.concat(
        [
            rolling_means.rename(columns={col: f"rolling_{col}_last5" for col in rolling_means.columns}),
            rolling_wins.rename('rolling_wins_last5'),
            rolling_losses.rename('rolling_losses_last5')
        ],
        axis=1
    )

    # Now merge back safely (indexes match)
    last_5_games = pd.concat([last_5_games, rolling_5], axis=1)

    # Merge previous season averages as fallback
    last_5_games = last_5_games.merge(
        prev_season_averages[['team_id', 'season_year'] + per_100_columns],
        on=['team_id', 'season_year'],
        how='left',
        suffixes=('', '_fallback')
    )

    # Fill rolling columns using fallback columns
    for col in [f"rolling_{stat}_last5" for stat in per_100_columns] + ['rolling_wins_last5', 'rolling_losses_last5']:
        fallback_col = col.replace('rolling_', '').replace('_last5', '') + '_fallback'
        if fallback_col in last_5_games.columns:
            last_5_games[col] = last_5_games[col].fillna(last_5_games[fallback_col])

    # Drop all *_fallback columns
    last_5_games.drop(columns=[c for c in last_5_games.columns if c.endswith('_fallback')], inplace=True)

    opponent_allowed_columns = [stat + "_allowed" for stat in per_100_columns]

    # Create df to store stats from the opposing team
    opponent_stats = long_stats[["game_id", "team_id", "game_date"] + per_100_columns].copy()
    opponent_stats = opponent_stats.rename(columns={col: col + "_allowed" for col in per_100_columns})

    # Pair each team with their opponent in the same game
    team_allowed_stats = long_stats[["game_id", "team_id", "season_year"]].merge(
        opponent_stats, on="game_id", suffixes=("", "_opp")
    )

    # Only keep rows where the opponent is different (i.e., get opponent stats)
    team_allowed_stats = team_allowed_stats[team_allowed_stats["team_id"] != team_allowed_stats["team_id_opp"]]

    # It doesn't matter who the opponenet in each game is so we can drop this column now
    team_allowed_stats.drop("team_id_opp", axis=1, inplace=True)

    def compute_rolling_averages(group):
        return group[opponent_allowed_columns].shift().expanding().mean()

    # Compute rolling averages of per-100-possession allowed stats
    team_allowed_stats[opponent_allowed_columns] = team_allowed_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)

    # Compute season averages of opponent stats allowed
    season_allowed_stats = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .mean()
        .reset_index()
    )

    # Fallback: previous season average per-100 allowed stats
    prev_allowed = season_allowed_stats.copy()
    prev_allowed["season_year"] = prev_allowed["season_year"].apply(shift_season)

    team_allowed_stats = team_allowed_stats.merge(
        prev_allowed,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback"),
    )

    # Fill any missing values in the allowed stats with fallback season averages
    for stat in opponent_allowed_columns:
        team_allowed_stats[stat] = team_allowed_stats[stat].fillna(team_allowed_stats[f"{stat}_fallback"])
        team_allowed_stats.drop(columns=[f"{stat}_fallback"], inplace=True)

    # Drop the first first game from the first season for each team in the database because is has no fallback
    team_allowed_stats.dropna(inplace=True)

    # Calculate rolling means of opponent stats allowed over past 5 games
    rolling_allowed_means = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    # Combine rolling and fallback for each stat
    for stat in per_100_columns:
        col = f"{stat}_allowed"
        rolling_col = f"rolling_{col}_last5"
        
        team_allowed_stats[rolling_col] = rolling_allowed_means[col].fillna(team_allowed_stats[col])

    # Final cleanup: drop any rows that still have NaNs in important rolling stats
    rolling_allowed_cols = [f"rolling_{stat}_allowed_last5" for stat in per_100_columns]
    team_allowed_stats.dropna(subset=rolling_allowed_cols, inplace=True)

    # Drop unneeded columns
    team_allowed_stats.drop(['season_year', 'game_date'], axis=1, inplace=True)

    # Add rolling stats for the last 5 games
    # First select only the rolling columns + game_id and team_id
    rolling_cols = ['game_id', 'team_id'] + [col for col in last_5_games.columns if col.startswith('rolling_')]

    # Pull out the rolling columns
    rolling_features_data = last_5_games[rolling_cols]

    # Merge rolling_features with long_stats_avg df
    long_stats_avg = long_stats_avg.merge(rolling_features_data, on=["game_id", "team_id"], how='left')

    # Add allowed stats to the df
    long_stats_avg = long_stats_avg.merge(team_allowed_stats, on=["game_id", "team_id"], how="left")

    # Drop the columns from the first 5 games for each team in the 2018-19 season
    long_stats_avg.dropna(inplace=True)

    # Home/Away features
    home_features = long_stats_avg.merge(game_stats[['game_id', 'home_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'home_team_id'], how='inner').drop(columns=['home_team_id'])
    away_features = long_stats_avg.merge(game_stats[['game_id', 'away_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'away_team_id'], how='inner').drop(columns=['away_team_id'])

    # Add wins and losses to home and away features
    home_features = home_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')
    away_features = away_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')

    # Rename the columns for home and away features
    exclude = {'game_id', 'season_year', 'team_id', 'game_date'}
    home_features.columns = [
        f"{col}_home" if col not in exclude else col
        for col in home_features.columns
    ]
    away_features.columns = [
        f"{col}_away" if col not in exclude else col
        for col in away_features.columns
    ]

    # Merge features
    ml_df = home_features.merge(away_features, on=["game_id", "game_date"], how="inner").merge(
        game_stats[["game_id", "total_score"]],
        on="game_id", how="inner"
    )
    ml_df = ml_df.drop_duplicates('game_id')

    # Clean up
    ml_df = ml_df.drop(columns=["team_id_x", "team_id_y", "season_year_x", "season_year_y"], errors='ignore')
    X = ml_df.drop(columns=["game_id", "total_score"])
    y = ml_df[["total_score", "game_date"]]

    return X, y

def pointspred_playoff_data(games_df, player_game_stats_df):
    # Load datasets
    games = games_df
    player_stats = player_game_stats_df

    # Filter for regular season games only
    games["game_id"] = games["game_id"].astype(str)
    player_stats["game_id"] = player_stats["game_id"].astype(str)
    games = games[games["game_id"].str.startswith(("2", "4"))]
    player_stats = player_stats[player_stats["game_id"].str.startswith(("2", "4"))]

    # Melt games dataframe for team-wise games played
    games_melted = games.melt(id_vars=["game_id", "season_year"], 
                            value_vars=["home_team_id", "away_team_id"],
                            value_name="team_id")

    # Count games played per team per season
    games_played = games_melted.groupby(["season_year", "team_id"])["game_id"].nunique().reset_index()
    games_played.rename(columns={"game_id": "games_played"}, inplace=True)

    # Parse nested player stats
    player_stats['player_game_stats'] = player_stats['player_game_stats'].apply(json.loads)
    player_stats = player_stats.dropna(subset=['player_game_stats']).copy()
    player_stats = pd.concat(
        [player_stats.drop(columns=['player_game_stats']), 
        player_stats['player_game_stats'].apply(pd.Series)], 
        axis=1
    )

    # Merge season info
    player_stats = player_stats.merge(games[['game_id', 'season_year']], on='game_id', how='left')

    # Define stat columns
    stats_columns = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 
                    'OREB', 'DREB', 'AST', 'STL', 'BLK', 
                    'TO', 'PTS']

    # Filter and aggregate player stats
    player_stats = player_stats[['season_year', 'game_id', 'team_id'] + stats_columns]
    team_stats = player_stats.groupby(['game_id', 'team_id'])[stats_columns].sum().reset_index()

    # Merge with games to determine home/away teams
    team_stats = team_stats.merge(
        games[['game_id', 'season_year', 'home_team_id', 'away_team_id']], 
        on='game_id', 
        how='left'
    )

    # Separate home and away stats
    home_stats = team_stats[team_stats['team_id'] == team_stats['home_team_id']]
    away_stats = team_stats[team_stats['team_id'] == team_stats['away_team_id']]

    # Rename columns
    home_stats = home_stats.rename(columns={col: col + "_home" for col in stats_columns}).drop(columns=['team_id'])
    away_stats = away_stats.rename(columns={col: col + "_away" for col in stats_columns}).drop(columns=['team_id'])

    # Merge into one row per game
    game_stats = home_stats.merge(away_stats, on=['game_id', 'season_year', 'home_team_id', 'away_team_id'], how='inner')

    # Compute outcome, 1 if home team wins, 0 otherwise
    game_stats["home_team_win"] = (game_stats["PTS_home"] > game_stats["PTS_away"]).astype(int)

    # Compute total score
    game_stats["total_score"] = (game_stats["PTS_home"] + game_stats["PTS_away"]).astype(int)

    # Create a dataframe of winners
    winners = pd.DataFrame({
        "game_id": game_stats["game_id"],
        "winner_team_id": game_stats["home_team_id"].where(game_stats["home_team_win"] == 1, game_stats["away_team_id"])
    })

    # Convert to long format for modeling (Home and away team stats for each game on the rows of the model input)
    home_team_stats = game_stats[["game_id", "season_year", "home_team_id"] + [col for col in game_stats.columns if col.endswith("_home")]].copy()
    away_team_stats = game_stats[["game_id", "season_year", "away_team_id"] + [col for col in game_stats.columns if col.endswith("_away")]].copy()

    home_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_home", "") for col in home_team_stats.columns[3:]]
    away_team_stats.columns = ["game_id", "season_year", "team_id"] + [col.replace("_away", "") for col in away_team_stats.columns[3:]]

    long_stats = pd.concat([home_team_stats, away_team_stats], axis=0).sort_values(["team_id", "season_year", "game_id"])

    # Sort by game_date in chonological order before calculating rolling averages
    long_stats = long_stats.merge(games[['game_id', 'game_date']], on='game_id', how='left')
    long_stats = long_stats.sort_values('game_date').reset_index(drop=True)

    wl_count = long_stats.copy()

    # Merge the winner lookup table into the long stats df
    wl_count = wl_count.merge(winners, on='game_id', how='left')

    # Calculate wins and losses for each team up to the current game
    wl_count["won_game"] = (wl_count["team_id"] == wl_count["winner_team_id"]).astype(int)
    wl_count["games_so_far"] = (
        wl_count.groupby(['team_id', 'season_year'])
        .cumcount()
    )
    wl_count["wins"] = (
        wl_count.groupby(['team_id', 'season_year'])["won_game"]
        .cumsum() - wl_count["won_game"]
    ).fillna(0).astype(int)
    wl_count["losses"] = (
        wl_count["games_so_far"] - wl_count["wins"]
    ).clip(lower=0).astype(int)

    # Compute number of possessions for each team (from NBA.com)
    long_stats["POSS"] = (
        (long_stats["FGA"] + 0.44 * long_stats["FTA"] - long_stats["OREB"] + long_stats["TO"])
    )
    long_stats["POSS"] = long_stats["POSS"].clip(lower=0)  # Ensure there are no negative possession values

    # Compute per 100 possession stats
    per_100_columns = [stat + "_100" for stat in stats_columns]
    for stat in stats_columns:
        long_stats[stat + "_100"] = 100 * long_stats[stat] / long_stats["POSS"]

    # Add the possession stat to per_100_columns so we can compute rolling averages for it
    per_100_columns.append("POSS")

    # Compute rolling averages of per-100-possession stats
    def compute_rolling_averages(group):
        return group[per_100_columns].shift().expanding().mean()

    long_stats_avg = long_stats.copy()
    long_stats_avg[per_100_columns] = long_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)
    long_stats_avg.drop(columns=stats_columns, inplace=True)

    # Fallback: previous season average per-100 stats
    prev_season_averages = long_stats.groupby(["team_id", "season_year"])[per_100_columns].mean().reset_index()

    def shift_season(season_str):
        start, end = season_str.split("-")
        next_start = str(int(start) + 1)
        next_end = str(int(end[-2:]) + 1).zfill(2)
        return f"{next_start}-{next_end}"

    prev_season_averages["season_year"] = prev_season_averages["season_year"].apply(shift_season)

    long_stats_avg = long_stats_avg.merge(
        prev_season_averages,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback")
    )

    for stat in per_100_columns:
        long_stats_avg[stat] = long_stats_avg[stat].fillna(long_stats_avg[f"{stat}_fallback"])
        long_stats_avg.drop(columns=[f"{stat}_fallback"], inplace=True)

    long_stats_avg.dropna(inplace=True)

    last_5_games = long_stats.merge(wl_count[['game_id', 'team_id', 'wins', 'losses', 'won_game']], 
                              on=['game_id', 'team_id'], how='left')

    # Define which columns to roll over
    rolling_features = per_100_columns  # exclude 'won_game' for mean calculations

    # Rolling mean stats over the last 5 games (using only previous games)
    rolling_means = (
        last_5_games.groupby(['team_id', 'season_year'])[rolling_features]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    rolling_wins = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    rolling_losses = (
        last_5_games.groupby(['team_id', 'season_year'])['won_game']
        .transform(lambda x: (1 - x.shift(1)).rolling(window=5, min_periods=5).sum())
        .fillna(0).astype(int)
    )

    # Merge based on index (team_id, season_year, original index inside group)
    rolling_5 = pd.concat(
        [
            rolling_means.rename(columns={col: f"rolling_{col}_last5" for col in rolling_means.columns}),
            rolling_wins.rename('rolling_wins_last5'),
            rolling_losses.rename('rolling_losses_last5')
        ],
        axis=1
    )

    # Now merge back safely (indexes match)
    last_5_games = pd.concat([last_5_games, rolling_5], axis=1)

    # Merge previous season averages as fallback
    last_5_games = last_5_games.merge(
        prev_season_averages[['team_id', 'season_year'] + per_100_columns],
        on=['team_id', 'season_year'],
        how='left',
        suffixes=('', '_fallback')
    )

    # Fill rolling columns using fallback columns
    for col in [f"rolling_{stat}_last5" for stat in per_100_columns] + ['rolling_wins_last5', 'rolling_losses_last5']:
        fallback_col = col.replace('rolling_', '').replace('_last5', '') + '_fallback'
        if fallback_col in last_5_games.columns:
            last_5_games[col] = last_5_games[col].fillna(last_5_games[fallback_col])

    # Drop all *_fallback columns
    last_5_games.drop(columns=[c for c in last_5_games.columns if c.endswith('_fallback')], inplace=True)

    opponent_allowed_columns = [stat + "_allowed" for stat in per_100_columns]

    # Create df to store stats from the opposing team
    opponent_stats = long_stats[["game_id", "team_id", "game_date"] + per_100_columns].copy()
    opponent_stats = opponent_stats.rename(columns={col: col + "_allowed" for col in per_100_columns})

    # Pair each team with their opponent in the same game
    team_allowed_stats = long_stats[["game_id", "team_id", "season_year"]].merge(
        opponent_stats, on="game_id", suffixes=("", "_opp")
    )

    # Only keep rows where the opponent is different (i.e., get opponent stats)
    team_allowed_stats = team_allowed_stats[team_allowed_stats["team_id"] != team_allowed_stats["team_id_opp"]]

    # It doesn't matter who the opponenet in each game is so we can drop this column now
    team_allowed_stats.drop("team_id_opp", axis=1, inplace=True)

    def compute_rolling_averages(group):
        return group[opponent_allowed_columns].shift().expanding().mean()

    # Compute rolling averages of per-100-possession allowed stats
    team_allowed_stats[opponent_allowed_columns] = team_allowed_stats.groupby(["team_id", "season_year"], group_keys=False).apply(compute_rolling_averages)

    # Compute season averages of opponent stats allowed
    season_allowed_stats = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .mean()
        .reset_index()
    )

    # Fallback: previous season average per-100 allowed stats
    prev_allowed = season_allowed_stats.copy()
    prev_allowed["season_year"] = prev_allowed["season_year"].apply(shift_season)

    team_allowed_stats = team_allowed_stats.merge(
        prev_allowed,
        on=["team_id", "season_year"],
        how="left",
        suffixes=("", "_fallback"),
    )

    # Fill any missing values in the allowed stats with fallback season averages
    for stat in opponent_allowed_columns:
        team_allowed_stats[stat] = team_allowed_stats[stat].fillna(team_allowed_stats[f"{stat}_fallback"])
        team_allowed_stats.drop(columns=[f"{stat}_fallback"], inplace=True)

    # Drop the first first game from the first season for each team in the database because is has no fallback
    team_allowed_stats.dropna(inplace=True)

    # Calculate rolling means of opponent stats allowed over past 5 games
    rolling_allowed_means = (
        team_allowed_stats.groupby(["team_id", "season_year"])[opponent_allowed_columns]
        .transform(lambda x: x.shift(1).rolling(window=5, min_periods=5).mean())
    )

    # Combine rolling and fallback for each stat
    for stat in per_100_columns:
        col = f"{stat}_allowed"
        rolling_col = f"rolling_{col}_last5"
        
        team_allowed_stats[rolling_col] = rolling_allowed_means[col].fillna(team_allowed_stats[col])

    # Final cleanup: drop any rows that still have NaNs in important rolling stats
    rolling_allowed_cols = [f"rolling_{stat}_allowed_last5" for stat in per_100_columns]
    team_allowed_stats.dropna(subset=rolling_allowed_cols, inplace=True)

    # Drop unneeded columns
    team_allowed_stats.drop(['season_year', 'game_date'], axis=1, inplace=True)

    # Add rolling stats for the last 5 games
    # First select only the rolling columns + game_id and team_id
    rolling_cols = ['game_id', 'team_id'] + [col for col in last_5_games.columns if col.startswith('rolling_')]

    # Pull out the rolling columns
    rolling_features_data = last_5_games[rolling_cols]

    # Merge rolling_features with long_stats_avg df
    long_stats_avg = long_stats_avg.merge(rolling_features_data, on=["game_id", "team_id"], how='left')

    # Add allowed stats to the df
    long_stats_avg = long_stats_avg.merge(team_allowed_stats, on=["game_id", "team_id"], how="left")

    # Drop the columns from the first 5 games for each team in the 2018-19 season
    long_stats_avg.dropna(inplace=True)

    # Home/Away features
    home_features = long_stats_avg.merge(game_stats[['game_id', 'home_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'home_team_id'], how='inner').drop(columns=['home_team_id'])
    away_features = long_stats_avg.merge(game_stats[['game_id', 'away_team_id']], left_on=['game_id', 'team_id'], right_on=['game_id', 'away_team_id'], how='inner').drop(columns=['away_team_id'])

    # Add wins and losses to home and away features
    home_features = home_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')
    away_features = away_features.merge(wl_count[['game_id', 'team_id', 'wins', 'losses']], on=['game_id', 'team_id'], how='left')

    # Rename the columns for home and away features
    exclude = {'game_id', 'season_year', 'team_id', 'game_date'}
    home_features.columns = [
        f"{col}_home" if col not in exclude else col
        for col in home_features.columns
    ]
    away_features.columns = [
        f"{col}_away" if col not in exclude else col
        for col in away_features.columns
    ]

    # Merge features
    ml_df = home_features.merge(away_features, on=["game_id", "game_date"], how="inner").merge(
        game_stats[["game_id", "total_score"]],
        on="game_id", how="inner"
    )
    ml_df = ml_df.drop_duplicates('game_id')

    # Only include playoff games in the model input
    ml_df = ml_df[ml_df["game_id"].str.startswith("4")]

    # Clean up
    ml_df = ml_df.drop(columns=["team_id_x", "team_id_y", "season_year_x", "season_year_y"], errors='ignore')
    X = ml_df.drop(columns=["game_id", "total_score"])
    y = ml_df[["total_score", "game_date"]]

    return X, y


# def filter_by_date(
#         date, X_win_reg, y_win_reg, X_win_playoff, y_win_playoff,
#         X_points_reg, y_points_reg, X_points_playoff, y_points_playoff
# ):
#     '''
#     Filter the data to only make predictions for games after the given date.
#     '''

#     # Convert the date string to a datetime object
#     date = pd.to_datetime(date)

#     # Filter the dataframes based on the date
#     X_win_reg = X_win_reg[X_win_reg['game_date'] >= date]
#     y_win_reg = y_win_reg[y_win_reg['game_date'] >= date]
#     X_win_playoff = X_win_playoff[X_win_playoff['game_date'] >= date]
#     y_win_playoff = y_win_playoff[y_win_playoff['game_date'] >= date]
#     X_points_reg = X_points_reg[X_points_reg['game_date'] >= date]
#     y_points_reg = y_points_reg[y_points_reg['game_date'] >= date]
#     X_points_playoff = X_points_playoff[X_points_playoff['game_date'] >= date]
#     y_points_playoff = y_points_playoff[y_points_playoff['game_date'] >= date]

#     return X_win_reg, y_win_reg, X_win_playoff, y_win_playoff, X_points_reg, y_points_reg, X_points_playoff, y_points_playoff

def filter_by_date_playoffs(date, X_win_playoff, y_win_playoff, X_points_playoff, y_points_playoff, games):
    '''
    Filter the data to only make predictions for games after the given date.
    '''

    # Convert the date string to a datetime object
    date = pd.to_datetime(date)

    # Filter the dataframes based on the date
    X_win_playoff = X_win_playoff[X_win_playoff['game_date'] >= date]
    y_win_playoff = y_win_playoff[y_win_playoff['game_date'] >= date]
    X_points_playoff = X_points_playoff[X_points_playoff['game_date'] >= date]
    y_points_playoff = y_points_playoff[y_points_playoff['game_date'] >= date]
    X_win_playoff = X_win_playoff.drop(columns=['game_date'])
    y_win_playoff = y_win_playoff.drop(columns=['game_date'])
    X_points_playoff = X_points_playoff.drop(columns=['game_date'])
    y_points_playoff = y_points_playoff.drop(columns=['game_date'])
    games = games[games['game_date'] == date]

    return X_win_playoff, y_win_playoff, X_points_playoff, y_points_playoff, games


# Only for playoffs at the moment
# TODO: Make compatible with regular season
def get_model_predictions(X_win_playoff, y_win_playoff, X_points_playoff, y_points_playoff):
    winpred_playoff_model = load_model("winreg_playoff.h5")
    pointspred_playoff_model = joblib.load("ridge_pointspred_playoff.joblib")

    win_scaler = MinMaxScaler()
    points_scaler = MinMaxScaler()

    # Scale the data
    X_win_playoff_scaled = win_scaler.fit_transform(X_win_playoff)
    X_points_playoff_scaled = points_scaler.fit_transform(X_points_playoff)
    X_points_playoff_scaled = np.log1p(X_points_playoff_scaled)


    y_win_playoff_pred = (winpred_playoff_model.predict(X_win_playoff_scaled) > 0.5).astype(int)
    y_points_playoff_pred = pointspred_playoff_model.predict(X_points_playoff_scaled)

    return y_win_playoff_pred, y_points_playoff_pred

def prediction_to_db(y_win_playoff_pred, y_points_playoff_pred, games):
    print("Predictions for playoff games:")
    print(y_win_playoff_pred)
    print(y_points_playoff_pred)

    # Ensure predictions are 1D
    y_win_playoff_pred = y_win_playoff_pred.ravel()
    y_points_playoff_pred = y_points_playoff_pred.ravel()

    merged_df = pd.DataFrame({
        "game_id": games["game_id"],
        "winner_prediction": y_win_playoff_pred,
        "score_prediction": y_points_playoff_pred
    })

    password = 'CS402OAAPass$'

    DATABASE_URL = f"postgresql://rgutkeecsoraclearenaadmin:{password}@rg-utk-eecs-oracle-arena-postgresql-db.postgres.database.azure.com:5432/postgres"

    engine = sqlalchemy.create_engine(DATABASE_URL, echo=True)

    with engine.connect() as connection:
        for _, row in merged_df.iterrows():
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE games
                    SET winner = :winner, total_score_prediction = :total_points
                    WHERE game_id = :game_id
                    """
                ),
                {
                    "game_id": int(row['game_id']),
                    "winner": int(row['winner_prediction']),
                    "total_points": float(row['score_prediction'])
                }
            )
        connection.commit()

    print("All predictions have been added to the database.")

    return 0

def main():
    # Get data from the database and prepare it for modeling
    games_df , player_game_stats_df = get_data_from_db()
    # X_win_reg, y_win_reg = winpred_reg_data(games_df, player_game_stats_df)
    X_win_playoff, y_win_playoff = winpred_playoff_data(games_df, player_game_stats_df)
    # X_points_reg, y_points_reg = pointspred_reg_data(games_df, player_game_stats_df)
    X_points_playoff, y_points_playoff = pointspred_playoff_data(games_df, player_game_stats_df)

    # Only use games on the given date or after
    date = '2025-05-01'
    X_win_playoff, y_win_playoff, X_points_playoff, y_points_playoff, games = filter_by_date_playoffs(
        date, X_win_playoff, y_win_playoff, X_points_playoff, y_points_playoff, games_df
    )
    # X_win_reg, y_win_reg, X_win_playoff, y_win_playoff, X_points_reg, y_points_reg, X_points_playoff, y_points_playoff = filter_by_date(
    #     date, X_win_reg, y_win_reg, X_win_playoff, y_win_playoff,
    #     X_points_reg, y_points_reg, X_points_playoff, y_points_playoff
    # )
    y_win_playoff_pred, y_points_playoff_pred = get_model_predictions(
        X_win_playoff, y_win_playoff, X_points_playoff, y_points_playoff
    )
    # Save the predictions to the database
    prediction_to_db(y_win_playoff_pred, y_points_playoff_pred, games)

if __name__ == "__main__":
    main()