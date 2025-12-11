#!/usr/bin/env python3
"""
Enhanced Options Risk Multi-Agent System
Complete system with all advanced features + Slack alerts
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from agents.core.enhanced_strategy_agent import EnhancedStrategyAgent
from agents.core.logistics_agent import LogisticsAgent
from agents.core.financial_agent import FinancialAgent
from utils.slack_manager import get_slack_manager
from datetime import datetime
import json


class EnhancedMultiAgentSystem:
    """
    Complete Enhanced Multi-Agent System
    - AI-powered strategy recommendations
    - Plain-English explanations
    - Scenario analysis
    - Confidence scoring
    - Slack real-time alerts
    """
    
    def __init__(self):
        print("🚀 Initializing Enhanced Multi-Agent System...")
        self.strategy_agent = EnhancedStrategyAgent()
        self.logistics_agent = LogisticsAgent()
        self.financial_agent = FinancialAgent()
        self.slack = get_slack_manager()
        print("✅ All agents ready!")
        
        if self.slack.enabled:
            print("📲 Slack alerts: ENABLED\n")
        else:
            print("📲 Slack alerts: DISABLED (add SLACK_WEBHOOK_URL to .env to enable)\n")
    
    def analyze(self, ticker: str, budget: float, risk_profile: str, goal: str):
        """
        Run complete analysis with all enhanced features
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            budget: Available capital
            risk_profile: 'conservative', 'moderate', or 'aggressive'
            goal: 'bullish', 'bearish', 'neutral', or 'volatility'
        """
        
        print("="*80)
        print(f"ENHANCED OPTIONS ANALYSIS: {ticker}")
        print("="*80)
        print(f"Budget: ${budget:,.2f}")
        print(f"Risk Profile: {risk_profile.title()}")
        print(f"Goal: {goal.title()}")
        print("="*80)
        
        # Phase 1: Enhanced Strategy with AI
        print("\n📊 PHASE 1: AI-POWERED STRATEGY ANALYSIS")
        print("-"*80)
        
        strategy_result = self.strategy_agent.safe_execute({
            'ticker': ticker,
            'budget': budget,
            'risk_profile': risk_profile,
            'goal': goal
        })
        
        if not strategy_result['success']:
            print(f"❌ Strategy analysis failed: {strategy_result.get('error')}")
            
            # Send error alert to Slack
            if self.slack.enabled:
                self.slack.send_error_alert(
                    strategy_result.get('error', 'Unknown error'),
                    {'ticker': ticker, 'budget': budget}
                )
            
            return None
        
        self._print_strategy_results(strategy_result)
        
        # Phase 2: Logistics
        print("\n🚚 PHASE 2: LOGISTICS & CONTRACT FILTERING")
        print("-"*80)
        
        logistics_result = self.logistics_agent.safe_execute({
            'ticker': ticker,
            'strategy': strategy_result['strategy']
        })
        
        if not logistics_result['success']:
            print(f"❌ Logistics failed: {logistics_result.get('error')}")
            
            # Send error alert to Slack
            if self.slack.enabled:
                self.slack.send_error_alert(
                    logistics_result.get('error', 'Unknown error'),
                    {'ticker': ticker, 'budget': budget}
                )
            
            return None
        
        self._print_logistics_results(logistics_result)
        
        # Phase 3: Financial
        print("\n💰 PHASE 3: FINANCIAL ANALYSIS & PORTFOLIO OPTIMIZATION")
        print("-"*80)
        
        financial_result = self.financial_agent.safe_execute({
            'budget': budget,
            'constraints': strategy_result['constraints'],
            'contracts': logistics_result['filtered_contracts']
        })
        
        if not financial_result['success']:
            print(f"❌ Financial analysis failed: {financial_result.get('error')}")
            
            # Send error alert to Slack
            if self.slack.enabled:
                self.slack.send_error_alert(
                    financial_result.get('error', 'Unknown error'),
                    {'ticker': ticker, 'budget': budget}
                )
            
            return None
        
        self._print_financial_results(financial_result)
        
        # Generate final output
        final_output = self._generate_final_output(
            ticker, budget, risk_profile, goal,
            strategy_result, logistics_result, financial_result
        )
        
        # Check for high-risk situations and send special alerts
        self._check_and_alert_high_risk(final_output)
        
        # Save report
        self._save_report(final_output)
        
        # NEW: Send Slack alert with complete analysis
        if self.slack.enabled:
            print("\n📲 Sending Slack alert...")
            slack_sent = self.slack.send_analysis_alert(final_output)
            if slack_sent:
                print("✅ Slack alert sent successfully!")
                print(f"   Check your Slack channel: {self.slack.channel}")
            else:
                print("⚠️  Slack alert failed (check logs)")
        
        return final_output
    
    def _check_and_alert_high_risk(self, final_output: dict):
        """Send special alerts for high-risk situations"""
        
        if not self.slack.enabled:
            return
        
        summary = final_output.get('summary', {})
        confidence = final_output.get('strategy', {}).get('confidence_analysis', {})
        
        # Alert if confidence is LOW
        if confidence.get('confidence_score', 100) < 60:
            self.slack.send_simple_alert(
                f"⚠️ LOW CONFIDENCE ALERT\n"
                f"Ticker: {summary.get('ticker', 'N/A')}\n"
                f"Confidence: {confidence.get('confidence_score', 0):.0f}%\n"
                f"Strategy: {summary.get('strategy_name', 'N/A')}\n"
                f"⚠️ Review carefully before executing!",
                emoji="🚨"
            )
        
        # Alert if risk is HIGH
        if summary.get('risk_score', 0) > 60:
            self.slack.send_simple_alert(
                f"🔴 HIGH RISK ALERT\n"
                f"Ticker: {summary.get('ticker', 'N/A')}\n"
                f"Risk Score: {summary.get('risk_score', 0):.0f}/100\n"
                f"⚠️ Consider reducing position sizes!",
                emoji="⚠️"
            )
        
        # Alert if no positions found
        if summary.get('positions_count', 0) == 0:
            self.slack.send_simple_alert(
                f"ℹ️ NO POSITIONS FOUND\n"
                f"Ticker: {summary.get('ticker', 'N/A')}\n"
                f"Reason: No contracts met criteria\n"
                f"Suggestion: Adjust risk profile or time horizon",
                emoji="ℹ️"
            )
    
    def _print_strategy_results(self, result: dict):
        """Print enhanced strategy results"""
        
        strategy = result['strategy']
        
        print(f"\n✅ Strategy Recommended: {strategy['name'].replace('_', ' ').title()}")
        print(f"Risk Score: {result['risk_score']:.1f}/100")
        
        # Plain-English Explanation
        if 'plain_english_summary' in result:
            print(f"\n💬 WHAT THIS MEANS:")
            print(self._wrap_text(result['plain_english_summary'], 76))
        
        # Scenario Analysis
        if 'scenario_analysis' in result:
            print(f"\n🎲 WHAT COULD HAPPEN:")
            scenarios = result['scenario_analysis']
            
            if 'bull_case_5pct' in scenarios:
                print(f"\n  📈 If stock rises 5%:")
                print(f"     {self._wrap_text(scenarios['bull_case_5pct'], 70, '     ')}")
            
            if 'bear_case_5pct' in scenarios:
                print(f"\n  📉 If stock falls 5%:")
                print(f"     {self._wrap_text(scenarios['bear_case_5pct'], 70, '     ')}")
            
            if 'sideways' in scenarios:
                print(f"\n  ➡️  If stock stays flat:")
                print(f"     {self._wrap_text(scenarios['sideways'], 70, '     ')}")
        
        # Confidence Analysis
        if 'confidence_analysis' in result:
            conf = result['confidence_analysis']
            
            # Visual confidence meter
            score = conf['confidence_score']
            meter_length = 40
            filled = int(meter_length * score / 100)
            meter = "█" * filled + "░" * (meter_length - filled)
            
            print(f"\n📊 CONFIDENCE LEVEL:")
            print(f"   {meter} {score:.0f}%")
            print(f"   Level: {conf['confidence_level']}")
            print(f"   {conf['recommendation']}")
            
            if conf['supporting_factors']:
                print(f"\n   ✅ Strengths:")
                for factor in conf['supporting_factors']:
                    print(f"      • {factor}")
            
            if conf['concerns']:
                print(f"\n   ⚠️  Watch Out For:")
                for concern in conf['concerns']:
                    print(f"      • {concern}")
    
    def _print_logistics_results(self, result: dict):
        """Print logistics results"""
        
        print(f"\n✅ Analyzed {result['available_contracts']} contracts")
        print(f"✅ Filtered to {result['liquid_contracts']} liquid options")
        print(f"✅ Execution: {'Feasible ✓' if result['feasible'] else 'Limited ⚠️'}")
        
        feas = result['feasibility_report']
        print(f"\n   Available: {feas.get('calls_available', 0)} Calls, {feas.get('puts_available', 0)} Puts")
        print(f"   Strike variety: {feas.get('unique_strikes', 0)} different prices")
    
    def _print_financial_results(self, result: dict):
        """Print financial results"""
        
        metrics = result['final_metrics']
        
        print(f"\n✅ Selected {metrics['total_positions']} optimal positions")
        print(f"✅ Total Investment: ${metrics['total_cost']:,.2f}")
        print(f"✅ Budget Remaining: ${result['remaining_budget']:,.2f}")
        print(f"✅ Utilization: {(metrics['total_cost']/result['budget']*100):.1f}%")
        
        print(f"\n📋 RECOMMENDED POSITIONS:")
        
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n   {i}. {rec['CONTRACT_SYMBOL']}")
            print(f"      {rec['OPTION_TYPE']} ${rec['STRIKE']} expires {rec['EXPIRY']} ({rec['DTE']} days)")
            print(f"      Cost: ${rec['total_cost']:,.2f} | Liquidity: {rec.get('liquidity_score', 0):.0f}/100")
    
    def _generate_final_output(self, ticker, budget, risk_profile, goal,
                               strategy_result, logistics_result, financial_result):
        """Generate complete output"""
        
        return {
            'timestamp': datetime.now().isoformat(),
            'input': {
                'ticker': ticker,
                'budget': budget,
                'risk_profile': risk_profile,
                'goal': goal
            },
            'strategy': strategy_result,
            'logistics': logistics_result,
            'financial': financial_result,
            'summary': {
                'ticker': ticker,
                'strategy_name': strategy_result['strategy']['name'],
                'positions_count': len(financial_result['recommendations']),
                'total_investment': financial_result['final_metrics']['total_cost'],
                'confidence_score': strategy_result.get('confidence_analysis', {}).get('confidence_score', 0),
                'risk_score': strategy_result['risk_score']
            }
        }
    
    def _save_report(self, output: dict):
        """Save comprehensive report"""
        
        os.makedirs('agent_outputs', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ticker = output['input']['ticker']
        
        # Save JSON
        json_file = f"agent_outputs/enhanced_{ticker}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        # Save readable report
        txt_file = f"agent_outputs/enhanced_{ticker}_{timestamp}.txt"
        with open(txt_file, 'w') as f:
            f.write(self._generate_text_report(output))
        
        print(f"\n💾 REPORTS SAVED:")
        print(f"   📄 {txt_file}")
        print(f"   📊 {json_file}")
    
    def _generate_text_report(self, output: dict) -> str:
        """Generate text report"""
        
        lines = []
        lines.append("="*80)
        lines.append("ENHANCED OPTIONS TRADING ANALYSIS")
        lines.append("="*80)
        lines.append(f"\nGenerated: {output['timestamp']}")
        lines.append(f"Ticker: {output['input']['ticker']}")
        lines.append(f"Budget: ${output['input']['budget']:,.2f}")
        lines.append(f"Risk Profile: {output['input']['risk_profile'].title()}")
        lines.append(f"Goal: {output['input']['goal'].title()}")
        
        lines.append("\n" + "-"*80)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-"*80)
        
        summary = output['summary']
        lines.append(f"Strategy: {summary['strategy_name'].replace('_', ' ').title()}")
        lines.append(f"Positions: {summary['positions_count']}")
        lines.append(f"Investment: ${summary['total_investment']:,.2f}")
        lines.append(f"Confidence: {summary['confidence_score']:.0f}/100")
        lines.append(f"Risk Score: {summary['risk_score']:.1f}/100")
        
        # Add recommendations
        financial = output.get('financial', {})
        recommendations = financial.get('recommendations', [])
        
        if recommendations:
            lines.append("\n" + "-"*80)
            lines.append("RECOMMENDED POSITIONS")
            lines.append("-"*80)
            
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"\n{i}. {rec.get('CONTRACT_SYMBOL', 'N/A')}")
                lines.append(f"   {rec.get('OPTION_TYPE', 'N/A')} ${rec.get('STRIKE', 0)} expires {rec.get('EXPIRY', 'N/A')} ({rec.get('DTE', 0)} days)")
                lines.append(f"   Cost: ${rec.get('total_cost', 0):,.2f}")
        
        lines.append("\n" + "="*80)
        
        return "\n".join(lines)
    
    def _wrap_text(self, text: str, width: int, indent: str = "     ") -> str:
        """Wrap text to width"""
        words = text.split()
        lines = []
        current_line = indent
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += word + " "
            else:
                lines.append(current_line.rstrip())
                current_line = indent + word + " "
        
        if current_line.strip():
            lines.append(current_line.rstrip())
        
        return "\n".join(lines)


def main():
    """Main execution with examples"""
    
    print("\n" + "🎯"*40)
    print("ENHANCED MULTI-AGENT OPTIONS ANALYSIS SYSTEM")
    print("WITH SLACK REAL-TIME ALERTS")
    print("🎯"*40 + "\n")
    
    system = EnhancedMultiAgentSystem()
    
    # Example 1: Bullish AAPL
    result = system.analyze(
        ticker='AAPL',
        budget=5000,
        risk_profile='moderate',
        goal='bullish'
    )
    
    if result:
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\nStrategy: {result['summary']['strategy_name']}")
        print(f"Confidence: {result['summary']['confidence_score']:.0f}%")
        print(f"Positions: {result['summary']['positions_count']}")
        print(f"Investment: ${result['summary']['total_investment']:,.2f}")
        
        if system.slack.enabled:
            print(f"\n📲 Slack notification sent to {system.slack.channel}")
            print("   Check your Slack workspace for the alert!")
    
    print("\n" + "🎉"*40)


if __name__ == "__main__":
    main()