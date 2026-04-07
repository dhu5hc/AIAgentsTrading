"""
Analysis Agent - Phân tích kỹ thuật và sentiment
"""
import json
import logging
from typing import Dict, List
import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

from kafka import KafkaConsumer, KafkaProducer
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisAgent:
    """Agent phân tích kỹ thuật và sentiment"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Kafka consumer
        self.consumer = KafkaConsumer(
            'market-data',
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id='analysis-agent'
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
        
        self.running = False
    
    def start(self):
        """Bắt đầu phân tích"""
        self.running = True
        logger.info("📊 Analysis Agent started")
        
        for message in self.consumer:
            if not self.running:
                break
                
            try:
                market_data = message.value
                symbol = market_data['symbol']
                
                # Phân tích kỹ thuật
                technical_analysis = self.analyze_technical(market_data)
                
                # Phân tích sentiment (placeholder)
                sentiment_analysis = self.analyze_sentiment(symbol)
                
                # Kết hợp kết quả
                analysis_result = {
                    'symbol': symbol,
                    'price': market_data['price'],
                    'technical': technical_analysis,
                    'sentiment': sentiment_analysis,
                    'timestamp': market_data['timestamp']
                }
                
                # Gửi kết quả phân tích
                self.producer.send('analysis-results', analysis_result)
                
                # Cache kết quả
                cache_key = f"analysis:{symbol}"
                self.redis_client.setex(cache_key, 300, json.dumps(analysis_result))
                
                logger.info(f"📈 Analyzed {symbol}: RSI={technical_analysis['rsi']:.2f}, "
                           f"Trend={technical_analysis['trend']}")
                
            except Exception as e:
                logger.error(f"Error analyzing data: {e}")
    
    def analyze_technical(self, market_data: Dict) -> Dict:
        """Phân tích kỹ thuật"""
        try:
            # Convert klines to DataFrame
            klines = market_data.get('klines', [])
            if not klines or len(klines) < 20:
                return self._default_technical()
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Calculate indicators
            # RSI
            rsi_indicator = RSIIndicator(close=df['close'], window=14)
            rsi = rsi_indicator.rsi().iloc[-1]
            
            # MACD
            macd_indicator = MACD(close=df['close'])
            macd = macd_indicator.macd().iloc[-1]
            macd_signal = macd_indicator.macd_signal().iloc[-1]
            macd_diff = macd_indicator.macd_diff().iloc[-1]
            
            # EMA
            ema20 = EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1]
            ema50 = EMAIndicator(close=df['close'], window=50).ema_indicator().iloc[-1] if len(df) >= 50 else ema20
            
            # Bollinger Bands
            bb_indicator = BollingerBands(close=df['close'])
            bb_upper = bb_indicator.bollinger_hband().iloc[-1]
            bb_lower = bb_indicator.bollinger_lband().iloc[-1]
            
            # Xác định xu hướng
            current_price = market_data['price']
            trend = 'bullish' if current_price > ema20 and macd_diff > 0 else 'bearish'
            
            # Signal strength
            strength = self._calculate_strength(rsi, macd_diff, trend)
            
            return {
                'rsi': float(rsi),
                'macd': float(macd),
                'macd_signal': float(macd_signal),
                'macd_diff': float(macd_diff),
                'ema20': float(ema20),
                'ema50': float(ema50),
                'bb_upper': float(bb_upper),
                'bb_lower': float(bb_lower),
                'trend': trend,
                'strength': strength
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return self._default_technical()
    
    def analyze_sentiment(self, symbol: str) -> Dict:
        """Phân tích sentiment (placeholder - cần tích hợp AI)"""
        # TODO: Tích hợp OpenAI GPT để phân tích tin tức
        return {
            'score': 0.5,  # -1 to 1
            'confidence': 0.7,
            'sources': ['news', 'social']
        }
    
    def _calculate_strength(self, rsi: float, macd_diff: float, trend: str) -> float:
        """Tính độ mạnh của signal (0-1)"""
        strength = 0.5
        
        # RSI contribution
        if trend == 'bullish':
            if rsi < 30:
                strength += 0.3  # Oversold
            elif rsi > 70:
                strength -= 0.2  # Overbought
        else:
            if rsi > 70:
                strength += 0.3
            elif rsi < 30:
                strength -= 0.2
        
        # MACD contribution
        if abs(macd_diff) > 10:
            strength += 0.2
        
        return max(0.0, min(1.0, strength))
    
    def _default_technical(self) -> Dict:
        """Default technical values khi không đủ dữ liệu"""
        return {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_diff': 0.0,
            'ema20': 0.0,
            'ema50': 0.0,
            'bb_upper': 0.0,
            'bb_lower': 0.0,
            'trend': 'neutral',
            'strength': 0.5
        }
    
    def stop(self):
        """Dừng agent"""
        self.running = False
        self.consumer.close()
        self.producer.close()
        logger.info("Analysis Agent stopped")


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
    
    agent = AnalysisAgent(config)
    agent.start()
