# 🏆 Clash Royale Meta Analysis Platform

A data-driven analytics platform that analyzes competitive Clash Royale battles to identify optimal card usage, winning deck compositions, and card synergies.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| **Battles Analyzed** | 13,974 |
| **Unique Players** | 291 |
| **Cards Tracked** | 121 |
| **Data Period** | Oct - Dec 2025 |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Automated Data Collection** | Crawls the Clash Royale API to discover players and collect battle data |
| **Card Usage Analysis** | Tracks how frequently each card appears in competitive decks |
| **Win Rate Calculation** | Computes win percentages for cards, card pairs, and deck archetypes |
| **Synergy Detection** | Identifies card combinations that perform above average together |
| **Meta Reporting** | Generates comprehensive reports with strategic recommendations |
| **Underrated/Overrated Cards** | Finds hidden gems and popular-but-underperforming cards |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- Clash Royale API Key ([Get one here](https://developer.clashroyale.com/))

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd windsurf-project-3

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API key and MySQL credentials

# 5. Initialize database
python3 src/db/init_db.py
```

### Running the Analysis

```bash
# Option 1: Full pipeline (recommended)
./run_full_pipeline.sh

# Option 2: Run steps individually
python3 src/tag_discovery.py      # Step 1: Discover player tags
python3 src/collector.py          # Step 2: Collect battle data
python3 analyze_meta.py           # Step 3: Analyze meta

# Option 3: Generate formatted report
python3 generate_report.py
```

---

## 📁 Project Structure

```
clash-royale-meta-analysis/
│
├── 📊 Analysis & Reports
│   ├── analyze_meta.py           # Basic meta statistics
│   ├── generate_report.py        # Formatted report generator
│   ├── meta_queries.sql          # Advanced SQL queries
│   ├── META_REPORT.txt           # Generated analysis report
│   └── PROJECT_REPORT.md         # Academic project report
│
├── 🗄️ Database
│   ├── src/db/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── config.py             # Database configuration
│   │   └── init_db.py            # Database initialization
│   ├── er_diagram.png            # Entity-Relationship diagram
│   └── er_diagram.pdf            # ER diagram (PDF)
│
├── 🔌 API & Data Collection
│   ├── src/api/
│   │   ├── client.py             # Clash Royale API client
│   │   └── processor.py          # Data transformation
│   ├── src/collector.py          # Main data collector
│   └── src/tag_discovery.py      # Player tag crawler
│
├── ⚙️ Configuration
│   ├── .env                      # Environment variables (API keys, DB)
│   ├── requirements.txt          # Python dependencies
│   └── player_tags.txt           # Seed player tags
│
└── 📝 Documentation
    ├── README.md                 # This file
    └── PROJECT_REPORT.md         # Full academic report
```

---

## 🗃️ Database Schema

![ER Diagram](er_diagram.png)

### Tables

| Table | Description | Records |
|-------|-------------|---------|
| `players` | Player profiles (tag, trophies, wins, etc.) | 291 |
| `cards` | Card metadata (name, rarity, elixir) | 121 |
| `battles` | Battle outcomes with deck compositions | 13,974 |
| `decks` | Unique deck compositions | ~8,000 |
| `deck_cards` | Junction table (deck ↔ cards) | - |
| `meta_snapshots` | Periodic meta statistics | - |

---

## 📈 Sample Analysis Results

### Top 5 Most Used Cards
| Card | Usage % | Win % |
|------|---------|-------|
| Arrows | 3.54% | 49.2% |
| Valkyrie | 2.63% | 49.9% |
| Mega Knight | 2.59% | 49.8% |
| Mini P.E.K.K.A | 2.58% | 48.1% |
| Firecracker | 2.57% | 50.9% |

### Hidden Gems (Underrated Cards)
| Card | Win % | Usage % |
|------|-------|---------|
| **Fisherman** | 60.2% | 0.24% |
| **Hunter** | 59.6% | 0.43% |
| **Little Prince** | 55.7% | 0.28% |

### Best Card Synergies
| Combo | Win Rate |
|-------|----------|
| Giant + Elite Barbarians | **72.4%** |
| Hunter + Electro Spirit | **71.3%** |
| Skeletons + Royal Ghost | **70.9%** |

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Database
DATABASE_URL=mysql+mysqlconnector://root:password@localhost/clash_royale

# API
CLASH_ROYALE_API_KEY=your_api_key_here

# Collection Settings
SAMPLE_PLAYER_TAG=#2RPPVLR8J
MAX_PLAYERS_TO_COLLECT=100
BATTLES_PER_PLAYER=25
```

### API Key Setup

1. Go to [developer.clashroyale.com](https://developer.clashroyale.com/)
2. Create an account and generate a new API key
3. **Important:** Whitelist your current IP address
4. Copy the key to your `.env` file

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **403 Forbidden** | Your IP isn't whitelisted. Create a new API key with your current IP. |
| **MySQL Access Denied** | Check credentials in `.env`. Run `unset DATABASE_URL` if previously exported. |
| **Import Errors** | Run with `PYTHONPATH=src python3 script.py` |
| **No Data Returned** | API rate limit hit. Wait 1 minute and retry. |

---

## 📚 Key Files

| File | Purpose | Run Command |
|------|---------|-------------|
| `analyze_meta.py` | Generate basic statistics | `python3 analyze_meta.py` |
| `generate_report.py` | Create formatted report | `python3 generate_report.py` |
| `create_er_diagram.py` | Generate ER diagram | `python3 create_er_diagram.py` |
| `meta_queries.sql` | Advanced SQL analysis | `mysql < meta_queries.sql` |

---

## 📖 Reports Generated

- **`META_REPORT.txt`** - Full formatted analysis with recommendations
- **`meta_analysis_report.txt`** - Raw statistics output
- **`PROJECT_REPORT.md`** - Academic project documentation
- **`er_diagram.png`** - Database schema visualization

---

## 🔗 Data Source

All data is collected from the [Official Clash Royale API](https://developer.clashroyale.com/) provided by Supercell.

- **Rate Limit:** 10 requests/second
- **Data Format:** JSON
- **Authentication:** Bearer token

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [Supercell](https://supercell.com/) for the Clash Royale API
- [SQLAlchemy](https://www.sqlalchemy.org/) for ORM
- [Graphviz](https://graphviz.org/) for ER diagram generation
