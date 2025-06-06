"""
URL configuration for oracle project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
# from .views import testfunction, playersummary, gamesummary
# from .views import presentGameSummary, player_stats, get_player_game_stats
from .views import get_players, get_player_game_stats, get_games, get_teams, get_all_player_game_stats, get_players, get_wins_losses, get_game_ids, get_player_stats_for_season, get_player_average_stats_for_season, get_players_from_team, get_team_game_results, get_game, get_home_away_team_info_on_date, get_player_game_stats_by_game, get_current_season
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('testfunction/', testfunction),
    #make a path that takes in just a playerid
    # path('playersummary/<int:playerid>/', playersummary),
    # path('presentGameSummary/', presentGameSummary),
    path('api/player_stats/', get_players, name='get_players'),
    # path('api/player_stats/', player_stats, name='player_stats'),
    path("api/player_game_stats/<int:player_id>/", get_player_game_stats, name="player_game_stats"),
    path("api/player_game_stats_by_game/<int:game_id>/", get_player_game_stats_by_game, name="player_game_stats_by_game"),
    path("api/player_game_stats/", get_all_player_game_stats, name="all_player_game_stats"),
    path("api/get_current_season", get_current_season, name="current_season"),
    path("api/game/<int:game_id>/", get_game, name="game"),
    path("api/games/", get_games, name="games"),
    path("api/teams/", get_teams, name="teams"),
    path("api/players/", get_players, name="players"),
    path("api/wins_losses/<int:team_id>/<str:season_year>/", get_wins_losses, name="wins_losses"),
    path("api/team_game_results/<int:team_id>/<str:season_year>/", get_team_game_results, name="team_game_results"),
    path("api/player_stats_for_season/<int:player_id>/<str:season_year>/", get_player_stats_for_season, name="player_stats_for_season"),
    path("api/player_average_stats_for_season/<int:player_id>/<str:season_year>/", get_player_average_stats_for_season, name="player_average_stats_for_season"),
    path("api/players_from_team/<int:team_id>/<str:season_year>/", get_players_from_team, name="players_from_team"),
    path("api/game/<int:game_id>/", get_game, name="game"),
    path("api/home_away_team_info_on_date/<str:game_date>/", get_home_away_team_info_on_date, name="home_away_team_info_on_date")
]
