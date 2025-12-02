"""
Migration script to add the clans table to the existing database.
This script adds the clans table and the clan_tag foreign key to players.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Add clans table and update players table with clan_tag FK."""

    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    # Create engine
    engine = create_engine(db_url)

    print("Starting migration...")

    with engine.connect() as conn:
        try:
            # Create clans table
            print("Creating clans table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clans (
                    tag VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(20),
                    description VARCHAR(500),
                    badge_id INT,
                    clan_score INT,
                    clan_war_trophies INT,
                    required_trophies INT,
                    donations_per_week INT,
                    members_count INT,
                    location VARCHAR(100),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
            """))
            conn.commit()
            print("✓ Clans table created successfully")

            # Check if clan_tag column already exists in players table
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'clash_royale'
                AND TABLE_NAME = 'players'
                AND COLUMN_NAME = 'clan_tag'
            """))

            exists = result.fetchone()[0] > 0

            if not exists:
                # Add clan_tag column to players table
                print("Adding clan_tag column to players table...")
                conn.execute(text("""
                    ALTER TABLE players
                    ADD COLUMN clan_tag VARCHAR(20) AFTER tournament_cards_won
                """))
                conn.commit()
                print("✓ clan_tag column added successfully")

                # Add foreign key constraint
                print("Adding foreign key constraint...")
                conn.execute(text("""
                    ALTER TABLE players
                    ADD CONSTRAINT fk_players_clan
                    FOREIGN KEY (clan_tag) REFERENCES clans(tag)
                    ON DELETE SET NULL
                """))
                conn.commit()
                print("✓ Foreign key constraint added successfully")
            else:
                print("✓ clan_tag column already exists, skipping...")

            print("\nMigration completed successfully!")
            print("\nDatabase now has 7 tables:")
            print("1. players")
            print("2. clans")
            print("3. cards")
            print("4. battles")
            print("5. decks")
            print("6. deck_cards")
            print("7. meta_snapshots")

            return True

        except Exception as e:
            print(f"\n✗ ERROR during migration: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
