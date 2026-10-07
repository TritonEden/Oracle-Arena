#!/usr/bin/env python3

import argparse
import json
import math
import random
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import (
    boxscoretraditionalv3,
    scoreboardv3,
)
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


# ---------------------------------------------------------------------------
# Database / output schema
# ---------------------------------------------------------------------------

TEAMS_COLUMNS = [
    "team_id",
    "season_year",
    "team_location",
    "team_name",
    "team_abbreviation",
]

PLAYERS_COLUMNS = [
    "player_id",
    "player_first_name",
    "player_last_name",
]

GAMES_COLUMNS = [
    "game_id",
    "season_year",
    "game_date",
    "home_team_id",
    "away_team_id",
    "game_time",
]

PLAYER_GAME_STATS_COLUMNS = [
    "game_id",
    "player_id",
    "team_id",
    "player_game_stats",
]

CSV_FILES = {
    "teams": "teams.csv",
    "players": "players.csv",
    "games": "games.csv",
    "player_game_stats": "player_game_stats.csv",
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract NBA schedule and player statistics for Oracle-Arena."
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save CSV files (default: current directory).",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days to fetch backwards from today.",
    )

    parser.add_argument(
        "--future-days",
        type=int,
        default=None,
        help="Number of days to fetch forwards from today.",
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        help="Absolute start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end-date",
        type=parse_date,
        help="Absolute end date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--retry-delay",
        type=float,
        default=5.0,
        help="Initial retry delay in seconds (default: 5).",
    )

    parser.add_argument(
        "--max-retry-delay",
        type=float,
        default=3000.0,
        help="Maximum retry delay in seconds (default: 3000).",
    )

    parser.add_argument(
        "--request-delay",
        type=float,
        default=1.5,
        help="Base delay between successful API requests (default: 1.5).",
    )

    return parser.parse_args()


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected YYYY-MM-DD."
        ) from exc


# ---------------------------------------------------------------------------
# Date handling
# ---------------------------------------------------------------------------

def get_date_range(args):
    absolute_mode = (
        args.start_date is not None
        or args.end_date is not None
    )

    relative_mode = (
        args.days is not None
        or args.future_days is not None
    )

    if absolute_mode and relative_mode:
        raise ValueError(
            "Use either --days/--future-days OR "
            "--start-date/--end-date, not both."
        )

    if absolute_mode:
        if args.start_date is None or args.end_date is None:
            raise ValueError(
                "--start-date and --end-date must be supplied together."
            )

        if args.start_date > args.end_date:
            raise ValueError(
                "--start-date cannot be after --end-date."
            )

        start = args.start_date
        end = args.end_date

    else:
        days = args.days if args.days is not None else 5
        future_days = (
            args.future_days
            if args.future_days is not None
            else 5
        )

        if days < 0 or future_days < 0:
            raise ValueError(
                "--days and --future-days must be >= 0."
            )

        today = date.today()

        start = today - timedelta(days=days)
        end = today + timedelta(days=future_days)

    current = start

    while current <= end:
        yield current
        current += timedelta(days=1)


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def empty_dataframes():
    return {
        "teams": pd.DataFrame(columns=TEAMS_COLUMNS),
        "players": pd.DataFrame(columns=PLAYERS_COLUMNS),
        "games": pd.DataFrame(columns=GAMES_COLUMNS),
        "player_game_stats": pd.DataFrame(
            columns=PLAYER_GAME_STATS_COLUMNS
        ),
    }


def normalize_game_id(game_id):
    if game_id is None:
        return None

    if pd.isna(game_id):
        return None

    game_id = str(game_id).strip()

    if not game_id:
        return None

    # NBA game IDs are normally 10 digits.
    # This also handles pandas converting an ID to an integer.
    if game_id.isdigit():
        game_id = game_id.zfill(10)

    return game_id


def season_from_game_id(game_id):
    """
    0022500001 -> 2025-26
    0012600001 -> 2026-27

    The middle two digits represent the season start year.
    """

    game_id = normalize_game_id(game_id)

    if game_id is None or len(game_id) < 4:
        return None

    season_start = 2000 + int(game_id[3:5])

    return f"{season_start}-{str(season_start + 1)[-2:]}"


