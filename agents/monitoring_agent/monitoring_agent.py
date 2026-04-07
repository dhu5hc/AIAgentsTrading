"""
Monitoring Agent - Giám sát hiệu suất và cảnh báo
"""
import json
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

from kafka import KafkaConsumer
import redis
from prometheus_client import start_http_server, Gauge, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringAgent:
    """Agent giám sát hệ thống"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Kafka - subscribe to multiple topics
        self.consumer = KafkaConsumer(
            'execution-results',
            'trading-signals',
            'market-data',
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='monitoring-agent'
        )
        
        # Redis
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            decode_responses=True
        )
        
        # Prometheus metrics
        self.metrics = {
            'total_trades': Counter('trading_total_trades', 'Total number of trades'),
            'successful_trades': Counter('trading_successful_trades', 'Successful trades'),
            'failed_trades': Counter('trading_failed_trades', 'Failed trades'),
            'portfolio_value': Gauge('trading_portfolio_value', 'Current portfolio value'),
            'daily_pnl': Gauge('trading_daily_pnl', 'Daily profit/loss'),
            'win_rate': Gauge('trading_win_rate', 'Win rate percentage'),
            'signals_generated': Counter('trading_signals_generated', 'Signals generated'),
        }
        
        # Stats
        self.stats = {
            'trades': [],
            'signals': [],
            'portfolio_value': 10000,  # Starting value
            'wins': 0,
            'losses': 0
        }
        
        self.running = False
        
        # Start Prometheus metrics server
        start_http_server(8000)
    
    def start(self):
        """Bắt đầu monitoring agent"""
        self.running = True
        logger.info("📊 Monitoring Agent started (Prometheus on :8000)")
        
        for message in self.consumer:
            if not self.running:
                break
                
            try:
                topic = message.topic
                data = message.value
                
                if topic == 'execution-results':
                    self._process_execution(data)
                elif topic == 'trading-signals':
                    self._process_signal(data)
                elif topic == 'market-data':
                    self._process_market_data(data)
                
                # Update metrics periodically
                self._update_metrics()
                
                # Check alerts
                self._check_alerts()
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
    
    def _process_execution(self, execution: Dict):
        """Process execution result"""
        self.stats['trades'].append(execution)
        self.metrics['total_trades'].inc()
        
        if execution['status'] == 'FILLED':
            self.metrics['successful_trades'].inc()
            
            # Calculate P&L (simplified)
            # TODO: Implement real P&L calculation
            
            logger.info(f"📈 Trade executed: {execution['symbol']} {execution['type']}")
        else:
            self.metrics['failed_trades'].inc()
            logger.warning(f"❌ Trade failed: {execution['symbol']}")
        
        # Save to Redis
        self._save_trade_history(execution)
    
    def _process_signal(self, signal: Dict):
        """Process trading signal"""
        self.stats['signals'].append(signal)
        self.metrics['signals_generated'].inc()
        
        logger.info(f"🔔 Signal: {signal['symbol']} {signal['type']} "
                   f"@ ${signal['price']} (Confidence: {signal['confidence']:.2%})")
    
    def _process_market_data(self, market_data: Dict):
        """Process market data"""
        # Just log periodically
        pass
    
    def _update_metrics(self):
        """Update Prometheus metrics"""
        # Portfolio value
        portfolio_value = self._calculate_portfolio_value()
        self.metrics['portfolio_value'].set(portfolio_value)
        
        # Daily P&L
        daily_pnl = self._calculate_daily_pnl()
        self.metrics['daily_pnl'].set(daily_pnl)
        
        # Win rate
        win_rate = self._calculate_win_rate()
        self.metrics['win_rate'].set(win_rate)
    
    def _calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        # TODO: Implement real calculation
        return self.stats['portfolio_value']
    
    def _calculate_daily_pnl(self) -> float:
        """Calculate daily profit/loss"""
        # TODO: Implement real calculation
        today_trades = [t for t in self.stats['trades'] 
                       if self._is_today(t.get('timestamp'))]
        
        # Simplified P&L
        return len(today_trades) * 10  # Placeholder
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        total = self.stats['wins'] + self.stats['losses']
        if total == 0:
            return 0.0
        return (self.stats['wins'] / total) * 100
    
    def _check_alerts(self):
        """Check for alert conditions"""
        # Check daily loss limit
        daily_pnl = self._calculate_daily_pnl()
        if daily_pnl < -500:  # Lost $500 today
            self._send_alert('CRITICAL', f'Daily loss: ${daily_pnl}')
        
        # Check drawdown
        portfolio_value = self._calculate_portfolio_value()
        initial_value = 10000
        drawdown = (initial_value - portfolio_value) / initial_value * 100
        
        if drawdown > 10:  # 10% drawdown
            self._send_alert('WARNING', f'Drawdown: {drawdown:.1f}%')
    
    def _send_alert(self, level: str, message: str):
        """Send alert (Slack, Email, etc.)"""
        logger.warning(f"🚨 {level}: {message}")
        
        # TODO: Integrate with Slack, Email, etc.
        alert = {
            'level': level,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save to Redis
        self.redis_client.lpush('alerts', json.dumps(alert))
        self.redis_client.ltrim('alerts', 0, 99)  # Keep last 100 alerts
    
    def _save_trade_history(self, execution: Dict):
        """Save trade to Redis"""
        key = f"trade_history:{datetime.utcnow().strftime('%Y%m%d')}"
        self.redis_client.lpush(key, json.dumps(execution))
        self.redis_client.expire(key, 604800)  # 7 days TTL
    
    def _is_today(self, timestamp_str: str) -> bool:
        """Check if timestamp is today"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp.date() == datetime.utcnow().date()
        except:
            return False
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        return {
            'total_trades': len(self.stats['trades']),
            'successful_trades': self.stats['wins'],
            'failed_trades': self.stats['losses'],
            'win_rate': self._calculate_win_rate(),
            'portfolio_value': self._calculate_portfolio_value(),
            'daily_pnl': self._calculate_daily_pnl(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def stop(self):
        """Dừng agent"""
        self.running = False
        self.consumer.close()
        logger.info("Monitoring Agent stopped")


if __name__ == "__main__":
    config = {
        'kafka': {
            'bootstrap_servers': ['localhost:9092']
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        }
    }
    
    agent = MonitoringAgent(config)
    agent.start()
