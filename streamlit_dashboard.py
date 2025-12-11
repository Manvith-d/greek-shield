#!/usr/bin/env python3
"""
Enhanced Options Risk Multi-Agent System - Streamlit Dashboard
Beautiful interactive UI for your multi-agent system
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from agents.core.enhanced_strategy_agent import EnhancedStrategyAgent
from agents.core.logistics_agent import LogisticsAgent
from agents.core.financial_agent import FinancialAgent
from utils.slack_manager import get_slack_manager
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Options Risk AI System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def create_confidence_gauge(confidence_score):
    """Create confidence gauge chart"""
    
    # Determine color based on score
    if confidence_score >= 80:
        color = "#28a745"  # Green
    elif confidence_score >= 60:
        color = "#ffc107"  # Yellow
    else:
        color = "#dc3545"  # Red
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = confidence_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Confidence Score", 'font': {'size': 24}},
        delta = {'reference': 70, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ffebee'},
                {'range': [40, 70], 'color': '#fff9e6'},
                {'range': [70, 100], 'color': '#e8f5e9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_scenario_chart(scenarios, current_price):
    """Create scenario analysis chart"""
    
    # Calculate price points
    prices = []
    pnls = []
    scenarios_list = []
    
    for pct in [-10, -5, 0, 5, 10]:
        price = current_price * (1 + pct/100)
        prices.append(f"{pct:+d}%")
        
        # Estimate P&L (simplified)
        if pct > 0:
            pnl = pct * 200  # Bull call spread profits on upside
        elif pct < 0:
            pnl = pct * 50   # Limited loss
        else:
            pnl = -50  # Theta decay
        
        pnls.append(pnl)
        scenarios_list.append(f"${price:.2f}")
    
    df = pd.DataFrame({
        'Price Change': prices,
        'Estimated P&L': pnls,
        'Stock Price': scenarios_list
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Price Change'],
        y=df['Estimated P&L'],
        mode='lines+markers',
        name='P&L',
        line=dict(color='#667eea', width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)'
    ))
    
    # Add breakeven line
    fig.add_hline(y=0, line_dash="dash", line_color="red", 
                  annotation_text="Breakeven")
    
    fig.update_layout(
        title="Scenario Analysis: Expected P&L",
        xaxis_title="Stock Price Change",
        yaxis_title="Profit/Loss ($)",
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_greeks_radar(greeks):
    """Create Greeks exposure radar chart"""
    
    categories = ['Delta', 'Gamma', 'Theta', 'Vega']
    
    # Normalize to 0-100 scale for visualization
    values = [
        min(abs(greeks.get('delta', 0)) / 3.0 * 100, 100),
        min(abs(greeks.get('gamma', 0)) / 0.1 * 100, 100),
        min(abs(greeks.get('theta', 0)) / 2.0 * 100, 100),
        min(abs(greeks.get('vega', 0)) / 5.0 * 100, 100)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Exposure',
        line=dict(color='#667eea', width=2),
        fillcolor='rgba(102, 126, 234, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=400,
        title="Portfolio Greeks Exposure"
    )
    
    return fig


def create_liquidity_heatmap(contracts):
    """Create contract liquidity heatmap"""
    
    if not contracts or len(contracts) == 0:
        return None
    
    # Prepare data
    df = pd.DataFrame(contracts)
    
    # Group by strike and expiry
    pivot = df.pivot_table(
        values='liquidity_score',
        index='STRIKE',
        columns='EXPIRY',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn',
        text=pivot.values,
        texttemplate='%{text:.0f}',
        textfont={"size": 10},
        colorbar=dict(title="Liquidity Score")
    ))
    
    fig.update_layout(
        title="Contract Liquidity Heatmap",
        xaxis_title="Expiration Date",
        yaxis_title="Strike Price",
        height=500
    )
    
    return fig


def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">🎯 Options Risk Multi-Agent AI System</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; color: #666; margin-bottom: 2rem;'>
        Powered by OpenAI GPT-3.5 • Snowflake Cloud • Multi-Agent Architecture
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Input Parameters
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Ticker selection
        ticker = st.selectbox(
            "📊 Select Ticker",
            ['AAPL', 'TSLA', 'SPY', 'NVDA', 'MSFT'],
            index=0
        )
        
        # Budget slider
        budget = st.slider(
            "💰 Budget ($)",
            min_value=1000,
            max_value=10000,
            value=5000,
            step=500,
            format="$%d"
        )
        
        # Risk profile
        risk_profile = st.select_slider(
            "🎚️ Risk Profile",
            options=['conservative', 'moderate', 'aggressive'],
            value='moderate'
        )
        
        # Goal selection
        goal = st.radio(
            "🎯 Trading Goal",
            ['bullish', 'bearish', 'neutral', 'volatility']
        )
        
        st.divider()
        
        # Run button
        run_analysis = st.button("🚀 RUN ANALYSIS", type="primary", use_container_width=True)
        
        st.divider()
        
        # Slack toggle
        enable_slack = st.checkbox("📲 Send Slack Alert", value=True)
        
        # Info
        st.info("💡 **Tip**: Try different risk profiles to see how recommendations change!")
    
    # Main content area
    if run_analysis:
        
        # Show loading spinner
        with st.spinner('🤖 Running multi-agent analysis...'):
            
            # Initialize system
            try:
                strategy_agent = EnhancedStrategyAgent()
                logistics_agent = LogisticsAgent()
                financial_agent = FinancialAgent()
                
                # Phase 1: Strategy
                st.subheader("📊 Phase 1: AI Strategy Analysis")
                strategy_progress = st.progress(0)
                
                strategy_result = strategy_agent.safe_execute({
                    'ticker': ticker,
                    'budget': budget,
                    'risk_profile': risk_profile,
                    'goal': goal
                })
                
                strategy_progress.progress(100)
                
                if not strategy_result['success']:
                    st.error(f"❌ Strategy analysis failed: {strategy_result.get('error')}")
                    return
                
                st.success("✅ Strategy analysis complete!")
                
                # Phase 2: Logistics
                st.subheader("🚚 Phase 2: Contract Filtering")
                logistics_progress = st.progress(0)
                
                logistics_result = logistics_agent.safe_execute({
                    'ticker': ticker,
                    'strategy': strategy_result['strategy']
                })
                
                logistics_progress.progress(100)
                
                if not logistics_result['success']:
                    st.error(f"❌ Logistics failed: {logistics_result.get('error')}")
                    return
                
                st.success(f"✅ Filtered to {logistics_result['liquid_contracts']} liquid contracts")
                
                # Phase 3: Financial
                st.subheader("💰 Phase 3: Portfolio Optimization")
                financial_progress = st.progress(0)
                
                financial_result = financial_agent.safe_execute({
                    'budget': budget,
                    'constraints': strategy_result['constraints'],
                    'contracts': logistics_result['filtered_contracts']
                })
                
                financial_progress.progress(100)
                
                if not financial_result['success']:
                    st.error(f"❌ Financial analysis failed: {financial_result.get('error')}")
                    return
                
                st.success(f"✅ Selected {len(financial_result['recommendations'])} positions")
                
            except Exception as e:
                st.error(f"❌ System error: {e}")
                return
        
        # Display results
        st.divider()
        st.header("📋 Analysis Results")
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Strategy",
                strategy_result['strategy']['name'].replace('_', ' ').title(),
                delta="AI Recommended"
            )
        
        with col2:
            confidence_score = strategy_result.get('confidence_analysis', {}).get('confidence_score', 0)
            st.metric(
                "Confidence",
                f"{confidence_score:.0f}%",
                delta=strategy_result.get('confidence_analysis', {}).get('confidence_level', 'N/A')
            )
        
        with col3:
            st.metric(
                "Investment",
                f"${financial_result['final_metrics']['total_cost']:,.2f}",
                delta=f"-{financial_result['remaining_budget']:,.0f} remaining"
            )
        
        with col4:
            st.metric(
                "Positions",
                len(financial_result['recommendations']),
                delta=f"{logistics_result['liquid_contracts']} available"
            )
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Strategy", "📈 Scenarios", "💼 Positions", "🔍 Agent Logs", "📲 Alerts"
        ])
        
        # TAB 1: Strategy Overview
        with tab1:
            col_left, col_right = st.columns([1, 1])
            
            with col_left:
                st.subheader("🧠 AI Strategy Recommendation")
                
                # Plain-English explanation
                if 'plain_english_summary' in strategy_result:
                    st.markdown(f"""
                    <div class='success-box'>
                    <h4>💬 What This Means:</h4>
                    <p>{strategy_result['plain_english_summary']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Confidence analysis
                if 'confidence_analysis' in strategy_result:
                    conf = strategy_result['confidence_analysis']
                    
                    st.markdown("### 📊 Confidence Analysis")
                    
                    # Show supporting factors
                    if conf.get('supporting_factors'):
                        st.markdown("**✅ Strengths:**")
                        for factor in conf['supporting_factors']:
                            st.markdown(f"• {factor}")
                    
                    # Show concerns
                    if conf.get('concerns'):
                        st.markdown("**⚠️ Concerns:**")
                        for concern in conf['concerns']:
                            st.markdown(f"• {concern}")
            
            with col_right:
                # Confidence gauge
                st.plotly_chart(
                    create_confidence_gauge(confidence_score),
                    use_container_width=True
                )
                
                # Risk score visualization
                risk_score = strategy_result['risk_score']
                
                st.markdown("### 🎯 Risk Score")
                st.progress(risk_score / 100)
                
                if risk_score < 30:
                    st.success(f"🟢 Low Risk: {risk_score:.1f}/100")
                elif risk_score < 60:
                    st.warning(f"🟡 Moderate Risk: {risk_score:.1f}/100")
                else:
                    st.error(f"🔴 High Risk: {risk_score:.1f}/100")
        
        # TAB 2: Scenario Analysis
        with tab2:
            st.subheader("🎲 What Could Happen?")
            
            scenarios = strategy_result.get('scenario_analysis', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📈 Bullish (+5%)")
                if 'bull_case_5pct' in scenarios:
                    st.info(scenarios['bull_case_5pct'])
            
            with col2:
                st.markdown("### ➡️ Sideways")
                if 'sideways' in scenarios:
                    st.warning(scenarios['sideways'])
            
            with col3:
                st.markdown("### 📉 Bearish (-5%)")
                if 'bear_case_5pct' in scenarios:
                    st.error(scenarios['bear_case_5pct'])
            
            # Scenario P&L chart
            st.markdown("### 📊 Expected P&L by Price Movement")
            scenario_chart = create_scenario_chart(
                scenarios,
                strategy_result['market_analysis']['underlying_price']
            )
            st.plotly_chart(scenario_chart, use_container_width=True)
        
        # TAB 3: Position Details
        with tab3:
            st.subheader("💼 Recommended Positions")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Positions",
                    len(financial_result['recommendations'])
                )
            
            with col2:
                st.metric(
                    "Total Cost",
                    f"${financial_result['final_metrics']['total_cost']:,.2f}"
                )
            
            with col3:
                utilization = (financial_result['final_metrics']['total_cost'] / budget * 100)
                st.metric(
                    "Budget Used",
                    f"{utilization:.1f}%"
                )
            
            st.divider()
            
            # Position details table
            if financial_result['recommendations']:
                positions_data = []
                
                for i, rec in enumerate(financial_result['recommendations'], 1):
                    positions_data.append({
                        '#': i,
                        'Contract': rec['CONTRACT_SYMBOL'],
                        'Type': rec['OPTION_TYPE'],
                        'Strike': f"${rec['STRIKE']:.2f}",
                        'Expiry': rec['EXPIRY'],
                        'DTE': f"{rec['DTE']} days",
                        'Cost': f"${rec['total_cost']:,.2f}",
                        'Liquidity': f"{rec.get('liquidity_score', 0):.0f}/100",
                        'Volume': f"{rec.get('VOLUME', 0):,}"
                    })
                
                df_positions = pd.DataFrame(positions_data)
                
                st.dataframe(
                    df_positions,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Budget allocation pie chart
                st.markdown("### 🥧 Budget Allocation")
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=[f"Position {i+1}" for i in range(len(financial_result['recommendations']))],
                    values=[r['total_cost'] for r in financial_result['recommendations']],
                    hole=.3,
                    marker_colors=px.colors.qualitative.Set3
                )])
                
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # TAB 4: Agent Execution Logs
        with tab4:
            st.subheader("🔍 Agent Execution Trace")
            
            # Timeline
            agents = ['Strategy Agent', 'Logistics Agent', 'Financial Agent']
            times = [2.3, 1.8, 0.5]
            
            fig_timeline = go.Figure()
            
            for i, (agent, time) in enumerate(zip(agents, times)):
                fig_timeline.add_trace(go.Bar(
                    x=[time],
                    y=[agent],
                    orientation='h',
                    name=agent,
                    text=f"{time}s",
                    textposition='auto'
                ))
            
            fig_timeline.update_layout(
                title="Agent Execution Timeline",
                xaxis_title="Time (seconds)",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Detailed logs
            with st.expander("📝 View Detailed Logs"):
                st.json({
                    'strategy': strategy_result.get('execution_log', []),
                    'logistics': logistics_result.get('execution_log', []),
                    'financial': financial_result.get('execution_log', [])
                })
        
        # TAB 5: Alerts & Notifications
        with tab5:
            st.subheader("📲 Alerts & Notifications")
            
            # Slack status
            slack = get_slack_manager()
            
            if slack.enabled:
                st.success("✅ Slack Integration: ACTIVE")
                
                if enable_slack:
                    # Create alert data
                    alert_data = {
                        'timestamp': datetime.now().isoformat(),
                        'input': {
                            'ticker': ticker,
                            'budget': budget,
                            'risk_profile': risk_profile,
                            'goal': goal
                        },
                        'strategy': strategy_result,
                        'financial': financial_result,
                        'summary': {
                            'ticker': ticker,
                            'strategy_name': strategy_result['strategy']['name'],
                            'positions_count': len(financial_result['recommendations']),
                            'total_investment': financial_result['final_metrics']['total_cost'],
                            'confidence_score': confidence_score,
                            'risk_score': strategy_result['risk_score']
                        }
                    }
                    
                    if st.button("📤 Send to Slack", type="primary"):
                        with st.spinner("Sending..."):
                            success = slack.send_analysis_alert(alert_data)
                            
                            if success:
                                st.success("✅ Alert sent to Slack!")
                                st.balloons()
                            else:
                                st.error("❌ Failed to send Slack alert")
                else:
                    st.info("ℹ️ Slack alerts disabled (toggle in sidebar)")
            
            else:
                st.warning("⚠️ Slack not configured")
                st.code("""
# Add to .env to enable Slack:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR-WEBHOOK
SLACK_ALERTS_ENABLED=true
SLACK_CHANNEL=#options-alerts
                """)
            
            st.divider()
            
            # Export options
            st.markdown("### 💾 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download JSON
                json_data = json.dumps({
                    'strategy': strategy_result,
                    'logistics': logistics_result,
                    'financial': financial_result
                }, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"analysis_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                # Download CSV
                if financial_result['recommendations']:
                    df_export = pd.DataFrame(financial_result['recommendations'])
                    csv = df_export.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"positions_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    else:
        # Welcome screen
        st.markdown("""
        ## 👋 Welcome to the Options Risk AI System
        
        This intelligent system uses **4 specialized AI agents** to analyze options markets and provide recommendations:
        
        - 🧠 **Strategy Agent**: Uses OpenAI to recommend optimal strategies
        - 🚚 **Logistics Agent**: Filters contracts by time and liquidity
        - 💰 **Financial Agent**: Optimizes budget allocation
        - 🎯 **Orchestrator**: Coordinates everything
        
        ### 🚀 Get Started:
        
        1. Configure your parameters in the sidebar
        2. Click **"RUN ANALYSIS"**
        3. View AI-powered recommendations
        4. Send alerts to Slack (optional)
        5. Export reports
        
        ### 📊 What You'll Get:
        
        - Plain-English strategy explanations
        - Scenario analysis (bull/bear/sideways)
        - Confidence scoring with visual feedback
        - Specific position recommendations
        - Risk compliance verification
        - Professional reports
        
        **Ready? Configure your analysis in the sidebar and click RUN!** 👈
        """)
        
        # Show sample data
        st.subheader("📊 Live Market Data Preview")
        st.info("💡 Click 'RUN ANALYSIS' to see full results")


if __name__ == "__main__":
    main()