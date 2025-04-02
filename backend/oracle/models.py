from django.db import models

class PlayerGameStats(models.Model):
    game_id = models.CharField(max_length=20)
    player_id = models.IntegerField()
    team_id = models.IntegerField()
    player_game_stats = models.JSONField()  # Store the JSON data directly

    def __str__(self):
        return f"Game ID: {self.game_id}, Player ID: {self.player_id}"

class Player(models.Model):
    player_id = models.AutoField(primary_key=True)  # Automatically generate a unique player ID
    player_first_name = models.CharField(max_length=100)
    player_last_name = models.CharField(max_length=100)
    # team_name = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)  # Optionally store image URL

    def __str__(self):
        return f"{self.player_first_name} {self.player_last_name} ({self.team_name})"
