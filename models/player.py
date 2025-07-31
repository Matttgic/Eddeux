# models/player.py
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd

@dataclass
class PlayerElo:
    """Player Elo ratings for different surfaces"""
    player_name: str
    elo_hard: float
    elo_clay: float
    elo_grass: float
    elo_overall: float
    matches_played: int = 0
    last_updated: Optional[str] = None
    
    def get_surface_elo(self, surface: str) -> float:
        """Get Elo rating for specific surface"""
        surface_map = {
            "Hard": self.elo_hard,
            "Clay": self.elo_clay,
            "Grass": self.elo_grass
        }
        return surface_map.get(surface, self.elo_overall)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame"""
        return {
            'player': self.player_name,
            'elo_hard': self.elo_hard,
            'elo_clay': self.elo_clay,
            'elo_grass': self.elo_grass,
            'elo': self.elo_overall,
            'matches_played': self.matches_played,
            'last_updated': self.last_updated
        }

@dataclass
class Match:
    """Tennis match data structure"""
    player1: str
    player2: str
    tournament: str
    surface: str
    odds1: float
    odds2: float
    start_time: Optional[str] = None
    round_info: Optional[str] = None
    
    def __str__(self):
        return f"{self.player1} vs {self.player2} ({self.tournament})"

@dataclass
class ValueBet:
    """Value bet opportunity"""
    match: Match
    elo_probability: float
    market_probability: float
    value: float
    kelly_bet_size: float
    recommended_stake: float
    confidence_score: float
    
    def __str__(self):
        return f"{self.match} - Value: {self.value:.1%}"