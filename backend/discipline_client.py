#!/usr/bin/env python3
"""
Kỷ Luật Tuyệt Đối Framework - Python Client
Python helper for AI Trading Agents to interact with Discipline Rule Engine
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DisciplineClient:
    """Client for Kỷ Luật Tuyệt Đối Framework REST API"""
    
    def __init__(self, base_url: str = "http://localhost:8080/api/discipline"):
        """
        Initialize the discipline client
        
        Args:
            base_url: Base URL for the discipline API (default: localhost:8080)
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def validate_trade(
        self,
        signal: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a trading signal against discipline rules
        
        Args:
            signal: Trading signal data
            config: Trader discipline configuration
            
        Returns:
            Validation result with violations and warnings
            
        Example:
            >>> signal = {
            ...     "symbol": "BTC/USDT",
            ...     "type": "BUY",
            ...     "price": 32000,
            ...     "confidence": 0.75,
            ...     "stopLoss": 31000,
            ...     "takeProfit": 33000,
            ...     "positionSize": 1.5
            ... }
            >>> config = {
            ...     "accountId": "trader-001",
            ...     "minConfidenceThreshold": 0.60,
            ...     "maxRiskPerTrade": 0.02
            ... }
            >>> result = client.validate_trade(signal, config)
            >>> if result['isValid']:
            ...     print("✅ Trade is valid!")
            ... else:
            ...     print("❌ Trade blocked:", result['violations'])
        """
        try:
            payload = {
                "signal": signal,
                "config": config
            }
            
            response = self.session.post(
                f"{self.base_url}/validate",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result['isValid']:
                logger.info(f"✅ Trade valid for {signal['symbol']}")
            else:
                logger.warning(f"❌ Trade blocked for {signal['symbol']}: "
                             f"{len(result['violations'])} violations")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Validation request failed: {e}")
            raise
    
    def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get current trading session status for an account
        
        Args:
            account_id: Account identifier
            
        Returns:
            Account status and discipline metrics
            
        Example:
            >>> status = client.get_account_status("trader-001")
            >>> print(f"Session: {status['sessionStatus']}")
            >>> print(f"Consecutive Losses: {status['consecutiveLosses']}")
            >>> print(f"Daily P&L: {status['dailyProfitLoss']}")
        """
        try:
            response = self.session.get(
                f"{self.base_url}/status/{account_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get account status: {e}")
            raise
    
    def record_win(self, account_id: str, amount: float) -> str:
        """
        Record a winning trade
        
        Args:
            account_id: Account identifier
            amount: Win amount in dollars
            
        Returns:
            Confirmation message
            
        Example:
            >>> client.record_win("trader-001", 250.50)
            "Win recorded successfully"
        """
        try:
            payload = {
                "accountId": account_id,
                "amount": amount
            }
            
            response = self.session.post(
                f"{self.base_url}/record-win",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Win recorded for {account_id}: +${amount}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to record win: {e}")
            raise
    
    def record_loss(self, account_id: str, amount: float) -> str:
        """
        Record a losing trade
        
        Args:
            account_id: Account identifier
            amount: Loss amount in dollars
            
        Returns:
            Confirmation message (may include break trigger warning)
            
        Example:
            >>> response = client.record_loss("trader-001", 150.50)
            >>> print(response)
            "Loss recorded - check if break period triggered"
        """
        try:
            payload = {
                "accountId": account_id,
                "amount": amount
            }
            
            response = self.session.post(
                f"{self.base_url}/record-loss",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.warning(f"❌ Loss recorded for {account_id}: -${amount}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to record loss: {e}")
            raise
    
    def initiate_break(self, account_id: str) -> str:
        """
        Manually initiate a break period (emotional recovery)
        
        Args:
            account_id: Account identifier
            
        Returns:
            Confirmation message with break end time
            
        Example:
            >>> response = client.initiate_break("trader-001")
            >>> print(response)
            "Break period initiated - until 2026-04-07T15:30:00"
        """
        try:
            payload = {"accountId": account_id}
            
            response = self.session.post(
                f"{self.base_url}/break",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"⏸️  Break initiated for {account_id}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to initiate break: {e}")
            raise
    
    def resume_trading(self, account_id: str) -> str:
        """
        Resume trading after break period
        
        Args:
            account_id: Account identifier
            
        Returns:
            Confirmation message
            
        Example:
            >>> response = client.resume_trading("trader-001")
            >>> print(response)
            "Trading resumed - stay disciplined!"
        """
        try:
            payload = {"accountId": account_id}
            
            response = self.session.post(
                f"{self.base_url}/resume",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"▶️  Trading resumed for {account_id}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to resume trading: {e}")
            raise
    
    def lock_account(self, account_id: str, reason: str) -> str:
        """
        Lock an account due to violations (admin only)
        
        Args:
            account_id: Account identifier
            reason: Reason for locking
            
        Returns:
            Confirmation message
            
        Example:
            >>> response = client.lock_account(
            ...     "trader-001",
            ...     "Multiple critical rule violations"
            ... )
        """
        try:
            payload = {
                "accountId": account_id,
                "reason": reason
            }
            
            response = self.session.post(
                f"{self.base_url}/lock",
                json=payload,
                timeout=10
            )
            
            logger.error(f"🔒 Account locked: {account_id} | Reason: {reason}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to lock account: {e}")
            raise
    
    def get_report(self, account_id: str) -> Dict[str, Any]:
        """
        Get full discipline report for an account
        
        Args:
            account_id: Account identifier
            
        Returns:
            Detailed discipline metrics
            
        Example:
            >>> report = client.get_report("trader-001")
            >>> print(json.dumps(report, indent=2))
        """
        try:
            response = self.session.get(
                f"{self.base_url}/report/{account_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get report: {e}")
            raise


class DisciplineValidator:
    """Helper class for validation workflows"""
    
    def __init__(self, client: DisciplineClient):
        self.client = client
    
    def validate_and_execute(
        self,
        signal: Dict[str, Any],
        config: Dict[str, Any],
        execution_callback=None
    ) -> bool:
        """
        Full validation workflow with execution callback
        
        Args:
            signal: Trading signal
            config: Trader configuration
            execution_callback: Function to call if validation passes
            
        Returns:
            True if trade executed, False otherwise
        """
        # Validate
        result = self.client.validate_trade(signal, config)
        
        if not result['isValid']:
            violations = result.get('violations', [])
            for v in violations:
                logger.error(f"❌ {v['vietnameseMessage']}")
            return False
        
        # Show warnings
        warnings = result.get('warnings', [])
        for w in warnings:
            logger.warning(f"⚠️  {w['vietnameseMessage']}")
        
        # Execute if callback provided
        if execution_callback:
            try:
                execution_callback(signal)
                logger.info(f"✅ Trade executed: {signal['symbol']}")
                return True
            except Exception as e:
                logger.error(f"Execution failed: {e}")
                return False
        
        return True
    
    def should_trade(self, signal: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """
        Quick check: is the signal valid to trade?
        
        Args:
            signal: Trading signal
            config: Trader configuration
            
        Returns:
            True if valid, False otherwise
        """
        result = self.client.validate_trade(signal, config)
        return result['isValid']


# ========== Example Usage ==========

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize client
    client = DisciplineClient()
    
    # Example 1: Validate a trade
    print("\n=== Example 1: Validate Trade ===")
    signal = {
        "symbol": "BTC/USDT",
        "type": "BUY",
        "price": 32000,
        "confidence": 0.75,
        "stopLoss": 31000,
        "takeProfit": 33000,
        "positionSize": 1.5
    }
    
    config = {
        "accountId": "trader-001",
        "minConfidenceThreshold": 0.60,
        "maxRiskPerTrade": 0.02,
        "accountBalance": 10000
    }
    
    result = client.validate_trade(signal, config)
    print("Feedback:", result['feedback'])
    
    # Example 2: Get account status
    print("\n=== Example 2: Account Status ===")
    status = client.get_account_status("trader-001")
    print(f"Session Status: {status['sessionStatus']}")
    print(f"Daily P&L: ${status['dailyProfitLoss']}")
    
    # Example 3: Record trade result
    print("\n=== Example 3: Record Trade Results ===")
    client.record_win("trader-001", 250.50)
    client.record_loss("trader-001", 150.00)
    
    # Example 4: Using validator helper
    print("\n=== Example 4: Validation Workflow ===")
    validator = DisciplineValidator(client)
    
    def execute_order(signal):
        print(f"🚀 Executing order: {signal['symbol']} {signal['type']}")
    
    is_valid = validator.validate_and_execute(signal, config, execute_order)
    print(f"Trade executed: {is_valid}")
