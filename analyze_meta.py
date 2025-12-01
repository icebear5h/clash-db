#!/usr/bin/env python3
"""
Advanced Meta Analysis for Clash Royale
Analyzes card usage, win rates, synergies, and deck archetypes
"""

import os
import json
from collections import defaultdict, Counter
from itertools import combinations
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

def get_db_session():
    """Create database session."""
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def analyze_meta():
    """Run comprehensive meta analysis."""
    session = get_db_session()
    
    print("=" * 70)
    print("CLASH ROYALE META ANALYSIS REPORT")
    print("=" * 70)
    
    # Get all cards for name mapping
    cards_result = session.execute(text("SELECT id, name, rarity, elixir FROM cards"))
    card_map = {row[0]: {'name': row[1], 'rarity': row[2], 'elixir': row[3]} for row in cards_result}
    
    # Get all battles with card data
    battles_result = session.execute(text("""
        SELECT id, player_cards, opponent_cards, is_winner 
        FROM battles 
        WHERE player_cards IS NOT NULL
    """))
    
    battles = list(battles_result)
    total_battles = len(battles)
    
    print(f"\nTotal Battles Analyzed: {total_battles:,}")
    print(f"Total Unique Cards: {len(card_map)}")
    
    # Initialize counters
    card_usage = Counter()
    card_wins = Counter()
    pair_usage = Counter()
    pair_wins = Counter()
    triple_usage = Counter()
    triple_wins = Counter()
    
    # Process each battle
    for battle_id, player_cards_json, opponent_cards_json, is_winner in battles:
        try:
            player_cards = json.loads(player_cards_json) if isinstance(player_cards_json, str) else player_cards_json
            
            # Get card IDs from player deck
            card_ids = tuple(sorted([c['id'] for c in player_cards]))
            
            # Count individual card usage
            for card_id in card_ids:
                card_usage[card_id] += 1
                if is_winner:
                    card_wins[card_id] += 1
            
            # Count pairs
            for pair in combinations(card_ids, 2):
                pair_usage[pair] += 1
                if is_winner:
                    pair_wins[pair] += 1
            
            # Count triples (for archetype detection)
            for triple in combinations(card_ids, 3):
                triple_usage[triple] += 1
                if is_winner:
                    triple_wins[triple] += 1
                    
        except Exception as e:
            continue
    
    # ==========================================================================
    # 1. MOST USED CARDS
    # ==========================================================================
    print("\n" + "=" * 70)
    print("TOP 25 MOST USED CARDS")
    print("=" * 70)
    print(f"{'Rank':<5} {'Card':<20} {'Rarity':<12} {'Uses':<8} {'Usage%':<8} {'Win%':<8}")
    print("-" * 70)
    
    for rank, (card_id, uses) in enumerate(card_usage.most_common(25), 1):
        card = card_map.get(card_id, {'name': f'Unknown ({card_id})', 'rarity': '?'})
        usage_pct = (uses / (total_battles * 8)) * 100  # 8 cards per deck
        win_pct = (card_wins[card_id] / uses) * 100 if uses > 0 else 0
        print(f"{rank:<5} {card['name']:<20} {card['rarity']:<12} {uses:<8} {usage_pct:<8.2f} {win_pct:<8.2f}")
    
    # ==========================================================================
    # 2. HIGHEST WIN RATE CARDS (min 100 uses)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("TOP 20 HIGHEST WIN RATE CARDS (min 100 uses)")
    print("=" * 70)
    print(f"{'Rank':<5} {'Card':<20} {'Rarity':<12} {'Uses':<8} {'Win%':<8} {'Usage%':<8}")
    print("-" * 70)
    
    win_rates = []
    for card_id, uses in card_usage.items():
        if uses >= 100:
            win_pct = (card_wins[card_id] / uses) * 100
            usage_pct = (uses / (total_battles * 8)) * 100
            win_rates.append((card_id, win_pct, uses, usage_pct))
    
    win_rates.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (card_id, win_pct, uses, usage_pct) in enumerate(win_rates[:20], 1):
        card = card_map.get(card_id, {'name': f'Unknown ({card_id})', 'rarity': '?'})
        print(f"{rank:<5} {card['name']:<20} {card['rarity']:<12} {uses:<8} {win_pct:<8.2f} {usage_pct:<8.2f}")
    
    # ==========================================================================
    # 3. MOST META CARDS (High usage + High win rate)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("TOP 20 MOST META CARDS (Usage × Win Rate)")
    print("=" * 70)
    print(f"{'Rank':<5} {'Card':<20} {'Usage%':<10} {'Win%':<10} {'Meta Score':<12}")
    print("-" * 70)
    
    meta_scores = []
    for card_id, uses in card_usage.items():
        if uses >= 50:
            usage_pct = (uses / (total_battles * 8)) * 100
            win_pct = (card_wins[card_id] / uses) * 100
            meta_score = usage_pct * (win_pct / 50)  # Normalize win rate around 50%
            meta_scores.append((card_id, usage_pct, win_pct, meta_score))
    
    meta_scores.sort(key=lambda x: x[3], reverse=True)
    
    for rank, (card_id, usage_pct, win_pct, meta_score) in enumerate(meta_scores[:20], 1):
        card = card_map.get(card_id, {'name': f'Unknown ({card_id})', 'rarity': '?'})
        print(f"{rank:<5} {card['name']:<20} {usage_pct:<10.2f} {win_pct:<10.2f} {meta_score:<12.2f}")
    
    # ==========================================================================
    # 4. TOP CARD SYNERGIES (Pairs that appear together)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("TOP 25 CARD SYNERGIES (Most used pairs)")
    print("=" * 70)
    print(f"{'Card 1':<18} {'Card 2':<18} {'Together':<10} {'Win%':<8} {'Synergy%':<10}")
    print("-" * 70)
    
    for (card1_id, card2_id), uses in pair_usage.most_common(25):
        card1 = card_map.get(card1_id, {'name': '?'})['name']
        card2 = card_map.get(card2_id, {'name': '?'})['name']
        win_pct = (pair_wins[(card1_id, card2_id)] / uses) * 100 if uses > 0 else 0
        synergy_pct = (uses / total_battles) * 100
        print(f"{card1:<18} {card2:<18} {uses:<10} {win_pct:<8.2f} {synergy_pct:<10.2f}")
    
    # ==========================================================================
    # 5. HIGHEST WIN RATE PAIRS (min 50 uses)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("TOP 20 WINNING COMBOS (Highest win rate pairs, min 50 uses)")
    print("=" * 70)
    print(f"{'Card 1':<18} {'Card 2':<18} {'Together':<10} {'Win%':<8}")
    print("-" * 70)
    
    pair_win_rates = []
    for (card1_id, card2_id), uses in pair_usage.items():
        if uses >= 50:
            win_pct = (pair_wins[(card1_id, card2_id)] / uses) * 100
            pair_win_rates.append(((card1_id, card2_id), win_pct, uses))
    
    pair_win_rates.sort(key=lambda x: x[1], reverse=True)
    
    for (card1_id, card2_id), win_pct, uses in pair_win_rates[:20]:
        card1 = card_map.get(card1_id, {'name': '?'})['name']
        card2 = card_map.get(card2_id, {'name': '?'})['name']
        print(f"{card1:<18} {card2:<18} {uses:<10} {win_pct:<8.2f}")
    
    # ==========================================================================
    # 6. DECK ARCHETYPES (Most common 3-card cores)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("TOP 15 DECK ARCHETYPES (Most common 3-card cores)")
    print("=" * 70)
    print(f"{'Core Cards':<50} {'Uses':<8} {'Win%':<8}")
    print("-" * 70)
    
    for (c1, c2, c3), uses in triple_usage.most_common(15):
        if uses >= 20:
            card1 = card_map.get(c1, {'name': '?'})['name']
            card2 = card_map.get(c2, {'name': '?'})['name']
            card3 = card_map.get(c3, {'name': '?'})['name']
            core = f"{card1} + {card2} + {card3}"
            win_pct = (triple_wins[(c1, c2, c3)] / uses) * 100 if uses > 0 else 0
            print(f"{core:<50} {uses:<8} {win_pct:<8.2f}")
    
    # ==========================================================================
    # 7. UNDERRATED CARDS (High win rate, low usage)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("UNDERRATED CARDS (Win% > 52%, Usage < 1%)")
    print("=" * 70)
    print(f"{'Card':<20} {'Rarity':<12} {'Uses':<8} {'Win%':<8} {'Usage%':<8}")
    print("-" * 70)
    
    underrated = []
    for card_id, uses in card_usage.items():
        if uses >= 30:
            usage_pct = (uses / (total_battles * 8)) * 100
            win_pct = (card_wins[card_id] / uses) * 100
            if usage_pct < 1.0 and win_pct > 52:
                underrated.append((card_id, uses, win_pct, usage_pct))
    
    underrated.sort(key=lambda x: x[2], reverse=True)
    
    for card_id, uses, win_pct, usage_pct in underrated[:15]:
        card = card_map.get(card_id, {'name': '?', 'rarity': '?'})
        print(f"{card['name']:<20} {card['rarity']:<12} {uses:<8} {win_pct:<8.2f} {usage_pct:<8.2f}")
    
    # ==========================================================================
    # 8. OVERRATED CARDS (High usage, low win rate)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("OVERRATED CARDS (Usage > 1%, Win% < 48%)")
    print("=" * 70)
    print(f"{'Card':<20} {'Rarity':<12} {'Uses':<8} {'Win%':<8} {'Usage%':<8}")
    print("-" * 70)
    
    overrated = []
    for card_id, uses in card_usage.items():
        if uses >= 100:
            usage_pct = (uses / (total_battles * 8)) * 100
            win_pct = (card_wins[card_id] / uses) * 100
            if usage_pct > 1.0 and win_pct < 48:
                overrated.append((card_id, uses, win_pct, usage_pct))
    
    overrated.sort(key=lambda x: x[3], reverse=True)  # Sort by usage
    
    for card_id, uses, win_pct, usage_pct in overrated[:15]:
        card = card_map.get(card_id, {'name': '?', 'rarity': '?'})
        print(f"{card['name']:<20} {card['rarity']:<12} {uses:<8} {win_pct:<8.2f} {usage_pct:<8.2f}")
    
    # ==========================================================================
    # 9. RARITY BREAKDOWN
    # ==========================================================================
    print("\n" + "=" * 70)
    print("STATS BY RARITY")
    print("=" * 70)
    
    rarity_stats = defaultdict(lambda: {'uses': 0, 'wins': 0, 'cards': set()})
    for card_id, uses in card_usage.items():
        card = card_map.get(card_id, {'rarity': 'unknown'})
        rarity = card.get('rarity', 'unknown')
        rarity_stats[rarity]['uses'] += uses
        rarity_stats[rarity]['wins'] += card_wins[card_id]
        rarity_stats[rarity]['cards'].add(card_id)
    
    print(f"{'Rarity':<12} {'Unique Cards':<14} {'Total Uses':<12} {'Avg Win%':<10}")
    print("-" * 50)
    for rarity in ['common', 'rare', 'epic', 'legendary', 'champion']:
        if rarity in rarity_stats:
            stats = rarity_stats[rarity]
            win_pct = (stats['wins'] / stats['uses']) * 100 if stats['uses'] > 0 else 0
            print(f"{rarity:<12} {len(stats['cards']):<14} {stats['uses']:<12} {win_pct:<10.2f}")
    
    print("\n" + "=" * 70)
    print("END OF META ANALYSIS REPORT")
    print("=" * 70)
    
    session.close()

if __name__ == '__main__':
    analyze_meta()
