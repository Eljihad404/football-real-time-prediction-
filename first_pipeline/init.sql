-- 1. Leagues Table
CREATE TABLE IF NOT EXISTS leagues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    logo_url TEXT
);

-- 2. Clubs Table
CREATE TABLE IF NOT EXISTS clubs (
    id SERIAL PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id),
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(50),
    stadium_name VARCHAR(100),
    current_manager VARCHAR(100),
    elo_rating INTEGER DEFAULT 1500,
    logo_url TEXT,
    UNIQUE(name)
);

-- 3. Players Table
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    club_id INTEGER REFERENCES clubs(id),
    name VARCHAR(100) NOT NULL,
    position VARCHAR(20),
    nationality VARCHAR(50),
    market_value DECIMAL,
    photo_url TEXT
);

-- 4. Matches Table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    league_id INTEGER REFERENCES leagues(id),
    home_club_id INTEGER REFERENCES clubs(id),
    away_club_id INTEGER REFERENCES clubs(id),
    match_date TIMESTAMP NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    season VARCHAR(10),
    status VARCHAR(20),
    UNIQUE(home_club_id, away_club_id, match_date)
);

-- 5. Match Statistics Table
CREATE TABLE IF NOT EXISTS match_stats (
    match_id INTEGER PRIMARY KEY REFERENCES matches(id),
    home_xg DECIMAL(4,2),
    away_xg DECIMAL(4,2),
    home_possession INTEGER,
    away_possession INTEGER,
    home_shots_on_target INTEGER,
    away_shots_on_target INTEGER,
    home_corners INTEGER,
    away_corners INTEGER
);