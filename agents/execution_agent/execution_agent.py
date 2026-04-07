"""
Execution Agent - Thực thi lệnh trading qua Binance Connector
"""
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import sys
import os

from kafka import KafkaConsumer, KafkaProducer
import redis

# Add parent directory to path to import binance_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from binance_client import BinanceClientWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionAgent:
    """Agent thực thi lệnh trading"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.paper_trading = config.get('paper_trading', True)
        self.backend_url = config.get('backend_url', 'http://localhost:8080')
        
        # Kafka
        self.consumer = KafkaConsumer(
            'approved-signals',
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='execution-agent',
            auto_offset_reset='earliest'
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
        
        # Binance client (using Binance Connector)
        self.binance_client = BinanceClientWrapper(
            api_key=config['binance'].get('api_key'),
            api_secret=config['binance'].get('api_secret'),
            testnet=config['binance'].get('testnet', True)
        )
        
        self.running = False
        self.open_orders = {}  # Track open orders
        self.account_balance = 0  # Cache account balance
        
        logger.info(f"⚡ Execution Agent initialized (paper_trading={self.paper_trading})")
    
    def start(self):
        """Bắt đầu execution agent"""
        self.running = True
        mode = "PAPER" if self.paper_trading else "LIVE"
        logger.info(f"⚡ Execution Agent started ({mode} trading)")
        
        # Load account info
        self._load_account_info()
        
        for message in self.consumer:
            if not self.running:
                break
            
            try:
                signal = message.value
                
                # Validate signal
                if not self._validate_signal(signal):
                    logger.warning(f"Invalid signal: {signal}")
                    continue
                
                # Execute order
                execution_result = self.execute_order(signal)
                
                # Cache execution result
                self._save_execution(execution_result)
                
                # Send to Kafka
                self.producer.send('execution-results', execution_result)
                
                logger.info(f"⚡ Executed {signal['symbol']} {signal['type']}: "
                           f"{execution_result['status']}")
                
            except Exception as e:
                logger.error(f"Error executing order: {e}", exc_info=True)
    
    def execute_order(self, signal: Dict) -> Dict:
        """Thực thi lệnh mua/bán"""
        symbol = signal['symbol']
        order_type = signal['type'].upper()  # BUY or SELL
        quantity = signal.get('quantity', 0)
        price = signal.get('price', 0)
        
        execution_result = {
            'signal_id': signal.get('id'),
            'symbol': symbol,
            'type': order_type,
            'quantity': quantity,
            'requested_price': price,
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'PAPER_TRADING' if self.paper_trading else 'LIVE_TRADING'
        }
        
        try:
            if self.paper_trading:
                # Paper trading - simulate execution
                result = self._execute_paper_order(signal)
            else:
                # Live trading - execute on Binance
                result = self._execute_live_order(signal)
            
            execution_result.update(result)
            
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            execution_result.update({
                'status': 'FAILED',
                'reason': str(e),
                'error': True
            })
        
        return execution_result
    
    def _execute_paper_order(self, signal: Dict) -> Dict:
        """Simulate order execution (paper trading)"""
        symbol = signal['symbol']
        order_type = signal['type'].upper()
        quantity = signal.get('quantity', 0)
        price = signal.get('price', 0)
        
        if quantity <= 0 or price <= 0:
            return {
                'status': 'REJECTED',
                'reason': 'Invalid quantity or price',
                'error': True
            }
        
        # Generate paper order ID
        paper_order_id = f"PAPER_{int(datetime.utcnow().timestamp() * 1000)}"
        
        order_value = quantity * price
        commission = order_value * 0.001  # Binance taker fee 0.1%
        
        # Cache paper order
        paper_order = {
            'order_id': paper_order_id,
            'symbol': symbol,
            'side': order_type,
            'quantity': quantity,
            'price': price,
            'status': 'FILLED',
            'filled_quantity': quantity,
            'filled_price': price,
            'commission': commission,
            'commission_asset': 'USDT',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.redis_client.hset(f"paper_orders:{symbol}", paper_order_id, json.dumps(paper_order))
        
        return {
            'status': 'FILLED',
            'order_id': paper_order_id,
            'filled_price': price,
            'filled_quantity': quantity,
            'commission': commission,
            'total_cost': order_value + commission,
            'transaction_time': datetime.utcnow().isoformat()
        }
    
    def _execute_live_order(self, signal: Dict) -> Dict:
        """Execute real order on Binance"""
        symbol = signal['symbol']
        order_type = signal['type'].upper()
        quantity = signal.get('quantity', 0)
        price = signal.get('price', 0)
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
            else:  # SELL
                order = self.binance_client.place_sell_order(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    order_type='LIMIT'
                )
            
            if not order:
                return {
                    'status': 'FAILED',
                    'reason': 'Failed to place order',
                    'error': True
                }
            
            # Place stop loss if provided
            sl_order_id = None
            if stop_loss and stop_loss > 0:
                opposite_side = 'SELL' if order_type == 'BUY' else 'BUY'
                sl_price = stop_loss * 0.999  # Slight buffer
                
                sl_order = self.binance_client.place_stop_loss_order(
                    symbol=symbol,
                    quantity=quantity,
                    stop_price=stop_loss,
                    limit_price=sl_price,
                    side=opposite_side
                )
                
                if sl_order:
                    sl_order_id = sl_order.get('order_id')
                    logger.info(f"Stop loss order placed: {sl_order_id}")
            
            # Place take profit if provided
            tp_order_id = None
            if take_profit and take_profit > 0:
                opposite_side = 'SELL' if order_type == 'BUY' else 'BUY'
                tp_price = take_profit * 1.001  # Slight buffer
                
                tp_order = self.binance_client.place_take_profit_order(
                    symbol=symbol,
                    quantity=quantity,
                    stop_price=take_profit,
                    limit_price=tp_price,
                    side=opposite_side
                )
                
                if tp_order:
                    tp_order_id = tp_order.get('order_id')
                    logger.info(f"Take profit order placed: {tp_order_id}")
            
            # Track open order
            self.open_orders[symbol] = {
                'order_id': order.get('order_id'),
                'sl_order_id': sl_order_id,
                'tp_order_id': tp_order_id,
                'entry_price': price,
                'quantity': quantity,
                'place_time': datetime.utcnow().isoformat()
            }
            
            return {
                'status': order.get('status', 'PENDING'),
                'order_id': order.get('order_id'),
                'filled_price': order.get('filled_price', price),
                'filled_quantity': order.get('filled_quantity', quantity),
                'sl_order_id': sl_order_id,
                'tp_order_id': tp_order_id,
                'transaction_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Live order execution failed: {e}")
            return {
                'status': 'FAILED',
                'reason': str(e),
                'error': True
            }
    
    def _validate_signal(self, signal: Dict) -> bool:
        """Validate trading signal"""
        required_fields = ['symbol', 'type', 'quantity', 'price']
        
        for field in required_fields:
            if field not in signal:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate values
        if signal['quantity'] <= 0:
            logger.warning(f"Invalid quantity: {signal['quantity']}")
            return False
        
        if signal['price'] <= 0:
            logger.warning(f"Invalid price: {signal['price']}")
            return False
        
        if signal['type'].upper() not in ['BUY', 'SELL']:
            logger.warning(f"Invalid type: {signal['type']}")
            return False
        
        return True
    
    def _load_account_info(self):
        """Load and cache account information"""
        try:
            if self.paper_trading:
                # Paper trading account balance
                self.account_balance = 10000  # Default paper account
            else:
                # Live trading account balance
                account = self.binance_client.get_account_info()
                if account:
                    balances = account.get('balances', {})
                    usdt_balance = balances.get('USDT', {}).get('free', 0)
                    self.account_balance = usdt_balance
                    logger.info(f"Account balance loaded: ${self.account_balance:.2f}")
        except Exception as e:
            logger.error(f"Error loading account info: {e}")
            self.account_balance = 0
    
    def _save_execution(self, execution_result: Dict):
        """Save execution result to Redis"""
        try:
            key = f"executions:{execution_result['symbol']}:{execution_result.get('order_id', 'unknown')}"
            self.redis_client.setex(
                key,
                86400,  # 24 hours TTL
                json.dumps(execution_result)
            )
        except Exception as e:
            logger.error(f"Error saving execution result: {e}")
    
    def get_open_orders(self, symbol: str = None) -> Dict:
        """Get open orders from Binance"""
        try:
            orders = self.binance_client.get_open_orders(symbol=symbol)
            
            result = {
                'symbol': symbol,
                'count': len(orders),
                'orders': orders,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return {'error': str(e)}
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        try:
            result = self.binance_client.cancel_order(symbol=symbol, order_id=order_id)
            
            if result:
                logger.info(f"Order {order_id} cancelled for {symbol}")
                return {'status': 'SUCCESS', 'order': result}
            else:
                return {'status': 'FAILED', 'reason': 'Unable to cancel order'}
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return {'status': 'FAILED', 'reason': str(e)}
    
    def stop(self):
        """Stop execution agent"""
        self.running = False
        logger.info("⚡ Execution Agent stopped")
