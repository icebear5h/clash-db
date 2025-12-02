"""
Reduce dataset to 5,000 random battles for easier class submission.
This keeps data integrity while making the SQL dump manageable.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def reduce_dataset():
    """Randomly select 5,000 battles and keep only related players."""

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found")
        return False

    engine = create_engine(db_url)

    print("Starting dataset reduction to 5,000 battles...")

    with engine.connect() as conn:
        try:
            # Get current counts
            result = conn.execute(text("SELECT COUNT(*) FROM battles"))
            original_battles = result.fetchone()[0]

            result = conn.execute(text("SELECT COUNT(*) FROM players"))
            original_players = result.fetchone()[0]

            print(f"\nOriginal data:")
            print(f"  Battles: {original_battles:,}")
            print(f"  Players: {original_players:,}")

            # Create temporary table with 5,000 random battles
            print("\nStep 1: Selecting 5,000 random battles...")
            conn.execute(text("DROP TABLE IF EXISTS battles_temp"))
            conn.execute(text("""
                CREATE TABLE battles_temp AS
                SELECT * FROM battles
                ORDER BY RAND()
                LIMIT 5000
            """))
            conn.commit()
            print("  ✓ Random sample created")

            # Get list of player tags referenced in sampled battles
            print("\nStep 2: Finding players in sampled battles...")
            conn.execute(text("DROP TABLE IF EXISTS players_to_keep"))
            conn.execute(text("""
                CREATE TABLE players_to_keep AS
                SELECT DISTINCT player_tag AS tag FROM battles_temp
                UNION
                SELECT DISTINCT opponent_tag AS tag FROM battles_temp
            """))
            conn.commit()

            result = conn.execute(text("SELECT COUNT(*) FROM players_to_keep"))
            players_to_keep = result.fetchone()[0]
            print(f"  ✓ Found {players_to_keep:,} unique players")

            # Temporarily disable foreign key checks
            print("\nStep 3: Disabling foreign key checks...")
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()

            # Replace battles table with sampled data first
            print("\nStep 4: Replacing battles table...")
            conn.execute(text("DROP TABLE battles"))
            conn.execute(text("ALTER TABLE battles_temp RENAME TO battles"))
            conn.commit()
            print("  ✓ Battles table updated")

            # Now delete players not in the sampled battles
            print("\nStep 5: Removing unused players...")
            conn.execute(text("""
                DELETE FROM players
                WHERE tag NOT IN (SELECT tag FROM players_to_keep)
            """))
            conn.commit()
            print("  ✓ Unused players removed")

            # Re-enable foreign key checks
            print("\nStep 6: Re-enabling foreign key checks...")
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()

            # Clean up meta_snapshots (optional - they're mostly empty anyway)
            print("\nStep 7: Cleaning meta_snapshots...")
            conn.execute(text("TRUNCATE TABLE meta_snapshots"))
            conn.commit()
            print("  ✓ Meta snapshots cleared")

            # Clean up temporary table
            conn.execute(text("DROP TABLE IF EXISTS players_to_keep"))
            conn.commit()

            # Get final counts
            result = conn.execute(text("SELECT COUNT(*) FROM battles"))
            final_battles = result.fetchone()[0]

            result = conn.execute(text("SELECT COUNT(*) FROM players"))
            final_players = result.fetchone()[0]

            result = conn.execute(text("SELECT COUNT(*) FROM cards"))
            cards_count = result.fetchone()[0]

            print("\n" + "="*50)
            print("DATASET REDUCTION COMPLETE!")
            print("="*50)
            print(f"\nFinal data:")
            print(f"  Battles: {final_battles:,} (was {original_battles:,})")
            print(f"  Players: {final_players:,} (was {original_players:,})")
            print(f"  Cards: {cards_count:,} (unchanged)")
            print(f"\nReduction: {((original_battles - final_battles) / original_battles * 100):.1f}% fewer battles")
            print(f"           {((original_players - final_players) / original_players * 100):.1f}% fewer players")

            print("\nNext step: Run mysqldump to create new database_dump.sql")
            print("  mysqldump -u root -plittlegenius clash_royale > database_dump.sql")

            return True

        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            conn.rollback()
            return False

if __name__ == "__main__":
    success = reduce_dataset()
    sys.exit(0 if success else 1)
