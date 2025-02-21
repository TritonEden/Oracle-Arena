-- Oracle Database Schema 

--  Stores info about a team overall - "Golden State Warriors"
CREATE TABLE Teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(40) NOT NULL,
    team_stats JSONB -- JSONB is useful for easily changing which stats we store
);

-- Stores info about a player - "Lebron" "James"
CREATE TABLE Players (
    player_id SERIAL PRIMARY KEY,
    first_name VARCHAR(30) NOT NULL,
    last_name VARCHAR(30) NOT NULL,
    team_id INT, -- Uses Teams table team_id
    player_stats JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_player_team -- rule ensures sync between players and teams
        FOREIGN KEY (team_id)
        REFERENCES Teams(team_id)
        ON DELETE SET NULL

);

-- Specific season - "2024"
CREATE TABLE Seasons (
    season_id SERIAL PRIMARY KEY,
    season_year INT NOT NULL UNIQUE
);

-- Each game - Lakers vs Warriors
CREATE TABLE Games (
    game_id SERIAL PRIMARY KEY,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    winner INT NULL, -- Winning team's id can be NULL if no winner yet
    total_score INT DEFAULT 0,
    season_id INT NOT NULL, 
    season_year INT NOT NULL, -- Redundant for easier querying 

    CONSTRAINT fk_home_team
        FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    CONSTRAINT fk_away_team
        FOREIGN KEY (away_team_id) REFERENCES Teams(team_id),
    CONSTRAINT fk_winner
        FOREIGN KEY (winner) REFERENCES Teams(team_id),
    CONSTRAINT fk_season_id
        FOREIGN KEY (season_id) REFERENCES Seasons(season_id)
);

-- Performance of Team in an individual game
CREATE TABLE TeamGameStats (
    game_team_stats_id SERIAL PRIMARY KEY,
    game_id INT NOT NULL,
    team_id INT NOT NULL,
    is_home BOOLEAN NOT NULL, -- TRUE home game, FALSE away game
    team_game_stats JSONB,

    CONSTRAINT fk_game 
        FOREIGN KEY (game_id) REFERENCES Games(game_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_team
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        ON DELETE CASCADE
);

-- Performance of a player in an individual game
CREATE TABLE PlayerGameStats (
    game_player_stats_id SERIAL PRIMARY KEY,
    game_id INT NOT NULL,
    player_id INT NOT NULL,
    team_id INT NOT NULL,
    player_game_stats JSONB,

    CONSTRAINT fk_game
        FOREIGN KEY (game_id) REFERENCES Games(game_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_player
        FOREIGN KEY (player_id) REFERENCES Players(player_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_player_game_team
        FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        ON DELETE CASCADE
);