def clean_scalar(value):
    if value is None:
        return None

    if isinstance(value, float) and math.isnan(value):
        return None

    if pd.isna(value):
        return None

    return value


def dataframe_column(df, *names):
    for name in names:
        if name in df.columns:
            return name

    return None


def normalize_json_value(value):
    """
    Convert pandas/numpy values into values that json.dumps can serialize.
    """

    if value is None:
        return None

    if isinstance(value, dict):
        return {
            str(key): normalize_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            normalize_json_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            normalize_json_value(item)
            for item in value
        ]

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

        return value

    if pd.isna(value):
        return None

    # numpy scalar types
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    return value


def dataframe_to_json(row):
    values = {}

    for key, value in row.items():
        values[str(key)] = normalize_json_value(value)

    return json.dumps(
        values,
        separators=(",", ":"),
        allow_nan=False,
    )


# ---------------------------------------------------------------------------
# Persistent API retry
# ---------------------------------------------------------------------------

def retry_api_request(
    request_function,
    description,
    retry_delay,
    max_retry_delay,
):
    """
    Retry API requests indefinitely.

    This is intentional. Historical extraction should eventually complete
    even if the NBA API has temporary failures.
    """

    attempt = 0
    delay = retry_delay

    while True:
        attempt += 1

        try:
            result = request_function()

            if result is None:
                raise RuntimeError(
                    f"{description} returned None."
                )

            print(
                f"  API request succeeded: {description}"
            )

            return result

        except KeyboardInterrupt:
            raise

        except Exception as exc:
            print(
                f"  API request failed: {description}"
            )
            print(
                f"    Attempt: {attempt}"
            )
            print(
                f"    Error: {type(exc).__name__}: {exc}"
            )
            print(
                f"    Retrying in {delay:.1f} seconds..."
            )

            time.sleep(delay)

            # Exponential backoff with a hard maximum.
            delay = min(
                delay * 2,
                max_retry_delay,
            )


def request_delay(seconds):
    if seconds <= 0:
        return

    jitter = random.uniform(0.0, seconds * 0.5)

    time.sleep(seconds + jitter)


# ---------------------------------------------------------------------------
# ScoreboardV3
# ---------------------------------------------------------------------------

def fetch_scoreboard(
    game_date,
    retry_delay,
    max_retry_delay,
):
    print(f"Fetching schedule: {game_date}")

    return retry_api_request(
        lambda: scoreboardv3.ScoreboardV3(
            game_date=game_date.strftime("%Y-%m-%d")
        ),
        f"ScoreboardV3 for {game_date}",
        retry_delay,
        max_retry_delay,
    )


def get_scoreboard_games(scoreboard):
    try:
        return scoreboard.game_header.get_data_frame()
    except Exception:
        pass

    try:
        return scoreboard.get_data_frames()[0]
    except Exception:
        return pd.DataFrame()


def get_scoreboard_line_score(scoreboard):
    try:
        return scoreboard.line_score.get_data_frame()
    except Exception:
        pass

    try:
        dataframes = scoreboard.get_data_frames()

        if len(dataframes) > 1:
            return dataframes[1]

    except Exception:
        pass

    return pd.DataFrame()


def get_game_status(row):
    status = clean_scalar(
        row.get("gameStatus")
    )

    if status is None:
        status = clean_scalar(
            row.get("GAME_STATUS_ID")
        )

    if status is not None:
        try:
            return int(status)
        except (TypeError, ValueError):
            pass

    text_value = clean_scalar(
        row.get("gameStatusText")
    )

    if text_value is None:
        text_value = clean_scalar(
            row.get("GAME_STATUS_TEXT")
        )

    if text_value is None:
        return None

    text_value = str(text_value).lower()

    if "final" in text_value:
        return 3

    if "live" in text_value:
        return 2

    return 1


def is_game_final(row):
    status = get_game_status(row)

    return status == 3


def get_game_time(row):
    """
    Prefer the scheduled Eastern Time value supplied by ScoreboardV3.
    """

    for field in (
        "gameEt",
        "GAME_ET",
        "gameTimeUTC",
        "GAME_TIME_UTC",
    ):
        value = clean_scalar(row.get(field))

        if value is not None:
            return value

    return None


