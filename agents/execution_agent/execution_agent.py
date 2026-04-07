"""
Execution Agent - Thực thi lệnh trading
"""
import json
import logging
from typing import Dict
from datetime import datetime
from binance.client import Client as BinanceClient
from binance.enums import *

from kafka import KafkaConsumer, KafkaProducer
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionAgent:
    """Agent thực thi lệnh"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.paper_trading = config.get('paper_trading', True)
        
        # Kafka
        self.consumer = KafkaConsumer(
            'approved-signals',
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='execution-agent'
        )
        
        self.producer = KafkaProducer(
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Redis
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            decode_responses=True
        )
        
        # Binance client (if live trading)
        if not self.paper_trading:
            self.binance_client = BinanceClient(
                config['binance']['api_key'],
                config['binance']['api_secret'],
                testnet=config['binance']['testnet']
            )
        
        self.running = False
    
    def start(self):
        """Bắt đầu execution agent"""
        self.running = True
        mode = "PAPER" if self.paper_trading else "LIVE"
        logger.info(f"⚡ Execution Agent started ({mode} trading)")
        
        for message in self.consumer:
            if not self.running:
                break
                
            try:
                signal = message.value
                
                # Execute order
                execution_result = self.execute_order(signal)
                
                # Save to database/cache
                self._save_execution(execution_result)
                
                # Send notification
                self.producer.send('execution-results', execution_result)
                
                logger.info(f"⚡ Executed {signal['symbol']} {signal['type']}: "
                           f"{execution_result['status']}")
                
            except Exception as e:
                logger.error(f"Error executing order: {e}")
    
    def execute_order(self, signal: Dict) -> Dict:
        """Thực thi lệnh mua/bán"""
        symbol = signal['symbol']
        order_type = signal['type']
        position_size = signal['position_size']
        price = signal['price']
        
        execution_result = {
            'signal_id': signal.get('id'),
            'symbol': symbol,
            'type': order_type,
            'position_size': position_size,
            'requested_price': price,
            'timestamp': datetime.utcnow().isoformat(),
            'paper_trading': self.paper_trading
        }
        
        if self.paper_trading:
            # Paper trading - simulate execution
            result = self._execute_paper_order(signal)
        else:
            # Live trading - real execution
            result = self._execute_live_order(signal)
        
        execution_result.update(result)
        return execution_result
    
    def _execute_paper_order(self, signal: Dict) -> Dict:
        """Simulate order execution (paper trading)"""
        symbol = signal['symbol']
        order_type = signal['type']
        price = signal['price']
        position_size = signal['position_size']
        
        # Calculate quantity based on position size
        # Assume portfolio value of $10,000
        portfolio_value = 10000
        order_value = portfolio_value * position_size
        quantity = order_value / price
        
        # Simulate order fill
        return {
            'status': 'FILLED',
            'order_id': f"PAPER_{datetime.utcnow().timestamp()}",
            'filled_price': price,
            'filled_quantity': quantity,
            'commission': 0.001 * order_value,  # 0.1% commission
            'total_cost': order_value + (0.001 * order_value)
        }
    
    def _execute_live_order(self, signal: Dict) -> Dict:
        """Execute real order on Binance"""
        try:
            symbol = signal['symbol']
            order_type = signal['type']
            price = signal['price']
            position_size = signal['position_size']
            
            # Get account balance
            account = self.binance_client.get_account()
            # TODO: Calculate quantity based on balance
            
            # Place order
            if order_type == 'BUY':
                order = self.binance_client.order_market_buy(
                    symbol=symbol,
                    quantity=0.001  # TODO: Calculate real quantity
                )
            elif order_type == 'SELL':
                order = self.binance_client.order_market_sell(
                    symbol=symbol,
                    quantity=0.001
                )
            else:
                return {'status': 'REJECTED', 'reason': 'Invalid order type'}
            
            # Place stop loss order
            if signal.get('stop_loss'):
                self._place_stop_loss(symbol, order_type, signal['stop_loss'])
            
            # Place take profit order
            if signal.get('take_profit'):
                self._place_take_profit(symbol, order_type, signal['take_profit'])
            
            return {
                'status': order['status'],
                'order_id': order['orderId'],
                'filled_price': float(order.get('fills', [{}])[0].get('price', 0)),
                'filled_quantity': float(order['executedQty']),
                'commission': sum([float(f['commission']) for f in order.get('fills', [])])
            }
            
        except Exception as e:
            logger.error(f"Live order execution failed: {e}")
            return {
                'status': 'FAILED',
                'reason': str(e)
            }
    
    def _place_stop_loss(self, symbol: str, order_type: str, stop_price: float):
        """Place stop loss order"""
        try:
            if order_type == 'BUY':
                # Place stop loss sell order
                self.binance_client.create_order(
                    symbol=symbol,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_STOP_LOSS_LIMIT,
                    stopPrice=stop_price,
                    price=stop_price * 0.99,
                    quantity=0.001  # TODO: Calculate
                )
        except Exception as e:
            logger.error(f"Failed to place stop loss: {e}")
    
    def _place_take_profit(self, symbol: str, order_type: str, take_profit: float):
        """Place take profit order"""
        try:
            if order_type == 'BUY':
                # Place take profit sell order
                self.binance_client.create_order(
                    symbol=symbol,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    price=take_profit,
                    quantity=0.001  # TODO: Calculate
                )
        except Exception as e:
            logger.error(f"Failed to place take profit: {e}")
    
    def _save_execution(self, execution_result: Dict):
        """Save execution result to Redis"""
        key = f"execution:{execution_result['symbol']}:{execution_result.get('order_id')}"
        self.redis_client.setex(key, 86400, json.dumps(execution_result))  # 24h TTL
    
    def stop(self):
        """Dừng agent"""
        self.running = False
        self.consumer.close()
        self.producer.close()
        logger.info("Execution Agent stopped")


if __name__ == "__main__":
    config = {
        'kafka': {
            'bootstrap_servers': ['localhost:9092']
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        },
        'paper_trading': True,
        'binance': {
            'api_key': '',
            'api_secret': '',
            'testnet': True
        }
    }
    
    agent = ExecutionAgent(config)
    agent.start()
