-- ============================================================================
-- CLASH ROYALE META ANALYSIS QUERIES
-- Run with: mysql -u root -plittlegenius clash_royale < meta_queries.sql
-- ============================================================================

-- ============================================================================
-- 1. MOST USED CARDS (Usage Rate)
-- ============================================================================
SELECT 
    c.name AS card_name,
    c.rarity,
    c.elixir,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles), 2) AS usage_rate_pct
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
GROUP BY c.id, c.name, c.rarity, c.elixir
ORDER BY times_used DESC
LIMIT 30;

-- ============================================================================
-- 2. MOST META CARDS (High Usage + High Win Rate)
-- Combines usage rate and win rate to find truly meta cards
-- ============================================================================
SELECT 
    c.name AS card_name,
    c.rarity,
    c.elixir,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles), 2) AS usage_rate,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate,
    ROUND(
        (COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles)) * 
        (SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)), 
    2) AS meta_score
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
GROUP BY c.id, c.name, c.rarity, c.elixir
HAVING COUNT(*) >= 100  -- Minimum sample size
ORDER BY meta_score DESC
LIMIT 25;

-- ============================================================================
-- 3. CARD WIN RATES (Which cards win the most?)
-- ============================================================================
SELECT 
    c.name AS card_name,
    c.rarity,
    c.elixir,
    COUNT(*) AS total_battles,
    SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) AS wins,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
GROUP BY c.id, c.name, c.rarity, c.elixir
HAVING COUNT(*) >= 50  -- Minimum sample size for statistical relevance
ORDER BY win_rate DESC
LIMIT 30;

-- ============================================================================
-- 4. CARD SYNERGIES (Which card pairs appear together most often?)
-- ============================================================================
SELECT 
    c1.name AS card_1,
    c2.name AS card_2,
    COUNT(*) AS times_together,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM battles), 2) AS pair_usage_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc1,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc2
JOIN cards c1 ON c1.id = pc1.card_id
JOIN cards c2 ON c2.id = pc2.card_id
WHERE pc1.card_id < pc2.card_id  -- Avoid duplicates (A,B) and (B,A)
GROUP BY c1.id, c1.name, c2.id, c2.name
ORDER BY times_together DESC
LIMIT 30;

-- ============================================================================
-- 5. WINNING CARD COMBINATIONS (Synergies that win together)
-- ============================================================================
SELECT 
    c1.name AS card_1,
    c2.name AS card_2,
    COUNT(*) AS times_together,
    SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) AS wins,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS combo_win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc1,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc2
JOIN cards c1 ON c1.id = pc1.card_id
JOIN cards c2 ON c2.id = pc2.card_id
WHERE pc1.card_id < pc2.card_id
GROUP BY c1.id, c1.name, c2.id, c2.name
HAVING COUNT(*) >= 50  -- Minimum sample size
ORDER BY combo_win_rate DESC
LIMIT 30;

-- ============================================================================
-- 6. CARD USAGE BY RARITY
-- ============================================================================
SELECT 
    c.rarity,
    COUNT(DISTINCT c.id) AS unique_cards,
    COUNT(*) AS total_uses,
    ROUND(AVG(sub.win_rate), 2) AS avg_win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
JOIN (
    SELECT 
        c2.id,
        SUM(CASE WHEN b2.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS win_rate
    FROM battles b2,
        JSON_TABLE(b2.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc2
    JOIN cards c2 ON c2.id = pc2.card_id
    GROUP BY c2.id
) sub ON sub.id = c.id
GROUP BY c.rarity
ORDER BY total_uses DESC;

-- ============================================================================
-- 7. MOST POPULAR 3-CARD CORES (Archetype Identification)
-- ============================================================================
SELECT 
    CONCAT(c1.name, ' + ', c2.name, ' + ', c3.name) AS card_core,
    COUNT(*) AS times_used,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc1,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc2,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc3
JOIN cards c1 ON c1.id = pc1.card_id
JOIN cards c2 ON c2.id = pc2.card_id
JOIN cards c3 ON c3.id = pc3.card_id
WHERE pc1.card_id < pc2.card_id AND pc2.card_id < pc3.card_id
GROUP BY c1.id, c1.name, c2.id, c2.name, c3.id, c3.name
HAVING COUNT(*) >= 30
ORDER BY times_used DESC
LIMIT 20;

-- ============================================================================
-- 8. UNDERRATED CARDS (High win rate, low usage)
-- Hidden gems that win but aren't popular
-- ============================================================================
SELECT 
    c.name AS card_name,
    c.rarity,
    c.elixir,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles), 2) AS usage_rate,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
