# config/settings.py
import os
from dataclasses import dataclass
from typing import Dict, Optional
import logging

@dataclass
class APIConfig:
    """API configuration settings"""
    pinnacle_api_key: str
    pinnacle_host: str
    cache_duration_minutes: int = 5
    request_timeout: int = 30
    max_retries: int = 3

@dataclass
class EloConfig:
    """Elo rating system configuration"""
    base_elo: int = 1500
    k_factor: int = 32
    surface_adjustment: Dict[str, float] = None
    
    def __post_init__(self):
        if self.surface_adjustment is None:
            self.surface_adjustment = {
                "Hard": 1.0,
                "Clay": 1.1,
                "Grass": 0.9
            }

@dataclass
class BettingConfig:
    """Betting strategy configuration"""
    default_value_threshold: float = 0.05
    kelly_fraction: float = 0.25
    max_bet_percentage: float = 0.05
    bankroll: float = 1000.0

@dataclass
class AppConfig:
    """Main application configuration"""
    data_dir: str = "Données"
    elo_file: str = "elo_probs.csv"
    cache_file: str = "api_cache.json"
    log_level: str = "INFO"
    
    # Component configs
    api: APIConfig = None
    elo: EloConfig = None
    betting: BettingConfig = None
    
    def __post_init__(self):
        if self.api is None:
            self.api = APIConfig(
                pinnacle_api_key=os.getenv("PINNACLE_API_KEY", ""),
                pinnacle_host=os.getenv("PINNACLE_HOST", "pinnacle-odds.p.rapidapi.com"),
                cache_duration_minutes=int(os.getenv("CACHE_DURATION", "5")),
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
            )
        
        if self.elo is None:
            self.elo = EloConfig()
            
        if self.betting is None:
            self.betting = BettingConfig(
                bankroll=float(os.getenv("BANKROLL", "1000.0")),
                kelly_fraction=float(os.getenv("KELLY_FRACTION", "0.25"))
            )

# Global configuration instance
config = AppConfig()

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tennis_betting.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()