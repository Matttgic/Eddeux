# utils/surface_detection.py
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

class SurfaceDetector:
    """Advanced surface detection from tournament names"""
    
    # Tournament surface mappings
    SURFACE_KEYWORDS = {
        "Clay": [
            "roland garros", "french open", "monte carlo", "rome", "madrid", 
            "barcelona", "hamburg", "munich", "geneva", "estoril", "bucharest",
            "casablanca", "marrakech", "houston", "charleston", "strasbourg"
        ],
        "Grass": [
            "wimbledon", "queens", "eastbourne", "s-hertogenbosch", "halle",
            "stuttgart", "mallorca", "newport"
        ],
        "Hard": [
            "australian open", "us open", "indian wells", "miami", "canada",
            "cincinnati", "washington", "atlanta", "los cabos", "winston-salem",
            "new york", "tokyo", "beijing", "shanghai", "paris masters", "atp finals"
        ]
    }
    
    # Default surfaces by month (Northern Hemisphere)
    SEASONAL_DEFAULTS = {
        1: "Hard",    # January - Australian Open season
        2: "Hard",    # February - Hard court season
        3: "Hard",    # March - Indian Wells, Miami
        4: "Clay",    # April - Clay season begins
        5: "Clay",    # May - Clay season peak
        6: "Clay",    # June - French Open, transition
        7: "Grass",   # July - Wimbledon
        8: "Hard",    # August - Hard court season
        9: "Hard",    # September - US Open
        10: "Hard",   # October - Asian hard courts
        11: "Hard",   # November - Indoor hard courts
        12: "Hard"    # December - Off-season/exhibitions
    }
    
    @classmethod
    def detect_surface(cls, tournament: str, month: Optional[int] = None) -> str:
        """Detect surface from tournament name with fallback to seasonal default"""
        if not tournament:
            return "Hard"  # Default fallback
        
        tournament_lower = tournament.lower().strip()
        
        # Check against known tournaments
        for surface, keywords in cls.SURFACE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in tournament_lower:
                    logger.debug(f"Surface detected: {surface} for tournament: {tournament}")
                    return surface
        
        # Clay court indicators
        if any(word in tournament_lower for word in ["clay", "terre", "polvo", "battue"]):
            return "Clay"
        
        # Grass court indicators  
        if any(word in tournament_lower for word in ["grass", "lawn", "rasen"]):
            return "Grass"
        
        # Hard court indicators
        if any(word in tournament_lower for word in ["hard", "indoor", "outdoor"]):
            return "Hard"
        
        # Fallback to seasonal default
        if month and month in cls.SEASONAL_DEFAULTS:
            surface = cls.SEASONAL_DEFAULTS[month]
            logger.debug(f"Using seasonal default: {surface} for month {month}")
            return surface
        
        # Ultimate fallback
        logger.warning(f"Could not detect surface for tournament: {tournament}, using Hard")
        return "Hard"
    
    @classmethod
    def get_surface_multiplier(cls, surface: str) -> float:
        """Get surface-specific Elo adjustment multiplier"""
        multipliers = {
            "Hard": 1.0,
            "Clay": 1.1,  # Slightly higher variance on clay
            "Grass": 0.9  # Lower variance on grass (fewer matches)
        }
        return multipliers.get(surface, 1.0)