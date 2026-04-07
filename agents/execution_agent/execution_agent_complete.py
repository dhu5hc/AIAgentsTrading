"""
EXECUTION AGENT - Complete Implementation
Demonstrates hybrid Kafka + Orchestrator usage
"""
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import sys
import os
import requests

from kafka import KafkaConsumer, KafkaProducer
import redis

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from binance_client import BinanceClientWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionAgentComplete:
    """
    COMPLETE EXECUTION AGENT showing:
    1. Kafka: Consume trading signals
    2. REST API (Orchestrator): Validate before execution
    3. REST API (Orchestrator): Record results
    4. Kafka: Publish execution results
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.paper_trading = config.get('paper_trading', True)
        self.orchestrator_url = config.get('orchestrator_url', 'http://orchestrator:8080')
        
        # ===================== KAFKA SETUP =====================
        # Subscribe to trading signals from Strategy Agent
        self.consumer = KafkaConsumer(
            'trading-signals',  # Topic to consume from
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='execution-agent',
            auto_offset_reset='earliest'
        )
        
        # Publish execution results for other agents to consume
        self.producer = KafkaProducer(
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # ===================== REDIS SETUP =====================
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            decode_responses=True
        )
        
        # ===================== BINANCE CLIENT =====================
        self.binance_client = BinanceClientWrapper(
            api_key=config['binance'].get('api_key'),
            api_secret=config['binance'].get('api_secret'),
            testnet=config['binance'].get('testnet', True)
        )
        
        self.running = False
        self.account_id = config.get('account_id', 'default-account')
        
        logger.info(f"✓ Execution Agent initialized")
        logger.info(f"  Mode: {'PAPER' if paper_trading else 'LIVE'}")
        logger.info(f"  Orchestrator: {self.orchestrator_url}")
    
    def start(self):
        """Main loop: consume signals, validate, execute, publish results"""
        self.running = True
        logger.info("⚡ Execution Agent started")
        
        for message in self.consumer:
            if not self.running:
                break
            
            try:
                # ===================== STEP 1: RECEIVE SIGNAL (Kafka) =====================
                signal = message.value
                logger.info(f"📨 Received signal from Kafka: {signal['symbol']} {signal['type']}")
                
                # ===================== STEP 2: VALIDATE WITH ORCHESTRATOR =====================
                is_valid, validation_result = self._validate_with_orchestrator(signal)
                
                if not is_valid:
                    logger.warning(f"❌ Validation FAILED: {validation_result['feedback']}")
                    
                    # Publish rejection to Kafka
                    self._publish_execution_result({
                        'status': 'REJECTED',
                        'signal': signal,
                        'reason': validation_result['feedback'],
                        'violations': validation_result['violations']
                    })
                    continue
                
                logger.info(f"✓ Validation PASSED")
                
                # ===================== STEP 3: EXECUTE TRADE =====================
                execution_result = self._execute_trade(signal)
                
                if execution_result['status'] != 'FILLED':
                    logger.error(f"❌ Execution FAILED: {execution_result.get('reason')}")
                    self._publish_execution_result(execution_result)
                    continue
                
                logger.info(f"✅ Trade EXECUTED: {execution_result['order_id']}")
                
                # ===================== STEP 4: RECORD RESULT IN ORCHESTRATOR =====================
                self._record_trade_result_in_orchestrator(execution_result)
                
                # ===================== STEP 5: PUBLISH RESULT TO KAFKA =====================
                self._publish_execution_result(execution_result)
                
                logger.info(f"✅ Execution completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Error: {e}", exc_info=True)
    
    # =========================================================================
    # ORCHESTRATOR INTEGRATION (REST API)
    # =========================================================================
    
    def _validate_with_orchestrator(self, signal: Dict) -> tuple:
        """
        SYNC REST API CALL to Orchestrator
        
        Returns: (is_valid: bool, validation_result: Dict)
        """
        try:
            logger.info("🔍 Validating with Orchestrator...")
            
            # Prepare validation request
            request_body = {
                'signal': signal,
                'config': {
                    'accountId': self.account_id,
                    'maxDailyLoss': self.config.get('max_daily_loss', -100),
                    'maxPositionRiskPercent': self.config.get('max_position_risk_percent', 2),
                    'maxTradesPerDay': self.config.get('max_trades_per_day', 10)
                }
            }
            
            # POST to Orchestrator validation endpoint
            response = requests.post(
                f"{self.orchestrator_url}/api/discipline/validate",
                json=request_body,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Orchestrator error: {response.status_code}")
                return False, {
                    'feedback': f"Orchestrator error: {response.status_code}",
                    'violations': []
                }
            
            result = response.json()
            is_valid = result['isValid']
            
            # Log violations if any
            if result['violations']:
                logger.warning(f"Violations found: {result['violations']}")
            
            return is_valid, result
            
        except requests.RequestException as e:
            logger.error(f"Orchestrator connection error: {e}")
            return False, {'feedback': f"Connection error: {e}", 'violations': []}
    
    def _record_trade_result_in_orchestrator(self, execution_result: Dict):
        """
        SYNC REST API CALL to record trade result
        Updates Orchestrator database with trade outcome
        """
        try:
            # Determine if win or loss
            profit_loss = execution_result.get('profit_loss', 0)
            
            if profit_loss > 0:
                endpoint = '/api/discipline/record-win'
                data = {
                    'accountId': self.account_id,
                    'amount': profit_loss
                }
            else:
                endpoint = '/api/discipline/record-loss'
                data = {
                    'accountId': self.account_id,
                    'amount': abs(profit_loss)
                }
            
            logger.info(f"📝 Recording trade result in Orchestrator...")
            
            response = requests.post(
                f"{self.orchestrator_url}{endpoint}",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Trade recorded in Orchestrator")
            else:
                logger.warning(f"Failed to record: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    def _check_account_status(self) -> Dict:
        """
        GET account status from Orchestrator
        Check if trading is allowed (not locked, not violated)
        """
        try:
            response = requests.get(
                f"{self.orchestrator_url}/api/discipline/status/{self.account_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'isLocked': True, 'reason': 'Cannot fetch status'}
                
        except Exception as e:
            logger.error(f"Error checking account status: {e}")
            return {'isLocked': True, 'reason': f'Connection error: {e}'}
    
    # =========================================================================
    # EXECUTION LOGIC
    # =========================================================================
    
    def _execute_trade(self, signal: Dict) -> Dict:
        """
        Execute the actual trade on Binance (or paper account)
        """
        symbol = signal['symbol']
        order_type = signal['type'].upper()  # BUY or SELL
        quantity = signal.get('quantity', 0)
        price = signal.get('price', 0)
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        execution_result = {
            'signal_id': signal.get('id'),
            'symbol': symbol,
            'type': order_type,
            'quantity': quantity,
            'requested_price': price,
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'PAPER' if self.paper_trading else 'LIVE'
        }
        
        try:
            if self.paper_trading:
                # PAPER TRADING
                result = self._execute_paper_trade(signal)
            else:
                # LIVE TRADING
                result = self._execute_live_trade(signal)
            
            execution_result.update(result)
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            execution_result['status'] = 'FAILED'
            execution_result['reason'] = str(e)
        
        return execution_result
    
    def _execute_paper_trade(self, signal: Dict) -> Dict:
        """Simulate trade in paper account"""
        symbol = signal['symbol']
        quantity = signal['quantity']
        price = signal['price']
        
        # Simulate execution
        order_id = f"PAPER_{int(datetime.utcnow().timestamp() * 1000)}"
        commission = quantity * price * 0.001  # 0.1% Binance fee
        
        result = {
            'status': 'FILLED',
            'order_id': order_id,
            'filled_price': price,
            'filled_quantity': quantity,
            'commission': commission,
            'total_cost': quantity * price + commission,
            'profit_loss': 0  # Placeholder
        }
        
        logger.info(f"📄 Paper trade: {symbol} {quantity} @ {price}")
        return result
    
    def _execute_live_trade(self, signal: Dict) -> Dict:
        """Execute real trade on Binance"""
        symbol = signal['symbol']
        order_type = signal['type'].upper()
        quantity = signal['quantity']
        price = signal['price']
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        try:
            # Place main order
            if order_type == 'BUY':
                order = self.binance_client.place_buy_order(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    order_type='LIMIT'
                )
            else:
                order = self.binance_client.place_sell_order(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    order_type='LIMIT'
                )
            
            if not order:
                return {'status': 'FAILED', 'reason': 'Failed to place order'}
            
            # Place stop loss
            if stop_loss:
                opposite_side = 'SELL' if order_type == 'BUY' else 'BUY'
                self.binance_client.place_stop_loss_order(
                    symbol=symbol,
                    quantity=quantity,
                    stop_price=stop_loss,
                    limit_price=stop_loss * 0.999,
                    side=opposite_side
                )
            
            # Place take profit
            if take_profit:
                opposite_side = 'SELL' if order_type == 'BUY' else 'BUY'
                self.binance_client.place_take_profit_order(
                    symbol=symbol,
                    quantity=quantity,
                    stop_price=take_profit,
                    limit_price=take_profit * 1.001,
                    side=opposite_side
                )
            
            logger.info(f"🎯 Live trade: {symbol} {quantity} @ {price}")
            
            return {
                'status': order.get('status', 'PENDING'),
                'order_id': order.get('order_id'),
                'filled_price': order.get('filled_price', price),
                'filled_quantity': order.get('filled_quantity', quantity),
                'commission': 0  # Populated later
            }
            
        except Exception as e:
            logger.error(f"Live trade error: {e}")
            return {'status': 'FAILED', 'reason': str(e)}
    
    # =========================================================================
    # KAFKA INTEGRATION (Publishing Results)
    # =========================================================================
    
    def _publish_execution_result(self, result: Dict):
        """
        ASYNC KAFKA PUBLISH
        Send execution result to Kafka for other agents to consume
        (Monitoring Agent, Risk Agent, etc.)
        """
        try:
            # Publish to Kafka topic
            self.producer.send('execution-results', result)
            
            # Also cache in Redis for quick access
            cache_key = f"exec:{result['symbol']}:{result.get('order_id', 'unknown')}"
            self.redis_client.setex(cache_key, 3600, json.dumps(result))
            
            logger.info(f"📤 Published to Kafka: {result['status']}")
            
        except Exception as e:
            logger.error(f"Error publishing result: {e}")
    
    def stop(self):
        """Graceful shutdown"""
        self.running = False
        self.consumer.close()
        self.producer.close()
        logger.info("⚡ Execution Agent stopped")


# =========================================================================
# CONFIGURATION EXAMPLE
# =========================================================================

CONFIG = {
    'kafka': {
        'bootstrap_servers': ['kafka:29092']
    },
    'redis': {
        'host': 'redis',
        'port': 6379
    },
    'binance': {
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret',
        'testnet': True
    },
    'orchestrator_url': 'http://orchestrator:8080',
    'account_id': 'user_123',
    'paper_trading': True,
    'max_daily_loss': -100,
    'max_position_risk_percent': 2,
    'max_trades_per_day': 10
}


# =========================================================================
# FLOW DIAGRAM
# =========================================================================

"""
EXECUTION FLOW with Kafka + Orchestrator:

