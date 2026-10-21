"""Import the checked-out exports into the local Compose database atomically.

Streams CSV rows through temporary staging tables so memory use stays bounded.
Adds missing stats without replacing restored rows. Metadata is merged by its
natural keys. Predictions and completed-game statuses are preserved.
"""

import argparse
import csv
from io import StringIO
import json
import math
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
COLUMNS = {
    "teams": ["team_id", "season_year", "team_location", "team_name", "team_abbreviation"],
    "players": ["player_id", "first_name", "last_name"],
    "games": ["game_id", "season_year", "game_date", "home_team_id", "away_team_id", "game_time"],
    "player_game_stats": ["game_id", "player_id", "team_id", "player_game_stats"],
}
# Primary keys, the unique identifiers for our stats 
KEYS = {"teams": ["team_id", "season_year"], "players": ["player_id"],
        "games": ["game_id"], "player_game_stats": ["game_id", "player_id"]}

# Used for player_game_stats because of the JSON object with stats 
def clean_json(value):
    # Search within JSON object to replace infinity and Nan with Null
    # Extra check against bad values 
    if isinstance(value, dict):
        return {k: clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


# Keep the last CSV row per team and season, most up to date.
# Update metadata and keep existing values if CSV fields are empty
def merge_teams_sql(columns):
    column_list = ", ".join(columns)
    return f"""
        WITH merged AS (
            INSERT INTO public.teams AS current ({column_list})
            SELECT DISTINCT ON (team_id, season_year) {column_list} FROM stage_teams
            ORDER BY team_id, season_year, import_order DESC
            ON CONFLICT (team_id, season_year) DO UPDATE SET
                team_location = COALESCE(NULLIF(EXCLUDED.team_location, ''), current.team_location),
                team_name = COALESCE(NULLIF(EXCLUDED.team_name, ''), current.team_name),
                team_abbreviation = COALESCE(NULLIF(EXCLUDED.team_abbreviation, ''), current.team_abbreviation)
            RETURNING 1
        ) SELECT 'teams rows merged', count(*) FROM merged;
    """


def import_teams(stream, paths):
    count = stage_csv(stream, "teams", paths)
    stream.write(merge_teams_sql(COLUMNS["teams"]))
    report_staged(stream, "teams", paths, count)


def merge_players_sql(columns):
    column_list = ", ".join(columns)
    return f"""
        WITH merged AS (
            INSERT INTO public.players AS current ({column_list})
            SELECT DISTINCT ON (player_id) {column_list} FROM stage_players
            ORDER BY player_id, import_order DESC
            ON CONFLICT (player_id) DO UPDATE SET
                first_name = COALESCE(NULLIF(EXCLUDED.first_name, ''), current.first_name),
                last_name = COALESCE(NULLIF(EXCLUDED.last_name, ''), current.last_name)
            RETURNING 1
        ) SELECT 'players rows merged', count(*) FROM merged;
    """


def import_players(stream, paths):
    count = stage_csv(stream, "players", paths)
    stream.write(merge_players_sql(COLUMNS["players"]))
    report_staged(stream, "players", paths, count)

# Check incoming game id matches season and teams
GAME_GUARD = """
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM stage_games s JOIN public.games g ON g.game_id = s.game_id
        WHERE (s.season_year, s.home_team_id, s.away_team_id)
              IS DISTINCT FROM (g.season_year, g.home_team_id, g.away_team_id)
    ) THEN
        RAISE EXCEPTION 'CSV game identity conflicts with restored season or teams; import rolled back';
    END IF;
END $$;
"""


def validate_game_identities(stream):
    stream.write(GAME_GUARD)


# Reject season or team conflicts before merging games
# Keep the last CSV row per game and leave predictions untouched
def merge_games_sql(columns):
    column_list = ", ".join(columns)
    # Prevents completed games from being overwritten 
    # by an accidental old csv import
    # This preserves the Final status while other imported fields still update
    return f"""
        WITH merged AS (
            INSERT INTO public.games AS current ({column_list})
            SELECT DISTINCT ON (game_id) {column_list} FROM stage_games
            ORDER BY game_id, import_order DESC
            ON CONFLICT (game_id) DO UPDATE SET
                season_year = EXCLUDED.season_year,
                game_date = EXCLUDED.game_date,
                home_team_id = EXCLUDED.home_team_id,
                away_team_id = EXCLUDED.away_team_id,
                game_time = CASE
                    WHEN current.game_time ILIKE 'Final%' THEN current.game_time
                    ELSE COALESCE(EXCLUDED.game_time, current.game_time)
                END
            RETURNING 1
        ) SELECT 'games rows merged', count(*) FROM merged;
    """


def import_games(stream, paths):
    count = stage_csv(stream, "games", paths)
    validate_game_identities(stream)
    stream.write(merge_games_sql(COLUMNS["games"]))
    report_staged(stream, "games", paths, count)


STATS_GUARD = """
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM stage_player_game_stats s
        LEFT JOIN public.games g ON g.game_id = s.game_id::bigint
        LEFT JOIN public.players p ON p.player_id = s.player_id
        LEFT JOIN public.teams t ON t.team_id = s.team_id AND t.season_year = g.season_year
        WHERE g.game_id IS NULL OR p.player_id IS NULL OR t.team_id IS NULL
    ) THEN
        RAISE EXCEPTION 'CSV stats reference missing games, players, or team seasons; import rolled back';
    END IF;
END $$;
"""


def validate_stats_references(stream):
    stream.write(STATS_GUARD)


# Reject missing references before adding stats
# Prefer non-null points then the last loaded row and keep existing database stats
def merge_player_stats_sql(columns):
    column_list = ", ".join(columns)
    # keep one row per game/player pair
    # and insert into the database
    return f"""
        WITH latest AS (
            SELECT DISTINCT ON (game_id::bigint, player_id) {column_list}
            FROM stage_player_game_stats
            ORDER BY game_id::bigint, player_id,
                     (player_game_stats::jsonb->>'PTS' IS NOT NULL) DESC,
                     import_order DESC
        ), added AS (
            INSERT INTO public.player_game_stats ({column_list})
            SELECT {', '.join('s.' + c for c in columns)} FROM latest s
            WHERE NOT EXISTS (
                SELECT 1 FROM public.player_game_stats existing
                WHERE existing.game_id::bigint = s.game_id::bigint
                  AND existing.player_id = s.player_id
            ) RETURNING 1
        ) SELECT 'player_game_stats rows added', count(*) FROM added;
    """


def import_player_stats(stream, paths):
    count = stage_csv(stream, "player_game_stats", paths)
    validate_stats_references(stream)
    stream.write(merge_player_stats_sql(COLUMNS["player_game_stats"]))
    report_staged(stream, "player_game_stats", paths, count)


# Keep the shared entry point used by existing validation code
def merge_sql(table, columns):
    mergers = {
        "teams": merge_teams_sql,
        "players": merge_players_sql,
        "games": merge_games_sql,
        "player_game_stats": merge_player_stats_sql,
    }
    return mergers[table](columns)


PREDICTION_GUARD = """
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM original_predictions original
        LEFT JOIN public.games g ON g.game_id = original.game_id
        WHERE g.game_id IS NULL OR g.winner IS DISTINCT FROM original.winner
              OR g.total_score_prediction IS DISTINCT FROM original.total_score_prediction
    ) THEN
        RAISE EXCEPTION 'Restored predictions changed; import rolled back';
    END IF;
END $$;
"""


def verify_predictions(stream):
    stream.write(PREDICTION_GUARD)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-dir", type=Path, default=ROOT / "data_extraction/tmp_csvs")
    parser.add_argument("--include-historical", action="store_true", help="Also seed older historical exports")
    parser.add_argument("--dry-run", action="store_true", help="Validate the merge, then roll back without refreshing views")
    return parser.parse_args()


def find_csv_files(csv_dir, include_historical):
    files = {}
    for table in COLUMNS:
        historical = "-full-fixed" if table == "player_game_stats" else "-full"
        suffixes = ([historical] if include_historical else []) + ["_24_25", "_25_26", ""]
        files[table] = [p for suffix in suffixes
                        if (p := csv_dir / f"{table}{suffix}.csv").exists()]
        if not files[table]:
            raise RuntimeError(f"No {table} CSV exports found in {csv_dir}")
    return files


def open_database():
    command = ["docker", "compose", "-f", str(ROOT / "docker-compose.database.yml"),
               "exec", "-T", "database", "sh", "-c",
               'export PGPASSWORD="$POSTGRES_PASSWORD"; exec psql -h 127.0.0.1 '
               '-U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-psqlrc -v ON_ERROR_STOP=1']
    return subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, text=True)


