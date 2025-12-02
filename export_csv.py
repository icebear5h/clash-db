#!/usr/bin/env python3
"""Export all database tables to CSV files."""

import os
import csv
from datetime import datetime
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# Add src to path
import sys
sys.path.insert(0, 'src')

from db import engine

OUTPUT_DIR = 'data/exports'

TABLES = [
    'locations',
    'players',
    'cards',
    'decks', 
    'deck_cards',
    'player_decks',
    'battles',
    'battle_players',
    'meta_snapshots',
    'deck_snapshot_stats',
    'card_snapshot_stats',
    'leaderboards',
    'leaderboard_snapshots',
    'leaderboard_snapshot_players',
    'tournaments',
    'tournament_members'
]


def export_table(table_name: str, output_dir: str) -> int:
    """Export a single table to CSV. Returns row count."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{table_name}.csv')
    
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT * FROM {table_name}'))
        rows = result.fetchall()
        columns = result.keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
    
    return len(rows)


def main():
    print(f"Exporting tables to {OUTPUT_DIR}/")
    print("-" * 40)
    
    total_rows = 0
    for table in TABLES:
        try:
            count = export_table(table, OUTPUT_DIR)
            print(f"  {table}: {count} rows")
            total_rows += count
        except Exception as e:
            print(f"  {table}: ERROR - {e}")
    
    print("-" * 40)
    print(f"Total: {total_rows} rows exported")
    print(f"Files saved to: {OUTPUT_DIR}/")


if __name__ == '__main__':
    main()
