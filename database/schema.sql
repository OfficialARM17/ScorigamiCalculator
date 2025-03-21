-- Drop existing tables if they exist
DROP TABLE IF EXISTS games, teams, seasons;

-- Seasons Table
CREATE TABLE seasons (
    season_id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    type TEXT CHECK(type IN ('regular-season', 'post-season')) NOT NULL,
    CONSTRAINT unique_season UNIQUE (year, type)  -- Add unique constraint for year and type
);

-- Teams Table
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL  -- Ensure 'name' is unique
);

-- Games Table
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    season_id INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    date TIMESTAMPTZ,
    week INTEGER,
    round TEXT CHECK(round IN ('Regular Season', 'Wild Card Round', 'Divisional Round', 'Championship Round', 'Super Bowl', 'Pro Bowl')) NOT NULL,
    FOREIGN KEY (season_id) REFERENCES seasons(season_id) ON DELETE CASCADE,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);