def begin_import(stream):
    stream.write("BEGIN;\n")
    # Serializes competing importers, including tables without a unique key.
    stream.write("SELECT pg_advisory_xact_lock(672913);\n")
    stream.write("LOCK TABLE public.teams, public.players, public.games, public.player_game_stats IN SHARE ROW EXCLUSIVE MODE;\n")
    stream.write("CREATE TEMP TABLE original_predictions ON COMMIT DROP AS SELECT game_id, winner, total_score_prediction FROM public.games;\n")
    stream.write("CREATE INDEX IF NOT EXISTS player_game_stats_game_player_numeric_idx ON public.player_game_stats ((game_id::bigint), player_id);\n")


def clean_row(table, row, path):
    if table == "players":
        row["first_name"] = row.get("first_name", row.get("player_first_name", ""))
        row["last_name"] = row.get("last_name", row.get("player_last_name", ""))
    values = []
    for column in COLUMNS[table]:
        value = row.get(column, "")
        if column.endswith("_id"):
            value = str(int(value))
        elif column == "player_game_stats":
            stats = json.loads(value)
            if isinstance(stats, str):
                stats = json.loads(stats)
            if not isinstance(stats, dict):
                raise ValueError(f"Invalid stats object in {path}")
            value = json.dumps(clean_json(stats), allow_nan=False)
        values.append(value)
    return values


