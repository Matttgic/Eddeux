# services/elo_service.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import logging
from glob import glob
import pickle

from models.player import PlayerElo
from config.settings import config
from utils.name_normalization import NameNormalizer
from utils.surface_detection import SurfaceDetector

logger = logging.getLogger(__name__)

class EloService:
    """Enhanced Elo rating system with caching and advanced features"""
    
    def __init__(self):
        self.players: Dict[str, PlayerElo] = {}
        self.surface_histories: Dict[str, Dict[str, List[float]]] = {}
        self.cache_file = "elo_cache.pkl"
        self.last_update = None
        
    def load_cached_elos(self) -> bool:
        """Load cached Elo ratings if available and recent"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Check if cache is recent (within 24 hours)
                if cache_data['timestamp'] > datetime.now() - timedelta(hours=24):
                    self.players = cache_data['players']
                    self.last_update = cache_data['timestamp']
                    logger.info(f"Loaded {len(self.players)} players from cache")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        
        return False
    
    def save_elos_to_cache(self):
        """Save current Elo ratings to cache"""
        try:
            cache_data = {
                'players': self.players,
                'timestamp': datetime.now()
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info("Elo ratings cached successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def calculate_expected_score(self, elo1: float, elo2: float) -> float:
        """Calculate expected score using Elo formula"""
        return 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    
    def update_elo(self, winner_elo: float, loser_elo: float, 
                   k_factor: Optional[int] = None) -> Tuple[float, float]:
        """Update Elo ratings after a match"""
        if k_factor is None:
            k_factor = config.elo.k_factor
        
        expected_winner = self.calculate_expected_score(winner_elo, loser_elo)
        expected_loser = 1 - expected_winner
        
        new_winner_elo = winner_elo + k_factor * (1 - expected_winner)
        new_loser_elo = loser_elo + k_factor * (0 - expected_loser)
        
        return new_winner_elo, new_loser_elo
    
    def get_adaptive_k_factor(self, matches_played: int, rating: float) -> int:
        """Calculate adaptive K-factor based on player experience and rating"""
        base_k = config.elo.k_factor
        
        # Higher K for new players
        if matches_played < 30:
            return int(base_k * 1.5)
        elif matches_played < 100:
            return int(base_k * 1.2)
        
        # Lower K for established high-rated players
        if rating > 2000:
            return int(base_k * 0.8)
        elif rating > 1800:
            return int(base_k * 0.9)
        
        return base_k
    
    def process_historical_data(self, force_rebuild: bool = False) -> bool:
        """Process all historical tennis data to calculate Elo ratings"""
        if not force_rebuild and self.load_cached_elos():
            return True
        
        logger.info("Processing historical tennis data...")
        
        # Load all data files
        data_files = glob(os.path.join(config.data_dir, "*.xls*"))
        if not data_files:
            logger.error(f"No data files found in {config.data_dir}")
            return False
        
        logger.info(f"Found {len(data_files)} data files")
        
        # Combine all data
        all_matches = []
        for file_path in data_files:
            try:
                df = pd.read_excel(file_path)
                df['file_year'] = os.path.basename(file_path)[:4]
                all_matches.append(df)
                logger.debug(f"Loaded {len(df)} matches from {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        
        if not all_matches:
            logger.error("No valid data files could be loaded")
            return False
        
        # Combine and sort by date
        df_all = pd.concat(all_matches, ignore_index=True)
        df_all = df_all.dropna(subset=['Winner', 'Loser', 'Date'])
        df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
        df_all = df_all.dropna(subset=['Date']).sort_values('Date')
        
        logger.info(f"Processing {len(df_all)} total matches")
        
        # Initialize player ratings
        self.players = {}
        match_counts = {}
        
        # Process matches chronologically
        for idx, match in df_all.iterrows():
            winner = NameNormalizer.normalize_excel_format(match['Winner'])
            loser = NameNormalizer.normalize_excel_format(match['Loser'])
            
            # Detect surface
            tournament = match.get('Tournament', '')
            surface = SurfaceDetector.detect_surface(tournament, match['Date'].month)
            
            # Initialize players if not exists
            if winner not in self.players:
                self.players[winner] = PlayerElo(
                    player_name=winner,
                    elo_hard=config.elo.base_elo,
                    elo_clay=config.elo.base_elo,
                    elo_grass=config.elo.base_elo,
                    elo_overall=config.elo.base_elo,
                    matches_played=0
                )
                match_counts[winner] = 0
            
            if loser not in self.players:
                self.players[loser] = PlayerElo(
                    player_name=loser,
                    elo_hard=config.elo.base_elo,
                    elo_clay=config.elo.base_elo,
                    elo_grass=config.elo.base_elo,
                    elo_overall=config.elo.base_elo,
                    matches_played=0
                )
                match_counts[loser] = 0
            
            # Get current ratings
            winner_player = self.players[winner]
            loser_player = self.players[loser]
            
            winner_elo = winner_player.get_surface_elo(surface)
            loser_elo = loser_player.get_surface_elo(surface)
            
            # Calculate adaptive K-factors
            winner_k = self.get_adaptive_k_factor(match_counts[winner], winner_elo)
            loser_k = self.get_adaptive_k_factor(match_counts[loser], loser_elo)
            
            # Update Elo ratings
            new_winner_elo, new_loser_elo = self.update_elo(winner_elo, loser_elo, winner_k)
            
            # Apply surface-specific updates
            if surface == "Hard":
                winner_player.elo_hard = new_winner_elo
                loser_player.elo_hard = new_loser_elo
            elif surface == "Clay":
                winner_player.elo_clay = new_winner_elo
                loser_player.elo_clay = new_loser_elo
            elif surface == "Grass":
                winner_player.elo_grass = new_winner_elo
                loser_player.elo_grass = new_loser_elo
            
            # Update overall Elo (weighted average)
            winner_player.elo_overall = (
                winner_player.elo_hard * 0.5 + 
                winner_player.elo_clay * 0.3 + 
                winner_player.elo_grass * 0.2
            )
            loser_player.elo_overall = (
                loser_player.elo_hard * 0.5 + 
                loser_player.elo_clay * 0.3 + 
                loser_player.elo_grass * 0.2
            )
            
            # Update match counts
            match_counts[winner] += 1
            match_counts[loser] += 1
            winner_player.matches_played = match_counts[winner]
            loser_player.matches_played = match_counts[loser]
        
        # Update last calculation time
        for player in self.players.values():
            player.last_updated = datetime.now().isoformat()
        
        logger.info(f"Calculated Elo ratings for {len(self.players)} players")
        
        # Save to cache and CSV
        self.save_elos_to_cache()
        self.export_to_csv()
        
        return True
    
    def export_to_csv(self):
        """Export current Elo ratings to CSV file"""
        try:
            df_data = [player.to_dict() for player in self.players.values()]
            df = pd.DataFrame(df_data)
            df.to_csv(config.elo_file, index=False)
            logger.info(f"Exported Elo ratings to {config.elo_file}")
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
    
    def get_player_elo(self, player_name: str, surface: str) -> Optional[float]:
        """Get Elo rating for a specific player and surface"""
        normalized_name = NameNormalizer.normalize_excel_format(player_name)
        
        if normalized_name in self.players:
            return self.players[normalized_name].get_surface_elo(surface)
        
        # Try fuzzy matching
        best_match = None
        best_score = 0.0
        
        for stored_name in self.players.keys():
            score = NameNormalizer.fuzzy_match_score(normalized_name, stored_name)
            if score > best_score and score >= 0.8:
                best_score = score
                best_match = stored_name
        
        if best_match:
            logger.debug(f"Fuzzy matched '{player_name}' to '{best_match}' (score: {best_score:.2f})")
            return self.players[best_match].get_surface_elo(surface)
        
        logger.warning(f"Player not found: {player_name}")
        return None
    
    def get_match_probability(self, player1: str, player2: str, surface: str) -> Optional[float]:
        """Calculate probability of player1 winning against player2"""
        elo1 = self.get_player_elo(player1, surface)
        elo2 = self.get_player_elo(player2, surface)
        
        if elo1 is None or elo2 is None:
            return None
        
        return self.calculate_expected_score(elo1, elo2)
    
    def get_top_players(self, surface: str = "Hard", limit: int = 50) -> List[PlayerElo]:
        """Get top players by Elo rating for a specific surface"""
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: p.get_surface_elo(surface),
            reverse=True
        )
        return sorted_players[:limit]