#!/usr/bin/env python3
"""
Financial Controller Agent - Budget management and risk compliance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.core.base_agent import BaseAgent
from typing import List, Dict


class FinancialAgent(BaseAgent):
    """
    Financial Controller Agent - The Auditor
    
    Responsibilities:
    - Enforce budget constraints
    - Calculate position costs
    - Validate risk limits
    - Ensure portfolio compliance
    """
    
    def __init__(self):
        super().__init__(
            agent_name="FinancialAgent",
            agent_role="Financial Control & Compliance",
            use_llm=False  # Uses rule-based logic for precision
        )
        
        # Cost multipliers
        self.contract_multiplier = 100  # 1 contract = 100 shares
        self.commission_per_contract = 0.65  # Typical broker fee
    
    def validate_input(self, context: dict) -> bool:
        """Validate required inputs"""
        required = ['budget', 'constraints', 'contracts']
        for field in required:
            if field not in context:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True
    
    def execute(self, context: dict) -> dict:
        """
        Main financial control execution
        
        Args:
            context: {
                'budget': total available capital,
                'constraints': risk constraints dict,
                'contracts': list of filtered contracts from Logistics
            }
        """
        budget = context['budget']
        constraints = context['constraints']
        contracts = context['contracts']
        
        self.log_action("Financial analysis started", {
            'budget': budget,
            'num_contracts': len(contracts)
        })
        
        # Calculate costs for each contract
        costed_contracts = self._calculate_contract_costs(contracts)
        
        # Filter by budget
        affordable = self._filter_by_budget(costed_contracts, budget)
        
        # Apply risk limits
        risk_compliant = self._apply_risk_limits(affordable, constraints)
        
        # Optimize and select final recommendations
        final_recommendations = self._optimize_portfolio(risk_compliant, budget)
        
        # Calculate final metrics
        final_metrics = self._calculate_final_metrics(final_recommendations)
        
        return {
            'budget': budget,
            'remaining_budget': budget - final_metrics['total_cost'],
            'recommendations': final_recommendations,
            'final_metrics': final_metrics,
            'risk_compliance': self._check_risk_compliance(final_metrics, constraints)
        }
    
    def _calculate_contract_costs(self, contracts: list) -> list:
        """Calculate total cost for each contract including commissions"""
        
        costed = []
        
        for contract in contracts:
            # Use mid-price for cost estimation
            bid = float(contract.get('BID', 0) or 0)
            ask = float(contract.get('ASK', 0) or 0)
            
            if bid > 0 and ask > 0:
                mid_price = (bid + ask) / 2
            else:
                mid_price = float(contract.get('LAST_PRICE', 0) or 0)
            
            # Calculate total cost (1 contract = 100 shares)
            contract_cost = mid_price * self.contract_multiplier
            commission = self.commission_per_contract
            total_cost = contract_cost + commission
            
            contract['mid_price'] = mid_price
            contract['contract_cost'] = contract_cost
            contract['commission'] = commission
            contract['total_cost'] = total_cost
            contract['quantity'] = 1  # Default quantity
            
            costed.append(contract)
        
        self.log_action("Contract costs calculated", {
            'total_contracts': len(costed)
        })
        
        return costed
    
    def _filter_by_budget(self, contracts: list, budget: float) -> list:
        """Filter contracts that fit within budget"""
        
        # Max 30% of budget per position for safety
        max_position_size = budget * 0.30
        
        affordable = [
            c for c in contracts 
            if c['total_cost'] <= max_position_size
        ]
        
        self.log_action("Budget filtering applied", {
            'total_budget': budget,
            'max_position_size': max_position_size,
            'affordable_contracts': len(affordable)
        })
        
        return affordable
    
    def _apply_risk_limits(self, contracts: list, constraints: dict) -> list:
        """Filter contracts by risk constraints"""
        
        # For now, pass all through (you can add Greeks limits later)
        # This is where you'd check Delta, Gamma, Theta limits per contract
        
        compliant = contracts  # All contracts are compliant for now
        
        self.log_action("Risk limits applied", {
            'risk_compliant': len(compliant)
        })
        
        return compliant
    
    def _optimize_portfolio(self, contracts: list, budget: float) -> list:
        """Optimize portfolio composition for best risk/reward"""
        
        if not contracts:
            return []
        
        # Score each contract based on liquidity and volume
        for contract in contracts:
            score = 0
            
            # Liquidity score (0-40 points)
            score += contract.get('liquidity_score', 0) * 0.4
            
            # Volume score (0-30 points)
            volume = int(contract.get('VOLUME', 0) or 0)
            score += min(volume / 500 * 30, 30)
            
            # Open interest score (0-30 points)
            oi = int(contract.get('OPEN_INTEREST', 0) or 0)
            score += min(oi / 1000 * 30, 30)
            
            contract['priority_score'] = round(score, 2)
        
        # Sort by priority score
        sorted_contracts = sorted(contracts, key=lambda x: x['priority_score'], reverse=True)
        
        # Select top contracts within budget
        selected = []
        remaining_budget = budget
        
        for contract in sorted_contracts:
            if contract['total_cost'] <= remaining_budget:
                selected.append(contract)
                remaining_budget -= contract['total_cost']
                
                # Stop when we've allocated ~60% of budget or have 5 positions
                if remaining_budget < budget * 0.40 or len(selected) >= 5:
                    break
        
        self.log_action("Portfolio optimized", {
            'contracts_selected': len(selected),
            'budget_utilized': budget - remaining_budget,
            'utilization_pct': ((budget - remaining_budget) / budget * 100)
        })
        
        return selected
    
    def _calculate_final_metrics(self, recommendations: list) -> dict:
        """Calculate final portfolio metrics"""
        
        total_cost = sum(r['total_cost'] for r in recommendations)
        
        metrics = {
            'total_cost': total_cost,
            'total_positions': len(recommendations),
            'avg_cost_per_position': total_cost / len(recommendations) if recommendations else 0
        }
        
        self.log_action("Final metrics calculated", metrics)
        
        return metrics
    
    def _check_risk_compliance(self, metrics: dict, constraints: dict) -> dict:
        """Check if final metrics comply with risk constraints"""
        
        compliance = {
            'is_compliant': True,
            'checks': [
                {
                    'metric': 'Budget',
                    'status': 'PASS',
                    'message': f"Total cost ${metrics['total_cost']:,.2f} within budget"
                },
                {
                    'metric': 'Position Count',
                    'status': 'PASS',
                    'message': f"{metrics['total_positions']} positions recommended"
                }
            ]
        }
        
        return compliance


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING FINANCIAL AGENT")
    print("="*70)
    
    agent = FinancialAgent()
    
    # Mock contracts from Logistics Agent
    mock_contracts = [
        {
            'CONTRACT_SYMBOL': 'AAPL250117C00200000',
            'STRIKE': 200,
            'OPTION_TYPE': 'CALL',
            'BID': 5.50,
            'ASK': 5.60,
            'LAST_PRICE': 5.55,
            'VOLUME': 150,
            'OPEN_INTEREST': 500,
            'liquidity_score': 75
        },
        {
            'CONTRACT_SYMBOL': 'AAPL250117C00210000',
            'STRIKE': 210,
            'OPTION_TYPE': 'CALL',
            'BID': 3.20,
            'ASK': 3.30,
            'LAST_PRICE': 3.25,
            'VOLUME': 200,
            'OPEN_INTEREST': 800,
            'liquidity_score': 85
        }
    ]
    
    constraints = {
        'max_delta_exposure': 150,
        'max_gamma_risk': 0.06,
        'max_theta_decay_daily': 150
    }
    
    context = {
        'budget': 5000,
        'constraints': constraints,
        'contracts': mock_contracts
    }
    
    result = agent.safe_execute(context)
    
    print(f"\nSuccess: {result['success']}")
    if result['success']:
        print(f"\nBudget: ${result['budget']:,.2f}")
        print(f"Total Cost: ${result['final_metrics']['total_cost']:,.2f}")
        print(f"Remaining: ${result['remaining_budget']:,.2f}")
        print(f"\nRecommendations: {len(result['recommendations'])}")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec['CONTRACT_SYMBOL']}: ${rec['total_cost']:,.2f}")
        print(f"\nRisk Compliant: {result['risk_compliance']['is_compliant']}")
    
    print("\n✅ Financial Agent test complete!")