from django.db import models

class PlayerGameStats(models.Model):
    game_id = models.CharField(max_length=20)
    player_id = models.IntegerField()
    team_id = models.IntegerField()
    player_game_stats = models.JSONField()  # Store the JSON data directly

    def __str__(self):
        return f"Game ID: {self.game_id}, Player ID: {self.player_id}"
