import csv
import ast
import math
from django.core.management.base import BaseCommand
from oracle.models import PlayerGameStats

def safe_eval(player_game_stats_str):
    # Replace 'None' with 'null' and 'nan' with 'float("nan")' for eval
    player_game_stats_str = player_game_stats_str.replace('None', 'null')
    player_game_stats_str = player_game_stats_str.replace('nan', 'float("nan")')
    
    try:
        # Safely evaluate the string into a Python object (list of dicts)
        stats = ast.literal_eval(player_game_stats_str)
        
        # Replace 'None' or 'nan' values with 0 in the dictionary
        for stat in stats:
            for key, value in stat.items():
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    stat[key] = 0.0  # Replace with 0
        return stats
    except (ValueError, SyntaxError, TypeError) as e:
        return None  # If evaluation fails, return None

class Command(BaseCommand):
    help = 'Import player game stats from a CSV file into the database'

    def handle(self, *args, **kwargs):
        with open('../data_extraction/player_game_stats-full.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Safely parse the player_game_stats field as a dictionary
                    player_game_stats = safe_eval(row['player_game_stats'])
                    
                    if player_game_stats is None:
                        self.stdout.write(self.style.WARNING(f"Skipping row with invalid stats: {row}"))
                        continue

                    # Create a new PlayerGameStats object
                    PlayerGameStats.objects.create(
                        game_id=row['game_id'],
                        player_id=row['player_id'],
                        team_id=row['team_id'],
                        player_game_stats=player_game_stats
                    )
                except (ValueError, SyntaxError) as e:
                    self.stdout.write(self.style.ERROR(f"Error parsing row {row}: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS('Successfully imported player game stats.'))