1. KAFKA CONSUMER
   └─ Receive 'trading-signals' topic
   └─ Get signal like:
      {
        'symbol': 'BTCUSDT',
        'type': 'BUY',
        'quantity': 0.5,
        'price': 45000,
        'stop_loss': 44000,
        'take_profit': 46000
      }

2. ORCHESTRATOR VALIDATION (REST API)
   └─ POST /api/discipline/validate
   └─ Check rules:
      - Has SL? Has TP?
      - Position size?
      - Daily loss limit?
      - Account locked?
   └─ Response:
      {'isValid': true/false, 'violations': [...]}

3. IF VALID → EXECUTE
   └─ Place order on Binance
   └─ Place SL + TP orders
   └─ Get order_id, filled_price, etc.

4. ORCHESTRATOR RECORDING (REST API)
   └─ POST /api/discipline/record-win (or record-loss)
   └─ Update Orchestrator DB:
      - Daily P&L
      - Account state
      - Trade history

5. KAFKA PRODUCER
   └─ Publish 'execution-results' topic
   └─ Other agents consume:
      - Monitoring Agent (track portfolio)
      - Risk Agent (check correlations)
      - Strategy Agent (adjust signals)

RESULT: Compliant, trackable, scalable trading execution!
"""


if __name__ == "__main__":
    agent = ExecutionAgentComplete(CONFIG)
    agent.start()
