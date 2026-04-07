"""
Data Agent - Thu thập dữ liệu thị trường real-time từ Binance
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List
import logging
import sys
import os

from kafka import KafkaProducer
import redis
import requests

# Add parent directory to path to import binance_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from binance_client import BinanceClientWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAgent:
    """Agent thu thập dữ liệu từ nhiều nguồn"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=config['kafka']['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Redis cache
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            decode_responses=True
        )
        
        # Binance client (using Binance Connector)
        self.binance_client = BinanceClientWrapper(
            api_key=config['binance'].get('api_key'),
            api_secret=config['binance'].get('api_secret'),
            testnet=config['binance'].get('testnet', False)
        )
        
        self.symbols = config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        self.running = False
        logger.info(f"🔍 Data Agent initialized for symbols: {self.symbols}")
        
    async def start(self):
        """Bắt đầu thu thập dữ liệu"""
        self.running = True
        logger.info("🔍 Data Agent started")
        
        tasks = [
            self.collect_price_data(),
            self.collect_news_sentiment(),
            self.collect_social_sentiment()
        ]
        
        await asyncio.gather(*tasks)
    
    async def collect_price_data(self):
        """Thu thập giá và volume từ Binance"""
        while self.running:
            try:
                for symbol in self.symbols:
                    # Lấy ticker 24h
                    ticker = self.binance_client.get_24h_ticker(symbol=symbol)
                    
                    if not ticker:
                        logger.warning(f"Failed to get ticker for {symbol}")
                        continue
                    
                    # Lấy klines (OHLCV) - multiple timeframes
                    klines_1h = self.binance_client.get_klines(
                        symbol=symbol,
                        interval='1h',
                        limit=24
                    )
                    
                    klines_5m = self.binance_client.get_klines(
                        symbol=symbol,
                        interval='5m',
                        limit=100
                    )
                    
                    # Lấy order book
                    order_book = self.binance_client.get_order_book(symbol=symbol, limit=20)
                    
                    market_data = {
                        'symbol': symbol,
                        'price': ticker['last_price'],
                        'volume': ticker['volume'],
                        'quote_volume': ticker['quote_volume'],
                        'high_24h': ticker['high_24h'],
                        'low_24h': ticker['low_24h'],
                        'change_24h': ticker['price_change'],
                        'change_percent_24h': ticker['price_change_percent'],
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'binance',
                        'klines': {
                            '1h': klines_1h[-12:],  # Last 12 hours
                            '5m': klines_5m[-20:]   # Last 100 minutes
                        },
                        'order_book': order_book,
                    }
                    
                    # Gửi vào Kafka
                    self.producer.send('market-data', market_data)
                    
                    # Cache vào Redis
                    cache_key = f"market:{symbol}"
                    self.redis_client.setex(
                        cache_key,
                        60,  # 1 minute TTL
                        json.dumps(market_data)
                    )
                    
                    logger.info(f"📊 {symbol}: ${ticker['last_price']} (24h: {ticker['price_change_percent']:+.2f}%)")
                
                await asyncio.sleep(5)  # 5 seconds interval
                
            except Exception as e:
                logger.error(f"Error collecting price data: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def collect_news_sentiment(self):
        """Thu thập tin tức và phân tích sentiment"""
        while self.running:
            try:
                # TODO: Implement news API integration
                # Example: NewsAPI, CryptoPanic, etc.
                news_data = {
                    'type': 'news',
                    'sentiment': 0.5,  # Placeholder
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.producer.send('sentiment-data', news_data)
                
                await asyncio.sleep(60)  # 1 minute interval
                
            except Exception as e:
                logger.error(f"Error collecting news: {e}")
                await asyncio.sleep(60)
    
    async def collect_social_sentiment(self):
        """Thu thập sentiment từ Twitter, Reddit"""
        while self.running:
            try:
                # TODO: Implement Twitter/Reddit API integration
                social_data = {
                    'type': 'social',
                    'sentiment': 0.5,  # Placeholder
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.producer.send('sentiment-data', social_data)
                
                await asyncio.sleep(120)  # 2 minutes interval
                
            except Exception as e:
                logger.error(f"Error collecting social data: {e}")
                await asyncio.sleep(120)
    
    async def stop(self):
        """Dừng agent"""
        self.running = False
        self.producer.close()
        logger.info("Data Agent stopped")


if __name__ == "__main__":
    config = {
        'kafka': {
            'bootstrap_servers': ['localhost:9092']
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        },
        'binance': {
            'api_key': '',
            'api_secret': '',
            'testnet': True
        },
        'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    }
    
    agent = DataAgent(config)
    asyncio.run(agent.start())
