# services/analytics_service.py
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

from models.player import ValueBet, Match
from config.settings import config

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Advanced analytics for betting performance and strategy optimization"""
    
    def __init__(self):
        self.results_file = Path("match_results.json")
        self.performance_file = Path("strategy_performance.json")
        
    def calculate_strategy_performance(self, historical_bets: List[Dict], 
                                     actual_results: List[Dict]) -> Dict:
        """Calculate actual performance of betting strategies"""
        try:
            if not historical_bets or not actual_results:
                return {"error": "Insufficient data for performance calculation"}
            
            # Match bets with results
            matched_bets = self._match_bets_with_results(historical_bets, actual_results)
            
            if not matched_bets:
                return {"error": "No bets could be matched with results"}
            
            # Calculate performance metrics
            total_bets = len(matched_bets)
            winning_bets = sum(1 for bet in matched_bets if bet["won"])
            win_rate = winning_bets / total_bets
            
            total_staked = sum(bet["stake"] for bet in matched_bets)
            total_returns = sum(bet["return"] for bet in matched_bets)
            profit = total_returns - total_staked
            roi = profit / total_staked if total_staked > 0 else 0
            
            # Value-based analysis
            value_groups = self._group_by_value_ranges(matched_bets)
            surface_analysis = self._analyze_by_surface(matched_bets)
            
            return {
                "total_bets": total_bets,
                "winning_bets": winning_bets,
                "win_rate": win_rate,
                "total_staked": total_staked,
                "total_returns": total_returns,
                "profit": profit,
                "roi": roi,
                "value_analysis": value_groups,
                "surface_analysis": surface_analysis,
                "average_odds": np.mean([bet["odds"] for bet in matched_bets]),
                "sharpe_ratio": self._calculate_sharpe_ratio(matched_bets)
            }
            
        except Exception as e:
            logger.error(f"Error calculating strategy performance: {e}")
            return {"error": str(e)}
    
    def _match_bets_with_results(self, bets: List[Dict], 
                               results: List[Dict]) -> List[Dict]:
        """Match historical bets with actual match results"""
        matched = []
        
        for bet in bets:
            # Find corresponding result
            for result in results:
                if self._is_same_match(bet, result):
                    matched_bet = {
                        "match": bet["match"],
                        "surface": bet.get("surface", "Hard"),
                        "value": bet["value"],
                        "odds": bet["odds"],
                        "stake": bet["recommended_stake"],
                        "predicted_winner": bet["match"].split(" vs ")[0],
                        "actual_winner": result["winner"],
                        "won": bet["match"].split(" vs ")[0] == result["winner"],
                        "return": bet["recommended_stake"] * bet["odds"] if bet["match"].split(" vs ")[0] == result["winner"] else 0
                    }
                    matched.append(matched_bet)
                    break
        
        return matched
    
    def _is_same_match(self, bet: Dict, result: Dict) -> bool:
        """Check if bet and result refer to the same match"""
        bet_players = set(bet["match"].split(" vs "))
        result_players = {result.get("player1", ""), result.get("player2", "")}
        
        # Simple name matching (could be enhanced)
        return len(bet_players.intersection(result_players)) >= 1
    
    def _group_by_value_ranges(self, bets: List[Dict]) -> Dict:
        """Analyze performance by value ranges"""
        ranges = [
            (0.0, 0.02, "0-2%"),
            (0.02, 0.05, "2-5%"),
            (0.05, 0.10, "5-10%"),
            (0.10, 0.20, "10-20%"),
            (0.20, 1.0, "20%+")
        ]
        
        analysis = {}
        
        for min_val, max_val, label in ranges:
            range_bets = [bet for bet in bets if min_val <= bet["value"] < max_val]
            
            if range_bets:
                win_rate = sum(bet["won"] for bet in range_bets) / len(range_bets)
                total_profit = sum(bet["return"] - bet["stake"] for bet in range_bets)
                total_staked = sum(bet["stake"] for bet in range_bets)
                roi = total_profit / total_staked if total_staked > 0 else 0
                
                analysis[label] = {
                    "bet_count": len(range_bets),
                    "win_rate": win_rate,
                    "roi": roi,
                    "profit": total_profit,
                    "average_value": np.mean([bet["value"] for bet in range_bets])
                }
        
        return analysis
    
    def _analyze_by_surface(self, bets: List[Dict]) -> Dict:
        """Analyze performance by surface"""
        surfaces = {}
        
        for surface in ["Hard", "Clay", "Grass"]:
            surface_bets = [bet for bet in bets if bet.get("surface") == surface]
            
            if surface_bets:
                win_rate = sum(bet["won"] for bet in surface_bets) / len(surface_bets)
                total_profit = sum(bet["return"] - bet["stake"] for bet in surface_bets)
                total_staked = sum(bet["stake"] for bet in surface_bets)
                roi = total_profit / total_staked if total_staked > 0 else 0
                
                surfaces[surface] = {
                    "bet_count": len(surface_bets),
                    "win_rate": win_rate,
                    "roi": roi,
                    "profit": total_profit
                }
        
        return surfaces
    
    def _calculate_sharpe_ratio(self, bets: List[Dict]) -> float:
        """Calculate Sharpe ratio for betting performance"""
        if not bets:
            return 0.0
        
        returns = [(bet["return"] - bet["stake"]) / bet["stake"] for bet in bets]
        
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        return mean_return / std_return if std_return > 0 else 0.0
    
    def generate_optimization_suggestions(self, performance_data: Dict) -> List[str]:
        """Generate suggestions for strategy optimization"""
        suggestions = []
        
        if not performance_data or "error" in performance_data:
            return ["Insufficient data for optimization suggestions"]
        
        # ROI-based suggestions
        roi = performance_data.get("roi", 0)
        if roi < 0.05:
            suggestions.append("Consider increasing minimum value threshold to improve ROI")
        elif roi > 0.30:
            suggestions.append("Excellent ROI! Consider increasing bet sizes gradually")
        
        # Win rate suggestions
        win_rate = performance_data.get("win_rate", 0)
        if win_rate < 0.45:
            suggestions.append("Low win rate detected. Review Elo model accuracy")
        elif win_rate > 0.60:
            suggestions.append("High win rate suggests conservative betting. Consider lower value thresholds")
        
        # Value analysis suggestions
        value_analysis = performance_data.get("value_analysis", {})
        if value_analysis:
            best_range = max(value_analysis.items(), key=lambda x: x[1].get("roi", 0))
            suggestions.append(f"Best performing value range: {best_range[0]} (ROI: {best_range[1]['roi']:.1%})")
        
        # Surface analysis suggestions
        surface_analysis = performance_data.get("surface_analysis", {})
        if surface_analysis:
            best_surface = max(surface_analysis.items(), key=lambda x: x[1].get("roi", 0))
            worst_surface = min(surface_analysis.items(), key=lambda x: x[1].get("roi", 0))
            
            suggestions.append(f"Best surface: {best_surface[0]} (ROI: {best_surface[1]['roi']:.1%})")
            suggestions.append(f"Consider avoiding {worst_surface[0]} matches (ROI: {worst_surface[1]['roi']:.1%})")
        
        return suggestions
    
    def backtest_strategy(self, strategy_params: Dict, 
                         historical_data: List[Dict]) -> Dict:
        """Backtest a strategy against historical data"""
        try:
            if not historical_data:
                return {"error": "No historical data provided"}
            
            # Simulate strategy application
            results = []
            total_profit = 0
            total_staked = 0
            
            for data_point in historical_data:
                # Apply strategy filters
                if self._strategy_filter(data_point, strategy_params):
                    bet_result = self._simulate_bet(data_point)
                    results.append(bet_result)
                    total_profit += bet_result["profit"]
                    total_staked += bet_result["stake"]
            
            if not results:
                return {"error": "No bets selected by strategy parameters"}
            
            win_rate = sum(1 for r in results if r["won"]) / len(results)
            roi = total_profit / total_staked if total_staked > 0 else 0
            
            return {
                "total_bets": len(results),
                "win_rate": win_rate,
                "total_profit": total_profit,
                "total_staked": total_staked,
                "roi": roi,
                "sharpe_ratio": self._calculate_sharpe_ratio(results),
                "max_drawdown": self._calculate_max_drawdown(results)
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {"error": str(e)}
    
    def _strategy_filter(self, data_point: Dict, strategy_params: Dict) -> bool:
        """Apply strategy filters to determine if bet should be placed"""
        min_value = strategy_params.get("min_value", 0.05)
        max_value = strategy_params.get("max_value", 1.0)
        surfaces = strategy_params.get("surfaces", ["Hard", "Clay", "Grass"])
        
        value = data_point.get("value", 0)
        surface = data_point.get("surface", "Hard")
        
        return min_value <= value <= max_value and surface in surfaces
    
    def _simulate_bet(self, data_point: Dict) -> Dict:
        """Simulate a single bet outcome"""
        won = data_point.get("actual_result") == "win"  # Simplified
        stake = data_point.get("recommended_stake", 10)
        odds = data_point.get("odds", 2.0)
        
        return {
            "won": won,
            "stake": stake,
            "return": stake * odds if won else 0,
            "profit": (stake * odds - stake) if won else -stake
        }
    
    def _calculate_max_drawdown(self, results: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        if not results:
            return 0.0
        
        cumulative = np.cumsum([r["profit"] for r in results])
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        
        return abs(min(drawdown)) if len(drawdown) > 0 else 0.0