# Import csv into a temporary table
def stage_csv(stream, table, paths):
    column_list = ", ".join(COLUMNS[table])
    copy_options = "FORMAT CSV, FORCE_NULL (game_time)" if table == "games" else "FORMAT CSV"
    stream.write(
        f"CREATE TEMP TABLE stage_{table} ON COMMIT DROP AS "
        f"SELECT {column_list} FROM public.{table} WITH NO DATA;\n"
        f"ALTER TABLE stage_{table} ADD COLUMN import_order BIGSERIAL;\n"
        f"COPY stage_{table} ({column_list}) FROM STDIN WITH ({copy_options});\n"
    )
    count = 0
    for path in paths:
        with path.open(newline="") as source:
            for row in csv.DictReader(source):
                values = clean_row(table, row, path)
                buffer = StringIO()
                csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_ALL).writerow(values)
                stream.write(buffer.getvalue())
                count += 1
    stream.write("\\.\n")
    return count


def report_staged(stream, table, paths, count):
    stream.flush()
    print(f"Staged {count} {table} rows from {len(paths)} exports.", flush=True)


def finish_import(stream, dry_run):
    if dry_run:
        stream.write("\nROLLBACK;\n")
    else:
        stream.write((ROOT / "backend/database/refresh_analytics_objects.sql").read_text())
        stream.write("\nCOMMIT;\n")


def main():
    args = parse_args()
    files = find_csv_files(args.csv_dir, args.include_historical)
    with open_database() as process:
        try:
            stream = process.stdin
            begin_import(stream)
            import_teams(stream, files["teams"])
            import_players(stream, files["players"])
            import_games(stream, files["games"])
            import_player_stats(stream, files["player_game_stats"])
            verify_predictions(stream)
            finish_import(stream, args.dry_run)
            stream.close()
            if process.wait() != 0:
                raise RuntimeError("CSV import failed; PostgreSQL rolled back the transaction.")
        except BaseException:
            if not process.stdin.closed:
                process.stdin.close()
            process.wait()
            raise
    print("CSV dry run passed; all changes rolled back." if args.dry_run
          else "CSV import and analytics refresh committed successfully.")


if __name__ == "__main__":
    main()
