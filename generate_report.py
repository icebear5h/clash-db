#!/usr/bin/env python3
"""
Clash Royale Meta Report Generator
Generates a professional, readable report explaining meta trends and insights
"""

import os
import json
from collections import defaultdict, Counter
from itertools import combinations
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

def get_db_session():
    """Create database session."""
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def generate_report():
    """Generate a comprehensive meta report."""
    session = get_db_session()
    
    # Get all cards for name mapping
    cards_result = session.execute(text("SELECT id, name, rarity, elixir FROM cards"))
    card_map = {row[0]: {'name': row[1], 'rarity': row[2], 'elixir': row[3]} for row in cards_result}
    
    # Get battle statistics
    battle_stats = session.execute(text("""
        SELECT 
            COUNT(*) as total,
            MIN(battle_time) as earliest,
            MAX(battle_time) as latest,
            COUNT(DISTINCT player_tag) as unique_players
        FROM battles 
        WHERE player_cards IS NOT NULL
    """)).fetchone()
    
    total_battles = battle_stats[0]
    earliest_battle = battle_stats[1]
    latest_battle = battle_stats[2]
    unique_players = battle_stats[3]
    
    # Get all battles with card data
    battles_result = session.execute(text("""
        SELECT id, player_cards, opponent_cards, is_winner 
        FROM battles 
        WHERE player_cards IS NOT NULL
    """))
    battles = list(battles_result)
    
    # Process battles
    card_usage = Counter()
    card_wins = Counter()
    pair_usage = Counter()
    pair_wins = Counter()
    
    for battle_id, player_cards_json, opponent_cards_json, is_winner in battles:
        try:
            player_cards = json.loads(player_cards_json) if isinstance(player_cards_json, str) else player_cards_json
            card_ids = tuple(sorted([c['id'] for c in player_cards]))
            
            for card_id in card_ids:
                card_usage[card_id] += 1
                if is_winner:
                    card_wins[card_id] += 1
            
            for pair in combinations(card_ids, 2):
                pair_usage[pair] += 1
                if is_winner:
                    pair_wins[pair] += 1
        except:
            continue
    
    # Calculate statistics
    top_used = card_usage.most_common(20)
    
    win_rates = []
    for card_id, uses in card_usage.items():
        if uses >= 100:
            win_pct = (card_wins[card_id] / uses) * 100
            usage_pct = (uses / (total_battles * 8)) * 100
            win_rates.append((card_id, win_pct, uses, usage_pct))
    win_rates.sort(key=lambda x: x[1], reverse=True)
    
    underrated = [(cid, u, (card_wins[cid]/u)*100, (u/(total_battles*8))*100) 
                  for cid, u in card_usage.items() 
                  if u >= 50 and (u/(total_battles*8))*100 < 1.0 and (card_wins[cid]/u)*100 > 52]
    underrated.sort(key=lambda x: x[2], reverse=True)
    
    overrated = [(cid, u, (card_wins[cid]/u)*100, (u/(total_battles*8))*100) 
                 for cid, u in card_usage.items() 
                 if u >= 100 and (u/(total_battles*8))*100 > 1.0 and (card_wins[cid]/u)*100 < 48]
    overrated.sort(key=lambda x: x[3], reverse=True)
    
    top_synergies = []
    for (c1, c2), uses in pair_usage.most_common(50):
        if uses >= 50:
            win_pct = (pair_wins[(c1, c2)] / uses) * 100
            top_synergies.append(((c1, c2), uses, win_pct))
    
    best_combos = []
    for (c1, c2), uses in pair_usage.items():
        if uses >= 50:
            win_pct = (pair_wins[(c1, c2)] / uses) * 100
            best_combos.append(((c1, c2), uses, win_pct))
    best_combos.sort(key=lambda x: x[2], reverse=True)
    
    # Generate report
    report = []
    report.append("=" * 80)
    report.append("CLASH ROYALE META ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"\nReport Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    report.append(f"Data Period: {earliest_battle.strftime('%b %d, %Y')} to {latest_battle.strftime('%b %d, %Y')}")
    report.append("")
    
    # Executive Summary
    report.append("-" * 80)
    report.append("EXECUTIVE SUMMARY")
    report.append("-" * 80)
    report.append(f"""
This report analyzes {total_battles:,} competitive Clash Royale battles from {unique_players:,} 
unique players. The analysis identifies the current meta trends, top-performing cards, 
optimal card synergies, and strategic insights for competitive play.

KEY FINDINGS:
""")
    
    # Top 3 meta cards
    top_meta = [(cid, (card_wins[cid]/u)*100, (u/(total_battles*8))*100) 
                for cid, u in card_usage.items() if u >= 100]
    top_meta.sort(key=lambda x: x[1] * x[2], reverse=True)
    
    report.append(f"  • The most dominant card in the meta is {card_map[top_meta[0][0]]['name']} ")
    report.append(f"    with a {top_meta[0][2]:.1f}% usage rate and {top_meta[0][1]:.1f}% win rate.")
    report.append("")
    
    if underrated:
        report.append(f"  • {card_map[underrated[0][0]]['name']} is the most underrated card, achieving ")
        report.append(f"    a {underrated[0][2]:.1f}% win rate despite only {underrated[0][3]:.2f}% usage.")
        report.append("")
    
    if overrated:
        report.append(f"  • {card_map[overrated[0][0]]['name']} may be overused - it has {overrated[0][3]:.1f}% usage ")
        report.append(f"    but only wins {overrated[0][2]:.1f}% of games.")
        report.append("")
    
    if best_combos:
        c1, c2 = best_combos[0][0]
        report.append(f"  • The strongest card combination is {card_map[c1]['name']} + {card_map[c2]['name']}")
        report.append(f"    with an impressive {best_combos[0][2]:.1f}% win rate.")
    
    # Section 1: Usage Analysis
    report.append("\n")
    report.append("-" * 80)
    report.append("SECTION 1: CARD USAGE ANALYSIS")
    report.append("-" * 80)
    report.append("""
Usage rate indicates how often a card appears in decks. A higher usage rate suggests 
the card is considered essential or versatile by the player community.

INTERPRETATION GUIDE:
  • >3% usage: Extremely popular, likely a meta staple
  • 2-3% usage: Very common, widely used
  • 1-2% usage: Moderately popular
  • <1% usage: Niche or underutilized
""")
    
    report.append("TOP 15 MOST USED CARDS:")
    report.append("-" * 50)
    report.append(f"{'Rank':<5} {'Card':<20} {'Rarity':<12} {'Usage%':<8}")
    report.append("-" * 50)
    
    for rank, (card_id, uses) in enumerate(top_used[:15], 1):
        card = card_map.get(card_id, {'name': '?', 'rarity': '?'})
        usage_pct = (uses / (total_battles * 8)) * 100
        report.append(f"{rank:<5} {card['name']:<20} {card['rarity']:<12} {usage_pct:.2f}%")
    
    report.append("""
ANALYSIS:
""")
    
    # Categorize top cards
    spells = ['Arrows', 'The Log', 'Zap', 'Fireball', 'Barbarian Barrel', 'Tornado']
    tanks = ['Mega Knight', 'P.E.K.K.A', 'Golem', 'Giant', 'Valkyrie']
    
    top_card_names = [card_map[cid]['name'] for cid, _ in top_used[:10]]
    spell_count = sum(1 for s in spells if s in top_card_names)
    tank_count = sum(1 for t in tanks if t in top_card_names)
    
    report.append(f"  The current meta favors {spell_count} spells and {tank_count} tanks in the top 10,")
    report.append(f"  indicating a {'spell-heavy' if spell_count > tank_count else 'tank-heavy'} meta.")
    
    # Section 2: Win Rate Analysis
    report.append("\n")
    report.append("-" * 80)
    report.append("SECTION 2: WIN RATE ANALYSIS")
    report.append("-" * 80)
    report.append("""
Win rate measures how often decks containing a card win their matches. Cards with 
win rates significantly above 50% are performing well in the current meta.

INTERPRETATION GUIDE:
  • >55% win rate: Overpowered, likely needs balancing
  • 52-55% win rate: Strong performer
  • 48-52% win rate: Balanced
  • <48% win rate: Underperforming
""")
    
    report.append("TOP 15 HIGHEST WIN RATE CARDS (min. 100 uses):")
    report.append("-" * 55)
    report.append(f"{'Rank':<5} {'Card':<20} {'Win Rate':<12} {'Sample Size':<12}")
    report.append("-" * 55)
    
    for rank, (card_id, win_pct, uses, _) in enumerate(win_rates[:15], 1):
        card = card_map.get(card_id, {'name': '?'})
        report.append(f"{rank:<5} {card['name']:<20} {win_pct:.1f}%{'':<6} {uses:,}")
    
    report.append("""
ANALYSIS:
""")
    if win_rates[0][1] > 55:
        report.append(f"  WARNING: {card_map[win_rates[0][0]]['name']} has an unusually high win rate of {win_rates[0][1]:.1f}%.")
        report.append(f"          This card may be overpowered in the current meta.")
    
    # Section 3: Card Synergies
    report.append("\n")
    report.append("-" * 80)
    report.append("SECTION 3: CARD SYNERGIES")
    report.append("-" * 80)
    report.append("""
Synergy analysis identifies card pairs that frequently appear together and perform 
well as a combination. Strong synergies indicate cards that complement each other's 
strengths and weaknesses.
""")
    
    report.append("MOST POPULAR CARD COMBINATIONS:")
    report.append("-" * 65)
    report.append(f"{'Card 1':<18} {'Card 2':<18} {'Together':<10} {'Win%':<8}")
    report.append("-" * 65)
    
    for (c1, c2), uses, win_pct in top_synergies[:10]:
        name1 = card_map.get(c1, {'name': '?'})['name']
        name2 = card_map.get(c2, {'name': '?'})['name']
        report.append(f"{name1:<18} {name2:<18} {uses:<10} {win_pct:.1f}%")
    
    report.append("\n\nHIGHEST WIN RATE COMBINATIONS (min. 50 games):")
    report.append("-" * 65)
    report.append(f"{'Card 1':<18} {'Card 2':<18} {'Together':<10} {'Win%':<8}")
    report.append("-" * 65)
    
    for (c1, c2), uses, win_pct in best_combos[:10]:
        name1 = card_map.get(c1, {'name': '?'})['name']
        name2 = card_map.get(c2, {'name': '?'})['name']
        report.append(f"{name1:<18} {name2:<18} {uses:<10} {win_pct:.1f}%")
    
    # Section 4: Hidden Gems & Traps
    report.append("\n")
    report.append("-" * 80)
    report.append("SECTION 4: STRATEGIC INSIGHTS")
    report.append("-" * 80)
    
    report.append("""
UNDERRATED CARDS (High win rate, low usage):
These cards win more than 52% of games but are used in less than 1% of decks.
Consider adding these to your deck for a competitive edge.
""")
    report.append("-" * 55)
    report.append(f"{'Card':<20} {'Win Rate':<12} {'Usage':<10} {'Verdict':<15}")
    report.append("-" * 55)
    
    for card_id, uses, win_pct, usage_pct in underrated[:8]:
        card = card_map.get(card_id, {'name': '?'})
        verdict = "Hidden Gem!" if win_pct > 55 else "Worth Trying"
        report.append(f"{card['name']:<20} {win_pct:.1f}%{'':<6} {usage_pct:.2f}%{'':<4} {verdict}")
    
    report.append("""
\nOVERRATED CARDS (High usage, low win rate):
These cards are popular but underperform. Consider replacing them in your deck.
""")
    report.append("-" * 55)
    report.append(f"{'Card':<20} {'Win Rate':<12} {'Usage':<10} {'Verdict':<15}")
    report.append("-" * 55)
    
    for card_id, uses, win_pct, usage_pct in overrated[:8]:
        card = card_map.get(card_id, {'name': '?'})
        verdict = "Avoid" if win_pct < 45 else "Reconsider"
        report.append(f"{card['name']:<20} {win_pct:.1f}%{'':<6} {usage_pct:.1f}%{'':<5} {verdict}")
    
    # Section 5: Conclusions
    report.append("\n")
    report.append("-" * 80)
    report.append("SECTION 5: CONCLUSIONS & RECOMMENDATIONS")
    report.append("-" * 80)
    report.append("""
DECK BUILDING RECOMMENDATIONS:
""")
    
    # Get most reliable cards (good usage AND good win rate)
    reliable = [(cid, (card_wins[cid]/u)*100, (u/(total_battles*8))*100) 
                for cid, u in card_usage.items() 
                if u >= 200 and (card_wins[cid]/u)*100 > 51]
    reliable.sort(key=lambda x: x[1], reverse=True)
    
    report.append("  MUST-HAVE CARDS (Reliable high performers):")
    for cid, win_pct, usage_pct in reliable[:5]:
        report.append(f"    • {card_map[cid]['name']} - {win_pct:.1f}% win rate, {usage_pct:.1f}% usage")
    
    report.append("\n  HIDDEN GEMS TO CONSIDER:")
    for cid, uses, win_pct, usage_pct in underrated[:3]:
        report.append(f"    • {card_map[cid]['name']} - {win_pct:.1f}% win rate (underused)")
    
    report.append("\n  CARDS TO AVOID:")
    for cid, uses, win_pct, usage_pct in overrated[:3]:
        report.append(f"    • {card_map[cid]['name']} - only {win_pct:.1f}% win rate despite popularity")
    
    report.append("\n  STRONGEST SYNERGIES TO BUILD AROUND:")
    for (c1, c2), uses, win_pct in best_combos[:3]:
        name1 = card_map.get(c1, {'name': '?'})['name']
        name2 = card_map.get(c2, {'name': '?'})['name']
        report.append(f"    • {name1} + {name2} ({win_pct:.1f}% win rate)")
    
    report.append("""
\nMETA HEALTH ASSESSMENT:
""")
    
    # Calculate diversity
    usage_rates = [(u/(total_battles*8))*100 for _, u in card_usage.items()]
    top_10_share = sum(sorted(usage_rates, reverse=True)[:10])
    
    if top_10_share > 25:
        report.append(f"  The meta is CONCENTRATED - Top 10 cards represent {top_10_share:.1f}% of all usage.")
        report.append("  This indicates a stale meta with limited viable options.")
    else:
        report.append(f"  The meta is DIVERSE - Top 10 cards only represent {top_10_share:.1f}% of usage.")
        report.append("  Many different strategies are viable.")
    
    avg_win_rate = sum((card_wins[cid]/u)*100 for cid, u in card_usage.items() if u >= 50) / len([1 for _, u in card_usage.items() if u >= 50])
    report.append(f"\n  Average card win rate: {avg_win_rate:.1f}% (expected: ~50%)")
    
    report.append("\n")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    report.append(f"\nData source: {total_battles:,} battles from Clash Royale API")
    report.append(f"Analysis by: Clash Royale Meta Analyzer")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    session.close()
    
    # Output
    report_text = "\n".join(report)
    
    # Save to file
    with open('META_REPORT.txt', 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\nReport saved to META_REPORT.txt")

if __name__ == '__main__':
    generate_report()
