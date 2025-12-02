# Clash Royale Meta Analysis Platform

A data-driven analytics platform that analyzes competitive Clash Royale battles to identify optimal card usage, winning deck compositions, and card synergies.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Database Setup](#database-setup)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Database Schema](#database-schema)
- [Analysis Examples](#analysis-examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

This platform collects battle data from the official Clash Royale API and performs statistical analysis to identify:
- Most effective cards and deck compositions
- Win rates across different trophy ranges
- Card synergies and counter-strategies
- Hidden gems (underrated cards)
- Meta trends over time

### Current Dataset

| Metric | Value |
|--------|-------|
| Battles Analyzed | 500 |
| Unique Players | 597 |
| Cards Tracked | 121 |
| Database Size | ~2 MB |

---

## Features

### Data Collection
- Automated player tag discovery via battle opponent crawling
- Batch collection across trophy ranges (0-4k, 4k-8k, 8k-10k, 10k+)
- Battle history extraction with full deck compositions
- Card metadata synchronization

### Analysis Capabilities
- Card usage frequency analysis
- Win rate calculations per card
- Card pair synergy detection
- Deck archetype identification
- Trophy range meta snapshots
- Underrated/overrated card discovery

### Reporting
- Formatted text reports with strategic insights
- SQL queries for custom analysis
- CSV data exports
- Entity-relationship diagrams

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **MySQL 8.0+**
- **Clash Royale API Key** ([Get one here](https://developer.clashroyale.com/))

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd windsurf-project-3

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API key and MySQL credentials
```

### Database Setup

**Option 1: Quick Setup (Recommended)**

Import the complete database with sample data:

```bash
# Create database and import everything in one step
mysql -u root -p -e "CREATE DATABASE clash_royale;"
mysql -u root -p clash_royale < database_dump.sql
```

**Option 2: Schema + Data Separately**

View the structure first, then populate:

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE clash_royale;"

# Import schema (structure only)
mysql -u root -p clash_royale < schema.sql

# Import sample data
mysql -u root -p clash_royale < database_dump.sql
```

**Verify Setup:**

```bash
# Check tables and row counts
./show_tables.sh

# Or use MySQL directly
mysql -u root -p clash_royale -e "SHOW TABLES;"
```

---

## Database Setup

### Files

| File | Size | Description |
|------|------|-------------|
| `schema.sql` | 6.4 KB | Database structure only (7 tables) |
| `database_dump.sql` | 885 KB | Complete dump with sample data (500 battles, 597 players, 121 cards) |

### Tables Created

1. **players** - Player profiles (tag, name, trophies, wins, losses, etc.)
2. **battles** - Battle records with full deck compositions
3. **cards** - Card metadata (name, rarity, type, elixir cost)
4. **clans** - Clan information (score, members, location)
5. **decks** - Unique deck compositions
6. **deck_cards** - Junction table linking decks to cards
7. **meta_snapshots** - Periodic meta analysis results

### Schema Details

```sql
-- Example: Players table structure
CREATE TABLE players (
  tag VARCHAR(20) PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  trophies INT,
  best_trophies INT,
  wins INT,
  losses INT,
  battle_count INT,
  clan_tag VARCHAR(20),
  last_updated DATETIME,
  FOREIGN KEY (clan_tag) REFERENCES clans(tag)
);
```

For complete schema, see [schema.sql](schema.sql).

---

## Project Structure

```
clash-royale-meta-analysis/
│
├── 📊 Analysis & Reports
│   ├── analyze_meta.py           # Statistical analysis script
│   ├── generate_report.py        # Formatted report generator
│   ├── meta_queries.sql          # Advanced SQL queries
│   ├── META_REPORT.txt           # Generated analysis report
│   └── PROJECT_REPORT.md         # Full project documentation
│
├── 🗄️ Database
│   ├── schema.sql                # Database structure (6.4 KB)
│   ├── database_dump.sql         # Complete data dump (885 KB)
│   ├── show_tables.sh            # Utility to view tables
│   └── src/db/
│       ├── models.py             # SQLAlchemy ORM models
│       ├── config.py             # Database configuration
│       └── init_db.py            # Database initialization
│
├── 🔌 API & Data Collection
│   ├── src/api/
│   │   ├── client.py             # Clash Royale API wrapper
│   │   └── processor.py          # Data transformation logic
│   ├── src/collector.py          # Main data collection pipeline
│   └── src/tag_discovery.py      # Player tag crawler
│
├── 📈 Data Exports
│   └── data/exports/
│       ├── battles_sample.csv    # Battle data export
│       ├── players.csv           # Player data export
│       └── cards.csv             # Card metadata export
│
├── ⚙️ Configuration
│   ├── .env                      # Environment variables (API keys, DB credentials)
│   ├── .env.example              # Template for environment setup
│   ├── requirements.txt          # Python dependencies
│   └── player_tags.txt           # Seed player tags for collection
│
└── 📝 Documentation
    └── README.md                 # This file
```

---

## Usage Guide

### 1. View Current Data

```bash
# Show all tables with row counts and sizes
./show_tables.sh

# Query specific data
mysql -u root -p clash_royale -e "SELECT COUNT(*) FROM battles;"
mysql -u root -p clash_royale -e "SELECT * FROM cards LIMIT 10;"
```

### 2. Collect New Data

```bash
# Activate virtual environment
source venv/bin/activate

# Collect data from a specific player
python3 src/collector.py

# Discover new player tags
python3 src/tag_discovery.py

# Batch collection across trophy ranges
# (Edit player_tags.txt first with seed tags)
python3 src/collector.py
```

### 3. Run Analysis

```bash
# Generate basic statistics
python3 analyze_meta.py

# Create formatted report
python3 generate_report.py

# Run custom SQL queries
mysql -u root -p clash_royale < meta_queries.sql
```

### 4. Export Data

Data is automatically exported to `data/exports/`:
- `battles_sample.csv` - Battle records
- `players.csv` - Player profiles
- `cards.csv` - Card metadata

---

## Database Schema

### Entity Relationships

```
┌─────────┐       ┌─────────┐       ┌─────────┐
│  Clans  │──────<│ Players │>──────│ Battles │
└─────────┘       └─────────┘       └─────────┘
                                          │
                                          │
                                          ▼
                                    ┌─────────┐
                                    │  Decks  │
                                    └─────────┘
                                          │
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                        ┌──────────┐           ┌─────────┐
                        │   Cards  │───────────│DeckCards│
                        └──────────┘           └─────────┘
```

### Key Tables

**Players**
- Primary Key: `tag` (e.g., "#ABC123")
- Stores: trophies, wins, losses, clan affiliation
- Foreign Key: `clan_tag` → `clans.tag`

**Battles**
- Primary Key: `id`
- Stores: battle outcomes, deck compositions (JSON), trophy changes
- Foreign Keys: `player_tag`, `opponent_tag` → `players.tag`

**Cards**
- Primary Key: `id`
- Stores: name, rarity, type, elixir cost
- Used for: deck composition analysis

---

## Analysis Examples

### Top 5 Most Used Cards

```sql
-- Query from meta_queries.sql
SELECT
    name,
    ROUND(usage_count * 100.0 / total_cards, 2) as usage_rate,
    ROUND(win_rate, 1) as win_rate
FROM card_usage
ORDER BY usage_count DESC
LIMIT 5;
```

| Card | Usage % | Win % |
|------|---------|-------|
| Arrows | 3.54% | 49.2% |
| Valkyrie | 2.63% | 49.9% |
| Mega Knight | 2.59% | 49.8% |
| Mini P.E.K.K.A | 2.58% | 48.1% |
| Firecracker | 2.57% | 50.9% |

### Hidden Gems (High Win Rate, Low Usage)

| Card | Win Rate | Usage % |
|------|----------|---------|
| Fisherman | 60.2% | 0.24% |
| Hunter | 59.6% | 0.43% |
| Little Prince | 55.7% | 0.28% |

### Best Card Synergies

| Pair | Combined Win Rate |
|------|-------------------|
| Giant + Elite Barbarians | 72.4% |
| Hunter + Electro Spirit | 71.3% |
| Skeletons + Royal Ghost | 70.9% |

---

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Database Connection
DATABASE_URL=mysql+mysqlconnector://root:your_password@localhost/clash_royale

# Clash Royale API
CLASH_ROYALE_API_KEY=your_api_key_here

# Collection Settings
SAMPLE_PLAYER_TAG=#2RPPVLR8J
MAX_PLAYERS_TO_COLLECT=100
BATTLES_PER_PLAYER=25

# Trophy Ranges for Collection
TROPHY_RANGES=0-4000,4000-8000,8000-10000,10000-15000

# Game Modes to Analyze
GAME_MODES=Ladder,pathOfLegend,riverRaceDuel
```

### Getting a Clash Royale API Key

1. Visit [developer.clashroyale.com](https://developer.clashroyale.com/)
2. Create an account (free)
3. Create a new API key
4. **Important:** Add your current IP address to the whitelist
5. Copy the key to your `.env` file

**Note:** API keys are IP-restricted. If your IP changes, you'll need to create a new key.

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | IP not whitelisted | Create new API key with current IP at [developer.clashroyale.com](https://developer.clashroyale.com/) |
| `MySQL Access Denied` | Wrong credentials | Check username/password in `.env` |
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r requirements.txt` |
| `Table doesn't exist` | Database not initialized | Run `mysql -u root -p clash_royale < database_dump.sql` |
| `No data returned` | API rate limit | Wait 60 seconds, then retry |
| `Import errors` | Wrong Python path | Use `PYTHONPATH=src python3 script.py` |

### Database Issues

```bash
# Check if database exists
mysql -u root -p -e "SHOW DATABASES LIKE 'clash_royale';"

# Verify tables
./show_tables.sh

# Reset database
mysql -u root -p -e "DROP DATABASE IF EXISTS clash_royale; CREATE DATABASE clash_royale;"
mysql -u root -p clash_royale < database_dump.sql
```

### Python Environment

```bash
# Verify Python version
python3 --version  # Should be 3.10+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check installed packages
pip list
```

---

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic

### Testing

Before submitting:
```bash
# Test database connection
python3 -c "from src.db.config import engine; print(engine.url)"

# Test API connection
python3 src/api/client.py

# Verify data collection
python3 src/collector.py --limit 1
```

---

## Utilities

### Helpful Scripts

```bash
# View database tables and sizes
./show_tables.sh

# Create fresh database dump
mysqldump -u root -p clash_royale > new_dump.sql

# Export specific table
mysql -u root -p clash_royale -e "SELECT * FROM cards;" > cards_export.csv

# Count battles by trophy range
mysql -u root -p clash_royale -e "
  SELECT
    CASE
      WHEN trophies < 4000 THEN '0-4000'
      WHEN trophies < 8000 THEN '4000-8000'
      WHEN trophies < 10000 THEN '8000-10000'
      ELSE '10000+'
    END as range,
    COUNT(*) as battles
  FROM battles b
  JOIN players p ON b.player_tag = p.tag
  GROUP BY range;"
```

---

## API Reference

### Clash Royale API Endpoints Used

| Endpoint | Purpose | Rate Limit |
|----------|---------|------------|
| `/players/{tag}` | Get player profile | 10/sec |
| `/players/{tag}/battlelog` | Get battle history | 10/sec |
| `/cards` | Get all card metadata | 10/sec |

Full API documentation: [developer.clashroyale.com/api](https://developer.clashroyale.com/api)

---

## Performance

### Optimization Tips

- **Batch Processing:** Collect 100+ players at once for efficiency
- **Rate Limiting:** Built-in 0.5s delay between API requests
- **Database Indexing:** Primary keys on `tag` fields for fast lookups
- **Data Deduplication:** Checks existing records before inserting

### Benchmarks

| Operation | Time | Records |
|-----------|------|---------|
| Import database_dump.sql | ~2s | 500 battles + 597 players |
| Collect 1 player + battles | ~3s | 1 player + 25 battles |
| Generate meta report | ~1s | Analyzes all data |
| Export to CSV | <1s | All tables |

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **[Supercell](https://supercell.com/)** - For the Clash Royale game and official API
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Python SQL toolkit and ORM
- **[Requests](https://requests.readthedocs.io/)** - HTTP library for API calls
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - Environment variable management

---

## Contact & Support

- **Issues:** Report bugs via GitHub Issues
- **Documentation:** This README and inline code comments
- **API Support:** [developer.clashroyale.com](https://developer.clashroyale.com/)

---

## Roadmap

### Planned Features

- [ ] Web dashboard for visualizing meta trends
- [ ] Real-time data collection scheduler
- [ ] Machine learning deck recommendation engine
- [ ] Discord bot for meta queries
- [ ] Historical meta tracking and comparison
- [ ] Deck counter suggestion algorithm

### Version History

**v1.0.0** (Current)
- Initial release
- Basic data collection and analysis
- 500 battle sample dataset
- CLI-based reporting

---

**Built with ❤️ for the Clash Royale community**