GROUP BY c.id, c.name, c.rarity, c.elixir
HAVING 
    COUNT(*) >= 30 AND  -- Minimum sample
    COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles) < 5 AND  -- Low usage (<5%)
    SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) > 52  -- High win rate (>52%)
ORDER BY win_rate DESC
LIMIT 20;

-- ============================================================================
-- 9. OVERRATED CARDS (High usage, low win rate)
-- Popular but underperforming cards
-- ============================================================================
SELECT 
    c.name AS card_name,
    c.rarity,
    c.elixir,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles), 2) AS usage_rate,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
GROUP BY c.id, c.name, c.rarity, c.elixir
HAVING 
    COUNT(*) >= 50 AND  -- Minimum sample
    COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles) > 5 AND  -- High usage (>5%)
    SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) < 48  -- Low win rate (<48%)
ORDER BY usage_rate DESC
LIMIT 20;

-- ============================================================================
-- 10. WIN CONDITIONS ANALYSIS
-- Which win conditions (heavy hitters) are most effective?
-- ============================================================================
SELECT 
    c.name AS win_condition,
    c.elixir,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles), 2) AS usage_rate,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
WHERE c.name IN (
    'Hog Rider', 'Golem', 'Giant', 'Royal Giant', 'Lava Hound', 
    'Balloon', 'X-Bow', 'Mortar', 'Three Musketeers', 'Graveyard',
    'Mega Knight', 'P.E.K.K.A', 'Giant Skeleton', 'Goblin Giant',
    'Elixir Golem', 'Ram Rider', 'Battle Ram', 'Royal Hogs',
    'Skeleton King', 'Mighty Miner', 'Archer Queen', 'Golden Knight',
    'Miner', 'Goblin Drill', 'Wall Breakers', 'Goblin Barrel',
    'Sparky', 'Electro Giant'
)
GROUP BY c.id, c.name, c.elixir
ORDER BY usage_rate DESC;

-- ============================================================================
-- 11. SPELL USAGE ANALYSIS
-- ============================================================================
SELECT 
    c.name AS spell,
    c.elixir,
    COUNT(*) AS times_used,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) * 8 FROM battles), 2) AS usage_rate,
    ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
JOIN cards c ON c.id = pc.card_id
WHERE c.name IN (
    'Fireball', 'Zap', 'The Log', 'Arrows', 'Poison', 'Lightning',
    'Rocket', 'Freeze', 'Tornado', 'Earthquake', 'Barbarian Barrel',
    'Snowball', 'Royal Delivery', 'Rage', 'Clone', 'Mirror', 'Graveyard',
    'Goblin Barrel'
)
GROUP BY c.id, c.name, c.elixir
ORDER BY usage_rate DESC;

-- ============================================================================
-- 12. AVERAGE DECK ELIXIR COST VS WIN RATE
-- ============================================================================
SELECT 
    CASE 
        WHEN avg_elixir < 3.0 THEN '< 3.0 (Cycle)'
        WHEN avg_elixir < 3.5 THEN '3.0-3.5 (Medium-Light)'
        WHEN avg_elixir < 4.0 THEN '3.5-4.0 (Medium)'
        WHEN avg_elixir < 4.5 THEN '4.0-4.5 (Medium-Heavy)'
        ELSE '4.5+ (Heavy/Beatdown)'
    END AS deck_type,
    COUNT(*) AS num_battles,
    ROUND(AVG(avg_elixir), 2) AS actual_avg_elixir,
    ROUND(SUM(is_winner) * 100.0 / COUNT(*), 2) AS win_rate
FROM (
    SELECT 
        b.id,
        b.is_winner,
        AVG(c.elixir) AS avg_elixir
    FROM battles b,
        JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
    JOIN cards c ON c.id = pc.card_id
    GROUP BY b.id, b.is_winner
) deck_costs
GROUP BY 
    CASE 
        WHEN avg_elixir < 3.0 THEN '< 3.0 (Cycle)'
        WHEN avg_elixir < 3.5 THEN '3.0-3.5 (Medium-Light)'
        WHEN avg_elixir < 4.0 THEN '3.5-4.0 (Medium)'
        WHEN avg_elixir < 4.5 THEN '4.0-4.5 (Medium-Heavy)'
        ELSE '4.5+ (Heavy/Beatdown)'
    END
ORDER BY actual_avg_elixir;

-- ============================================================================
-- 13. COMPLETE META SUMMARY
-- ============================================================================
SELECT '=== META SUMMARY ===' AS report;

SELECT CONCAT('Total Battles Analyzed: ', COUNT(*)) AS stat FROM battles;

