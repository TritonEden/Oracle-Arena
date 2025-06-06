import random
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import connection
from django.db import models
from .utils import get_player_stats_from_csv, get_players_from_csv
from .models import PlayerGameStats
from nba_api.live.nba.endpoints import scoreboard

# Gets all player game stats
def get_player_game_stats(request, player_id):
    with connection.cursor() as cursor:
        # Execute raw SQL query, with paramaterized query to prevent SQL injection
        cursor.execute("""
                        WITH new_player_game_stats as (
                            SELECT DISTINCT ON (game_id, player_id) *
                            FROM player_game_stats
                        ) SELECT * FROM new_player_game_stats WHERE player_id::INT = %s;
                       """, [player_id])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]
        # Get column names
        return JsonResponse([dict(zip(columns, row)) for row in rows], safe=False)

def get_player_game_stats_by_game(request, game_id):
    with connection.cursor() as cursor:
        # Execute raw SQL query, with paramaterized query to prevent SQL injection
        cursor.execute("""
                        WITH new_player_game_stats as (
                            SELECT DISTINCT ON (game_id, player_id) *
                            FROM player_game_stats
                        ) SELECT * FROM new_player_game_stats WHERE game_id::INT = %s;
                       """, [game_id])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]
        # Get column names
        return JsonResponse([dict(zip(columns, row)) for row in rows], safe=False)


# Gets all player game stats
def get_game(request, game_id):
    with connection.cursor() as cursor:
        # Execute raw SQL query, with paramaterized query to prevent SQL injection
        cursor.execute("SELECT * FROM games WHERE game_id = %s;", [game_id])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]
        # Get column names
        return JsonResponse([dict(zip(columns, row)) for row in rows], safe=False)
    
