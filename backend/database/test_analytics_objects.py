"""Integration checks in a disposable PostgreSQL container; no mounts or ports.

Requires Docker and the postgres:16-alpine image. Run with Python's standard library.
The container is capped at 256 MiB and is removed even when an assertion fails.
"""

import json
from pathlib import Path
import subprocess
import time
import uuid

from import_local_csvs import COLUMNS, GAME_GUARD, PREDICTION_GUARD, merge_sql


HERE = Path(__file__).resolve().parent
IMAGE = "postgres:16-alpine"


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs)


def main():
    name = "oracle-analytics-test-" + uuid.uuid4().hex[:12]
    run("docker", "run", "--detach", "--rm", "--name", name,
        "--memory", "256m", "--memory-swap", "256m", "--cpus", "0.5",
        "--network", "none", "--env", "POSTGRES_HOST_AUTH_METHOD=trust",
        "--env", "PGDATA=/tmp/oracle-test-data", IMAGE,
        "-c", "shared_buffers=16MB", "-c", "max_connections=10")

    def sql(statement):
        return run("docker", "exec", "--interactive", name,
                   "psql", "-U", "postgres", "-d", "postgres",
                   "--no-psqlrc", "--set", "ON_ERROR_STOP=1",
                   "--single-transaction", "--tuples-only", "--no-align",
                   input=statement).stdout.strip()

    def expect(query, expected):
        actual = sql(query)
        assert actual == expected, f"{query}\nExpected {expected!r}; got {actual!r}"

    try:
        for _ in range(60):
            ready = subprocess.run(
                ["docker", "exec", name, "pg_isready", "-U", "postgres"],
                capture_output=True, timeout=5,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Disposable PostgreSQL did not start.")

        for ids_type, stats_type, optional_columns in [
            ("text", "text", True), ("bigint", "jsonb", True),
            ("text", "jsonb", False), ("bigint", "json", False),
        ]:
            sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            extra = ", game_time text, winner numeric, total_score_prediction numeric" if optional_columns else ""
            source_id = "id bigserial PRIMARY KEY," if optional_columns else ""
            sql(f"""
                CREATE TABLE public.teams (team_id integer, season_year text,
                    team_location text, team_name text, team_abbreviation text,
                    PRIMARY KEY(team_id, season_year));
                CREATE TABLE public.games (game_id {ids_type} PRIMARY KEY,
                    season_year text, game_date date, home_team_id integer,
                    away_team_id integer{extra});
                CREATE TABLE public.player_game_stats ({source_id}
                    game_id {ids_type}, player_id integer, team_id integer,
                    player_game_stats {stats_type});
                INSERT INTO teams VALUES
                    (1, '2024-25', 'Home', 'Home team', 'HOM'),
                    (2, '2024-25', 'Away', 'Away team', 'AWY'),
                    (3, '2024-25', 'Idle', 'Idle team', 'IDL'),
                    (1, '2023-24', 'Old', 'Old home name', 'OLD');
                INSERT INTO games (game_id, season_year, game_date, home_team_id, away_team_id)
                    VALUES ('0022400001', '2024-25', '2024-10-22', 1, 2),
                           ('0022400002', '2024-25', '2024-10-23', 1, 2),
                           ('0022400003', '2024-25', '2024-10-24', 1, 2),
                           ('0022400004', '2024-25', '2024-10-25', 1, 2);
            """)
            if optional_columns:
                sql("""UPDATE games SET game_time = 'Final', winner = 1,
                           total_score_prediction = 55 WHERE game_id::bigint = 22400001;
                       UPDATE games SET game_time = 'Final/OT' WHERE game_id::bigint = 22400002;
                       UPDATE games SET game_time = '7:00 PM ET' WHERE game_id::bigint = 22400003;
                       UPDATE games SET game_time = 'Q3' WHERE game_id::bigint = 22400004;""")

            def insert(game, player, team, stats, double_encoded=False):
                payload = json.dumps(stats)
                if double_encoded:
                    payload = json.dumps(payload)
                literal = "'" + payload.replace("'", "''") + "'"
                sql(f"INSERT INTO player_game_stats(game_id, player_id, team_id, player_game_stats) "
                    f"VALUES ('{game}', {player}, {team}, {literal});")

            insert("0022400001", 11, 1, {"MIN": "30.000000:30", "PTS": 10, "AST": 2, "PLAYER_ID": 11})
            insert("22400001", 11, 1, {"MIN": "30.000000:30", "PTS": 10, "AST": 2, "PLAYER_ID": 11}, True)
            insert("0022400001", 12, 1, {"MIN": "20:00", "PTS": 20})
            insert("0022400001", 21, 2, {"MIN": "30:00", "PTS": 25})
            insert("0022400001", 13, 1, {"MIN": "0:00", "PTS": 0, "AST": 0})
            insert("0022400002", 11, 1, {"MIN": "20.000000:30", "PTS": 20, "AST": 4})
            insert("0022400002", 21, 2, {"MIN": "30:00", "PTS": 30})
            if optional_columns:
                insert("0022400004", 31, 1, {"MIN": "5:00", "PTS": 5})
                insert("0022400004", 41, 2, {"MIN": "5:00", "PTS": 4})

            create = (HERE / "analytics_objects.sql").read_text()
            refresh = (HERE / "refresh_analytics_objects.sql").read_text()
            sql(create)
            sql(create)  # Safe to rerun without dropping existing definitions/data.
            expect("SELECT count(*) FROM pg_matviews WHERE schemaname = 'public';", "4")
            expect("SELECT count(*) FROM player_game_stats_slim WHERE game_id=22400001 AND player_id=11;", "1")
            expect("SELECT player_game_stats::jsonb->>'PTS' FROM player_game_stats_slim WHERE game_id=22400001 AND player_id=11;", "10")
            expect("SELECT count(*) FROM player_season_averages WHERE player_id=13;", "0")
            expect("SELECT avg_val=15 FROM player_season_averages WHERE player_id=11 AND key='PTS';", "t")
            expect("SELECT avg_val=25.5 FROM player_season_averages WHERE player_id=11 AND key='MIN';", "t")
            expect("SELECT count(*) FROM player_season_averages WHERE key='PLAYER_ID';", "0")
            expect("SELECT home_score || '|' || away_score || '|' || home_team_name FROM mv_game_stats WHERE game_id=22400001;", "30|25|Home team")
            expect("SELECT home_score || '|' || away_score FROM mv_game_stats WHERE game_id=22400003;", "0|0")
            expect("SELECT wins || '|' || losses || '|' || wl_record FROM mv_team_win_loss_records WHERE target_team_id=1 AND season_year='2024-25';", "1|1|1 - 1")
            expect("SELECT wl_record FROM mv_team_win_loss_records WHERE target_team_id=3;", "0 - 0")
            expect("SELECT count(*) FROM mv_game_stats WHERE game_date='2024-10-22';", "1")
            expect("SELECT pg_typeof(jsonb_object_agg(key, avg_val)::text) FROM player_season_averages WHERE player_id=11;", "text")
            if not optional_columns:
                expect("SELECT winner IS NULL AND total_score_prediction IS NULL AND game_time IS NULL FROM mv_game_stats WHERE game_id=22400001;", "t")
            # Merge against tables without a unique player/game key. Leading-zero
            # IDs must match restored rows, and reruns must not insert duplicates.
            sql("""
                CREATE TEMP TABLE stage_player_game_stats AS
                    SELECT game_id, player_id, team_id, player_game_stats
                    FROM player_game_stats WITH NO DATA;
                ALTER TABLE stage_player_game_stats ADD COLUMN import_order BIGSERIAL;
                INSERT INTO stage_player_game_stats(game_id,player_id,team_id,player_game_stats)
                    VALUES ('00022400001',11,1,'{"MIN":"30:00","PTS":999}'),
                           ('0022400003',99,1,'{"MIN":"5:00","PTS":3}'),
                           ('22400003',99,1,'{"MIN":"5:00","PTS":4}');
            """ + merge_sql("player_game_stats", COLUMNS["player_game_stats"])
                + merge_sql("player_game_stats", COLUMNS["player_game_stats"]) + """
                DO $$ BEGIN
                    IF (SELECT count(*) FROM player_game_stats WHERE game_id::bigint=22400001 AND player_id=11) <> 2
                        OR EXISTS (SELECT 1 FROM player_game_stats WHERE player_game_stats::jsonb->>'PTS'='999')
                        OR (SELECT count(*) FROM player_game_stats WHERE player_id=99) <> 1
                        OR (SELECT player_game_stats::jsonb->>'PTS' FROM player_game_stats WHERE player_id=99) <> '4'
                    THEN RAISE EXCEPTION 'Stats merge failed preservation or idempotency'; END IF;
                END $$;
            """)
            # The restored/fresh source games table uses numeric primary keys;
            # text-game fixtures above exercise analytics compatibility only.
            if optional_columns and ids_type == "bigint":
                sql("""
                    CREATE TEMP TABLE original_predictions AS SELECT game_id,winner,total_score_prediction FROM games;
                    CREATE TEMP TABLE stage_games AS
                        SELECT game_id,season_year,game_date,home_team_id,away_team_id,game_time
                        FROM games WITH NO DATA;
                    ALTER TABLE stage_games ADD COLUMN import_order BIGSERIAL;
                    INSERT INTO stage_games(game_id,season_year,game_date,home_team_id,away_team_id,game_time)
                        VALUES ('22400001','2024-25','2024-10-22',1,2,'Q3'),
                               ('22400005','2024-25','2024-10-26',1,2,'TBD');
                """ + GAME_GUARD + merge_sql("games", COLUMNS["games"])
                    + merge_sql("games", COLUMNS["games"]) + PREDICTION_GUARD + """
                    DO $$ BEGIN
                        IF (SELECT game_time FROM games WHERE game_id::bigint=22400001) <> 'Final'
                            OR (SELECT count(*) FROM games WHERE game_id::bigint=22400005) <> 1
                        THEN RAISE EXCEPTION 'Game merge failed completed status or idempotency'; END IF;
                    END $$;
                """)
            sql("UPDATE player_game_stats SET player_game_stats = "
                "'{\"MIN\":\"30:00\",\"PTS\":40}' WHERE player_id=21 AND game_id::bigint=22400001;")
            expect("SELECT wl_record FROM mv_team_win_loss_records WHERE target_team_id=1 AND season_year='2024-25';", "1 - 1")
            sql(refresh)
            expect("SELECT away_score FROM mv_game_stats WHERE game_id=22400001;", "40")
            expect("SELECT wl_record FROM mv_team_win_loss_records WHERE target_team_id=1 AND season_year='2024-25';", "0 - 2")
            print(f"PASS: {ids_type} IDs, {stats_type} stats, optional game columns={optional_columns}")
        print("All analytics integration checks passed.")
    finally:
        run("docker", "stop", "--time", "5", name)
        print("Disposable PostgreSQL container and its volumes removed.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(error.stderr)
        raise