def build_games_df(
    scoreboard,
    game_date,
):
    """
    Build the existing Oracle-Arena games schema.

    ScoreboardV3's DataFrame representation does not consistently expose
    home/away IDs in GameHeader, so we map team IDs from LineScore using
    the visitor/home tricodes encoded in gameCode.
    """

    game_header = get_scoreboard_games(scoreboard)
    line_score = get_scoreboard_line_score(scoreboard)

    if game_header.empty:
        return pd.DataFrame(columns=GAMES_COLUMNS)

    team_lookup = {}

    if not line_score.empty:
        for _, row in line_score.iterrows():
            game_id = clean_scalar(
                row.get("gameId")
            )

            if game_id is None:
                game_id = clean_scalar(
                    row.get("GAME_ID")
                )

            team_id = clean_scalar(
                row.get("teamId")
            )

            if team_id is None:
                team_id = clean_scalar(
                    row.get("TEAM_ID")
                )

            tricode = clean_scalar(
                row.get("teamTricode")
            )

            if tricode is None:
                tricode = clean_scalar(
                    row.get("TEAM_ABBREVIATION")
                )

            if (
                game_id is None
                or team_id is None
                or tricode is None
            ):
                continue

            game_id = normalize_game_id(game_id)
            tricode = str(tricode).upper()

            team_lookup[
                (game_id, tricode)
            ] = team_id

    rows = []

    for _, raw_game in game_header.iterrows():
        game = raw_game.to_dict()

        game_id = clean_scalar(
            game.get("gameId")
        )

        if game_id is None:
            game_id = clean_scalar(
                game.get("GAME_ID")
            )

        game_id = normalize_game_id(game_id)

        if game_id is None:
            continue

        game_code = clean_scalar(
            game.get("gameCode")
        )

        if game_code is None:
            game_code = clean_scalar(
                game.get("GAMECODE")
            )

        visitor_team_id = None
        home_team_id = None

        if game_code and "/" in str(game_code):
            matchup = str(game_code).split("/", 1)[1]

            if len(matchup) == 6:
                visitor_tricode = matchup[:3].upper()
                home_tricode = matchup[3:].upper()

                visitor_team_id = team_lookup.get(
                    (game_id, visitor_tricode)
                )

                home_team_id = team_lookup.get(
                    (game_id, home_tricode)
                )

        # If LineScore did not give us the IDs, try the direct fields.
        if visitor_team_id is None:
            visitor_team_id = clean_scalar(
                game.get("awayTeamId")
            )

        if visitor_team_id is None:
            visitor_team_id = clean_scalar(
                game.get("VISITOR_TEAM_ID")
            )

        if home_team_id is None:
            home_team_id = clean_scalar(
                game.get("homeTeamId")
            )

        if home_team_id is None:
            home_team_id = clean_scalar(
                game.get("HOME_TEAM_ID")
            )

        if visitor_team_id is None or home_team_id is None:
            print(
                f"  WARNING: Could not determine home/away IDs "
                f"for game {game_id}."
            )
            continue

        rows.append(
            {
                "game_id": game_id,
                "season_year": season_from_game_id(game_id),
                "game_date": game_date,
                "home_team_id": home_team_id,
                "away_team_id": visitor_team_id,
                "game_time": get_game_time(game),
            }
        )

    games_df = pd.DataFrame(
        rows,
        columns=GAMES_COLUMNS,
    )

    if not games_df.empty:
        games_df = games_df.drop_duplicates(
            subset=["game_id"]
        )

    return games_df


def build_teams_df(
    scoreboard,
    game_date,
):
    """
    Build the existing Oracle-Arena teams schema from ScoreboardV3.
    """

    line_score = get_scoreboard_line_score(scoreboard)

    if line_score.empty:
        return pd.DataFrame(columns=TEAMS_COLUMNS)

    season_start = (
        game_date.year
        if game_date.month >= 7
        else game_date.year - 1
    )

    season_year = (
        f"{season_start}-{str(season_start + 1)[-2:]}"
    )

    rows = []

    for _, raw_team in line_score.iterrows():
        team = raw_team.to_dict()

        team_id = clean_scalar(
            team.get("teamId")
        )

        if team_id is None:
            team_id = clean_scalar(
                team.get("TEAM_ID")
            )

        if team_id is None:
            continue

        team_location = clean_scalar(
            team.get("teamCity")
        )

        if team_location is None:
            team_location = clean_scalar(
                team.get("TEAM_CITY")
            )

        team_name = clean_scalar(
            team.get("teamName")
        )

        if team_name is None:
            team_name = clean_scalar(
                team.get("TEAM_NAME")
            )

        team_abbreviation = clean_scalar(
            team.get("teamTricode")
        )

        if team_abbreviation is None:
            team_abbreviation = clean_scalar(
                team.get("TEAM_ABBREVIATION")
            )

        rows.append(
            {
                "team_id": team_id,
                "season_year": season_year,
                "team_location": team_location or "",
                "team_name": team_name or "",
                "team_abbreviation": team_abbreviation or "",
            }
        )

    teams_df = pd.DataFrame(
        rows,
        columns=TEAMS_COLUMNS,
    )

    if not teams_df.empty:
        teams_df = teams_df.drop_duplicates(
            subset=["team_id", "season_year"]
        )

    return teams_df


