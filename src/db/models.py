from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, DECIMAL, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ============================================
# REFERENCE TABLES
# ============================================

class Location(Base):
    __tablename__ = 'locations'
    
    location_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    is_country = Column(Boolean, default=False)
    country_code = Column(String(10))
    
    leaderboards = relationship("Leaderboard", back_populates="location")

    def __repr__(self):
        return f"<Location {self.name} ({self.location_id})>"


class Player(Base):
    __tablename__ = 'players'
    
    player_tag = Column(String(20), primary_key=True)
    
    leaderboard_entries = relationship("LeaderboardSnapshotPlayer", back_populates="player")
    tournament_entries = relationship("TournamentMember", back_populates="player")
    decks = relationship("PlayerDeck", back_populates="player")
    battle_entries = relationship("BattlePlayer", back_populates="player")

    def __repr__(self):
        return f"<Player {self.player_tag}>"


class Card(Base):
    __tablename__ = 'cards'
    
    card_id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    rarity = Column(String(20))
    elixir_cost = Column(Integer)
    card_type = Column(String(20))
    icon_url = Column(String(255))
    
    deck_cards = relationship("DeckCard", back_populates="card")
    snapshot_stats = relationship("CardSnapshotStats", back_populates="card")

    def __repr__(self):
        return f"<Card {self.name} ({self.card_id})>"


class Deck(Base):
    __tablename__ = 'decks'
    
    deck_id = Column(Integer, primary_key=True, autoincrement=True)
    deck_hash = Column(String(64), unique=True, nullable=False)
    avg_elixir = Column(DECIMAL(3, 1))
    created_at = Column(DateTime, server_default=func.now())
    
    deck_cards = relationship("DeckCard", back_populates="deck", cascade="all, delete-orphan")
    snapshot_stats = relationship("DeckSnapshotStats", back_populates="deck")

    def __repr__(self):
        return f"<Deck {self.deck_id} ({self.deck_hash[:8]}...)>"


