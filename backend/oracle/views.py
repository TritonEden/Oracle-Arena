import random
from django.http import JsonResponse
from django.db import connection
from django.db import models
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

def playerSummary(request, playerid):
    data = [
        {"player_name": "Leanne Graham", "points_per_game": 11.38, "player_team": "Kulas Light"},
        {"player_name": "Ervin Howell", "points_per_game": 5.47, "player_team": "Victor Plains"},
        {"player_name": "Clementine Bauch", "points_per_game": 26.50, "player_team": "Douglas Extension"},
        {"player_name": "Patricia Lebsack", "points_per_game": 17.54, "player_team": "Hoeger Mall"},
        {"player_name": "Chelsey Dietrich", "points_per_game": 19.87, "player_team": "Skiles Walks"},
        {"player_name": "Mrs. Dennis Schulist", "points_per_game": 12.70, "player_team": "Norberto Crossing"},
        {"player_name": "Kurtis Weissnat", "points_per_game": 15.11, "player_team": "Rex Trail"},
        {"player_name": "Nicholas Runolfsdottir V", "points_per_game": 19.58, "player_team": "Ellsworth Summit"},
        {"player_name": "Glenna Reichert", "points_per_game": 10.53, "player_team": "Dayna Park"},
        {"player_name": "Clementina DuBuque", "points_per_game": 15.55, "player_team": "Kattie Turnpike"}
    ]
    return JsonResponse(data, safe=False)

# Mock player stats data
# def player_stats(request):
#     player_stats = [
#         {
#             "game_id": "0021800001",
#             "player_id": 203967,
#             "team_id": 1610612755,
#             "player_game_stats": {"PF": 5.0, "TO": 3.0, "AST": 1.0, "BLK": 0.0, "FGA": 8.0, "FGM": 3.0, "FTA": 0.0, "FTM": 0.0, "MIN": "22.000000:54", "PTS": 6.0, "REB": 6.0, "STL": 0.0, "DREB": 6.0, "FG3A": 4.0, "FG3M": 0.0, "OREB": 0.0, "FG_PCT": 0.375, "FT_PCT": 0.0, "FG3_PCT": 0.0, "PLUS_MINUS": -4.0}
#         },
#         {
#             "game_id": "0021800001",
#             "player_id": 203496,
#             "team_id": 1610612755,
#             "player_game_stats": {"PF": 5.0, "TO": 3.0, "AST": 1.0, "BLK": 0.0, "FGA": 8.0, "FGM": 3.0, "FTA": 0.0, "FTM": 0.0, "MIN": "22.000000:54", "PTS": 6.0, "REB": 6.0, "STL": 0.0, "DREB": 6.0, "FG3A": 4.0, "FG3M": 0.0, "OREB": 0.0, "FG_PCT": 0.375, "FT_PCT": 0.0, "FG3_PCT": 0.0, "PLUS_MINUS": -4.0}
#         }
#     ]
    
#     return JsonResponse(player_stats, safe=False)

from django.db import connection

def player_stats(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM public."oracle_playergamestats" LIMIT 1000')
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        # # Log the rows and columns
        # print("Rows:", rows)
        # print("Columns:", columns)

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