# ---------------------------------------------------------------------------
# BoxScoreTraditionalV3
# ---------------------------------------------------------------------------

def fetch_boxscore(
    game_id,
    retry_delay,
    max_retry_delay,
):
    return retry_api_request(
        lambda: boxscoretraditionalv3.BoxScoreTraditionalV3(
            game_id=game_id
        ),
        f"BoxScoreTraditionalV3 for {game_id}",
        retry_delay,
        max_retry_delay,
    )


def get_boxscore_player_stats(boxscore):
    dataframes = boxscore.get_data_frames()

    if not dataframes:
        return pd.DataFrame()

    return dataframes[0].copy()


def get_boxscore_team_stats(boxscore):
    dataframes = boxscore.get_data_frames()

    # BoxScoreTraditionalV3:
    #
    # 0 = PlayerStats
    # 1 = TeamStarterBenchStats
    # 2 = TeamStats
    #
    # TeamStats is what we want for team identity information.
    if len(dataframes) >= 3:
        return dataframes[2].copy()

    if len(dataframes) >= 2:
        return dataframes[1].copy()

    return pd.DataFrame()


def clean_player_stats(player_stats):
    """
    Normalize V3 player statistics while preserving the information that
    ultimately goes into player_game_stats.
    """

    if player_stats.empty:
        return player_stats

    player_stats = player_stats.copy()

    rename_map = {
        "gameId": "GAME_ID",
        "personId": "PLAYER_ID",
        "teamId": "TEAM_ID",
        "teamCity": "TEAM_CITY",
        "teamName": "TEAM_NAME",
        "teamTricode": "TEAM_ABBREVIATION",
        "firstName": "PLAYER_FIRST_NAME",
        "familyName": "PLAYER_LAST_NAME",
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
        "plusMinusPoints": "PLUS_MINUS",
    }

    player_stats = player_stats.rename(
        columns=rename_map
    )

    # Match the old extraction behavior:
    # players who did not play have no statistical values.
    if "MIN" in player_stats.columns:
        did_not_play = (
            player_stats["MIN"].isna()
            | player_stats["MIN"].eq("")
        )

        player_stats.loc[
            did_not_play,
            [
                column
                for column in [
                    "FGM",
                    "FGA",
                    "FG_PCT",
                    "FG3M",
                    "FG3A",
                    "FG3_PCT",
                    "FTM",
                    "FTA",
                    "FT_PCT",
                    "OREB",
                    "DREB",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "TO",
                    "PF",
                    "PTS",
                    "PLUS_MINUS",
                ]
                if column in player_stats.columns
            ],
        ] = None

    return player_stats


def build_players_df(player_stats):
    if player_stats.empty:
        return pd.DataFrame(columns=PLAYERS_COLUMNS)

    rows = []

    for _, row in player_stats.iterrows():
        player_id = clean_scalar(
            row.get("PLAYER_ID")
        )

        if player_id is None:
            continue

        first_name = clean_scalar(
            row.get("PLAYER_FIRST_NAME")
        )

        last_name = clean_scalar(
            row.get("PLAYER_LAST_NAME")
        )

        rows.append(
            {
                "player_id": player_id,
                "player_first_name": first_name or "",
                "player_last_name": last_name or "",
            }
        )

    players_df = pd.DataFrame(
        rows,
        columns=PLAYERS_COLUMNS,
    )

    if not players_df.empty:
        players_df = players_df.drop_duplicates(
            subset=["player_id"]
        )

    return players_df


