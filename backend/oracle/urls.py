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
from .views import presentGameSummary, get_players, get_player_game_stats, get_games, get_teams, get_all_player_game_stats
urlpatterns = [
    path('admin/', admin.site.urls),
    # path('testfunction/', testfunction),
    #make a path that takes in just a playerid
    # path('playersummary/<int:playerid>/', playersummary),
    path('presentGameSummary/', presentGameSummary),
    path('api/player_stats/', get_players, name='get_players'),
    # path('api/player_stats/', player_stats, name='player_stats'),
    path("api/player_game_stats/<int:player_id>/", get_player_game_stats, name="player_game_stats"),
    path("api/player_game_stats/", get_all_player_game_stats, name="all_player_game_stats"),
    path("api/games/", get_games, name="games"),
    path("api/teams/", get_teams, name="teams"),
]
