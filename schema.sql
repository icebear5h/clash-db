-- Clash Royale Meta Database Schema
-- Tracks decks, meta snapshots, leaderboards, and tournaments

DROP DATABASE IF EXISTS clash_meta;
CREATE DATABASE clash_meta;
USE clash_meta;

-- ============================================
-- REFERENCE TABLES
-- ============================================

-- Locations (regions/countries)
CREATE TABLE locations (
    location_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_country BOOLEAN DEFAULT FALSE,
    country_code VARCHAR(10)
);

-- Players (just tags for foreign key references)
CREATE TABLE players (
    player_tag VARCHAR(20) PRIMARY KEY
);

-- All cards in the game
CREATE TABLE cards (
    card_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    rarity VARCHAR(20),
    elixir_cost INT,
    card_type VARCHAR(20),  -- troop/spell/building (derived from card_id prefix)
    icon_url VARCHAR(255)
);

-- Unique 8-card deck combinations
CREATE TABLE decks (
    deck_id INT PRIMARY KEY AUTO_INCREMENT,
    deck_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 of sorted card_ids
    avg_elixir DECIMAL(3,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many: cards in each deck
CREATE TABLE deck_cards (
    deck_id INT NOT NULL,
    card_id INT NOT NULL,
    PRIMARY KEY (deck_id, card_id),
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE
);

-- Meta snapshots (aggregated data collection runs)
CREATE TABLE meta_snapshots (
    snapshot_id INT PRIMARY KEY AUTO_INCREMENT,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    snapshot_type VARCHAR(30) NOT NULL,  -- 'ladder', 'top_1000', 'tournament', 'path_of_legend'
    trophy_min INT,
    trophy_max INT,
    sample_size INT DEFAULT 0,  -- total battles analyzed
    total_decks INT DEFAULT 0,  -- unique decks found
    description VARCHAR(200)
);

-- Per-deck stats within a snapshot
CREATE TABLE deck_snapshot_stats (
    snapshot_id INT NOT NULL,
    deck_id INT NOT NULL,
    games_played INT DEFAULT 0,
    games_won INT DEFAULT 0,
    win_rate DECIMAL(5,2),  -- percentage
    pick_rate DECIMAL(5,2),  -- percentage of total games
    PRIMARY KEY (snapshot_id, deck_id),
    FOREIGN KEY (snapshot_id) REFERENCES meta_snapshots(snapshot_id) ON DELETE CASCADE,
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
);

-- Per-card stats within a snapshot
CREATE TABLE card_snapshot_stats (
    snapshot_id INT NOT NULL,
    card_id INT NOT NULL,
    games_played INT DEFAULT 0,
    games_won INT DEFAULT 0,
    win_rate DECIMAL(5,2),
    pick_rate DECIMAL(5,2),
    PRIMARY KEY (snapshot_id, card_id),
    FOREIGN KEY (snapshot_id) REFERENCES meta_snapshots(snapshot_id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE
);

-- ============================================
-- LEADERBOARDS / RANKINGS
-- ============================================

-- Leaderboard definitions
CREATE TABLE leaderboards (
    leaderboard_id VARCHAR(50) PRIMARY KEY,  -- e.g., 'global', '57000249' (location id)
    name VARCHAR(100) NOT NULL,
    leaderboard_type VARCHAR(30) NOT NULL,   -- 'global', 'location', 'path_of_legend'
    location_id INT,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE SET NULL
);

-- Snapshots of leaderboard rankings
CREATE TABLE leaderboard_snapshots (
    snapshot_id INT PRIMARY KEY AUTO_INCREMENT,
    leaderboard_id VARCHAR(50) NOT NULL,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    player_count INT DEFAULT 0,
    FOREIGN KEY (leaderboard_id) REFERENCES leaderboards(leaderboard_id) ON DELETE CASCADE
);

-- Players in each leaderboard snapshot
CREATE TABLE leaderboard_snapshot_players (
    snapshot_id INT NOT NULL,
    rank_position INT NOT NULL,
    player_tag VARCHAR(20) NOT NULL,
    trophies INT,
    deck_id INT,  -- Their current deck at snapshot time
    PRIMARY KEY (snapshot_id, rank_position),
    FOREIGN KEY (snapshot_id) REFERENCES leaderboard_snapshots(snapshot_id) ON DELETE CASCADE,
    FOREIGN KEY (player_tag) REFERENCES players(player_tag) ON DELETE CASCADE,
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE SET NULL
);

-- Player's current/saved decks (from profile)
CREATE TABLE player_decks (
    player_tag VARCHAR(20) NOT NULL,
    deck_id INT NOT NULL,
    is_current BOOLEAN DEFAULT TRUE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_tag, deck_id),
    FOREIGN KEY (player_tag) REFERENCES players(player_tag) ON DELETE CASCADE,
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE CASCADE
);

-- ============================================
-- TOURNAMENTS
-- ============================================

-- Tournament definitions
CREATE TABLE tournaments (
    tournament_tag VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    status VARCHAR(20),           -- 'preparation', 'inProgress', 'ended'
    tournament_type VARCHAR(30),
    capacity INT,
    max_capacity INT,
    level_cap INT,
    game_mode_name VARCHAR(50),
    created_time TIMESTAMP,
    started_time TIMESTAMP,
    first_place_prize INT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tournament participants
CREATE TABLE tournament_members (
    tournament_tag VARCHAR(20) NOT NULL,
    player_tag VARCHAR(20) NOT NULL,
    rank_position INT,
    score INT,
    PRIMARY KEY (tournament_tag, player_tag),
    FOREIGN KEY (tournament_tag) REFERENCES tournaments(tournament_tag) ON DELETE CASCADE,
    FOREIGN KEY (player_tag) REFERENCES players(player_tag) ON DELETE CASCADE
);

-- ============================================
-- BATTLES (from battlelogs)
-- ============================================

-- Individual battles from player battlelogs
CREATE TABLE battles (
    battle_id VARCHAR(64) PRIMARY KEY,  -- Hash of battleTime + player tags
    battle_type VARCHAR(30),            -- PvP, tournament, challenge, etc.
    game_mode VARCHAR(50),
    arena_name VARCHAR(50),
    is_ladder BOOLEAN DEFAULT FALSE
);

-- Players in each battle (2 per battle)
CREATE TABLE battle_players (
    battle_id VARCHAR(64) NOT NULL,
    team_side TINYINT NOT NULL,         -- 0 = team, 1 = opponent
    player_tag VARCHAR(20) NOT NULL,
    deck_id INT,
    starting_trophies INT,
    trophy_change INT,
    crowns INT,
    is_winner BOOLEAN,
    PRIMARY KEY (battle_id, team_side),
    FOREIGN KEY (battle_id) REFERENCES battles(battle_id) ON DELETE CASCADE,
    FOREIGN KEY (player_tag) REFERENCES players(player_tag) ON DELETE CASCADE,
    FOREIGN KEY (deck_id) REFERENCES decks(deck_id) ON DELETE SET NULL
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_deck_stats_winrate ON deck_snapshot_stats(snapshot_id, win_rate DESC);
CREATE INDEX idx_deck_stats_pickrate ON deck_snapshot_stats(snapshot_id, pick_rate DESC);
CREATE INDEX idx_card_stats_winrate ON card_snapshot_stats(snapshot_id, win_rate DESC);
CREATE INDEX idx_card_stats_pickrate ON card_snapshot_stats(snapshot_id, pick_rate DESC);
CREATE INDEX idx_snapshots_type ON meta_snapshots(snapshot_type, taken_at DESC);
CREATE INDEX idx_leaderboard_snapshots ON leaderboard_snapshots(leaderboard_id, taken_at DESC);
CREATE INDEX idx_tournament_status ON tournaments(status, created_time DESC);
CREATE INDEX idx_battles_type ON battles(battle_type, is_ladder);
CREATE INDEX idx_battle_players_player ON battle_players(player_tag);
CREATE INDEX idx_battle_players_deck ON battle_players(deck_id);
