from django.http import JsonResponse
from django.db import connection

def testfunction(request):
    with connection.cursor() as cursor:
        # Execute raw SQL query
        cursor.execute("SELECT * FROM test_table;")
        rows = cursor.fetchall()  # Get all rows
        columns = [col[0] for col in cursor.description]  # Get column names

        # Format the result as a list of dictionaries
        result = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(result, safe=False)

def playersummary(request, playerid):
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