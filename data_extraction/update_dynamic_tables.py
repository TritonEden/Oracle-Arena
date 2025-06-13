from modules import *
import sqlalchemy
from sqlalchemy import text

#Env vars: again, no need for a library here
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

DATABASE_URL = get_database_url(host, password, user, port, db_name)
# print(f"Connecting to database at {DATABASE_URL}")

engine = sqlalchemy.create_engine(DATABASE_URL)
connection = engine.connect()

print("Updating dynamic table: winloss")

#Obtain every team id and season year from the Teams and Games tables
with engine.connect() as connection:
    result = connection.execute(text("""
        SELECT DISTINCT t.team_id, g.season_year
        FROM Teams t
        JOIN Games g ON t.team_id = g.home_team_id OR t.team_id = g.away_team_id
        WHERE g.season_year IS NOT NULL AND (t.team_id, g.season_year) NOT IN (SELECT team_id, season_year FROM winloss)
    """))
    team_season_pairs = result.fetchall()

print(f"Found {len(team_season_pairs)} team-season pairs to process.")

#For each team id and season year, calculate the win-loss record
for team_id, season_year in team_season_pairs:
    print(f"Calculating win-loss record for team {team_id} in season {season_year}")

    #Calculate the win-loss record -- this looks compilicated, but all it's doing is aggregating the player_game_stats table to get the team scores, then comparing them to get wins and losses, then aggregating those results to get the final win-loss record
    with engine.connect() as connection:
        result = connection.execute(text("""
            WITH new_player_game_stats AS (
                SELECT DISTINCT ON (game_id, player_id) *
                FROM player_game_stats
            ),
            TeamGames AS (
                SELECT DISTINCT g.game_id, g.game_date,
                    CASE 
                        WHEN g.home_team_id = t.team_id THEN 'home'
                        ELSE 'away'
                    END AS role,
                    g.home_team_id, g.away_team_id
                FROM Games g
                JOIN Teams t ON g.home_team_id = t.team_id OR g.away_team_id = t.team_id
                WHERE t.team_id = :team_id AND g.season_year = :season_year
            ),
            Scores AS (
                SELECT 
                    pgs.game_id, pgs.team_id,
                    SUM((pgs.player_game_stats::JSONB ->> 'PTS')::NUMERIC) AS team_score
                FROM new_player_game_stats pgs
                GROUP BY pgs.game_id, pgs.team_id
            ),
            GameResults AS (
                SELECT tg.game_id::INTEGER, tg.game_date, 
                    s1.team_score::NUMERIC AS team_score,
                    s2.team_score::NUMERIC AS opp_score,
                    CASE WHEN s1.team_score > s2.team_score THEN 1 ELSE 0 END AS win
                FROM TeamGames tg
                JOIN Scores s1 ON tg.game_id::INTEGER = s1.game_id::INTEGER AND s1.team_id::INTEGER = tg.home_team_id::INTEGER
                JOIN Scores s2 ON tg.game_id::INTEGER = s2.game_id::INTEGER AND s2.team_id::INTEGER = tg.away_team_id::INTEGER
                WHERE tg.role = 'home' AND tg.game_id >= 20000000 AND tg.game_id < 30000000

                UNION

                SELECT tg.game_id::INTEGER, tg.game_date, 
                    s1.team_score::NUMERIC AS team_score,
                    s2.team_score::NUMERIC AS opp_score,
                    CASE WHEN s1.team_score > s2.team_score THEN 1 ELSE 0 END AS win
                FROM TeamGames tg
                JOIN Scores s1 ON tg.game_id::INTEGER = s1.game_id::INTEGER AND s1.team_id::INTEGER = tg.away_team_id::INTEGER
                JOIN Scores s2 ON tg.game_id::INTEGER = s2.game_id::INTEGER AND s2.team_id::INTEGER = tg.home_team_id::INTEGER
                WHERE tg.role = 'away' AND tg.game_id >= 20000000 AND tg.game_id < 30000000
            )
            SELECT 
                COUNT(*) FILTER (WHERE win = 1) AS wins,
                COUNT(*) FILTER (WHERE win = 0) AS losses,
                CONCAT(COUNT(*) FILTER (WHERE win = 1), ' - ', COUNT(*) FILTER (WHERE win = 0)) AS wl_record
            FROM GameResults;
        """), {
            "team_id": team_id,
            "season_year": season_year
        })
        result = result.fetchone()
        wins, losses, wl_record = result
        print(f"Team {team_id} in season {season_year} has record {wl_record}")

    #Update the winloss table with the win-loss record
    with engine.connect() as connection:
        #Insert the row. If it already exists, update it. This shouldn't happened due to the initial query, but just in case
        connection.execute(text("""
            INSERT INTO winloss (team_id, season_year, wins, losses, wl_record)
            VALUES (:team_id, :season_year, :wins, :losses, :wl_record)
            ON CONFLICT (team_id, season_year) DO UPDATE 
            SET wins = EXCLUDED.wins,
                losses = EXCLUDED.losses,
                wl_record = EXCLUDED.wl_record;
        """), {
            "team_id": team_id,
            "season_year": season_year,
            "wins": wins,
            "losses": losses,
            "wl_record": wl_record
        })
        connection.commit()

#Add other dynamic tables here, if needed
print("Dynamic tables updated.")

print("Updating each and every materialized view...")

with engine.connect() as connection:
    #Get all materialized views
    result = connection.execute(text("""
        SELECT matviewname FROM pg_matviews;
    """))
    matviews = result.fetchall()

    for matview in matviews:
        matview_name = matview[0]
        print(f"Refreshing materialized view: {matview_name}")
        connection.execute(text(f"REFRESH MATERIALIZED VIEW {matview_name};"))
    connection.commit()
print("All materialized views updated.")
