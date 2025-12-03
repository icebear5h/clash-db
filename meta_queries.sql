-- CLASH ROYALE META ANALYSIS
-- Run: mysql < meta_queries.sql

-- 1. MOST USED CARDS
SELECT c.name, c.rarity, c.elixir_cost, COUNT(*) AS times_used,
ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battle_players WHERE deck_id IS NOT NULL), 2) AS usage_pct
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c.card_id, c.name, c.rarity, c.elixir_cost
ORDER BY times_used DESC LIMIT 20;

-- 2. CARD WIN RATES
SELECT c.name, c.rarity, COUNT(*) AS battles, SUM(bp.is_winner) AS wins,
ROUND(SUM(bp.is_winner) * 100.0 / COUNT(*), 2) AS win_rate
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c.card_id, c.name, c.rarity
HAVING COUNT(*) >= 50
ORDER BY win_rate DESC LIMIT 20;

-- 3. META SCORE
SELECT c.name, COUNT(*) AS games, ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate,
ROUND(COUNT(*) * SUM(bp.is_winner) / COUNT(*) / 100, 2) AS meta_score
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c.card_id, c.name
HAVING COUNT(*) >= 100
ORDER BY meta_score DESC LIMIT 20;

-- 4. CARD PAIRS
SELECT c1.name AS card_1, c2.name AS card_2, COUNT(*) AS together,
ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate
FROM battle_players bp
JOIN deck_cards dc1 ON bp.deck_id = dc1.deck_id
JOIN deck_cards dc2 ON bp.deck_id = dc2.deck_id AND dc1.card_id < dc2.card_id
JOIN cards c1 ON dc1.card_id = c1.card_id
JOIN cards c2 ON dc2.card_id = c2.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c1.card_id, c1.name, c2.card_id, c2.name
HAVING COUNT(*) >= 50
ORDER BY together DESC LIMIT 20;

-- 5. GOOD CARD PAIRS (HIGH WIN RATE)
SELECT 
    c1.name AS card_1, 
    c2.name AS card_2, 
    COUNT(*) AS times_together,
    ROUND(SUM(bp.is_winner) * 100.0 / COUNT(*), 2) AS win_rate,
    ROUND(COUNT(*) * SUM(bp.is_winner) / COUNT(*) / 100, 2) AS synergy_score
FROM battle_players bp
JOIN deck_cards dc1 ON bp.deck_id = dc1.deck_id
JOIN deck_cards dc2 ON bp.deck_id = dc2.deck_id AND dc1.card_id < dc2.card_id
JOIN cards c1 ON dc1.card_id = c1.card_id
JOIN cards c2 ON dc2.card_id = c2.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c1.card_id, c1.name, c2.card_id, c2.name
HAVING COUNT(*) >= 50 
ORDER BY synergy_score DESC  
LIMIT 30;

-- 6. UNDERRATED CARDS (LOW USAGE, HIGH WIN)
SELECT 
    c.name,
    c.rarity,
    c.elixir_cost,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battle_players WHERE deck_id IS NOT NULL), 2) AS usage_pct,
    SUM(bp.is_winner) AS wins,
    ROUND(SUM(bp.is_winner) * 100.0 / COUNT(*), 2) AS win_rate
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c.card_id, c.name, c.rarity, c.elixir_cost
HAVING 
    COUNT(*) >= 50
    AND usage_pct < 5.0
    AND win_rate >= 55.0
ORDER BY win_rate DESC
LIMIT 20;

-- 7. OVERRATED CARDS (HIGH USAGE, LOW WIN)
SELECT 
    c.name,
    c.rarity,
    c.elixir_cost,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battle_players WHERE deck_id IS NOT NULL), 2) AS usage_pct,
    SUM(bp.is_winner) AS wins,
    ROUND(SUM(bp.is_winner) * 100.0 / COUNT(*), 2) AS win_rate
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c.card_id, c.name, c.rarity, c.elixir_cost
HAVING 
    COUNT(*) >= 100
    AND usage_pct >= .75
    AND win_rate <= 50.0
ORDER BY usage_pct DESC
LIMIT 20;

-- 7. HARD COUNTERS
SELECT 
    win_condition,
    hardest_counter,
    matchups,
    losses,
    loss_rate
FROM (
    SELECT 
        wc.name AS win_condition,
        opp_c.name AS hardest_counter,
        COUNT(*) AS matchups,
        SUM(CASE WHEN bp.is_winner = 0 THEN 1 ELSE 0 END) AS losses,
        ROUND(SUM(CASE WHEN bp.is_winner = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS loss_rate,
        ROW_NUMBER() OVER (PARTITION BY wc.name ORDER BY ROUND(SUM(CASE WHEN bp.is_winner = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) DESC) AS rn
    FROM battle_players bp
    JOIN deck_cards dc ON bp.deck_id = dc.deck_id
    JOIN cards wc ON dc.card_id = wc.card_id
    JOIN battles b ON bp.battle_id = b.battle_id
    JOIN battle_players opp_bp ON b.battle_id = opp_bp.battle_id AND opp_bp.player_tag != bp.player_tag
    JOIN deck_cards opp_dc ON opp_bp.deck_id = opp_dc.deck_id
    JOIN cards opp_c ON opp_dc.card_id = opp_c.card_id
    WHERE 
        bp.deck_id IS NOT NULL 
        AND opp_bp.deck_id IS NOT NULL
        AND wc.name IN (
            'Hog Rider', 'Golem', 'Giant', 'Royal Giant', 'Lava Hound', 'Balloon', 
            'X-Bow', 'Mortar', 'Graveyard', 'Mega Knight', 'P.E.K.K.A', 'Miner', 
            'Goblin Barrel', 'Sparky', 'Electro Giant', 'Ram Rider', 'Battle Ram'
        )
    GROUP BY wc.card_id, wc.name, opp_c.card_id, opp_c.name
    HAVING COUNT(*) >= 20
) AS ranked
WHERE rn = 1
ORDER BY win_condition;

-- 9. TOURNAMENT META - Most used cards by tournament players
SELECT c.name, c.rarity, c.elixir_cost, COUNT(*) AS times_used,
ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM player_decks pd
JOIN tournament_members tm ON pd.player_tag = tm.player_tag), 2) AS usage_pct
FROM tournament_members tm
JOIN player_decks pd ON tm.player_tag = pd.player_tag
JOIN deck_cards dc ON pd.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
GROUP BY c.card_id, c.name, c.rarity, c.elixir_cost
ORDER BY times_used DESC LIMIT 20;

-- 11. TOP LADDER META (10k+ trophies from battles)
SELECT c.name, c.rarity, c.elixir_cost, COUNT(*) AS times_used,
ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battle_players
WHERE starting_trophies >= 10000 AND deck_id IS NOT NULL), 2) AS usage_pct
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.starting_trophies >= 10000 AND bp.deck_id IS NOT NULL
GROUP BY c.card_id, c.name, c.rarity, c.elixir_cost
ORDER BY times_used DESC LIMIT 20;

-- 13. SUMMARY
SELECT 'BATTLES' AS metric, COUNT(*) AS value FROM battles
UNION SELECT 'DECKS', COUNT(*) FROM decks
UNION SELECT 'PLAYERS', COUNT(*) FROM players
UNION SELECT 'TOURNAMENT_MEMBERS', COUNT(*) FROM tournament_members
UNION SELECT 'LEADERBOARD_PLAYERS', COUNT(*) FROM leaderboard_snapshot_players;