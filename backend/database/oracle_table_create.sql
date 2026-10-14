-- Source tables used by the raw SQL API and analytics views.
-- Create missing tables only; do not replace an existing database schema.
CREATE TABLE IF NOT EXISTS public.teams (
    team_id INTEGER NOT NULL,
    season_year VARCHAR(10) NOT NULL,
    team_location VARCHAR(100) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    team_abbreviation VARCHAR(10) NOT NULL,
    team_photo_url VARCHAR(255),
    PRIMARY KEY (team_id, season_year)
);

CREATE TABLE IF NOT EXISTS public.players (
    player_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    player_photo_url VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS public.games (
    game_id BIGINT PRIMARY KEY,
    season_year VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    game_time TEXT,
    winner NUMERIC,
    total_score_prediction NUMERIC,
    FOREIGN KEY (home_team_id, season_year) REFERENCES public.teams(team_id, season_year),
    FOREIGN KEY (away_team_id, season_year) REFERENCES public.teams(team_id, season_year)
);

CREATE TABLE IF NOT EXISTS public.player_game_stats (
    game_id BIGINT NOT NULL REFERENCES public.games(game_id),
    player_id INTEGER NOT NULL REFERENCES public.players(player_id),
    team_id INTEGER NOT NULL,
    player_game_stats JSONB,
    PRIMARY KEY (game_id, player_id)
);

CREATE INDEX IF NOT EXISTS player_game_stats_player_idx
    ON public.player_game_stats (player_id, game_id);
CREATE INDEX IF NOT EXISTS games_date_idx ON public.games (game_date);