def build_player_game_stats_df(
    game_id,
    player_stats,
):
    if player_stats.empty:
        return pd.DataFrame(
            columns=PLAYER_GAME_STATS_COLUMNS
        )

    rows = []

    for _, row in player_stats.iterrows():
        player_id = clean_scalar(
            row.get("PLAYER_ID")
        )

        team_id = clean_scalar(
            row.get("TEAM_ID")
        )

        if player_id is None or team_id is None:
            continue

        stats_json = dataframe_to_json(row)

        rows.append(
            {
                "game_id": normalize_game_id(game_id),
                "player_id": player_id,
                "team_id": team_id,
                "player_game_stats": stats_json,
            }
        )

    stats_df = pd.DataFrame(
        rows,
        columns=PLAYER_GAME_STATS_COLUMNS,
    )

    if not stats_df.empty:
        stats_df = stats_df.drop_duplicates(
            subset=["game_id", "player_id"]
        )

    return stats_df


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def csv_path(name, dir):
    return Path(dir) / Path(CSV_FILES[name])


def read_existing_csv(name, dir):
    path = csv_path(name, dir)

    if not path.exists():
        if name == "teams":
            return pd.DataFrame(columns=TEAMS_COLUMNS)

        if name == "players":
            return pd.DataFrame(columns=PLAYERS_COLUMNS)

        if name == "games":
            return pd.DataFrame(columns=GAMES_COLUMNS)

        return pd.DataFrame(
            columns=PLAYER_GAME_STATS_COLUMNS
        )

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        if name == "teams":
            return pd.DataFrame(columns=TEAMS_COLUMNS)

        if name == "players":
            return pd.DataFrame(columns=PLAYERS_COLUMNS)

        if name == "games":
            return pd.DataFrame(columns=GAMES_COLUMNS)

        return pd.DataFrame(
            columns=PLAYER_GAME_STATS_COLUMNS
        )

    # Normalize identifiers when reading existing CSV data.
    if name == "games" and "game_id" in df.columns:
        df["game_id"] = df["game_id"].apply(
            normalize_game_id
        )

    elif name == "player_game_stats" and "game_id" in df.columns:
        df["game_id"] = df["game_id"].apply(
            normalize_game_id
        )

    return df


def merge_csv(name, new_df, dir):
    if new_df.empty:
        return

    existing = read_existing_csv(name, dir)

    new_df = new_df.copy()

    # Normalize IDs before combining old and new data.
    if name == "games" and "game_id" in new_df.columns:
        new_df["game_id"] = new_df["game_id"].apply(
            normalize_game_id
        )

    elif (
        name == "player_game_stats"
        and "game_id" in new_df.columns
    ):
        new_df["game_id"] = new_df["game_id"].apply(
            normalize_game_id
        )

    combined = pd.concat(
        [existing, new_df],
        ignore_index=True,
    )

    if name == "teams":
        combined = combined.drop_duplicates(
            subset=["team_id", "season_year"],
            keep="last",
        )

    elif name == "players":
        combined = combined.drop_duplicates(
            subset=["player_id"],
            keep="last",
        )

    elif name == "games":
        combined = combined.drop_duplicates(
            subset=["game_id"],
            keep="last",
        )

    elif name == "player_game_stats":
        combined = combined.drop_duplicates(
            subset=["game_id", "player_id"],
            keep="last",
        )

    combined.to_csv(
        csv_path(name, dir),
        index=False,
    )


def save_csv(dataframes, dir):
    for name, df in dataframes.items():
        if df.empty:
            continue

        merge_csv(name, df, dir)


# ---------------------------------------------------------------------------
# Game processing
# ---------------------------------------------------------------------------

def process_completed_game(
    game_id,
    player_stats,
    dataframes,
):
    """
    Add a completed game's player data to our four existing DataFrames.
    """

    player_stats = clean_player_stats(
        player_stats
    )

    if player_stats.empty:
        print(
            f"  WARNING: No player stats returned for {game_id}."
        )
        return

    players_df = build_players_df(
        player_stats
    )

    stats_df = build_player_game_stats_df(
        game_id,
        player_stats,
    )

    dataframes["players"] = pd.concat(
        [
            dataframes["players"],
            players_df,
        ],
        ignore_index=True,
    )

    dataframes["player_game_stats"] = pd.concat(
        [
            dataframes["player_game_stats"],
            stats_df,
        ],
        ignore_index=True,
    )


