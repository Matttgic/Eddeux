# ui/components.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional
from datetime import datetime

from models.player import ValueBet
from services.betting_service import BettingService
from services.analytics_service import AnalyticsService

class UIComponents:
    """Reusable UI components for the Streamlit app"""
    
    @staticmethod
    def display_header():
        """Display app header with modern styling"""
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; text-align: center; margin: 0;">
                🎾 Tennis Value Betting System
            </h1>
            <p style="color: #e8f4fd; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                AI-Powered Tennis Betting Analysis with Elo Ratings vs Market Odds
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_metrics_row(metrics: Dict):
        """Display key metrics in a row"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="🎯 Value Bets Found",
                value=metrics.get("bet_count", 0),
                delta=metrics.get("bet_count_delta", None)
            )
        
        with col2:
            avg_value = metrics.get("average_value", 0)
            st.metric(
                label="📈 Average Value",
                value=f"{avg_value:.1%}",
                delta=f"{metrics.get('value_delta', 0):.1%}" if metrics.get('value_delta') else None
            )
        
        with col3:
            total_stake = metrics.get("total_stake", 0)
            st.metric(
                label="💰 Total Stake",
                value=f"${total_stake:.0f}",
                delta=f"${metrics.get('stake_delta', 0):.0f}" if metrics.get('stake_delta') else None
            )
        
        with col4:
            expected_roi = metrics.get("expected_roi", 0)
            st.metric(
                label="🚀 Expected ROI",
                value=f"{expected_roi:.1%}",
                delta=f"{metrics.get('roi_delta', 0):.1%}" if metrics.get('roi_delta') else None
            )
    
    @staticmethod
    def display_value_bets_table(value_bets: List[ValueBet], show_advanced: bool = True):
        """Display value bets in an enhanced table"""
        if not value_bets:
            st.warning("No value bets found with current criteria.")
            return
        
        # Prepare data for display
        display_data = []
        for bet in value_bets:
            row = {
                "🎾 Match": f"{bet.match.player1} vs {bet.match.player2}",
                "🏆 Tournament": bet.match.tournament,
                "🎯 Surface": bet.match.surface,
                "📊 Elo Prob": f"{bet.elo_probability:.1%}",
                "💹 Market Prob": f"{bet.market_probability:.1%}",
                "⚡ Value": f"{bet.value:.1%}",
                "🎲 Odds": f"{bet.match.odds1:.2f}",
                "💰 Kelly Size": f"${bet.kelly_bet_size:.0f}",
                "✅ Recommended": f"${bet.recommended_stake:.0f}",
                "🔥 Confidence": f"{bet.confidence_score:.2f}"
            }
            
            if not show_advanced:
                # Remove advanced columns for basic view
                row = {k: v for k, v in row.items() if k not in ["💰 Kelly Size", "🔥 Confidence"]}
            
            display_data.append(row)
        
        df_display = pd.DataFrame(display_data)
        
        # Style the dataframe
        styled_df = df_display.style.format({
            "⚡ Value": lambda x: f"<span style='color: {'green' if float(x.strip('%')) > 5 else 'orange'}'>{x}</span>",
            "🔥 Confidence": lambda x: f"<span style='color: {'green' if float(x) > 0.7 else 'orange'}'>{x}</span>"
        })
        
        st.dataframe(
            df_display,
            use_container_width=True,
            height=min(len(df_display) * 35 + 38, 400)  # Dynamic height with max
        )
    
    @staticmethod
    def create_value_distribution_chart(value_bets: List[ValueBet]) -> go.Figure:
        """Create value distribution histogram"""
        if not value_bets:
            return go.Figure()
        
        values = [bet.value * 100 for bet in value_bets]  # Convert to percentage
        
        fig = go.Figure(data=[
            go.Histogram(
                x=values,
                nbinsx=20,
                marker_color='rgba(26, 118, 255, 0.7)',
                marker_line_color='rgba(26, 118, 255, 1.0)',
                marker_line_width=1
            )
        ])
        
        fig.update_layout(
            title="Distribution of Value Percentages",
            xaxis_title="Value (%)",
            yaxis_title="Number of Bets",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_surface_breakdown_chart(value_bets: List[ValueBet]) -> go.Figure:
        """Create surface breakdown pie chart"""
        if not value_bets:
            return go.Figure()
        
        surface_counts = {}
        for bet in value_bets:
            surface = bet.match.surface
            surface_counts[surface] = surface_counts.get(surface, 0) + 1
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(surface_counts.keys()),
                values=list(surface_counts.values()),
                hole=0.4,
                marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1']
            )
        ])
        
        fig.update_layout(
            title="Value Bets by Surface",
            template="plotly_white",
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_confidence_vs_value_scatter(value_bets: List[ValueBet]) -> go.Figure:
        """Create scatter plot of confidence vs value"""
        if not value_bets:
            return go.Figure()
        
        x_values = [bet.value * 100 for bet in value_bets]
        y_values = [bet.confidence_score for bet in value_bets]
        colors = [bet.recommended_stake for bet in value_bets]
        texts = [f"{bet.match.player1} vs {bet.match.player2}" for bet in value_bets]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='markers',
                marker=dict(
                    size=10,
                    color=colors,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Recommended Stake ($)")
                ),
                text=texts,
                hovertemplate="<b>%{text}</b><br>" +
                             "Value: %{x:.1f}%<br>" +
                             "Confidence: %{y:.2f}<br>" +
                             "Stake: $%{marker.color:.0f}<br>" +
                             "<extra></extra>"
            )
        ])
        
        fig.update_layout(
            title="Confidence vs Value Analysis",
            xaxis_title="Value (%)",
            yaxis_title="Confidence Score",
            template="plotly_white",
            height=500
        )
        
        return fig
    
    @staticmethod
    def display_strategy_comparison(strategies_data: Dict):
        """Display strategy comparison table"""
        if not strategies_data:
            st.warning("No strategy data available.")
            return
        
        comparison_data = []
        for strategy_name, data in strategies_data.items():
            comparison_data.append({
                "📋 Strategy": strategy_name,
                "🎯 Bets": data.get("bet_count", 0),
                "💰 Total Stake": f"${data.get('total_stake', 0):.0f}",
                "📈 Avg Value": f"{data.get('average_value', 0):.1%}",
                "🔥 Avg Confidence": f"{data.get('average_confidence', 0):.2f}",
                "🚀 Expected ROI": f"{data.get('expected_roi', 0):.1%}",
                "💵 Expected Return": f"${data.get('expected_return', 0):.0f}"
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)
    
    @staticmethod
    def display_sidebar_controls() -> Dict:
        """Display sidebar controls and return selected options"""
        st.sidebar.header("🎛️ Analysis Controls")
        
        # Strategy selection
        strategy_type = st.sidebar.radio(
            "Select Strategy:",
            ["🎯 Fixed Threshold", "🏆 Top Percentage", "🔧 Custom"]
        )
        
        # Strategy parameters
        if strategy_type == "🎯 Fixed Threshold":
            threshold = st.sidebar.slider(
                "Minimum Value Threshold (%)",
                min_value=0.0,
                max_value=15.0,
                value=5.0,
                step=0.5
            ) / 100
            strategy_param = threshold
        elif strategy_type == "🏆 Top Percentage":
            percentage = st.sidebar.slider(
                "Top Percentage to Keep",
                min_value=1,
                max_value=50,
                value=10,
                step=1
            )
            strategy_param = percentage
        else:  # Custom
            threshold = st.sidebar.slider(
                "Minimum Value (%)",
                min_value=0.0,
                max_value=15.0,
                value=3.0,
                step=0.5
            ) / 100
            min_confidence = st.sidebar.slider(
                "Minimum Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.1
            )
            strategy_param = {"threshold": threshold, "min_confidence": min_confidence}
        
        # Surface filters
        st.sidebar.subheader("🎾 Surface Filters")
        surfaces = st.sidebar.multiselect(
            "Select Surfaces:",
            ["Hard", "Clay", "Grass"],
            default=["Hard", "Clay", "Grass"]
        )
        
        # Advanced options
        st.sidebar.subheader("⚙️ Advanced Options")
        show_advanced = st.sidebar.checkbox("Show Advanced Metrics", value=True)
        auto_refresh = st.sidebar.checkbox("Auto Refresh (5min)", value=False)
        
        # Bankroll settings
        st.sidebar.subheader("💰 Bankroll Settings")
        bankroll = st.sidebar.number_input(
            "Bankroll ($)",
            min_value=100,
            max_value=100000,
            value=1000,
            step=100
        )
        
        return {
            "strategy_type": strategy_type,
            "strategy_param": strategy_param,
            "surfaces": surfaces,
            "show_advanced": show_advanced,
            "auto_refresh": auto_refresh,
            "bankroll": bankroll
        }
    
    @staticmethod
    def display_performance_metrics(performance_data: Dict):
        """Display historical performance metrics"""
        if not performance_data or "error" in performance_data:
            st.info("No historical performance data available.")
            return
        
        st.subheader("📊 Historical Performance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Analyses",
                performance_data.get("total_analyses", 0)
            )
        
        with col2:
            st.metric(
                "Total Bets Identified",
                performance_data.get("total_bets_identified", 0)
            )
        
        with col3:
            avg_bets = performance_data.get("average_bets_per_analysis", 0)
            st.metric(
                "Avg Bets/Analysis",
                f"{avg_bets:.1f}"
            )
        
        if performance_data.get("last_analysis"):
            last_analysis = datetime.fromisoformat(performance_data["last_analysis"])
            st.info(f"Last analysis: {last_analysis.strftime('%Y-%m-%d %H:%M')}")