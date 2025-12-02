from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .config import Base

# Association table for many-to-many relationship between decks and cards
deck_cards = Table(
    'deck_cards',
    Base.metadata,
    Column('deck_id', Integer, ForeignKey('decks.id'), primary_key=True),
    Column('card_id', Integer, ForeignKey('cards.id'), primary_key=True)
)

class Clan(Base):
    __tablename__ = 'clans'

    tag = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20))  # open, inviteOnly, closed
    description = Column(String(500))
    badge_id = Column(Integer)
    clan_score = Column(Integer)
    clan_war_trophies = Column(Integer)
    required_trophies = Column(Integer)
    donations_per_week = Column(Integer)
    members_count = Column(Integer)
    location = Column(String(100))
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    players = relationship("Player", back_populates="clan")

class Player(Base):
    __tablename__ = 'players'

    tag = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    exp_level = Column(Integer)
    trophies = Column(Integer)
    best_trophies = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    battle_count = Column(Integer)
    three_crown_wins = Column(Integer)
    challenge_cards_won = Column(Integer)
    tournament_cards_won = Column(Integer)
    clan_tag = Column(String(20), ForeignKey('clans.tag'))  # Foreign key to clans
    role = Column(String(20))  # member, elder, coLeader, leader
    donations = Column(Integer)
    donations_received = Column(Integer)
    total_donations = Column(Integer)
    war_day_wins = Column(Integer)
    clan_cards_collected = Column(Integer)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    clan = relationship("Clan", back_populates="players")
    battles = relationship("Battle", foreign_keys="Battle.player_tag", back_populates="player")
    
class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    rarity = Column(String(20))
    type = Column(String(20))  # troop, spell, building
    elixir = Column(Integer)
    arena = Column(Integer)
    description = Column(String(500))
    
    # Relationships
    decks = relationship("Deck", secondary=deck_cards, back_populates="cards")

class Deck(Base):
    __tablename__ = 'decks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    avg_elixir = Column(Float)
    win_rate = Column(Float)
    use_rate = Column(Float)
    cards_count = Column(Integer)

    # Relationships
    cards = relationship("Card", secondary=deck_cards, back_populates="decks")
    battles = relationship("Battle", foreign_keys="Battle.deck_id", back_populates="deck")

class Battle(Base):
    __tablename__ = 'battles'
    
    id = Column(Integer, primary_key=True)
    battle_time = Column(DateTime, nullable=False)
    battle_type = Column(String(50))
    game_mode = Column(String(50))
    arena_name = Column(String(50))
    deck_type = Column(String(20))  # ladder, challenge, tournament, etc.
    trophy_change = Column(Integer)
    crown_difference = Column(Integer)
    player_tag = Column(String(20), ForeignKey('players.tag'))
    opponent_tag = Column(String(20), ForeignKey('players.tag'))
    deck_id = Column(Integer, ForeignKey('decks.id'))
    opponent_deck_id = Column(Integer, ForeignKey('decks.id'))
    is_winner = Column(Boolean)
    player_crowns = Column(Integer)
    opponent_crowns = Column(Integer)
    player_cards = Column(JSON)  # List of card levels used by player
    opponent_cards = Column(JSON)  # List of card levels used by opponent
    
    # Relationships
    player = relationship("Player", foreign_keys=[player_tag], back_populates="battles")
    opponent = relationship("Player", foreign_keys=[opponent_tag])
    deck = relationship("Deck", foreign_keys=[deck_id], back_populates="battles")
    opponent_deck = relationship("Deck", foreign_keys=[opponent_deck_id])

class MetaSnapshot(Base):
    __tablename__ = 'meta_snapshots'
    
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(DateTime, default=func.now())
    trophy_range = Column(String(20))  # e.g., '0-3000', '3000-4000', etc.
    game_mode = Column(String(50))
    meta_data = Column(JSON)  # JSON containing meta statistics
    
    def __repr__(self):
        return f"<MetaSnapshot {self.snapshot_date} - {self.trophy_range} - {self.game_mode}>"