def process_date(
    game_date,
    dataframes,
    args,
):
    print()
    print("=" * 70)
    print(f"Processing {game_date}")
    print("=" * 70)

    scoreboard = fetch_scoreboard(
        game_date,
        args.retry_delay,
        args.max_retry_delay,
    )

    request_delay(args.request_delay)

    game_header = get_scoreboard_games(
        scoreboard
    )

    if game_header.empty:
        print(
            f"No games found for {game_date}."
        )
        return {
            "games": 0,
            "completed": 0,
            "stats": 0,
        }

    games_df = build_games_df(
        scoreboard,
        game_date,
    )

    teams_df = build_teams_df(
        scoreboard,
        game_date,
    )

    if not games_df.empty:
        dataframes["games"] = pd.concat(
            [
                dataframes["games"],
                games_df,
            ],
            ignore_index=True,
        )

    if not teams_df.empty:
        dataframes["teams"] = pd.concat(
            [
                dataframes["teams"],
                teams_df,
            ],
            ignore_index=True,
        )

    game_count = len(games_df)

    print(
        f"Found {game_count} game(s) for {game_date}."
    )

    completed = 0
    stats_count = 0

    # Create a lookup from game ID -> GameHeader row.
    game_rows = {}

    for _, row in game_header.iterrows():
        row_dict = row.to_dict()

        game_id = clean_scalar(
            row_dict.get("gameId")
        )

        if game_id is None:
            game_id = clean_scalar(
                row_dict.get("GAME_ID")
            )

        game_id = normalize_game_id(game_id)

        if game_id is not None:
            game_rows[game_id] = row_dict

    for game_id in games_df["game_id"].tolist():
        game = game_rows.get(game_id)

        if game is None:
            print(
                f"  WARNING: No GameHeader row for {game_id}."
            )
            continue

        status_text = (
            clean_scalar(
                game.get("gameStatusText")
            )
            or clean_scalar(
                game.get("GAME_STATUS_TEXT")
            )
            or "Unknown"
        )

        print(
            f"  Game {game_id}: {status_text}"
        )

        if not is_game_final(game):
            print(
                f"    Not final; schedule saved, "
                f"box score skipped."
            )
            continue

        print(
            f"    Fetching BoxScoreTraditionalV3..."
        )

        boxscore = fetch_boxscore(
            game_id,
            args.retry_delay,
            args.max_retry_delay,
        )

        request_delay(args.request_delay)

        player_stats = get_boxscore_player_stats(
            boxscore
        )

        team_stats = get_boxscore_team_stats(
            boxscore
        )

        # Team stats can give us more complete team information than
        # the scoreboard line score. Add them to the existing team frame
        # if necessary.
        if not team_stats.empty:
            team_stats = team_stats.copy()

        before = len(
            dataframes["player_game_stats"]
        )

        process_completed_game(
            game_id,
            player_stats,
            dataframes,
        )

        after = len(
            dataframes["player_game_stats"]
        )

        new_stats = after - before

        if new_stats > 0:
            completed += 1
            stats_count += new_stats

            print(
                f"    Added {new_stats} player stat row(s)."
            )
        else:
            print(
                f"    Box score returned no player rows."
            )

    # Remove duplicates before writing.
    clean_dataframes(dataframes)

    save_csv(dataframes, args.output_dir)


    return {
        "games": game_count,
        "completed": completed,
        "stats": stats_count,
    }


# ---------------------------------------------------------------------------
# Data cleanup / validation
# ---------------------------------------------------------------------------

