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

-- 5. RARITY STATS
SELECT c.rarity, COUNT(DISTINCT c.card_id) AS cards, COUNT(*) AS uses,
ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY c.rarity ORDER BY uses DESC;

-- 6. ELIXIR VS WIN RATE
SELECT CASE WHEN d.avg_elixir < 3.0 THEN '<3.0' WHEN d.avg_elixir < 3.5 THEN '3.0-3.5'
WHEN d.avg_elixir < 4.0 THEN '3.5-4.0' WHEN d.avg_elixir < 4.5 THEN '4.0-4.5'
ELSE '4.5+' END AS elixir_range,
COUNT(*) AS battles, ROUND(AVG(d.avg_elixir),2) AS avg,
ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate
FROM battle_players bp
JOIN decks d ON bp.deck_id = d.deck_id
WHERE bp.deck_id IS NOT NULL
GROUP BY CASE WHEN d.avg_elixir < 3.0 THEN '<3.0' WHEN d.avg_elixir < 3.5 THEN '3.0-3.5'
WHEN d.avg_elixir < 4.0 THEN '3.5-4.0' WHEN d.avg_elixir < 4.5 THEN '4.0-4.5'
ELSE '4.5+' END
ORDER BY avg;

-- 7. WIN CONDITIONS
SELECT c.name, c.elixir_cost, COUNT(*) AS used, ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate
FROM battle_players bp
JOIN deck_cards dc ON bp.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL AND c.name IN (
'Hog Rider','Golem','Giant','Royal Giant','Lava Hound','Balloon','X-Bow','Mortar',
'Graveyard','Mega Knight','P.E.K.K.A','Miner','Goblin Barrel','Sparky','Electro Giant')
GROUP BY c.card_id, c.name, c.elixir_cost
ORDER BY used DESC;

-- 8. TOP DECKS
SELECT d.deck_id, d.avg_elixir, GROUP_CONCAT(c.name ORDER BY c.elixir_cost DESC SEPARATOR ', ') AS cards,
COUNT(*)/8 AS games, ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate
FROM battle_players bp
JOIN decks d ON bp.deck_id = d.deck_id
JOIN deck_cards dc ON d.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.deck_id IS NOT NULL
GROUP BY d.deck_id, d.avg_elixir
HAVING COUNT(*)/8 >= 3
ORDER BY win_rate DESC LIMIT 15;

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

-- 10. TOURNAMENT TOP DECKS
SELECT d.avg_elixir, GROUP_CONCAT(c.name ORDER BY c.elixir_cost DESC SEPARATOR ', ') AS cards,
COUNT(*)/8 AS players
FROM tournament_members tm
JOIN player_decks pd ON tm.player_tag = pd.player_tag
JOIN decks d ON pd.deck_id = d.deck_id
JOIN deck_cards dc ON d.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
GROUP BY d.deck_id, d.avg_elixir
HAVING COUNT(*)/8 >= 2
ORDER BY players DESC LIMIT 15;

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

-- 12. TOP LADDER DECKS (10k+ trophies)
SELECT d.avg_elixir, GROUP_CONCAT(c.name ORDER BY c.elixir_cost DESC SEPARATOR ', ') AS cards,
COUNT(*)/8 AS games, ROUND(SUM(bp.is_winner)*100.0/COUNT(*),2) AS win_rate
FROM battle_players bp
JOIN decks d ON bp.deck_id = d.deck_id
JOIN deck_cards dc ON d.deck_id = dc.deck_id
JOIN cards c ON dc.card_id = c.card_id
WHERE bp.starting_trophies >= 10000 AND bp.deck_id IS NOT NULL
GROUP BY d.deck_id, d.avg_elixir
HAVING COUNT(*)/8 >= 3
ORDER BY win_rate DESC LIMIT 15;

-- 13. SUMMARY
SELECT 'BATTLES' AS metric, COUNT(*) AS value FROM battles
UNION SELECT 'DECKS', COUNT(*) FROM decks
UNION SELECT 'PLAYERS', COUNT(*) FROM players
UNION SELECT 'TOURNAMENT_MEMBERS', COUNT(*) FROM tournament_members
UNION SELECT 'LEADERBOARD_PLAYERS', COUNT(*) FROM leaderboard_snapshot_players;