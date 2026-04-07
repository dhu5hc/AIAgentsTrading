"""
Data Agent - Thu thập dữ liệu thị trường real-time
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List
import logging

from kafka import KafkaProducer
import redis
from binance.client import Client as BinanceClient
import requests

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
        
        # Binance client
        self.binance_client = BinanceClient(
            config['binance']['api_key'],
            config['binance']['api_secret'],
            testnet=config['binance']['testnet']
        )
        
        self.symbols = config['symbols']
        self.running = False
        
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
                    ticker = self.binance_client.get_ticker(symbol=symbol)
                    
                    # Lấy klines (OHLCV)
                    klines = self.binance_client.get_klines(
                        symbol=symbol,
                        interval='5m',
                        limit=100
                    )
                    
                    market_data = {
                        'symbol': symbol,
                        'price': float(ticker['lastPrice']),
                        'volume': float(ticker['volume']),
                        'high_24h': float(ticker['highPrice']),
                        'low_24h': float(ticker['lowPrice']),
                        'change_24h': float(ticker['priceChange']),
                        'change_percent_24h': float(ticker['priceChangePercent']),
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'binance',
                        'klines': klines[-20:]  # Last 20 candles
                    }
                    
                    # Gửi vào Kafka
                    self.producer.send('market-data', market_data)
                    
                    # Cache vào Redis
                    cache_key = f"market:{symbol}"
                    self.redis_client.setex(
                        cache_key,
                        300,  # 5 minutes TTL
                        json.dumps(market_data)
                    )
                    
                    logger.info(f"📊 {symbol}: ${market_data['price']}")
                
                await asyncio.sleep(5)  # 5 seconds interval
                
            except Exception as e:
                logger.error(f"Error collecting price data: {e}")
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