def get_all_player_game_stats(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("""
                        WITH new_player_game_stats as (
                            SELECT DISTINCT ON (game_id, player_id) *
                            FROM player_game_stats
                        ) SELECT * FROM new_player_game_stats;""")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

def get_current_season(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT MAX(season_year) FROM games;")
        row = cursor.fetchone()  # Get the single row
        current_season = row[0] if row else None  # Extract the value

    return JsonResponse({"current_season": current_season})

# Given a day, return all the game IDs for that day
def get_game_ids(request, date):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT game_id FROM games WHERE game_date = %s;", [date])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

# Gets the wins and losses for the SEASON for a given team and season year
def get_wins_losses(request, team_id, season_year):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM winloss
            WHERE season_year = %s AND team_id = %s;
            """, [season_year, team_id])
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]  # Get column names
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result[0] if result else {"wins": 0, "losses": 0, "wl_record": "0 - 0"})

#Given a team id and season year, show all of the games and results from that game -- essentially it is how the wins and losses are calculated
def get_team_game_results(request, team_id, season_year):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("""
            WITH new_player_game_stats as (
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
                WHERE t.team_id = %s AND g.season_year = %s
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
                WHERE tg.role = 'home'

                UNION

                SELECT tg.game_id::INTEGER, tg.game_date, 
                    s1.team_score::NUMERIC AS team_score,
                    s2.team_score::NUMERIC AS opp_score,
                    CASE WHEN s1.team_score > s2.team_score THEN 1 ELSE 0 END AS win
                FROM TeamGames tg
                JOIN Scores s1 ON tg.game_id::INTEGER = s1.game_id::INTEGER AND s1.team_id::INTEGER = tg.away_team_id::INTEGER
                JOIN Scores s2 ON tg.game_id::INTEGER = s2.game_id::INTEGER AND s2.team_id::INTEGER = tg.home_team_id::INTEGER
                WHERE tg.role = 'away'
            ),
            Streak AS (
                SELECT *, 
                    ROW_NUMBER() OVER (ORDER BY game_date ASC) AS rn,
                    SUM(win) OVER (ORDER BY game_date ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_wins
                FROM GameResults
            )
            SELECT *
            FROM GameResults;
        """, [team_id, season_year])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

def get_players(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT * FROM players;")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

def get_teams(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT * FROM teams;")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

def get_games(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT * FROM games;")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

# Gets the player stats for a given player and season year
def get_player_stats_for_season(request, player_id, season_year):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("""
            WITH new_player_game_stats as (
                SELECT DISTINCT ON (game_id, player_id) *
                FROM player_game_stats
            )
            SELECT pgs.game_id, pgs.player_game_stats
            FROM new_player_game_stats pgs
            JOIN Games g ON g.game_id = pgs.game_id::INTEGER
            WHERE pgs.player_id = %s
            AND g.season_year = %s;
        """, [player_id, season_year])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

# Gets the average stats for a player for a given season
def get_player_average_stats_for_season(request, player_id, season_year):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("""
            WITH new_player_game_stats as (
                SELECT DISTINCT ON (game_id, player_id) *
                FROM player_game_stats
            )
            SELECT 
                jsonb_object_agg(key, avg_val) AS average_stats
            FROM (
            SELECT 
                key,
                AVG((value)::NUMERIC) AS avg_val
            FROM new_player_game_stats pgs
            JOIN Games g ON g.game_id = pgs.game_id::INTEGER
            CROSS JOIN LATERAL jsonb_each_text(pgs.player_game_stats::JSONB)
            WHERE pgs.player_id::INTEGER = %s::INTEGER
                AND g.season_year = %s
                AND value ~ '^\d+(\.\d+)?$'  -- only allow numbers or decimals
            GROUP BY key
            ) sub;
        """, [player_id, season_year])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

#Gets home and away team names given a game date -- used for the game summary page
def get_home_away_team_info_on_date(request, game_date):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("""
            WITH new_player_game_stats as (
                SELECT DISTINCT ON (game_id, player_id) *
                FROM player_game_stats
            ),
            TeamScores AS (
                SELECT 
                    pgs.game_id::TEXT AS game_id,
                    pgs.team_id::TEXT AS team_id,
                    SUM((pgs.player_game_stats::JSONB ->> 'PTS')::NUMERIC) AS team_score
                FROM new_player_game_stats pgs
                GROUP BY pgs.game_id, pgs.team_id
            ), 
            GameStats AS (
                SELECT 
                    ht.team_location AS home_team_location,
                    ht.team_name AS home_team_name,
                    ht.team_abbreviation AS home_team_abbreviation,
                    ht.team_id AS home_team_id,
                    at.team_location AS away_team_location,
                    at.team_name AS away_team_name,
                    at.team_abbreviation AS away_team_abbreviation,
                    at.team_id AS away_team_id,
                    COALESCE(hs.team_score, -1) AS home_score,
                    COALESCE(ascore.team_score, -1) AS away_score,
                    g.game_date,
                    g.season_year AS season_year,
                    g.game_id AS game_id,
                    g.game_time AS game_time,
                    g.winner AS winner,
                    g.total_score_prediction as total_score_prediction
                FROM games g
                JOIN teams ht 
                    ON g.home_team_id::TEXT = ht.team_id::TEXT AND g.season_year = ht.season_year
                JOIN teams at 
                    ON g.away_team_id::TEXT = at.team_id::TEXT AND g.season_year = at.season_year
                LEFT JOIN TeamScores hs 
                    ON hs.game_id = g.game_id::TEXT AND hs.team_id = g.home_team_id::TEXT
                LEFT JOIN TeamScores ascore 
                    ON ascore.game_id = g.game_id::TEXT AND ascore.team_id = g.away_team_id::TEXT
                WHERE g.game_date = %s
            )
            SELECT * FROM GameStats;


        """, [game_date])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        result = []
        for row in rows:
            game_id = row[columns.index('game_id')]
            season_year = row[columns.index('season_year')]
            game_time = row[columns.index('game_time')]
            
            home_stats = {
                "team_id": row[columns.index('home_team_id')],
                "team_city": row[columns.index('home_team_location')],
                "team_name": row[columns.index('home_team_name')],
                "team_abbreviation": row[columns.index('home_team_abbreviation')],
                "team_score" : int(row[columns.index('home_score')])
            }

            away_stats = {
                "team_id": row[columns.index('away_team_id')],
                "team_city": row[columns.index('away_team_location')],
                "team_name": row[columns.index('away_team_name')],
                "team_abbreviation": row[columns.index('away_team_abbreviation')],
                "team_score" : int(row[columns.index('away_score')])
            }

            total_score_prediction = row[columns.index('total_score_prediction')]
            total_score = int((float(row[columns.index('home_score')])) + (float(row[columns.index('away_score')])))
            total_score_actual = str(total_score) if (
                float(row[columns.index('home_score')]) + float(row[columns.index('away_score')]) > 0
            ) else '--'
            
            winner_prediction_binary = row[columns.index('winner')]
            winner_prediction = home_stats["team_abbreviation"] if winner_prediction_binary == 1.0 else away_stats["team_abbreviation"]
            
            if total_score_actual != '--':
                winner_actual = (
                    home_stats["team_abbreviation"]
                    if home_stats["team_score"] > away_stats["team_score"]
                    else away_stats["team_abbreviation"]
                )
            else:
                winner_actual = '--'

            # Construct the result dictionary
            game_info = {
                'gameId' : game_id,
                'seasonYear' : season_year,
                'startTime' : game_time,
                'homeTeamID' : home_stats["team_id"],
                'homeTeamLogoID': home_stats["team_id"],
                'homeTeamCity': home_stats["team_city"],
                'homeTeamName': home_stats["team_name"],
                'homeTeamAbbreviation': home_stats["team_abbreviation"],
                'homeTeamScore' : home_stats["team_score"],
                'awayTeamID' : away_stats["team_id"],
                'awayTeamLogoID': away_stats["team_id"],
                'awayTeamCity': away_stats["team_city"],
                'awayTeamName': away_stats["team_name"],
                'awayTeamAbbreviation': away_stats["team_abbreviation"],
                'awayTeamScore' : away_stats["team_score"],
                'predictedWinner': winner_prediction,
                'actualWinner': winner_actual,
                'predictedTotal': total_score_prediction,
                'actualTotal': total_score_actual
            }

            result.append(game_info)

    return JsonResponse(result, safe=False)

#Gets all players from a team, given a season and team
def get_players_from_team(request, team_id, season_year):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT 
                p.player_id,
                p.first_name,
                p.last_name
            FROM player_game_stats pgs
            JOIN players p ON p.player_id = pgs.player_id::INTEGER
            JOIN games g ON g.game_id = pgs.game_id::INTEGER
            WHERE pgs.team_id = %s
            AND g.season_year = %s;
        """, [team_id, season_year])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

# def presentGameSummary(request):
#     games = scoreboard.ScoreBoard()

#     games_data = games.get_dict()

#     data = []

#     for game in games_data['scoreboard']['games']: 
#         start_time = game['gameStatusText']

#         # Home team details
#         home_team = game['homeTeam']
#         home_stats = {
#             "team_name": home_team["teamName"],
#             "team_city" : home_team["teamCity"],
#             "team_id": home_team["teamId"],
#             "team_abbrev": home_team["teamTricode"],
#             "wins": home_team["wins"],
#             "losses": home_team["losses"],
#             "score": home_team["score"]
#         }

#         # Away team details
#         away_team = game['awayTeam']
#         away_stats = {
#             "team_name": away_team["teamName"],
#             "team_city" : away_team["teamCity"],
#             "team_id": away_team["teamId"],
#             "team_abbrev": away_team["teamTricode"],
#             "wins": away_team["wins"],
#             "losses": away_team["losses"],
#             "score": away_team["score"]
#         }

#         # Store game data in a dictionary
#         game_info = {
#             "start_time": start_time,
#             "home_team": home_stats,
#             "away_team": away_stats
#         }

#         win_prediction = home_stats["team_abbrev"] if home_stats["wins"] > away_stats["wins"] else away_stats["team_abbrev"]
#         over_under_prediction = random.randint(223, 233)
#         # Decide whether to add 0.5 or not
#         if random.choice([True, False]):
#             over_under_prediction = over_under_prediction + 0.5
#         else:
#             over_under_prediction = over_under_prediction
    
#         data.append({
#             'startTime': game_info["start_time"],
#             'homeTeamLogoID': home_stats["team_id"],
#             'homeTeamCity' : home_stats["team_city"],
#             'homeTeamName': home_stats["team_name"],
#             'awayTeamLogoID': away_stats["team_id"],
#             'awayTeamCity' : away_stats["team_city"],
#             'awayTeamName': away_stats["team_name"],   
#             'predictedWinner': win_prediction,
#             'actualWinner': "--",
#             'predictedTotal': over_under_prediction,
#             'actualTotal': "--"
#         })


#     response = JsonResponse(data, safe=False)
#     response['Access-Control-Allow-Origin'] = '*'
#     response['Access-Control-Allow-Methods'] = 'GET'
#     response['Access-Control-Allow-Headers'] = 'Content-Type'
    
#     return response