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
KEYS = {"teams": ["team_id", "season_year"], "players": ["player_id"],
        "games": ["game_id"], "player_game_stats": ["game_id", "player_id"]}


def clean_json(value):
    if isinstance(value, dict):
        return {k: clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def merge_sql(table, columns):
    column_list = ", ".join(columns)
    key_list = ", ".join(KEYS[table])
    if table == "player_game_stats":
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
    assignments = []
    for column in columns:
        if column in KEYS[table]:
            continue
        if table == "games" and column == "game_time":
            expression = "CASE WHEN current.game_time ILIKE 'Final%' THEN current.game_time ELSE COALESCE(EXCLUDED.game_time, current.game_time) END"
        elif table in {"teams", "players"}:
            expression = f"COALESCE(NULLIF(EXCLUDED.{column}, ''), current.{column})"
        else:
            expression = f"EXCLUDED.{column}"
        assignments.append(f"{column} = {expression}")
    return f"""
        WITH merged AS (
            INSERT INTO public.{table} AS current ({column_list})
            SELECT DISTINCT ON ({key_list}) {column_list} FROM stage_{table}
            ORDER BY {key_list}, import_order DESC
            ON CONFLICT ({key_list}) DO UPDATE SET {', '.join(assignments)}
            RETURNING 1
        ) SELECT '{table} rows merged', count(*) FROM merged;
    """


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-dir", type=Path, default=ROOT / "data_extraction/tmp_csvs")
    parser.add_argument("--include-historical", action="store_true", help="Also seed older historical exports")
    parser.add_argument("--dry-run", action="store_true", help="Validate the merge, then roll back without refreshing views")
    args = parser.parse_args()
    files = {}
    for table in COLUMNS:
        historical = "-full-fixed" if table == "player_game_stats" else "-full"
        suffixes = ([historical] if args.include_historical else []) + ["_24_25", "_25_26", ""]
        files[table] = [p for suffix in suffixes
                        if (p := args.csv_dir / f"{table}{suffix}.csv").exists()]
        if not files[table]:
            raise RuntimeError(f"No {table} CSV exports found in {args.csv_dir}")
    command = ["docker", "compose", "-f", str(ROOT / "docker-compose.database.yml"),
               "exec", "-T", "database", "sh", "-c",
               'export PGPASSWORD="$POSTGRES_PASSWORD"; exec psql -h 127.0.0.1 '
               '-U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-psqlrc -v ON_ERROR_STOP=1']
    with subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, text=True) as process:
        try:
            process.stdin.write("BEGIN;\n")
            # Serializes competing importers, including tables without a unique key.
            process.stdin.write("SELECT pg_advisory_xact_lock(672913);\n")
            process.stdin.write("LOCK TABLE public.teams, public.players, public.games, public.player_game_stats IN SHARE ROW EXCLUSIVE MODE;\n")
            process.stdin.write("CREATE TEMP TABLE original_predictions ON COMMIT DROP AS SELECT game_id, winner, total_score_prediction FROM public.games;\n")
            process.stdin.write("CREATE INDEX IF NOT EXISTS player_game_stats_game_player_numeric_idx ON public.player_game_stats ((game_id::bigint), player_id);\n")
            for table, columns in COLUMNS.items():
                column_list = ", ".join(columns)
                key_list = ", ".join(KEYS[table])
                copy_options = "FORMAT CSV, FORCE_NULL (game_time)" if table == "games" else "FORMAT CSV"
                process.stdin.write(
                    f"CREATE TEMP TABLE stage_{table} ON COMMIT DROP AS "
                    f"SELECT {column_list} FROM public.{table} WITH NO DATA;\n"
                    f"ALTER TABLE stage_{table} ADD COLUMN import_order BIGSERIAL;\n"
                    f"COPY stage_{table} ({column_list}) FROM STDIN WITH ({copy_options});\n"
                )
                count = 0
                for path in files[table]:
                    with path.open(newline="") as source:
                        for row in csv.DictReader(source):
                            if table == "players":
                                row["first_name"] = row.get("first_name", row.get("player_first_name", ""))
                                row["last_name"] = row.get("last_name", row.get("player_last_name", ""))
                            values = []
                            for column in columns:
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
                            buffer = StringIO()
                            csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_ALL).writerow(values)
                            process.stdin.write(buffer.getvalue())
                            count += 1
                process.stdin.write("\\.\n")
                if table == "games":
                    process.stdin.write(GAME_GUARD)
                if table == "player_game_stats":
                    process.stdin.write(STATS_GUARD)
                process.stdin.write(merge_sql(table, columns))
                process.stdin.flush()
                print(f"Staged {count} {table} rows from {len(files[table])} exports.", flush=True)
            process.stdin.write(PREDICTION_GUARD)
            if args.dry_run:
                process.stdin.write("\nROLLBACK;\n")
            else:
                process.stdin.write((ROOT / "backend/database/refresh_analytics_objects.sql").read_text())
                process.stdin.write("\nCOMMIT;\n")
            process.stdin.close()
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
