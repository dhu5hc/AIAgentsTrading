"""
Risk Management Agent - Quản lý rủi ro và kiểm tra trading signals
"""
import json
import logging
from typing import Dict
from datetime import datetime

from kafka import KafkaConsumer, KafkaProducer
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManagementAgent:
    """Agent quản lý rủi ro"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Kafka
        self.consumer = KafkaConsumer(
            'trading-signals',
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='risk-agent'
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
        
        # Risk parameters
        self.max_position_size = config['risk']['max_position_size']  # 10%
        self.stop_loss_percent = config['risk']['stop_loss_percent']  # 2%
        self.max_daily_loss = config['risk']['max_daily_loss']  # 5%
        self.max_drawdown = config['risk']['max_drawdown']  # 15%
        
        self.running = False
    
    def start(self):
        """Bắt đầu risk agent"""
        self.running = True
        logger.info("🛡️ Risk Management Agent started")
        
        for message in self.consumer:
            if not self.running:
                break
                
            try:
                signal = message.value
                
                # Kiểm tra rủi ro
                risk_check = self.check_risk(signal)
                
                if risk_check['approved']:
                    # Điều chỉnh position size nếu cần
                    adjusted_signal = self.adjust_position_size(signal, risk_check)
                    adjusted_signal['risk_check'] = risk_check
                    adjusted_signal['status'] = 'APPROVED'
                    
                    # Gửi đến execution agent
                    self.producer.send('approved-signals', adjusted_signal)
                    
                    logger.info(f"✅ Approved {signal['symbol']} {signal['type']} "
                               f"(Position: {adjusted_signal['position_size']:.2%})")
                else:
                    # Reject signal
                    signal['status'] = 'REJECTED'
                    signal['rejection_reason'] = risk_check['reason']
                    
                    self.producer.send('rejected-signals', signal)
                    
                    logger.warning(f"❌ Rejected {signal['symbol']} {signal['type']}: "
                                  f"{risk_check['reason']}")
                
            except Exception as e:
                logger.error(f"Error in risk management: {e}")
    
    def check_risk(self, signal: Dict) -> Dict:
        """Kiểm tra các điều kiện rủi ro"""
        checks = {
            'approved': True,
            'reason': '',
            'checks': {}
        }
        
        # 1. Check confidence threshold
        if signal['confidence'] < 0.6:
            checks['approved'] = False
            checks['reason'] = f"Low confidence: {signal['confidence']:.2%}"
            return checks
        
        # 2. Check position size
        if signal.get('position_size', 0) > self.max_position_size:
            checks['checks']['position_size'] = f"Exceeds max: {signal['position_size']:.2%}"
        
        # 3. Check stop loss
        price = signal['price']
        stop_loss = signal.get('stop_loss')
        if stop_loss:
            loss_percent = abs(price - stop_loss) / price
            if loss_percent > self.stop_loss_percent * 2:  # 2x normal
                checks['approved'] = False
                checks['reason'] = f"Stop loss too wide: {loss_percent:.2%}"
                return checks
        
        # 4. Check daily loss limit
        daily_loss = self._get_daily_loss()
        if daily_loss >= self.max_daily_loss:
            checks['approved'] = False
            checks['reason'] = f"Daily loss limit reached: {daily_loss:.2%}"
            return checks
        
        # 5. Check max drawdown
        current_drawdown = self._get_current_drawdown()
        if current_drawdown >= self.max_drawdown:
            checks['approved'] = False
            checks['reason'] = f"Max drawdown reached: {current_drawdown:.2%}"
            return checks
        
        # 6. Check portfolio concentration
        if not self._check_diversification(signal['symbol']):
            checks['approved'] = False
            checks['reason'] = "Portfolio too concentrated in this asset"
            return checks
        
        return checks
    
    def adjust_position_size(self, signal: Dict, risk_check: Dict) -> Dict:
        """Điều chỉnh position size dựa trên rủi ro"""
        original_size = signal.get('position_size', 0.1)
        
        # Adjust based on confidence
        confidence_multiplier = signal['confidence']
        
        # Adjust based on volatility (TODO: get from analysis)
        volatility_multiplier = 1.0
        
        # Adjust based on current portfolio risk
        portfolio_risk = self._get_portfolio_risk()
        if portfolio_risk > 0.7:
            risk_multiplier = 0.5
        elif portfolio_risk > 0.5:
            risk_multiplier = 0.75
        else:
            risk_multiplier = 1.0
        
        adjusted_size = original_size * confidence_multiplier * volatility_multiplier * risk_multiplier
        adjusted_size = min(adjusted_size, self.max_position_size)
        
        signal['position_size'] = adjusted_size
        signal['original_position_size'] = original_size
        
        return signal
    
    def _get_daily_loss(self) -> float:
        """Lấy daily loss từ Redis"""
        try:
            daily_loss = self.redis_client.get('daily_loss')
            return float(daily_loss) if daily_loss else 0.0
        except:
            return 0.0
    
    def _get_current_drawdown(self) -> float:
        """Lấy current drawdown"""
        try:
            drawdown = self.redis_client.get('current_drawdown')
            return float(drawdown) if drawdown else 0.0
        except:
            return 0.0
    
    def _check_diversification(self, symbol: str) -> bool:
        """Kiểm tra portfolio có quá tập trung không"""
        # TODO: Implement real portfolio check
        return True
    
    def _get_portfolio_risk(self) -> float:
        """Tính portfolio risk level (0-1)"""
        # TODO: Implement real risk calculation
        return 0.3  # Placeholder
    
    def stop(self):
        """Dừng agent"""
        self.running = False
        self.consumer.close()
        self.producer.close()
        logger.info("Risk Management Agent stopped")


if __name__ == "__main__":
    config = {
        'kafka': {
            'bootstrap_servers': ['localhost:9092']
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        },
        'risk': {
            'max_position_size': 0.1,
            'stop_loss_percent': 0.02,
            'max_daily_loss': 0.05,
            'max_drawdown': 0.15
        }
    }
    
    agent = RiskManagementAgent(config)
    agent.start()
