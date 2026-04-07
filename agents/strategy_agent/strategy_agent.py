"""
Strategy Agent - Quyết định Buy/Sell/Hold dựa trên phân tích
"""
import json
import logging
from typing import Dict
from datetime import datetime

from kafka import KafkaConsumer, KafkaProducer
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyAgent:
    """Agent quyết định chiến lược trading"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Kafka consumer
        self.consumer = KafkaConsumer(
            'analysis-results',
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='strategy-agent'
        )
        
        # Kafka producer
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
        
        self.strategies = {
            'rsi_macd': self.rsi_macd_strategy,
            'trend_following': self.trend_following_strategy,
            'mean_reversion': self.mean_reversion_strategy
        }
        
        self.running = False
    
    def start(self):
        """Bắt đầu strategy agent"""
        self.running = True
        logger.info("🎯 Strategy Agent started")
        
        for message in self.consumer:
            if not self.running:
                break
                
            try:
                analysis = message.value
                symbol = analysis['symbol']
                
                # Áp dụng các chiến lược
                signals = []
                for strategy_name, strategy_func in self.strategies.items():
                    signal = strategy_func(analysis)
                    if signal:
                        signal['strategy'] = strategy_name
                        signals.append(signal)
                
                # Chọn signal tốt nhất
                if signals:
                    best_signal = self._select_best_signal(signals)
                    
                    # Tạo trading signal
                    trading_signal = {
                        'symbol': symbol,
                        'type': best_signal['type'],  # BUY, SELL, HOLD
                        'price': analysis['price'],
                        'confidence': best_signal['confidence'],
                        'strategy': best_signal['strategy'],
                        'reasoning': best_signal['reasoning'],
                        'stop_loss': best_signal.get('stop_loss'),
                        'take_profit': best_signal.get('take_profit'),
                        'position_size': best_signal.get('position_size', 0.1),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    # Gửi signal để risk agent kiểm tra
                    self.producer.send('trading-signals', trading_signal)
                    
                    logger.info(f"🎯 {symbol}: {best_signal['type']} @ ${analysis['price']} "
                               f"(Confidence: {best_signal['confidence']:.2%})")
                
            except Exception as e:
                logger.error(f"Error in strategy: {e}")
    
    def rsi_macd_strategy(self, analysis: Dict) -> Dict:
        """Chiến lược RSI + MACD"""
        technical = analysis['technical']
        rsi = technical['rsi']
        macd_diff = technical['macd_diff']
        trend = technical['trend']
        
        signal = None
        confidence = 0.5
        reasoning = ""
        
        # Buy signals
        if rsi < 30 and macd_diff > 0 and trend == 'bullish':
            signal = 'BUY'
            confidence = 0.8
            reasoning = f"RSI oversold ({rsi:.1f}) with bullish MACD crossover"
        
        # Sell signals
        elif rsi > 70 and macd_diff < 0 and trend == 'bearish':
            signal = 'SELL'
            confidence = 0.8
            reasoning = f"RSI overbought ({rsi:.1f}) with bearish MACD crossover"
        
        # Hold
        else:
            signal = 'HOLD'
            confidence = 0.6
            reasoning = "No strong signal"
        
        if signal in ['BUY', 'SELL']:
            price = analysis['price']
            return {
                'type': signal,
                'confidence': confidence,
                'reasoning': reasoning,
                'stop_loss': price * 0.98 if signal == 'BUY' else price * 1.02,
                'take_profit': price * 1.05 if signal == 'BUY' else price * 0.95,
                'position_size': 0.1  # 10% of portfolio
            }
        
        return None
    
    def trend_following_strategy(self, analysis: Dict) -> Dict:
        """Chiến lược follow trend"""
        technical = analysis['technical']
        trend = technical['trend']
        strength = technical['strength']
        price = analysis['price']
        ema20 = technical['ema20']
        
        if trend == 'bullish' and strength > 0.7 and price > ema20:
            return {
                'type': 'BUY',
                'confidence': strength,
                'reasoning': f"Strong bullish trend (strength: {strength:.2f})",
                'stop_loss': ema20 * 0.98,
                'take_profit': price * 1.08,
                'position_size': 0.15
            }
        
        elif trend == 'bearish' and strength > 0.7 and price < ema20:
            return {
                'type': 'SELL',
                'confidence': strength,
                'reasoning': f"Strong bearish trend (strength: {strength:.2f})",
                'stop_loss': ema20 * 1.02,
                'take_profit': price * 0.92,
                'position_size': 0.15
            }
        
        return None
    
    def mean_reversion_strategy(self, analysis: Dict) -> Dict:
        """Chiến lược mean reversion (Bollinger Bands)"""
        technical = analysis['technical']
        price = analysis['price']
        bb_upper = technical['bb_upper']
        bb_lower = technical['bb_lower']
        
        # Price touches lower band - potential buy
        if price <= bb_lower * 1.01:
            return {
                'type': 'BUY',
                'confidence': 0.75,
                'reasoning': f"Price at lower Bollinger Band ({price} <= {bb_lower})",
                'stop_loss': bb_lower * 0.97,
                'take_profit': (bb_upper + bb_lower) / 2,
                'position_size': 0.12
            }
        
        # Price touches upper band - potential sell
        elif price >= bb_upper * 0.99:
            return {
                'type': 'SELL',
                'confidence': 0.75,
                'reasoning': f"Price at upper Bollinger Band ({price} >= {bb_upper})",
                'stop_loss': bb_upper * 1.03,
                'take_profit': (bb_upper + bb_lower) / 2,
                'position_size': 0.12
            }
        
        return None
    
    def _select_best_signal(self, signals: list) -> Dict:
        """Chọn signal tốt nhất dựa trên confidence"""
        # Loại bỏ HOLD signals
        action_signals = [s for s in signals if s['type'] != 'HOLD']
        
        if not action_signals:
            return signals[0]
        
        # Chọn signal có confidence cao nhất
        return max(action_signals, key=lambda s: s['confidence'])
    
    def stop(self):
        """Dừng agent"""
        self.running = False
        self.consumer.close()
        self.producer.close()
        logger.info("Strategy Agent stopped")


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
    
    agent = StrategyAgent(config)
    agent.start()
