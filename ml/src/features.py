"""Feature engineering shared by training and prediction.

One builder serves all four models so the training and live-prediction
features cannot drift apart.
"""
import json

import numpy as np
import pandas as pd

SEASON_PREFIXES = {
    "regular": ("2",),
    "playoff": ("2", "4"),  # playoff rolling stats need regular-season history
}
TARGET_COLUMNS = {"win": "home_team_win", "points": "total_score"}
STATS_COLUMNS = ['FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA',
                 'OREB', 'DREB', 'AST', 'STL', 'BLK',
                 'TO', 'PTS']


def build_features(games_df, player_game_stats_df, season_type, target, include_unplayed=False):
    """Build the model inputs for every game.

    season_type: "regular" (game ids starting with 2) or "playoff" (rolling stats
        still use regular-season history, but only playoff games (ids starting with 4)
        are returned).
    target: "win" (home_team_win) or "points" (total_score).
    include_unplayed: keep games with no stats yet (0 total points). Training drops them;
        prediction keeps them, since a game's features only use earlier games.
    Returns X and y; both include a game_date column so callers can split by time.
    y also carries game_id (X's rows line up with y's).
    """
    if season_type not in SEASON_PREFIXES:
        raise ValueError(f"season_type must be one of {list(SEASON_PREFIXES)}")
    target_col = TARGET_COLUMNS[target]
    prefixes = SEASON_PREFIXES[season_type]
    games_df = games_df.copy()
    player_game_stats_df = player_game_stats_df.copy()
    games = games_df
    player_stats = player_game_stats_df

    games["game_id"] = games["game_id"].astype(str)
    player_stats["game_id"] = player_stats["game_id"].astype(str)
    games = games[games["game_id"].str.startswith(prefixes)]
    player_stats = player_stats[player_stats["game_id"].str.startswith(prefixes)]

    # Melt games dataframe for team-wise games played
    games_melted = games.melt(id_vars=["game_id", "season_year"], 
                            value_vars=["home_team_id", "away_team_id"],
                            value_name="team_id")

    # Count games played per team per season
    games_played = games_melted.groupby(["season_year", "team_id"])["game_id"].nunique().reset_index()
    games_played.rename(columns={"game_id": "games_played"}, inplace=True)

    # Parse nested player stats
    player_stats['player_game_stats'] = player_stats['player_game_stats'].apply(
        lambda v: json.loads(v) if isinstance(v, str) else v
    )
    player_stats = player_stats.dropna(subset=['player_game_stats']).copy()
    player_stats = pd.concat(
        [player_stats.drop(columns=['player_game_stats']), 
        player_stats['player_game_stats'].apply(pd.Series)], 
        axis=1
    )

    # Merge season info
    player_stats = player_stats.merge(games[['game_id', 'season_year']], on='game_id', how='left')

    # Define stat columns
    stats_columns = STATS_COLUMNS

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
        game_stats[["game_id", target_col]],
        on="game_id", how="inner"
    )
    ml_df = ml_df.drop_duplicates('game_id')

    # Unplayed games have no stats and sum to 0 points; they are not training examples
    if not include_unplayed:
        played = game_stats.loc[game_stats["total_score"] > 0, "game_id"]
        ml_df = ml_df[ml_df["game_id"].isin(played)]

    # Clean up
    ml_df = ml_df.drop(columns=["team_id_x", "team_id_y", "season_year_x", "season_year_y"], errors='ignore')
    if season_type == "playoff":
        ml_df = ml_df[ml_df["game_id"].str.startswith("4")]

    X = ml_df.drop(columns=["game_id", target_col])
    y = ml_df[[target_col, "game_date", "game_id"]]
    
    return X, y
