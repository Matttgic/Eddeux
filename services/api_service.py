# services/api_service.py
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import time
import logging
from pathlib import Path

from models.player import Match
from config.settings import config
from utils.name_normalization import NameNormalizer
from utils.surface_detection import SurfaceDetector

logger = logging.getLogger(__name__)

class APIService:
    """Enhanced API service with caching, rate limiting, and error handling"""
    
    def __init__(self):
        self.cache_file = Path(config.cache_file)
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window = 3600  # 1 hour
        self.max_requests_per_hour = 100
        
    def _load_cache(self) -> Optional[List[Dict]]:
        """Load cached API data if recent enough"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                
                cache_time = datetime.fromisoformat(cache['timestamp'])
                if datetime.now() - cache_time < timedelta(minutes=config.api.cache_duration_minutes):
                    logger.info(f"Using cached data from {cache_time}")
                    return cache['data']
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    def _save_cache(self, data: List[Dict]):
        """Save API data to cache"""
        try:
            cache = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            logger.info("API data cached successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter every hour
        if current_time - self.last_request_time > self.rate_limit_window:
            self.request_count = 0
        
        if self.request_count >= self.max_requests_per_hour:
            wait_time = self.rate_limit_window - (current_time - self.last_request_time)
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.0f} seconds")
                time.sleep(wait_time)
                self.request_count = 0
        
        # Minimum delay between requests
        if current_time - self.last_request_time < 1:
            time.sleep(1)
        
        self.last_request_time = current_time
        self.request_count += 1
    
    def _make_api_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make API request with retry logic"""
        headers = {
            "X-RapidAPI-Key": config.api.pinnacle_api_key,
            "X-RapidAPI-Host": config.api.pinnacle_host
        }
        
        for attempt in range(config.api.max_retries):
            try:
                self._rate_limit_check()
                
                logger.debug(f"API request attempt {attempt + 1}: {url}")
                response = requests.get(
                    url, 
                    headers=headers, 
                    params=params, 
                    timeout=config.api.request_timeout
                )
                response.raise_for_status()
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < config.api.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    logger.error(f"All API retry attempts failed for {url}")
                    return None
        
        return None
    
    def fetch_tennis_matches(self) -> List[Match]:
        """Fetch current tennis matches with enhanced processing"""
        # Check cache first
        cached_data = self._load_cache()
        if cached_data:
            return [self._dict_to_match(match_data) for match_data in cached_data]
        
        # Make API request
        url = "https://pinnacle-odds.p.rapidapi.com/kit/v1/markets"
        params = {"sport_id": 2}  # Tennis
        
        data = self._make_api_request(url, params)
        if not data:
            logger.error("Failed to fetch tennis matches from API")
            return []
        
        matches = []
        events = data.get("events", [])
        logger.info(f"Processing {len(events)} events from API")
        
        for event in events:
            try:
                match = self._process_event(event)
                if match:
                    matches.append(match)
            except Exception as e:
                logger.warning(f"Failed to process event: {e}")
                continue
        
        # Save to cache
        match_dicts = [self._match_to_dict(match) for match in matches]
        self._save_cache(match_dicts)
        
        logger.info(f"Successfully processed {len(matches)} tennis matches")
        return matches
    
    def _process_event(self, event: Dict) -> Optional[Match]:
        """Process individual event from API response"""
        league = event.get("league_name", "").lower()
        
        # Filter for ATP tournaments only (exclude WTA, Challenger, ITF, Doubles)
        if not self._is_atp_tournament(league):
            return None
        
        # Extract match details
        player1 = event.get("home", "")
        player2 = event.get("away", "")
        tournament = event.get("league_name", "")
        start_time = event.get("starts")
        
        if not player1 or not player2:
            return None
        
        # Get odds
        periods = event.get("periods", {})
        match_period = periods.get("num_0", {})
        money_line = match_period.get("money_line", {})
        
        odds1 = money_line.get("home")
        odds2 = money_line.get("away")
        
        if not odds1 or not odds2:
            logger.debug(f"Missing odds for {player1} vs {player2}")
            return None
        
        # Normalize names and detect surface
        player1_norm = NameNormalizer.normalize_excel_format(player1)
        player2_norm = NameNormalizer.normalize_excel_format(player2)
        surface = SurfaceDetector.detect_surface(tournament)
        
        return Match(
            player1=player1_norm,
            player2=player2_norm,
            tournament=tournament,
            surface=surface,
            odds1=float(odds1),
            odds2=float(odds2),
            start_time=start_time
        )
    
    def _is_atp_tournament(self, league_name: str) -> bool:
        """Check if tournament is ATP (not WTA, Challenger, etc.)"""
        league_lower = league_name.lower()
        
        # Must contain ATP or be a major tournament
        if "atp" in league_lower:
            # Exclude Challenger and lower levels
            if any(exclude in league_lower for exclude in ["challenger", "125", "itf"]):
                return False
            # Exclude doubles
            if "double" in league_lower:
                return False
            return True
        
        # Major tournaments (even if not labeled ATP)
        majors = ["wimbledon", "us open", "australian open", "french open", "roland garros"]
        if any(major in league_lower for major in majors):
            return "women" not in league_lower and "wta" not in league_lower
        
        return False
    
    def _match_to_dict(self, match: Match) -> Dict:
        """Convert Match object to dictionary for caching"""
        return {
            "player1": match.player1,
            "player2": match.player2,
            "tournament": match.tournament,
            "surface": match.surface,
            "odds1": match.odds1,
            "odds2": match.odds2,
            "start_time": match.start_time,
            "round_info": match.round_info
        }
    
    def _dict_to_match(self, match_dict: Dict) -> Match:
        """Convert dictionary to Match object"""
        return Match(
            player1=match_dict["player1"],
            player2=match_dict["player2"],
            tournament=match_dict["tournament"],
            surface=match_dict["surface"],
            odds1=match_dict["odds1"],
            odds2=match_dict["odds2"],
            start_time=match_dict.get("start_time"),
            round_info=match_dict.get("round_info")
        )
    
    def get_match_count_by_surface(self, matches: List[Match]) -> Dict[str, int]:
        """Get count of matches by surface"""
        surface_counts = {}
        for match in matches:
            surface_counts[match.surface] = surface_counts.get(match.surface, 0) + 1
        return surface_counts
    
    def filter_matches_by_surface(self, matches: List[Match], surface: str) -> List[Match]:
        """Filter matches by specific surface"""
        return [match for match in matches if match.surface == surface]