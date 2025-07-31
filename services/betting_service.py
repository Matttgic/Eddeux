# services/betting_service.py
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
import json
from pathlib import Path

from models.player import Match, ValueBet
from services.elo_service import EloService
from services.api_service import APIService
from config.settings import config

logger = logging.getLogger(__name__)

class BettingService:
    """Advanced betting service with Kelly criterion and risk management"""
    
    def __init__(self):
        self.elo_service = EloService()
        self.api_service = APIService()
        self.bet_history_file = Path("bet_history.json")
        self.performance_file = Path("performance_metrics.json")
        
    def calculate_kelly_bet_size(self, probability: float, odds: float, 
                               bankroll: float, max_percentage: float = 0.05) -> float:
        """Calculate optimal bet size using Kelly criterion"""
        if probability <= 0 or odds <= 1:
            return 0.0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = probability, q = 1 - p
        b = odds - 1
        p = probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Apply fractional Kelly for risk management
        fractional_kelly = kelly_fraction * config.betting.kelly_fraction
        
        # Cap at maximum percentage of bankroll
        kelly_percentage = max(0, min(fractional_kelly, max_percentage))
        
        return bankroll * kelly_percentage
    
    def calculate_value(self, elo_prob: float, market_prob: float) -> float:
        """Calculate betting value (edge over market)"""
        return elo_prob - market_prob
    
    def calculate_confidence_score(self, match: Match, elo1: float, elo2: float) -> float:
        """Calculate confidence score for a bet based on various factors"""
        base_score = 0.5
        
        # Factor 1: Elo difference (higher difference = more confidence)
        elo_diff = abs(elo1 - elo2)
        if elo_diff > 200:
            base_score += 0.3
        elif elo_diff > 100:
            base_score += 0.2
        elif elo_diff > 50:
            base_score += 0.1
        
        # Factor 2: Surface specialization
        surface_bonus = 0.1 if match.surface in ["Clay", "Grass"] else 0.05
        base_score += surface_bonus
        
        # Factor 3: Tournament level (major tournaments = higher confidence)
        tournament_lower = match.tournament.lower()
        if any(major in tournament_lower for major in 
               ["wimbledon", "us open", "australian open", "french open", "roland garros"]):
            base_score += 0.2
        elif "masters" in tournament_lower or "1000" in tournament_lower:
            base_score += 0.15
        elif "500" in tournament_lower:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def remove_bookmaker_margin(self, odds1: float, odds2: float) -> Tuple[float, float]:
        """Remove bookmaker margin and get true probabilities"""
        prob1_raw = 1 / odds1
        prob2_raw = 1 / odds2
        total_prob = prob1_raw + prob2_raw
        
        # Normalize to remove margin
        prob1_true = prob1_raw / total_prob
        prob2_true = prob2_raw / total_prob
        
        return prob1_true, prob2_true
    
    def analyze_matches(self, min_value_threshold: float = 0.0) -> List[ValueBet]:
        """Analyze current matches for value betting opportunities"""
        logger.info("Starting match analysis for value bets...")
        
        # Ensure Elo ratings are calculated
        if not self.elo_service.process_historical_data():
            logger.error("Failed to process Elo data")
            return []
        
        # Fetch current matches
        matches = self.api_service.fetch_tennis_matches()
        if not matches:
            logger.warning("No matches found from API")
            return []
        
        value_bets = []
        analyzed_count = 0
        matched_count = 0
        
        for match in matches:
            try:
                analyzed_count += 1
                
                # Get Elo ratings
                elo1 = self.elo_service.get_player_elo(match.player1, match.surface)
                elo2 = self.elo_service.get_player_elo(match.player2, match.surface)
                
                if elo1 is None or elo2 is None:
                    logger.debug(f"Missing Elo for: {match.player1} vs {match.player2}")
                    continue
                
                matched_count += 1
                
                # Calculate probabilities
                elo_prob = self.elo_service.calculate_expected_score(elo1, elo2)
                market_prob, _ = self.remove_bookmaker_margin(match.odds1, match.odds2)
                
                # Calculate value
                value = self.calculate_value(elo_prob, market_prob)
                
                if value >= min_value_threshold:
                    # Calculate Kelly bet size
                    kelly_size = self.calculate_kelly_bet_size(
                        elo_prob, match.odds1, config.betting.bankroll
                    )
                    
                    # Calculate recommended stake (conservative approach)
                    recommended_stake = min(
                        kelly_size,
                        config.betting.bankroll * config.betting.max_bet_percentage
                    )
                    
                    # Calculate confidence score
                    confidence = self.calculate_confidence_score(match, elo1, elo2)
                    
                    value_bet = ValueBet(
                        match=match,
                        elo_probability=elo_prob,
                        market_probability=market_prob,
                        value=value,
                        kelly_bet_size=kelly_size,
                        recommended_stake=recommended_stake,
                        confidence_score=confidence
                    )
                    
                    value_bets.append(value_bet)
                    
                    logger.info(
                        f"Value bet found: {match.player1} vs {match.player2} "
                        f"(Value: {value:.1%}, Confidence: {confidence:.2f})"
                    )
                
            except Exception as e:
                logger.warning(f"Error analyzing match {match}: {e}")
                continue
        
        logger.info(
            f"Analysis complete: {analyzed_count} matches analyzed, "
            f"{matched_count} with Elo data, {len(value_bets)} value bets found"
        )
        
        return sorted(value_bets, key=lambda x: x.value, reverse=True)
    
    def get_strategy_results(self, value_bets: List[ValueBet], 
                           strategy_type: str, parameter: float) -> Dict:
        """Apply strategy filters and return results"""
        if strategy_type == "threshold":
            # Strategy A: Fixed threshold
            filtered_bets = [bet for bet in value_bets if bet.value >= parameter]
            strategy_name = f"Fixed Threshold ({parameter:.1%})"
            
        elif strategy_type == "top_percentage":
            # Strategy B: Top X% of bets
            if not value_bets:
                filtered_bets = []
            else:
                count = max(1, int(len(value_bets) * parameter / 100))
                filtered_bets = value_bets[:count]
            strategy_name = f"Top {parameter:.0f}%"
            
        else:
            filtered_bets = value_bets
            strategy_name = "All Bets"
        
        if not filtered_bets:
            return {
                "strategy": strategy_name,
                "bet_count": 0,
                "total_stake": 0.0,
                "average_value": 0.0,
                "average_confidence": 0.0,
                "expected_return": 0.0,
                "bets": []
            }
        
        # Calculate metrics
        total_stake = sum(bet.recommended_stake for bet in filtered_bets)
        avg_value = np.mean([bet.value for bet in filtered_bets])
        avg_confidence = np.mean([bet.confidence_score for bet in filtered_bets])
        
        # Expected return calculation (simplified)
        expected_return = sum(
            bet.recommended_stake * bet.elo_probability * bet.match.odds1 - bet.recommended_stake
            for bet in filtered_bets
        )
        
        return {
            "strategy": strategy_name,
            "bet_count": len(filtered_bets),
            "total_stake": total_stake,
            "average_value": avg_value,
            "average_confidence": avg_confidence,
            "expected_return": expected_return,
            "expected_roi": expected_return / total_stake if total_stake > 0 else 0,
            "bets": filtered_bets
        }
    
    def save_bet_analysis(self, value_bets: List[ValueBet]):
        """Save current bet analysis to history"""
        try:
            analysis_data = {
                "timestamp": datetime.now().isoformat(),
                "bet_count": len(value_bets),
                "bets": [
                    {
                        "match": f"{bet.match.player1} vs {bet.match.player2}",
                        "tournament": bet.match.tournament,
                        "surface": bet.match.surface,
                        "odds": bet.match.odds1,
                        "elo_probability": bet.elo_probability,
                        "market_probability": bet.market_probability,
                        "value": bet.value,
                        "kelly_size": bet.kelly_bet_size,
                        "recommended_stake": bet.recommended_stake,
                        "confidence": bet.confidence_score
                    }
                    for bet in value_bets
                ]
            }
            
            # Load existing history
            history = []
            if self.bet_history_file.exists():
                with open(self.bet_history_file, 'r') as f:
                    history = json.load(f)
            
            history.append(analysis_data)
            
            # Keep only last 100 analyses
            history = history[-100:]
            
            with open(self.bet_history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Saved bet analysis with {len(value_bets)} value bets")
            
        except Exception as e:
            logger.error(f"Failed to save bet analysis: {e}")
    
    def get_historical_performance(self) -> Dict:
        """Get historical performance metrics"""
        try:
            if not self.bet_history_file.exists():
                return {"message": "No historical data available"}
            
            with open(self.bet_history_file, 'r') as f:
                history = json.load(f)
            
            if not history:
                return {"message": "No historical data available"}
            
            # Calculate aggregate metrics
            total_analyses = len(history)
            total_bets = sum(analysis["bet_count"] for analysis in history)
            
            # Recent activity (last 7 days)
            recent_threshold = (datetime.now() - pd.Timedelta(days=7)).isoformat()
            recent_analyses = [
                analysis for analysis in history 
                if analysis["timestamp"] > recent_threshold
            ]
            
            return {
                "total_analyses": total_analyses,
                "total_bets_identified": total_bets,
                "recent_analyses": len(recent_analyses),
                "average_bets_per_analysis": total_bets / total_analyses if total_analyses > 0 else 0,
                "last_analysis": history[-1]["timestamp"] if history else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical performance: {e}")
            return {"error": str(e)}