SELECT CONCAT('Unique Cards Used: ', COUNT(DISTINCT pc.card_id)) AS stat
FROM battles b,
    JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc;

SELECT CONCAT('Overall Win Rate (sanity check): ', ROUND(AVG(is_winner) * 100, 1), '%') AS stat 
FROM battles;

-- ============================================================================
-- 14. CARD COUNTER ANALYSIS
-- Which cards beat which? (When card X is in winner deck, what's in loser deck?)
-- ============================================================================
SELECT
    c_winner.name AS winning_card,
    c_loser.name AS losing_to,
    COUNT(*) AS times,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY c_winner.name), 2) AS pct_of_wins
FROM battles b
JOIN JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc_winner
    ON b.is_winner = 1
JOIN JSON_TABLE(b.opponent_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc_loser
    ON 1=1
JOIN cards c_winner ON c_winner.id = pc_winner.card_id
JOIN cards c_loser ON c_loser.id = pc_loser.card_id
WHERE c_winner.name IN ('Hog Rider', 'Golem', 'X-Bow', 'Royal Giant', 'Lava Hound', 'Graveyard')
GROUP BY c_winner.id, c_winner.name, c_loser.id, c_loser.name
HAVING COUNT(*) >= 20
ORDER BY c_winner.name, times DESC;

-- ============================================================================
-- 15. ADVANCED 3-CARD SYNERGY META (Enhanced Combination Analysis)
-- Identifies 3-card combinations with synergy scores and role balance
-- Shows whether cards perform better together than individually
-- ============================================================================
WITH card_stats AS (
    -- Get baseline win rate for each card
    SELECT
        c.id,
        c.name,
        c.rarity,
        c.elixir,
        COUNT(*) AS total_uses,
        ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS individual_win_rate
    FROM battles b,
        JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc
    JOIN cards c ON c.id = pc.card_id
    GROUP BY c.id, c.name, c.rarity, c.elixir
),
triple_combos AS (
    -- Find all 3-card combinations
    SELECT
        c1.id AS card1_id, c1.name AS card1,
        c2.id AS card2_id, c2.name AS card2,
        c3.id AS card3_id, c3.name AS card3,
        ROUND((c1.elixir + c2.elixir + c3.elixir) / 3.0, 2) AS avg_elixir,
        COUNT(*) AS combo_uses,
        ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS combo_win_rate
    FROM battles b,
        JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc1,
        JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc2,
        JSON_TABLE(b.player_cards, '$[*]' COLUMNS (card_id INT PATH '$.id')) AS pc3
    JOIN cards c1 ON c1.id = pc1.card_id
    JOIN cards c2 ON c2.id = pc2.card_id
    JOIN cards c3 ON c3.id = pc3.card_id
    WHERE pc1.card_id < pc2.card_id AND pc2.card_id < pc3.card_id
    GROUP BY c1.id, c1.name, c2.id, c2.name, c3.id, c3.name, c1.elixir, c2.elixir, c3.elixir
    HAVING COUNT(*) >= 25
)
SELECT
    CONCAT(tc.card1, ' + ', tc.card2, ' + ', tc.card3) AS card_combo,
    tc.combo_uses AS times_used,
    tc.avg_elixir AS avg_cost,
    tc.combo_win_rate AS actual_win_rate,
    ROUND((cs1.individual_win_rate + cs2.individual_win_rate + cs3.individual_win_rate) / 3, 2) AS expected_win_rate,
    ROUND(tc.combo_win_rate - ((cs1.individual_win_rate + cs2.individual_win_rate + cs3.individual_win_rate) / 3), 2) AS synergy_score,
    CASE
        WHEN tc.combo_win_rate - ((cs1.individual_win_rate + cs2.individual_win_rate + cs3.individual_win_rate) / 3) > 5
        THEN 'Strong Synergy'
        WHEN tc.combo_win_rate - ((cs1.individual_win_rate + cs2.individual_win_rate + cs3.individual_win_rate) / 3) > 2
        THEN 'Good Synergy'
        WHEN tc.combo_win_rate - ((cs1.individual_win_rate + cs2.individual_win_rate + cs3.individual_win_rate) / 3) < -2
        THEN 'Anti-Synergy'
        ELSE 'Neutral'
    END AS synergy_rating
FROM triple_combos tc
JOIN card_stats cs1 ON cs1.id = tc.card1_id
JOIN card_stats cs2 ON cs2.id = tc.card2_id
JOIN card_stats cs3 ON cs3.id = tc.card3_id
ORDER BY synergy_score DESC, combo_uses DESC
LIMIT 30;
