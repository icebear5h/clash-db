#!/usr/bin/env python3
"""
Create meta snapshots for different trophy ranges from existing battle data.

Trophy Ranges:
- 10k+: Top ladder / Ultimate Champion+
- 7k-10k: Mid-high ladder / Champion  
- 1k-7k: Mid ladder

Usage:
    python create_trophy_snapshots.py
"""

import sys
sys.path.insert(0, 'src')

from collector import MetaCollector, create_trophy_range_snapshots, collect_meta_by_trophy_range


def main():
    print("🏅 Creating Trophy Range Meta Snapshots")
    print("=" * 50)
    
    collector = MetaCollector()
    
    try:
        # Ensure card cache is populated
        collector._refresh_card_cache()
        
        # Create snapshots for all predefined trophy ranges
        snapshots = create_trophy_range_snapshots(collector)
        
        print("\n📊 Created Snapshots:")
        print("-" * 50)
        
        for snapshot in snapshots:
            trophy_range = ""
            if snapshot.trophy_min and snapshot.trophy_max:
                trophy_range = f"{snapshot.trophy_min:,} - {snapshot.trophy_max:,}"
            elif snapshot.trophy_min:
                trophy_range = f"{snapshot.trophy_min:,}+"
            
            print(f"\n  📌 {snapshot.snapshot_type}")
            print(f"     Trophy Range: {trophy_range}")
            print(f"     Battles: {snapshot.sample_size}")
            print(f"     Unique Decks: {snapshot.total_decks}")
        
        if not snapshots:
            print("\n⚠️  No snapshots created. This could mean:")
            print("   - No battle data exists in the database")
            print("   - No battles have trophy data recorded")
            print("   - Run the collector first to gather battle data")
        
        print("\n" + "=" * 50)
        print("✅ Done!")
        
    finally:
        collector.close()


if __name__ == '__main__':
    main()
