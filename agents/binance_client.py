"""
Binance Client Wrapper - Unified interface for Binance Connector
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from binance.spot import Spot
from binance.error import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class BinanceClientWrapper:
    """Wrapper cho Binance Connector để dễ sử dụng"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 testnet: bool = False):
        """
        Initialize Binance Client
        
        Args:
            api_key: Binance API key (defaults to env var)
            api_secret: Binance API secret (defaults to env var)
            testnet: Use testnet if True
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        self.testnet = testnet
        
        # Binance Connector client
        if self.testnet:
            base_url = "https://testnet.binance.vision"
        else:
            base_url = "https://api.binance.com"
        
        self.client = Spot(
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url=base_url
        )
        
        logger.info(f"✓ Binance Client initialized (testnet={testnet})")
    
    # ===================== MARKET DATA =====================
    
    def get_price(self, symbol: str) -> Dict:
        """Get current price"""
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return {
                'symbol': symbol,
                'price': float(ticker['price']),
                'timestamp': datetime.utcnow().isoformat()
            }
        except ClientError as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_24h_ticker(self, symbol: str) -> Dict:
        """Get 24h ticker data"""
        try:
            ticker = self.client.ticker_24hr(symbol=symbol)
            return {
                'symbol': symbol,
                'last_price': float(ticker['lastPrice']),
                'high_24h': float(ticker['highPrice']),
                'low_24h': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteAssetVolume']),
                'opens': float(ticker['openPrice']),
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'bid': float(ticker['bidPrice']),
                'bid_qty': float(ticker['bidQty']),
                'ask': float(ticker['askPrice']),
                'ask_qty': float(ticker['askQty']),
            }
        except ClientError as e:
            logger.error(f"Error getting 24h ticker for {symbol}: {e}")
            return None
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """
        Get candle data (OHLCV)
        
        Intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.
        """
        try:
            klines = self.client.klines(symbol=symbol, interval=interval, limit=limit)
            
            result = []
            for kline in klines:
                result.append({
                    'timestamp': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': int(kline[6]),
                    'quote_asset_volume': float(kline[7]),
                    'num_trades': int(kline[8]),
                    'taker_buy_base': float(kline[9]),
                    'taker_buy_quote': float(kline[10]),
                })
            
            return result
        except ClientError as e:
            logger.error(f"Error getting klines for {symbol}: {e}")
            return []
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book"""
        try:
            book = self.client.depth(symbol=symbol, limit=limit)
            return {
                'symbol': symbol,
                'bids': [(float(b[0]), float(b[1])) for b in book['bids']],
                'asks': [(float(a[0]), float(a[1])) for a in book['asks']],
                'timestamp': int(book.get('E', datetime.utcnow().timestamp() * 1000))
            }
        except ClientError as e:
            logger.error(f"Error getting order book for {symbol}: {e}")
            return None
    
    def get_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        try:
            trades = self.client.recent_trades(symbol=symbol, limit=limit)
            return [
                {
                    'id': t['id'],
                    'price': float(t['price']),
                    'qty': float(t['qty']),
                    'time': int(t['time']),
                    'is_buyer_maker': t['isBuyerMaker'],
                    'is_best_match': t['isBestMatch']
                }
                for t in trades
            ]
        except ClientError as e:
            logger.error(f"Error getting trades for {symbol}: {e}")
            return []
    
    # ===================== ACCOUNT INFO =====================
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account = self.client.account()
            
            balances = {}
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                
                if free > 0 or locked > 0:
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }
            
            return {
                'uid': account.get('uid'),
                'can_trade': account.get('canTrade'),
                'can_withdraw': account.get('canWithdraw'),
                'can_deposit': account.get('canDeposit'),
                'balances': balances,
                'maker_commission': float(account.get('makerCommission', 0)),
                'taker_commission': float(account.get('takerCommission', 0)),
                'update_time': int(account.get('updateTime'))
            }
        except ClientError as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_balance(self, asset: str = 'USDT') -> Tuple[float, float]:
        """Get balance for specific asset"""
        try:
            account = self.client.account()
            
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free']), float(balance['locked'])
            
            return 0.0, 0.0
        except ClientError as e:
            logger.error(f"Error getting balance for {asset}: {e}")
            return 0.0, 0.0
    
    # ===================== ORDERS =====================
    
    def place_buy_order(self, 
                       symbol: str,
                       quantity: float,
                       price: Optional[float] = None,
                       order_type: str = 'LIMIT') -> Optional[Dict]:
        """
        Place BUY order
        
        order_type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT
        """
        try:
            params = {
                'symbol': symbol,
                'side': 'BUY',
                'type': order_type,
                'quantity': quantity,
            }
            
            if order_type == 'LIMIT' and price:
                params['price'] = price
                params['timeInForce'] = 'GTC'  # Good Till Cancel
            
            order = self.client.new_order(**params)
            
            return self._format_order(order)
        except ClientError as e:
            logger.error(f"Error placing BUY order for {symbol}: {e}")
            return None
    
    def place_sell_order(self,
                        symbol: str,
                        quantity: float,
                        price: Optional[float] = None,
                        order_type: str = 'LIMIT') -> Optional[Dict]:
        """Place SELL order"""
        try:
            params = {
                'symbol': symbol,
                'side': 'SELL',
                'type': order_type,
                'quantity': quantity,
            }
            
            if order_type == 'LIMIT' and price:
                params['price'] = price
                params['timeInForce'] = 'GTC'
            
            order = self.client.new_order(**params)
            
            return self._format_order(order)
        except ClientError as e:
            logger.error(f"Error placing SELL order for {symbol}: {e}")
            return None
    
    def place_stop_loss_order(self,
                             symbol: str,
                             quantity: float,
                             stop_price: float,
                             limit_price: float,
                             side: str = 'SELL') -> Optional[Dict]:
        """Place STOP_LOSS_LIMIT order"""
        try:
            order = self.client.new_order(
                symbol=symbol,
                side=side,
                type='STOP_LOSS_LIMIT',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                timeInForce='GTC'
            )
            
            return self._format_order(order)
        except ClientError as e:
            logger.error(f"Error placing stop loss order: {e}")
            return None
    
    def place_take_profit_order(self,
                               symbol: str,
                               quantity: float,
                               stop_price: float,
                               limit_price: float,
                               side: str = 'SELL') -> Optional[Dict]:
        """Place TAKE_PROFIT_LIMIT order"""
        try:
            order = self.client.new_order(
                symbol=symbol,
                side=side,
                type='TAKE_PROFIT_LIMIT',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                timeInForce='GTC'
            )
            
            return self._format_order(order)
        except ClientError as e:
            logger.error(f"Error placing take profit order: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: int) -> Optional[Dict]:
        """Cancel an order"""
        try:
            order = self.client.cancel_order(symbol=symbol, orderId=order_id)
            return self._format_order(order)
        except ClientError as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return None
    
    def get_order(self, symbol: str, order_id: int) -> Optional[Dict]:
        """Get order status"""
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return self._format_order(order)
        except ClientError as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            orders = self.client.get_open_orders(**params)
            
            return [self._format_order(order) for order in orders]
        except ClientError as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def get_orders_history(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get order history"""
        try:
            orders = self.client.get_orders(symbol=symbol, limit=limit)
            
            return [self._format_order(order) for order in orders]
        except ClientError as e:
            logger.error(f"Error getting order history: {e}")
            return []
    
    # ===================== TRADES =====================
    
    def get_account_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get account trade history"""
        try:
            trades = self.client.get_account_trades(symbol=symbol, limit=limit)
            
            return [
                {
                    'id': t['id'],
                    'symbol': t['symbol'],
                    'price': float(t['price']),
                    'qty': float(t['qty']),
                    'commission': float(t['commission']),
                    'commission_asset': t['commissionAsset'],
                    'time': int(t['time']),
                    'is_buyer': t['isBuyer'],
                    'is_maker': t['isMaker'],
                    'order_id': t['orderId'],
                }
                for t in trades
            ]
        except ClientError as e:
            logger.error(f"Error getting account trades: {e}")
            return []
    
    # ===================== HELPER METHODS =====================
    
    def _format_order(self, order: Dict) -> Dict:
        """Format order response"""
        return {
            'order_id': order['orderId'],
            'symbol': order['symbol'],
            'side': order['side'],
            'type': order['type'],
            'price': float(order.get('price', 0)),
            'quantity': float(order['origQty']),
            'executed_qty': float(order.get('executedQty', 0)),
            'status': order['status'],
            'time': int(order.get('time', datetime.utcnow().timestamp() * 1000)),
            'update_time': int(order.get('updateTime', datetime.utcnow().timestamp() * 1000)),
            'client_order_id': order.get('clientOrderId'),
            'fills': order.get('fills', []),
        }
    
    def calculate_position_size(self,
                               account_balance: float,
                               risk_percent: float,
                               entry_price: float,
                               stop_loss_price: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            account_balance: Current account balance
            risk_percent: Risk percentage (e.g., 2 for 2%)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            
        Returns:
            Position size in base asset
        """
        if entry_price <= 0 or stop_loss_price <= 0:
            return 0
        
        risk_amount = account_balance * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss_price)
        position_size = risk_amount / price_diff
        
        return position_size
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol trading info (filters, limits, etc.)"""
        try:
            info = self.client.exchange_info(symbol=symbol)
            
            if not info.get('symbols'):
                return None
            
            symbol_info = info['symbols'][0]
            
            # Extract filters
            filters = {}
            for f in symbol_info.get('filters', []):
                f_type = f['filterType']
                if f_type == 'PRICE_FILTER':
                    filters['price'] = {
                        'min_price': float(f['minPrice']),
                        'max_price': float(f['maxPrice']),
                        'tick_size': float(f['tickSize']),
                    }
                elif f_type == 'LOT_SIZE':
                    filters['lot_size'] = {
                        'min_qty': float(f['minQty']),
                        'max_qty': float(f['maxQty']),
                        'step_size': float(f['stepSize']),
                    }
            
            return {
                'symbol': symbol,
                'status': symbol_info.get('status'),
                'base_asset': symbol_info.get('baseAsset'),
                'quote_asset': symbol_info.get('quoteAsset'),
                'is_spot_trading_allowed': symbol_info.get('isSpotTradingAllowed'),
                'filters': filters,
            }
        except ClientError as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_min_notional(self, symbol: str) -> float:
        """Get minimum notional value for symbol"""
        try:
            info = self.get_symbol_info(symbol)
            
            if info:
                for f in self.client.exchange_info(symbol=symbol)['symbols'][0].get('filters', []):
                    if f['filterType'] == 'MIN_NOTIONAL':
                        return float(f['minNotional'])
            
            return 10.0  # Default minimum
        except:
            return 10.0
