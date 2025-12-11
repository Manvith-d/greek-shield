#!/usr/bin/env python3
"""
Orchestrator Agent - Coordinates all agents and produces final output
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.core.base_agent import BaseAgent
from agents.core.strategy_agent import StrategyAgent
from agents.core.logistics_agent import LogisticsAgent
from agents.core.financial_agent import FinancialAgent
from datetime import datetime
import json


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - The Manager
    
    Coordinates all specialized agents to produce comprehensive
    options trading recommendations
    """
    
    def __init__(self):
        super().__init__(
            agent_name="OrchestratorAgent",
            agent_role="Multi-Agent Coordination & Orchestration",
            use_llm=False  # Orchestration is rule-based
        )
        
        # Initialize all specialized agents
        self.logger.info("Initializing specialized agents...")
        self.strategy_agent = StrategyAgent()
        self.logistics_agent = LogisticsAgent()
        self.financial_agent = FinancialAgent()
        
        self.execution_trace = []
    
    def validate_input(self, context: dict) -> bool:
        """Validate orchestrator inputs"""
        required = ['ticker', 'budget', 'risk_profile', 'goal']
        for field in required:
            if field not in context:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True
    
    def execute(self, context: dict) -> dict:
        """
        Main orchestration workflow - runs all 4 agents
        
        Args:
            context: {
                'ticker': 'AAPL',
                'budget': 5000,
                'risk_profile': 'moderate',
                'goal': 'bullish'
            }
        """
        self.logger.info("🎯 ORCHESTRATOR: Starting multi-agent workflow")
        self.log_action("Orchestration started", context)
        
        # Phase 1: Strategy Discovery
        strategy_result = self._run_strategy_phase(context)
        if not strategy_result['success']:
            return self._handle_failure('Strategy', strategy_result)
        
        # Phase 2: Logistics & Scheduling
        logistics_result = self._run_logistics_phase(context, strategy_result)
        if not logistics_result['success']:
            return self._handle_failure('Logistics', logistics_result)
        
        # Phase 3: Financial Control
        financial_result = self._run_financial_phase(context, logistics_result, strategy_result)
        if not financial_result['success']:
            return self._handle_failure('Financial', financial_result)
        
        # Phase 4: Generate Final Output
        final_output = self._generate_final_output(
            context,
            strategy_result,
            logistics_result,
            financial_result
        )
        
        self.logger.info("✅ ORCHESTRATOR: Workflow completed successfully")
        
        return final_output
    
    def _run_strategy_phase(self, context: dict) -> dict:
        """Execute Strategy Agent"""
        self.logger.info("\n" + "="*70)
        self.logger.info("📊 PHASE 1: STRATEGY DISCOVERY")
        self.logger.info("="*70)
        
        strategy_context = {
            'ticker': context['ticker'],
            'budget': context['budget'],
            'risk_profile': context['risk_profile'],
            'goal': context['goal']
        }
        
        result = self.strategy_agent.safe_execute(strategy_context)
        
        self.execution_trace.append({
            'phase': 'Strategy Discovery',
            'agent': 'StrategyAgent',
            'status': 'success' if result['success'] else 'failed',
            'timestamp': datetime.now().isoformat()
        })
        
        if result['success']:
            self.logger.info(f"✅ Strategy: {result['strategy']['name']}")
            self.logger.info(f"✅ Risk Score: {result['risk_score']}/100")
        
        return result
    
    def _run_logistics_phase(self, context: dict, strategy_result: dict) -> dict:
        """Execute Logistics Agent"""
        self.logger.info("\n" + "="*70)
        self.logger.info("🚚 PHASE 2: LOGISTICS & TEMPORAL MANAGEMENT")
        self.logger.info("="*70)
        
        logistics_context = {
            'ticker': context['ticker'],
            'strategy': strategy_result['strategy']
        }
        
        result = self.logistics_agent.safe_execute(logistics_context)
        
        self.execution_trace.append({
            'phase': 'Logistics & Scheduling',
            'agent': 'LogisticsAgent',
            'status': 'success' if result['success'] else 'failed',
            'timestamp': datetime.now().isoformat()
        })
        
        if result['success']:
            self.logger.info(f"✅ Available: {result['available_contracts']}")
            self.logger.info(f"✅ Liquid: {result['liquid_contracts']}")
            self.logger.info(f"✅ Feasible: {result['feasible']}")
        
        return result
    
    def _run_financial_phase(self, context: dict, logistics_result: dict, 
                            strategy_result: dict) -> dict:
        """Execute Financial Agent"""
        self.logger.info("\n" + "="*70)
        self.logger.info("💰 PHASE 3: FINANCIAL CONTROL & COMPLIANCE")
        self.logger.info("="*70)
        
        financial_context = {
            'budget': context['budget'],
            'constraints': strategy_result['constraints'],
            'contracts': logistics_result.get('filtered_contracts', [])
        }
        
        result = self.financial_agent.safe_execute(financial_context)
        
        self.execution_trace.append({
            'phase': 'Financial Control',
            'agent': 'FinancialAgent',
            'status': 'success' if result['success'] else 'failed',
            'timestamp': datetime.now().isoformat()
        })
        
        if result['success']:
            self.logger.info(f"✅ Budget: ${result['budget']:,.2f}")
            self.logger.info(f"✅ Investment: ${result['final_metrics']['total_cost']:,.2f}")
            self.logger.info(f"✅ Positions: {len(result['recommendations'])}")
        
        return result
    
    def _handle_failure(self, phase: str, result: dict) -> dict:
        """Handle agent execution failure"""
        self.logger.error(f"❌ {phase} phase failed: {result.get('error', 'Unknown')}")
        
        return {
            'success': False,
            'error': f'{phase} Agent execution failed',
            'details': result,
            'execution_trace': self.execution_trace
        }
    
    def _generate_final_output(self, context: dict, strategy_result: dict,
                              logistics_result: dict, financial_result: dict) -> dict:
        """Generate comprehensive final output"""
        
        self.logger.info("\n" + "="*70)
        self.logger.info("📋 PHASE 4: GENERATING FINAL OUTPUT")
        self.logger.info("="*70)
        
        recommendations = financial_result.get('recommendations', [])
        
        # Create executive summary
        summary = {
            'ticker': context['ticker'],
            'strategy': strategy_result['strategy']['name'],
            'goal': context['goal'],
            'risk_profile': context['risk_profile'],
            'positions_recommended': len(recommendations),
            'total_investment': financial_result['final_metrics']['total_cost'],
            'budget_remaining': financial_result['remaining_budget'],
            'budget_utilization_pct': (
                (financial_result['final_metrics']['total_cost'] / context['budget']) * 100
            ),
            'risk_score': strategy_result['risk_score'],
            'risk_compliant': financial_result['risk_compliance']['is_compliant']
        }
        
        # Create detailed recommendations
        detailed_recs = []
        for i, rec in enumerate(recommendations, 1):
            detailed_recs.append({
                'position_number': i,
                'contract_symbol': rec.get('CONTRACT_SYMBOL', 'N/A'),
                'type': rec.get('OPTION_TYPE', 'N/A'),
                'strike': float(rec.get('STRIKE', 0)),
                'expiry': str(rec.get('EXPIRY', 'N/A')),
                'dte': int(rec.get('DTE', 0)),
                'cost': float(rec.get('total_cost', 0)),
                'liquidity_score': float(rec.get('liquidity_score', 0)),
                'volume': int(rec.get('VOLUME', 0)),
                'open_interest': int(rec.get('OPEN_INTEREST', 0))
            })
        
        final_output = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'execution_trace': self.execution_trace,
            
            # Executive Summary
            'summary': summary,
            
            # Detailed Recommendations
            'recommendations': detailed_recs,
            
            # All Agent Results
            'detailed_results': {
                'strategy': strategy_result,
                'logistics': logistics_result,
                'financial': financial_result
            }
        }
        
        self.log_action("Final output generated", {
            'recommendations_count': len(recommendations),
            'total_investment': summary['total_investment']
        })
        
        return final_output
    
    def generate_report(self, output: dict) -> str:
        """Generate human-readable text report"""
        
        if not output.get('success'):
            return f"❌ Orchestration failed: {output.get('error', 'Unknown error')}"
        
        summary = output['summary']
        
        report = []
        report.append("\n" + "="*80)
        report.append("OPTIONS TRADING RECOMMENDATIONS - MULTI-AGENT ANALYSIS")
        report.append("="*80)
        report.append(f"\nGenerated: {output['timestamp']}")
        report.append(f"Ticker: {summary['ticker']}")
        report.append(f"Strategy: {summary['strategy'].replace('_', ' ').title()}")
        report.append(f"Goal: {summary['goal'].title()}")
        report.append(f"Risk Profile: {summary['risk_profile'].title()}")
        
        report.append("\n" + "-"*80)
        report.append("EXECUTIVE SUMMARY")
        report.append("-"*80)
        report.append(f"Positions Recommended: {summary['positions_recommended']}")
        report.append(f"Total Investment: ${summary['total_investment']:,.2f}")
        report.append(f"Budget Remaining: ${summary['budget_remaining']:,.2f}")
        report.append(f"Budget Utilization: {summary['budget_utilization_pct']:.1f}%")
        report.append(f"Risk Score: {summary['risk_score']:.1f}/100")
        report.append(f"Risk Compliant: {'✅ Yes' if summary['risk_compliant'] else '❌ No'}")
        
        report.append("\n" + "-"*80)
        report.append("DETAILED RECOMMENDATIONS")
        report.append("-"*80)
        
        for rec in output['recommendations']:
            report.append(f"\nPosition #{rec['position_number']}: {rec['contract_symbol']}")
            report.append(f"  Type: {rec['type']} | Strike: ${rec['strike']} | Expires: {rec['expiry']} ({rec['dte']} days)")
            report.append(f"  Cost: ${rec['cost']:,.2f}")
            report.append(f"  Liquidity: Score {rec['liquidity_score']:.1f}, Volume {rec['volume']}, OI {rec['open_interest']}")
        
        report.append("\n" + "="*80)
        report.append(f"Agent Execution Trace:")
        for trace in output['execution_trace']:
            report.append(f"  {trace['phase']}: {trace['status'].upper()}")
        report.append("="*80 + "\n")
        
        return "\n".join(report)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING COMPLETE MULTI-AGENT SYSTEM")
    print("="*80)
    
    orchestrator = OrchestratorAgent()
    
    context = {
        'ticker': 'AAPL',
        'budget': 5000,
        'risk_profile': 'moderate',
        'goal': 'bullish'
    }
    
    print("\n🚀 Running complete multi-agent workflow...\n")
    
    result = orchestrator.safe_execute(context)
    
    if result['success']:
        # Print the formatted report
        report = orchestrator.generate_report(result)
        print(report)
        
        # Save to file
        os.makedirs('agent_outputs', exist_ok=True)
        filename = f"agent_outputs/recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n💾 Full report saved to: {filename}")
        
    else:
        print(f"\n❌ System failed: {result.get('error', 'Unknown error')}")
    
    print("\n✅ Complete system test done!")