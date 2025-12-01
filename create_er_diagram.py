#!/usr/bin/env python3
"""
Generate ER Diagram for Clash Royale Database
Creates a visual entity-relationship diagram using graphviz
"""

import subprocess
import sys

# Check if graphviz is installed
try:
    from graphviz import Digraph
except ImportError:
    print("Installing graphviz...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "graphviz"])
    from graphviz import Digraph

def create_er_diagram():
    """Create an ER diagram for the Clash Royale database."""
    
    # Create a new directed graph
    dot = Digraph(comment='Clash Royale Database ER Diagram')
    dot.attr(rankdir='TB', size='12,12', dpi='150')
    dot.attr('node', shape='none', fontname='Helvetica')
    
    # Define entity tables with HTML-like labels
    
    # PLAYERS table
    players_label = '''<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightblue">
        <TR><TD COLSPAN="2" BGCOLOR="steelblue"><FONT COLOR="white"><B>PLAYERS</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">tag VARCHAR(20)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">name VARCHAR(50)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">exp_level INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">trophies INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">best_trophies INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">wins INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">losses INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">battle_count INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">donations INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">last_updated DATETIME</TD></TR>
    </TABLE>>'''
    dot.node('players', players_label)
    
    # CARDS table
    cards_label = '''<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightgreen">
        <TR><TD COLSPAN="2" BGCOLOR="darkgreen"><FONT COLOR="white"><B>CARDS</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">name VARCHAR(50)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">rarity VARCHAR(20)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">type VARCHAR(20)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">elixir INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">arena INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">description TEXT</TD></TR>
    </TABLE>>'''
    dot.node('cards', cards_label)
    
    # DECKS table
    decks_label = '''<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lightyellow">
        <TR><TD COLSPAN="2" BGCOLOR="goldenrod"><FONT COLOR="white"><B>DECKS</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">name VARCHAR(100)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">avg_elixir FLOAT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">win_rate FLOAT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">use_rate FLOAT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">cards_count INT</TD></TR>
    </TABLE>>'''
    dot.node('decks', decks_label)
    
    # DECK_CARDS junction table
    deck_cards_label = '''<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="lavender">
        <TR><TD COLSPAN="2" BGCOLOR="purple"><FONT COLOR="white"><B>DECK_CARDS</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK,FK</B></TD><TD ALIGN="LEFT">deck_id INT</TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK,FK</B></TD><TD ALIGN="LEFT">card_id INT</TD></TR>
    </TABLE>>'''
    dot.node('deck_cards', deck_cards_label)
    
    # BATTLES table
    battles_label = '''<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="mistyrose">
        <TR><TD COLSPAN="2" BGCOLOR="crimson"><FONT COLOR="white"><B>BATTLES</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id INT</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">player_tag VARCHAR(20)</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">opponent_tag VARCHAR(20)</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">deck_id INT</TD></TR>
        <TR><TD ALIGN="LEFT"><B>FK</B></TD><TD ALIGN="LEFT">opponent_deck_id INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">battle_time DATETIME</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">battle_type VARCHAR(50)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">game_mode VARCHAR(50)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">arena_name VARCHAR(50)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">is_winner BOOLEAN</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">player_crowns INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">opponent_crowns INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">trophy_change INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">player_cards JSON</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">opponent_cards JSON</TD></TR>
    </TABLE>>'''
    dot.node('battles', battles_label)
    
    # META_SNAPSHOTS table
    meta_label = '''<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="honeydew">
        <TR><TD COLSPAN="2" BGCOLOR="seagreen"><FONT COLOR="white"><B>META_SNAPSHOTS</B></FONT></TD></TR>
        <TR><TD ALIGN="LEFT"><B>PK</B></TD><TD ALIGN="LEFT">id INT</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">snapshot_date DATETIME</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">trophy_range VARCHAR(20)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">game_mode VARCHAR(50)</TD></TR>
        <TR><TD></TD><TD ALIGN="LEFT">meta_data JSON</TD></TR>
    </TABLE>>'''
    dot.node('meta_snapshots', meta_label)
    
    # Define relationships with crow's foot notation style
    dot.attr('edge', fontname='Helvetica', fontsize='10')
    
    # Players -> Battles (1:N)
    dot.edge('players', 'battles', 
             label='  1:N\n  has', 
             arrowhead='crow', 
             arrowtail='none',
             dir='both',
             color='steelblue',
             penwidth='2')
    
    # Decks -> Battles (1:N) - player deck
    dot.edge('decks', 'battles', 
             label='  1:N\n  used in', 
             arrowhead='crow',
             arrowtail='none', 
             dir='both',
             color='goldenrod',
             penwidth='2')
    
    # Decks -> Deck_Cards (1:N)
    dot.edge('decks', 'deck_cards', 
             label='  1:N\n  contains', 
             arrowhead='crow',
             arrowtail='none',
             dir='both',
             color='purple',
             penwidth='2')
    
    # Cards -> Deck_Cards (1:N)
    dot.edge('cards', 'deck_cards', 
             label='  1:N\n  in', 
             arrowhead='crow',
             arrowtail='none',
             dir='both',
             color='darkgreen',
             penwidth='2')
    
    # Add title
    dot.attr(label='\n\nClash Royale Meta Analysis - ER Diagram\n', fontsize='20', fontname='Helvetica-Bold')
    
    # Add legend
    legend = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
        <TR><TD COLSPAN="2" BGCOLOR="gray"><FONT COLOR="white"><B>LEGEND</B></FONT></TD></TR>
        <TR><TD>PK</TD><TD>Primary Key</TD></TR>
        <TR><TD>FK</TD><TD>Foreign Key</TD></TR>
        <TR><TD>1:N</TD><TD>One-to-Many</TD></TR>
        <TR><TD>M:N</TD><TD>Many-to-Many (via junction)</TD></TR>
    </TABLE>>'''
    dot.node('legend', legend, pos='0,0!')
    
    # Render to file
    output_path = 'er_diagram'
    dot.render(output_path, format='png', cleanup=True)
    dot.render(output_path, format='pdf', cleanup=True)
    
    print(f"✅ ER Diagram created successfully!")
    print(f"   - PNG: {output_path}.png")
    print(f"   - PDF: {output_path}.pdf")
    
    return output_path

if __name__ == '__main__':
    create_er_diagram()
