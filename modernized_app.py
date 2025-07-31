# modernized_app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
import time

# Import modernized services
from services.betting_service import BettingService
from services.analytics_service import AnalyticsService
from services.elo_service import EloService
from services.api_service import APIService
from ui.components import UIComponents
from config.settings import config, logger

# Page configuration
st.set_page_config(
    page_title="Tennis Value Betting System",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def initialize_services():
    """Initialize all services (cached for performance)"""
    try:
        betting_service = BettingService()
        analytics_service = AnalyticsService()
        return betting_service, analytics_service
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return None, None

def load_custom_css():
    """Load custom CSS for enhanced styling"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .value-positive {
        color: #28a745;
        font-weight: bold;
    }
    
    .value-negative {
        color: #dc3545;
        font-weight: bold;
    }
    
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e3c72;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def validate_api_configuration():
    """Validate API configuration and show security warnings"""
    api_key = config.api.pinnacle_api_key
    
    if not api_key or api_key == "":
        st.error("🔑 **API Key Missing!** Please configure your Pinnacle API key in Streamlit secrets.")
        st.markdown("""
        **For Streamlit Cloud:**
        1. Go to app settings → Secrets
        2. Add: `PINNACLE_API_KEY = "your_api_key_here"`
        
        **For Local Development:**
        1. Copy `.env.example` to `.env`
        2. Add your real API key to `.env`
        """)
        return False
    
    if api_key == "YOUR_API_KEY_HERE" or len(api_key) < 20:
        st.warning("⚠️ **Invalid API Key!** Please use a valid Pinnacle API key.")
        return False
    
    return True

def show_security_status():
    """Display security status in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Security Status")
    
    api_key = config.api.pinnacle_api_key
    if api_key and len(api_key) > 20 and api_key != "YOUR_API_KEY_HERE":
        st.sidebar.success("✅ API Key Configured")
    else:
        st.sidebar.error("❌ API Key Missing")
    
    env_file_secure = not os.path.exists(".env") or "YOUR_API_KEY_HERE" not in open(".env", "r").read()
    if env_file_secure:
        st.sidebar.success("✅ Environment Secure")
    else:
        st.sidebar.warning("⚠️ Check Environment")

def main():
    """Main application function"""
    load_custom_css()
    
    # Initialize services
    betting_service, analytics_service = initialize_services()
    if not betting_service or not analytics_service:
        st.error("Failed to initialize application services. Please check logs.")
        return
    
    # Display header
    UIComponents.display_header()
    
    # Sidebar controls
    controls = UIComponents.display_sidebar_controls()
    
    # Update config with user settings
    config.betting.bankroll = controls["bankroll"]
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Current Analysis", 
        "📊 Strategy Comparison", 
        "📈 Performance Analytics", 
        "🔧 System Status",
        "📚 Educational"
    ])
    
    with tab1:
        st.header("🎯 Current Value Bet Analysis")
        
        # Analysis controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("🔄 Refresh Analysis", type="primary"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            export_format = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])
        
        with col3:
            show_debug = st.checkbox("Debug Mode")
        
        # Get current analysis
        try:
            with st.spinner("Analyzing current matches..."):
                value_bets = betting_service.analyze_matches(
                    min_value_threshold=controls.get("strategy_param", 0.05) 
                    if controls["strategy_type"] == "🎯 Fixed Threshold" else 0.0
                )
            
            # Filter by surfaces
            if controls["surfaces"]:
                value_bets = [bet for bet in value_bets if bet.match.surface in controls["surfaces"]]
            
            # Apply custom filters if using custom strategy
            if controls["strategy_type"] == "🔧 Custom" and isinstance(controls["strategy_param"], dict):
                custom_params = controls["strategy_param"]
                value_bets = [
                    bet for bet in value_bets 
                    if bet.value >= custom_params["threshold"] and 
                       bet.confidence_score >= custom_params["min_confidence"]
                ]
            
            if value_bets:
                # Calculate and display metrics
                strategy_results = betting_service.get_strategy_results(
                    value_bets, 
                    "threshold" if controls["strategy_type"] == "🎯 Fixed Threshold" else "top_percentage",
                    controls.get("strategy_param", 0.05)
                )
                
                UIComponents.display_metrics_row(strategy_results)
                
                # Display bets table
                st.subheader("💎 Value Betting Opportunities")
                UIComponents.display_value_bets_table(value_bets, controls["show_advanced"])
                
                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    fig_dist = UIComponents.create_value_distribution_chart(value_bets)
                    st.plotly_chart(fig_dist, use_container_width=True)
                
                with col2:
                    fig_surface = UIComponents.create_surface_breakdown_chart(value_bets)
                    st.plotly_chart(fig_surface, use_container_width=True)
                
                # Advanced analysis
                if controls["show_advanced"]:
                    st.subheader("🔬 Advanced Analysis")
                    fig_scatter = UIComponents.create_confidence_vs_value_scatter(value_bets)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Export functionality
                if st.button(f"📄 Export as {export_format}"):
                    export_data = pd.DataFrame([
                        {
                            "Match": f"{bet.match.player1} vs {bet.match.player2}",
                            "Tournament": bet.match.tournament,
                            "Surface": bet.match.surface,
                            "Odds": bet.match.odds1,
                            "Elo_Probability": bet.elo_probability,
                            "Market_Probability": bet.market_probability,
                            "Value": bet.value,
                            "Kelly_Size": bet.kelly_bet_size,
                            "Recommended_Stake": bet.recommended_stake,
                            "Confidence": bet.confidence_score,
                            "Start_Time": bet.match.start_time
                        }
                        for bet in value_bets
                    ])
                    
                    if export_format == "CSV":
                        csv = export_data.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"value_bets_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime='text/csv'
                        )
                
                # Save analysis
                betting_service.save_bet_analysis(value_bets)
                
            else:
                st.warning("No value bets found with current criteria.")
                
                # Show debug information
                if show_debug:
                    st.subheader("🔍 Debug Information")
                    st.info("Fetching all matches for analysis...")
                    
                    debug_bets = betting_service.analyze_matches(min_value_threshold=0.0)
                    if debug_bets:
                        st.write(f"Total matches analyzed: {len(debug_bets)}")
                        
                        debug_df = pd.DataFrame([
                            {
                                "Match": f"{bet.match.player1} vs {bet.match.player2}",
                                "Surface": bet.match.surface,
                                "Value": f"{bet.value:.1%}",
                                "Confidence": f"{bet.confidence_score:.2f}"
                            }
                            for bet in debug_bets[:10]  # Show top 10
                        ])
                        st.dataframe(debug_df)
                    else:
                        st.error("No matches could be analyzed. Check API and Elo data.")
                        
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            logger.error(f"Analysis error: {e}")
    
    with tab2:
        st.header("📊 Strategy Comparison")
        
        if st.button("🔄 Run Strategy Comparison"):
            try:
                with st.spinner("Comparing strategies..."):
                    # Get base analysis
                    all_bets = betting_service.analyze_matches(min_value_threshold=0.0)
                    
                    if all_bets:
                        # Compare different strategies
                        strategies = {
                            "Conservative (5%+)": betting_service.get_strategy_results(
                                all_bets, "threshold", 0.05
                            ),
                            "Moderate (3%+)": betting_service.get_strategy_results(
                                all_bets, "threshold", 0.03
                            ),
                            "Aggressive (1%+)": betting_service.get_strategy_results(
                                all_bets, "threshold", 0.01
                            ),
                            "Top 10%": betting_service.get_strategy_results(
                                all_bets, "top_percentage", 10
                            ),
                            "Top 20%": betting_service.get_strategy_results(
                                all_bets, "top_percentage", 20
                            )
                        }
                        
                        UIComponents.display_strategy_comparison(strategies)
                        
                        # Strategy recommendations
                        st.subheader("🎯 Strategy Recommendations")
                        
                        best_roi_strategy = max(strategies.items(), key=lambda x: x[1].get("expected_roi", 0))
                        most_bets_strategy = max(strategies.items(), key=lambda x: x[1].get("bet_count", 0))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.success(f"**Best ROI:** {best_roi_strategy[0]} ({best_roi_strategy[1]['expected_roi']:.1%})")
                        with col2:
                            st.info(f"**Most Opportunities:** {most_bets_strategy[0]} ({most_bets_strategy[1]['bet_count']} bets)")
                    
                    else:
                        st.warning("No bets available for strategy comparison.")
            
            except Exception as e:
                st.error(f"Strategy comparison failed: {e}")
    
    with tab3:
        st.header("📈 Performance Analytics")
        
        # Historical performance
        performance_data = betting_service.get_historical_performance()
        UIComponents.display_performance_metrics(performance_data)
        
        # Performance charts would go here
        st.info("Historical performance tracking will be enhanced with actual betting results.")
    
    with tab4:
        st.header("🔧 System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Status")
            
            # Check Elo data
            elo_file_exists = os.path.exists(config.elo_file)
            st.write(f"Elo Data File: {'✅' if elo_file_exists else '❌'}")
            
            if elo_file_exists:
                try:
                    elo_df = pd.read_csv(config.elo_file)
                    st.write(f"Players in database: {len(elo_df)}")
                    st.write(f"Last updated: {elo_df.get('last_updated', ['Unknown']).iloc[0] if len(elo_df) > 0 else 'Unknown'}")
                except:
                    st.write("Error reading Elo file")
            
            # Check data directory
            data_files = len([f for f in os.listdir(config.data_dir) if f.endswith(('.xls', '.xlsx'))])
            st.write(f"Historical data files: {data_files}")
        
        with col2:
            st.subheader("🌐 API Status")
            
            try:
                api_service = APIService()
                test_matches = api_service.fetch_tennis_matches()
                st.write(f"API Connection: ✅")
                st.write(f"Current matches available: {len(test_matches)}")
                
                if test_matches:
                    surface_counts = api_service.get_match_count_by_surface(test_matches)
                    for surface, count in surface_counts.items():
                        st.write(f"  {surface}: {count} matches")
                
            except Exception as e:
                st.write(f"API Connection: ❌ ({str(e)})")
        
        # System actions
        st.subheader("⚙️ System Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Rebuild Elo Ratings"):
                with st.spinner("Rebuilding Elo ratings..."):
                    elo_service = EloService()
                    success = elo_service.process_historical_data(force_rebuild=True)
                    if success:
                        st.success("Elo ratings rebuilt successfully!")
                    else:
                        st.error("Failed to rebuild Elo ratings.")
        
        with col2:
            if st.button("🗑️ Clear Cache"):
                # Clear Streamlit cache
                st.cache_data.clear()
                st.cache_resource.clear()
                
                # Clear application caches
                cache_files = ["api_cache.json", "elo_cache.pkl"]
                for cache_file in cache_files:
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                
                st.success("All caches cleared!")
        
        with col3:
            if st.button("📋 Export Logs"):
                try:
                    if os.path.exists("tennis_betting.log"):
                        with open("tennis_betting.log", "r") as f:
                            log_content = f.read()
                        
                        st.download_button(
                            label="Download Logs",
                            data=log_content,
                            file_name=f"tennis_betting_logs_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("No log file found.")
                except Exception as e:
                    st.error(f"Failed to export logs: {e}")
    
    with tab5:
        st.header("📚 Educational Resources")
        
        st.markdown("""
        ## 🎓 Understanding Value Betting
        
        **Value betting** occurs when the probability of an outcome is higher than what the betting odds suggest.
        
        ### 🧮 Key Concepts:
        
        **Elo Rating System:**
        - Originally designed for chess, adapted for tennis
        - Dynamically adjusts based on match results
        - Considers surface specialization (Hard, Clay, Grass)
        
        **Value Calculation:**
        ```
        Value = Elo Probability - Market Probability
        ```
        
        **Kelly Criterion:**
        ```
        Optimal Bet Size = (bp - q) / b
        where:
        - b = odds - 1
        - p = true probability
        - q = 1 - p
        ```
        
        ### 📊 Strategy Types:
        
        **Fixed Threshold Strategy:**
        - Bet on all matches with value above X%
        - Higher thresholds = fewer bets, higher ROI
        - More consistent, easier to implement
        
        **Top Percentage Strategy:**
        - Select best X% of available bets
        - Adaptive to market conditions
        - Higher variance, potentially higher returns
        
        ### ⚠️ Risk Management:
        
        1. **Never bet more than 5% of bankroll on single bet**
        2. **Use fractional Kelly (25-50% of full Kelly)**
        3. **Diversify across surfaces and tournaments**
        4. **Track performance and adjust strategies**
        
        ### 📈 Historical Performance:
        
        Based on backtesting (2000-2024):
        - 5%+ value threshold: ~21.6% ROI
        - Top 10% strategy: ~50% ROI
        - Win rate typically 50-55%
        """)
        
        # Performance tables
        st.subheader("📊 Historical Strategy Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Fixed Threshold Strategy:**")
            threshold_data = {
                "Threshold": [">0%", ">1%", ">2%", ">3%", ">4%", ">5%", ">6%", ">7%", ">8%", ">9%", ">10%"],
                "Bets": [4298, 3823, 3262, 2732, 2223, 1742, 1364, 1062, 828, 659, 510],
                "ROI": ["9.8%", "11.2%", "13.1%", "15.6%", "18.6%", "21.6%", "24.7%", "27.6%", "29.9%", "31.9%", "33.9%"]
            }
            st.dataframe(pd.DataFrame(threshold_data))
        
        with col2:
            st.markdown("**Top Percentage Strategy:**")
            percentage_data = {
                "Strategy": ["Top 5%", "Top 10%", "Top 20%"],
                "ROI": ["~70%", "~50%", "~35%"],
                "Risk": ["High", "Medium", "Low"]
            }
            st.dataframe(pd.DataFrame(percentage_data))

    # Auto-refresh functionality
    if controls.get("auto_refresh", False):
        time.sleep(300)  # 5 minutes
        st.rerun()

if __name__ == "__main__":
    main()