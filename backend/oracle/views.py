import random
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import connection
from django.db import models
from .utils import get_player_stats_from_csv, get_players_from_csv
from .models import PlayerGameStats
from nba_api.live.nba.endpoints import scoreboard

# def testFunction(request):
#     with connection.cursor() as cursor:
#         # Execute raw SQL query
#         cursor.execute("SELECT * FROM test_table;")
#         rows = cursor.fetchall()  # Get all rows
#         columns = [col[0] for col in cursor.description]  # Get column names

#         # Format the result as a list of dictionaries
#         result = [dict(zip(columns, row)) for row in rows]

#     return JsonResponse(result, safe=False)

def get_player_game_stats(request, player_id):
    with connection.cursor() as cursor:
        # Execute raw SQL query, with paramaterized query to prevent SQL injection
        cursor.execute("SELECT * FROM playergamestats WHERE player_id = %s;", [player_id])
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]
        # Get column names
        return JsonResponse([dict(zip(columns, row)) for row in rows], safe=False)
    
def get_all_player_game_stats(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT * FROM playergamestats;")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

# def get_player_game_stats(request, player_id):
#     stats = get_player_stats_from_csv(player_id)
#     return JsonResponse(stats, safe=False)

# def get_players(request):
#     players = get_players_from_csv()
#     return JsonResponse(players, safe=False)

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


def presentGameSummary(request):
    games = scoreboard.ScoreBoard()

    games_data = games.get_dict()

    data = []

    for game in games_data['scoreboard']['games']: 
        start_time = game['gameStatusText']

        # Home team details
        home_team = game['homeTeam']
        home_stats = {
            "team_name": home_team["teamName"],
            "team_city" : home_team["teamCity"],
            "team_id": home_team["teamId"],
            "team_abbrev": home_team["teamTricode"],
            "wins": home_team["wins"],
            "losses": home_team["losses"],
            "score": home_team["score"]
        }

        # Away team details
        away_team = game['awayTeam']
        away_stats = {
            "team_name": away_team["teamName"],
            "team_city" : away_team["teamCity"],
            "team_id": away_team["teamId"],
            "team_abbrev": away_team["teamTricode"],
            "wins": away_team["wins"],
            "losses": away_team["losses"],
            "score": away_team["score"]
        }

        # Store game data in a dictionary
        game_info = {
            "start_time": start_time,
            "home_team": home_stats,
            "away_team": away_stats
        }

        win_prediction = home_stats["team_abbrev"] if home_stats["wins"] > away_stats["wins"] else away_stats["team_abbrev"]
        over_under_prediction = random.randint(223, 233)
        # Decide whether to add 0.5 or not
        if random.choice([True, False]):
            over_under_prediction = over_under_prediction + 0.5
        else:
            over_under_prediction = over_under_prediction
    
        data.append({
            'startTime': game_info["start_time"],
            'homeTeamLogoID': home_stats["team_id"],
            'homeTeamCity' : home_stats["team_city"],
            'homeTeamName': home_stats["team_name"],
            'awayTeamLogoID': away_stats["team_id"],
            'awayTeamCity' : away_stats["team_city"],
            'awayTeamName': away_stats["team_name"],   
            'predictedWinner': win_prediction,
            'actualWinner': "--",
            'predictedTotal': over_under_prediction,
            'actualTotal': "--"
        })


    response = JsonResponse(data, safe=False)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response