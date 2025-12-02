-- MySQL dump 10.13  Distrib 8.0.39, for macos14 (arm64)
--
-- Host: localhost    Database: clash_royale
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `battles`
--

DROP TABLE IF EXISTS `battles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `battles` (
  `id` int NOT NULL DEFAULT '0',
  `battle_time` datetime NOT NULL,
  `battle_type` varchar(50) DEFAULT NULL,
  `game_mode` varchar(50) DEFAULT NULL,
  `arena_name` varchar(50) DEFAULT NULL,
  `deck_type` varchar(20) DEFAULT NULL,
  `trophy_change` int DEFAULT NULL,
  `crown_difference` int DEFAULT NULL,
  `player_tag` varchar(20) DEFAULT NULL,
  `opponent_tag` varchar(20) DEFAULT NULL,
  `deck_id` int DEFAULT NULL,
  `opponent_deck_id` int DEFAULT NULL,
  `is_winner` tinyint(1) DEFAULT NULL,
  `player_crowns` int DEFAULT NULL,
  `opponent_crowns` int DEFAULT NULL,
  `player_cards` json DEFAULT NULL,
  `opponent_cards` json DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cards`
--

DROP TABLE IF EXISTS `cards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `rarity` varchar(20) DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `elixir` int DEFAULT NULL,
  `arena` int DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=28000027 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `clans`
--

DROP TABLE IF EXISTS `clans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clans` (
  `tag` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `type` varchar(20) DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `badge_id` int DEFAULT NULL,
  `clan_score` int DEFAULT NULL,
  `clan_war_trophies` int DEFAULT NULL,
  `required_trophies` int DEFAULT NULL,
  `donations_per_week` int DEFAULT NULL,
  `members_count` int DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `deck_cards`
--

DROP TABLE IF EXISTS `deck_cards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `deck_cards` (
  `deck_id` int NOT NULL,
  `card_id` int NOT NULL,
  PRIMARY KEY (`deck_id`,`card_id`),
  KEY `card_id` (`card_id`),
  CONSTRAINT `deck_cards_ibfk_1` FOREIGN KEY (`deck_id`) REFERENCES `decks` (`id`),
  CONSTRAINT `deck_cards_ibfk_2` FOREIGN KEY (`card_id`) REFERENCES `cards` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `decks`
--

DROP TABLE IF EXISTS `decks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `decks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `avg_elixir` float DEFAULT NULL,
  `win_rate` float DEFAULT NULL,
  `use_rate` float DEFAULT NULL,
  `cards_count` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `meta_snapshots`
--

DROP TABLE IF EXISTS `meta_snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meta_snapshots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `snapshot_date` datetime DEFAULT NULL,
  `trophy_range` varchar(20) DEFAULT NULL,
  `game_mode` varchar(50) DEFAULT NULL,
  `meta_data` json DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `players`
--

DROP TABLE IF EXISTS `players`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `players` (
  `tag` varchar(20) NOT NULL,
  `name` varchar(50) NOT NULL,
  `exp_level` int DEFAULT NULL,
  `trophies` int DEFAULT NULL,
  `best_trophies` int DEFAULT NULL,
  `wins` int DEFAULT NULL,
  `losses` int DEFAULT NULL,
  `battle_count` int DEFAULT NULL,
  `three_crown_wins` int DEFAULT NULL,
  `challenge_cards_won` int DEFAULT NULL,
  `tournament_cards_won` int DEFAULT NULL,
  `clan_tag` varchar(20) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `donations` int DEFAULT NULL,
  `donations_received` int DEFAULT NULL,
  `total_donations` int DEFAULT NULL,
  `war_day_wins` int DEFAULT NULL,
  `clan_cards_collected` int DEFAULT NULL,
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`tag`),
  KEY `fk_players_clan` (`clan_tag`),
  CONSTRAINT `fk_players_clan` FOREIGN KEY (`clan_tag`) REFERENCES `clans` (`tag`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-02 13:06:41