def clean_dataframes(dataframes):
    if not dataframes["teams"].empty:
        dataframes["teams"] = (
            dataframes["teams"]
            .drop_duplicates(
                subset=[
                    "team_id",
                    "season_year",
                ]
            )
            .reset_index(drop=True)
        )

    if not dataframes["players"].empty:
        dataframes["players"] = (
            dataframes["players"]
            .drop_duplicates(
                subset=["player_id"]
            )
            .reset_index(drop=True)
        )

    if not dataframes["games"].empty:
        dataframes["games"]["game_id"] = (
            dataframes["games"]["game_id"]
            .apply(normalize_game_id)
        )

        dataframes["games"] = (
            dataframes["games"]
            .drop_duplicates(
                subset=["game_id"]
            )
            .reset_index(drop=True)
        )

    if not dataframes["player_game_stats"].empty:
        dataframes["player_game_stats"]["game_id"] = (
            dataframes["player_game_stats"]["game_id"]
            .apply(normalize_game_id)
        )

        dataframes["player_game_stats"] = (
            dataframes["player_game_stats"]
            .drop_duplicates(
                subset=[
                    "game_id",
                    "player_id",
                ]
            )
            .reset_index(drop=True)
        )


def validate_dataframes(dataframes):
    """
    Validate identity columns without rejecting legitimate null statistical
    values for players who did not play.
    """

    required_columns = {
        "teams": TEAMS_COLUMNS,
        "players": PLAYERS_COLUMNS,
        "games": GAMES_COLUMNS,
        "player_game_stats": PLAYER_GAME_STATS_COLUMNS,
    }

    for name, columns in required_columns.items():
        df = dataframes[name]

        if list(df.columns) != columns:
            raise ValueError(
                f"{name} has incorrect columns.\n"
                f"Expected: {columns}\n"
                f"Actual: {list(df.columns)}"
            )

    if not dataframes["games"].empty:
        required = [
            "game_id",
            "season_year",
            "game_date",
            "home_team_id",
            "away_team_id",
        ]

        if dataframes["games"][required].isnull().any().any():
            raise ValueError(
                "Games DataFrame contains null identity fields."
            )

    if not dataframes["player_game_stats"].empty:
        required = [
            "game_id",
            "player_id",
            "team_id",
            "player_game_stats",
        ]

        if (
            dataframes["player_game_stats"][required]
            .isnull()
            .any()
            .any()
        ):
            raise ValueError(
                "Player game stats contains null identity fields."
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    try:
        dates = list(
            get_date_range(args)
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    today = date.today()

    print(
        f"NBA data extraction starting for {today}."
    )

    print(
        f"Date range: {dates[0]} -> {dates[-1]}"
    )

    print(
        f"Total dates: {len(dates)}"
    )

    print(
        f"Output directory: {args.output_dir}"
    )

    # These accumulate the data discovered during this invocation.
    dataframes = empty_dataframes()

    total_games = 0
    total_completed = 0
    total_stats = 0

    failed_dates = []

    for game_date in dates:
        try:
            result = process_date(
                game_date,
                dataframes,
                args,
            )

            total_games += result["games"]
            total_completed += result["completed"]
            total_stats += result["stats"]

        except KeyboardInterrupt:
            print()
            print(
                "Interrupted by user."
            )
            raise

        except Exception as exc:
            # We don't retry the entire date here because individual API
            # requests already retry forever. This catches unexpected
            # programming/data/database errors so the remaining dates can
            # still be processed.
            print()
            print(
                f"ERROR processing {game_date}: "
                f"{type(exc).__name__}: {exc}"
            )
            print(
                "Continuing with the next date."
            )

            failed_dates.append(
                game_date
            )

    # Final cleanup.
    clean_dataframes(
        dataframes
    )

    validate_dataframes(
        dataframes
    )

    save_csv(
        dataframes,
        args.output_dir
    )

    print()
    print("=" * 70)
    print("FINAL EXTRACTION SUMMARY")
    print("=" * 70)

    print(
        f"Date range: {dates[0]} -> {dates[-1]}"
    )

    print(
        f"Games found: {total_games}"
    )

    print(
        f"Completed games processed: {total_completed}"
    )

    print(
        f"Player-game stat rows: {total_stats}"
    )

    print()
    print("Current invocation row counts:")

    for name, df in dataframes.items():
        print(
            f"  {name}: {len(df)}"
        )

    print()
    print("CSV files:")

    for name, filename in CSV_FILES.items():
        print(
            f"  {name}: {filename}"
        )

    if failed_dates:
        print()
        print(
            "Dates with unexpected processing errors:"
        )

        for failed_date in failed_dates:
            print(
                f"  {failed_date}"
            )

        print()
        print(
            "These dates should be run again."
        )

        sys.exit(2)

    print()
    print(
        "Extraction complete."
    )


if __name__ == "__main__":
    main()