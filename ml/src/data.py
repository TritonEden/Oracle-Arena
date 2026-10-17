"""Load games and player stats from the database, with an optional CSV cache."""
from pathlib import Path

import pandas as pd
import sqlalchemy

from config import ML_DIR, get_database_url

CACHE_DIR = ML_DIR / "data"


def query_tables():
    engine = sqlalchemy.create_engine(get_database_url())
    with engine.connect() as connection:
        games = pd.read_sql_table("games", connection)
        # player_game_stats holds duplicate rows; keep one per game and player
        stats = pd.read_sql_query(
            "SELECT DISTINCT ON (game_id, player_id) * FROM player_game_stats", connection
        )
    return games, stats


def load_tables(end_season=None, end_date=None, use_cache=True, data_dir=None):
    """Return (games, player_game_stats), optionally capped at end_season (e.g. "2025-26") and end_date."""
    # data_dir points at a fixed snapshot (games.csv + player_game_stats.csv); never touches the DB
    folder = Path(data_dir) if data_dir else CACHE_DIR
    games_path, stats_path = folder / "games.csv", folder / "player_game_stats.csv"
    if data_dir:
        if not (games_path.exists() and stats_path.exists()):
            raise FileNotFoundError(f"{folder} must contain games.csv and player_game_stats.csv")
        use_cache = True
    if not (use_cache and games_path.exists() and stats_path.exists()):
        games, stats = query_tables()
        CACHE_DIR.mkdir(exist_ok=True)
        games.to_csv(games_path, index=False)
        stats.to_csv(stats_path, index=False)

    # Always read back from the CSVs so column dtypes are the same on every path
    games = pd.read_csv(games_path)
    stats = pd.read_csv(stats_path)

    if end_season:
        games = games[games["season_year"] <= end_season]
    if end_date:
        games = games[pd.to_datetime(games["game_date"]) <= pd.to_datetime(end_date)]
    if end_season or end_date:
        stats = stats[stats["game_id"].isin(games["game_id"])]
    return games, stats
