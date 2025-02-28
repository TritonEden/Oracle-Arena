-- Oracle Database Schema 

--  Stores info about a team overall - "Golden State Warriors"
CREATE TABLE Teams (
    team_id INT NOT NULL,
    season_year VARCHAR(10) NOT NULL,
    team_location VARCHAR(40) NOT NULL,
    team_name VARCHAR(40) NOT NULL,
    team_abbreviation VARCHAR(3) NOT NULL,
    team_photo_url VARCHAR(255),
    PRIMARY KEY (team_id, season_year)
);

-- Stores info about a player - "Lebron" "James"
CREATE TABLE Players (
    player_id INT PRIMARY KEY,
    first_name VARCHAR(30) NOT NULL,
    last_name VARCHAR(30) NOT NULL,
    player_photo_url VARCHAR(255),
);

-- Metadata for each game - Lakers vs Warriors
CREATE TABLE Games (
    game_id INT PRIMARY KEY,
    season_year VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,

    CONSTRAINT fk_home_team
        FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    CONSTRAINT fk_away_team
        FOREIGN KEY (away_team_id) REFERENCES Teams(team_id),
);

-- Performance of a player in an individual game
CREATE TABLE PlayerGameStats (
    game_id INT NOT NULL,
    player_id INT NOT NULL,
    team_id INT NOT NULL,
    player_game_stats JSONB,
    PRIMARY KEY (game_id, player_id), -- Composite primary key

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