class DeckCard(Base):
    __tablename__ = 'deck_cards'
    
    deck_id = Column(Integer, ForeignKey('decks.deck_id', ondelete='CASCADE'), primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.card_id', ondelete='CASCADE'), primary_key=True)
    
    deck = relationship("Deck", back_populates="deck_cards")
    card = relationship("Card", back_populates="deck_cards")


class MetaSnapshot(Base):
    __tablename__ = 'meta_snapshots'
    
    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    taken_at = Column(DateTime, server_default=func.now())
    snapshot_type = Column(String(30), nullable=False)
    trophy_min = Column(Integer)
    trophy_max = Column(Integer)
    sample_size = Column(Integer, default=0)
    total_decks = Column(Integer, default=0)
    description = Column(String(200))
    
    deck_stats = relationship("DeckSnapshotStats", back_populates="snapshot", cascade="all, delete-orphan")
    card_stats = relationship("CardSnapshotStats", back_populates="snapshot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MetaSnapshot {self.snapshot_id} ({self.snapshot_type})>"


class DeckSnapshotStats(Base):
    __tablename__ = 'deck_snapshot_stats'
    
    snapshot_id = Column(Integer, ForeignKey('meta_snapshots.snapshot_id', ondelete='CASCADE'), primary_key=True)
    deck_id = Column(Integer, ForeignKey('decks.deck_id', ondelete='CASCADE'), primary_key=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    win_rate = Column(DECIMAL(5, 2))
    pick_rate = Column(DECIMAL(5, 2))
    
    snapshot = relationship("MetaSnapshot", back_populates="deck_stats")
    deck = relationship("Deck", back_populates="snapshot_stats")


class CardSnapshotStats(Base):
    __tablename__ = 'card_snapshot_stats'
    
    snapshot_id = Column(Integer, ForeignKey('meta_snapshots.snapshot_id', ondelete='CASCADE'), primary_key=True)
    card_id = Column(Integer, ForeignKey('cards.card_id', ondelete='CASCADE'), primary_key=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    win_rate = Column(DECIMAL(5, 2))
    pick_rate = Column(DECIMAL(5, 2))
    
    snapshot = relationship("MetaSnapshot", back_populates="card_stats")
    card = relationship("Card", back_populates="snapshot_stats")


# ============================================
# LEADERBOARDS / RANKINGS
# ============================================

class Leaderboard(Base):
    __tablename__ = 'leaderboards'
    
    leaderboard_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    leaderboard_type = Column(String(30), nullable=False)  # 'global', 'location', 'path_of_legend'
    location_id = Column(Integer, ForeignKey('locations.location_id', ondelete='SET NULL'))
    
    location = relationship("Location", back_populates="leaderboards")
    snapshots = relationship("LeaderboardSnapshot", back_populates="leaderboard", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Leaderboard {self.name} ({self.leaderboard_id})>"


class LeaderboardSnapshot(Base):
    __tablename__ = 'leaderboard_snapshots'
    
    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    leaderboard_id = Column(String(50), ForeignKey('leaderboards.leaderboard_id', ondelete='CASCADE'), nullable=False)
    taken_at = Column(DateTime, server_default=func.now())
    player_count = Column(Integer, default=0)
    
    leaderboard = relationship("Leaderboard", back_populates="snapshots")
    players = relationship("LeaderboardSnapshotPlayer", back_populates="snapshot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LeaderboardSnapshot {self.snapshot_id} ({self.leaderboard_id})>"


class LeaderboardSnapshotPlayer(Base):
    __tablename__ = 'leaderboard_snapshot_players'
    
    snapshot_id = Column(Integer, ForeignKey('leaderboard_snapshots.snapshot_id', ondelete='CASCADE'), primary_key=True)
    rank_position = Column(Integer, primary_key=True)
    player_tag = Column(String(20), ForeignKey('players.player_tag', ondelete='CASCADE'), nullable=False)
    trophies = Column(Integer)
    deck_id = Column(Integer, ForeignKey('decks.deck_id', ondelete='SET NULL'))
    
    snapshot = relationship("LeaderboardSnapshot", back_populates="players")
    player = relationship("Player", back_populates="leaderboard_entries")
    deck = relationship("Deck")


class PlayerDeck(Base):
    __tablename__ = 'player_decks'
    
    player_tag = Column(String(20), ForeignKey('players.player_tag', ondelete='CASCADE'), primary_key=True)
    deck_id = Column(Integer, ForeignKey('decks.deck_id', ondelete='CASCADE'), primary_key=True)
    is_current = Column(Boolean, default=True)
    recorded_at = Column(DateTime, server_default=func.now())
    
    player = relationship("Player", back_populates="decks")
    deck = relationship("Deck")


# ============================================
# TOURNAMENTS
# ============================================

class Tournament(Base):
    __tablename__ = 'tournaments'
    
    tournament_tag = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(String(20))  # 'preparation', 'inProgress', 'ended'
    tournament_type = Column(String(30))
    capacity = Column(Integer)
    max_capacity = Column(Integer)
    level_cap = Column(Integer)
    game_mode_name = Column(String(50))
    created_time = Column(DateTime)
    started_time = Column(DateTime)
    first_place_prize = Column(Integer)
    collected_at = Column(DateTime, server_default=func.now())
    
    members = relationship("TournamentMember", back_populates="tournament", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tournament {self.name} ({self.tournament_tag})>"


class TournamentMember(Base):
    __tablename__ = 'tournament_members'
    
    tournament_tag = Column(String(20), ForeignKey('tournaments.tournament_tag', ondelete='CASCADE'), primary_key=True)
    player_tag = Column(String(20), ForeignKey('players.player_tag', ondelete='CASCADE'), primary_key=True)
    rank_position = Column(Integer)
    score = Column(Integer)
    
    tournament = relationship("Tournament", back_populates="members")
    player = relationship("Player", back_populates="tournament_entries")


# ============================================
# BATTLES
# ============================================

class Battle(Base):
    __tablename__ = 'battles'
    
    battle_id = Column(String(64), primary_key=True)
    battle_type = Column(String(30))
    game_mode = Column(String(50))
    arena_name = Column(String(50))
    is_ladder = Column(Boolean, default=False)
    
    players = relationship("BattlePlayer", back_populates="battle", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Battle {self.battle_id[:8]}... ({self.battle_type})>"


class BattlePlayer(Base):
    __tablename__ = 'battle_players'
    
    battle_id = Column(String(64), ForeignKey('battles.battle_id', ondelete='CASCADE'), primary_key=True)
    team_side = Column(Integer, primary_key=True)  # 0 = team, 1 = opponent
    player_tag = Column(String(20), ForeignKey('players.player_tag', ondelete='CASCADE'), nullable=False)
    deck_id = Column(Integer, ForeignKey('decks.deck_id', ondelete='SET NULL'))
    starting_trophies = Column(Integer)
    trophy_change = Column(Integer)
    crowns = Column(Integer)
    is_winner = Column(Boolean)
    
    battle = relationship("Battle", back_populates="players")
    player = relationship("Player", back_populates="battle_entries")
    deck = relationship("Deck")
