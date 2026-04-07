# Binance API Integration Guide

## Tổng Quan

Backend đã được tích hợp Binance Connector Java để kết nối trực tiếp tới Binance API. Execution Agent và Monitoring Agent sử dụng HTTP để gọi các endpoint từ backend.

## Kiến Trúc

```
┌─────────────────────────────────────────────────────────┐
│                   Trading Agents (Python)               │
├─────────────────────────────────────────────────────────┤
│  • Execution Agent                                       │
│  • Monitoring Agent                                      │
│  • Data Agent                                            │
│  • Analysis Agent                                        │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP REST API Calls
                  ▼
┌─────────────────────────────────────────────────────────┐
│            Backend (Spring Boot + Java)                 │
├─────────────────────────────────────────────────────────┤
│  BinanceController                                       │
│  └─ BinanceApiClient (Binance Connector Java)           │
└─────────────────┬───────────────────────────────────────┘
                  │ Binance REST API
                  ▼
           ┌──────────────┐
           │   Binance    │
           │     API      │
           └──────────────┘
```

## Cài Đặt

### 1. Backend Dependencies

Trong `build.gradle.kts` đã được thêm:

```kotlin
// Binance Connector Java
implementation("com.binance.connector:binance-connector-java:3.5.0")

// JSON parsing
implementation("org.json:json:20231013")

// OkHttp for HTTP requests
implementation("com.squareup.okhttp3:okhttp:4.11.0")
```

### 2. Cấu Hình Binance API Keys

Tạo file `.env` hoặc set environment variables:

```bash
# Binance Testnet (recommended for development)
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
export BINANCE_TESTNET=true

# Live Trading
# export BINANCE_TESTNET=false
```

Cấu hình trong `application.yml`:

```yaml
binance:
  api-key: ${BINANCE_API_KEY:}
  api-secret: ${BINANCE_API_SECRET:}
  testnet: ${BINANCE_TESTNET:true}
```

### 3. Python Agents Configuration

Execution Agent và Monitoring Agent cần biết backend URL:

```python
config = {
    'kafka': {
        'bootstrap_servers': ['localhost:9092']
    },
    'redis': {
        'host': 'localhost',
        'port': 6379
    },
    'paper_trading': True,  # Set to False for live trading
    'backend_url': 'http://localhost:8080'  # Backend URL
}
```

## API Endpoints

### Market Data Endpoints

#### 1. Lấy giá hiện tại
```http
GET /api/binance/ticker/{symbol}

Example:
GET /api/binance/ticker/BTCUSDT

Response:
{
  "symbol": "BTCUSDT",
  "price": "45000.00"
}
```

#### 2. Lấy 24h statistics
```http
GET /api/binance/stats24h/{symbol}

Example:
GET /api/binance/stats24h/ETHUSDT

Response:
{
  "symbol": "ETHUSDT",
  "priceChange": "1000.00",
  "priceChangePercent": "5.50",
  "highPrice": "20000.00",
  "lowPrice": "18000.00",
  "volume": "1000000.00"
}
```

### Account Endpoints

#### 1. Lấy thông tin tài khoản
```http
GET /api/binance/account

Response:
{
  "makerCommission": 10,
  "takerCommission": 10,
  "buyerCommission": 0,
  "sellerCommission": 0,
  "canTrade": true,
  "canWithdraw": true,
  "canDeposit": true,
  "updateTime": 1234567890,
  "balances": [
    {
      "asset": "BTC",
      "free": "0.5",
      "locked": "0.1"
    },
    {
      "asset": "USDT",
      "free": "5000.00",
      "locked": "1000.00"
    }
  ]
}
```

#### 2. Lấy balance của một asset
```http
GET /api/binance/balance/{asset}

Example:
GET /api/binance/balance/BTC

Response:
{
  "asset": "BTC",
  "balance": "0.5",
  "locked": "0.1"
}
```

### Trading Endpoints

#### 1. Đặt lệnh LIMIT
```http
POST /api/binance/order/limit

Parameters:
- symbol: BTCUSDT (required)
- side: BUY or SELL (required)
- quantity: 0.001 (required)
- price: 45000.00 (required)

Example:
curl -X POST "http://localhost:8080/api/binance/order/limit?symbol=BTCUSDT&side=BUY&quantity=0.001&price=45000.00"

Response:
{
  "symbol": "BTCUSDT",
  "orderId": 12345678,
  "clientOrderId": "web_1234567890",
  "transactTime": 1234567890,
  "price": "45000.00",
  "origQty": "0.001",
  "executedQty": "0.001",
  "cummulativeQuoteQty": "45.00",
  "status": "FILLED",
  "timeInForce": "GTC",
  "type": "LIMIT",
  "side": "BUY"
}
```

#### 2. Đặt lệnh MARKET
```http
POST /api/binance/order/market

Parameters:
- symbol: BTCUSDT (required)
- side: BUY or SELL (required)
- quantity: 0.001 (required)

Example:
curl -X POST "http://localhost:8080/api/binance/order/market?symbol=BTCUSDT&side=BUY&quantity=0.001"
```

#### 3. Đặt lệnh với Stop Loss
```http
POST /api/binance/order/stop-loss

Parameters:
- symbol: BTCUSDT (required)
- side: BUY or SELL (required)
- quantity: 0.001 (required)
- price: 44000.00 (required)
- stopPrice: 43000.00 (required)

Example:
curl -X POST "http://localhost:8080/api/binance/order/stop-loss?symbol=BTCUSDT&side=SELL&quantity=0.001&price=44000.00&stopPrice=43000.00"
```

#### 4. Lấy lệnh mở
```http
GET /api/binance/orders/open/{symbol}

Example:
GET /api/binance/orders/open/BTCUSDT

Response:
{
  "orders": [
    {
      "symbol": "BTCUSDT",
      "orderId": 12345678,
      "price": "45000.00",
      "origQty": "0.001",
      "executedQty": "0.000",
      "status": "NEW",
      "type": "LIMIT",
      "side": "BUY",
      "time": 1234567890
    }
  ]
}
```

#### 5. Lấy thông tin chi tiết lệnh
```http
GET /api/binance/order/{symbol}/{orderId}

Example:
GET /api/binance/order/BTCUSDT/12345678
```

#### 6. Hủy lệnh
```http
DELETE /api/binance/order/{symbol}/{orderId}

Example:
curl -X DELETE "http://localhost:8080/api/binance/order/BTCUSDT/12345678"
```

### Trade History

#### 1. Lấy trade history
```http
GET /api/binance/trades/{symbol}?limit=10

Example:
GET /api/binance/trades/BTCUSDT?limit=10

Response:
{
  "trades": [
    {
      "id": 123456,
      "orderId": 12345678,
      "symbol": "BTCUSDT",
      "price": "45000.00",
      "qty": "0.001",
      "quoteQty": "45.00",
      "commission": "0.0045",
      "commissionAsset": "USDT",
      "time": 1234567890,
      "isBuyer": true,
      "isMaker": false,
      "isBestMatch": true
    }
  ]
}
```

## Sử Dụng trong Execution Agent

```python
def _execute_live_order(self, signal: Dict) -> Dict:
    """Execute real order via backend Binance API"""
    try:
        symbol = signal['symbol']
        side = "BUY" if signal['type'] == "BUY" else "SELL"
        quantity = self._calculate_quantity(symbol, signal['position_size'])
        
        # Place market order
        order_response = requests.post(
            f"{self.backend_url}/api/binance/order/market",
            params={
                'symbol': symbol,
                'side': side,
                'quantity': str(quantity)
            }
        )
        
        if order_response.status_code == 200:
            order = order_response.json()
            
            # Place stop loss if provided
            if signal.get('stop_loss'):
                self._place_stop_loss(symbol, side, quantity, signal['stop_loss'])
            
            return {
                'status': order.get('status', 'FILLED'),
                'order_id': order.get('orderId'),
                'filled_price': float(order.get('price')),
                'filled_quantity': float(quantity)
            }
    except Exception as e:
        logger.error(f"Live order execution failed: {e}")
        return {'status': 'FAILED', 'reason': str(e)}
```

## Sử Dụng trong Monitoring Agent

```python
def _calculate_portfolio_value(self) -> float:
    """Calculate current portfolio value from Binance account"""
    try:
        response = requests.get(f"{self.backend_url}/api/binance/account")
        if response.status_code == 200:
            account = response.json()
            total_value = 0
            
            # Sum all assets value
            for balance in account.get('balances', []):
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total_holding = free + locked
                
                if total_holding > 0 and asset != 'USDT':
                    # Get current ticker price
                    ticker_response = requests.get(
                        f"{self.backend_url}/api/binance/ticker/{asset}USDT"
                    )
                    if ticker_response.status_code == 200:
                        price = float(ticker_response.json().get('price', 0))
                        total_value += total_holding * price
                elif asset == 'USDT':
                    total_value += total_holding
            
            return total_value
    except Exception as e:
        logger.error(f"Error calculating portfolio value: {e}")
        return self.stats['portfolio_value']
```

## Lỗi Thường Gặp

### 1. 401 Unauthorized
**Nguyên nhân**: API key hoặc secret key không đúng
**Giải pháp**: Kiểm tra `BINANCE_API_KEY` và `BINANCE_API_SECRET` environment variables

### 2. API Rate Limit
**Nguyên nhân**: Gửi quá nhiều yêu cầu
**Giải pháp**: Thêm delay giữa các yêu cầu hoặc implement rate limiter

### 3. Insufficient Balance
**Nguyên nhân**: Không đủ balance để đặt lệnh
**Giải pháp**: Kiểm tra balance trước khi đặt lệnh

### 4. Invalid Symbol
**Nguyên nhân**: Symbol không tồn tại (ví dụ: `BTC` thay vì `BTCUSDT`)
**Giải pháp**: Luôn sử dụng full symbol (ví dụ: `BTCUSDT`, `ETHUSDT`)

## Testing

### 1. Test API Connection
```bash
curl http://localhost:8080/api/binance/account
```

### 2. Test Market Data
```bash
curl http://localhost:8080/api/binance/ticker/BTCUSDT
```

### 3. Test Paper Trading (Execution Agent)
```python
# Set paper_trading = True in config
# Orders will be simulated, not sent to Binance
```

### 4. Enable Live Trading
```python
# Set paper_trading = False in config
# Ensure API keys are configured
# Use Testnet first: BINANCE_TESTNET=true
```

## Best Practices

1. **Luôn sử dụng Testnet trước khi live trading**
   ```yaml
   binance:
     testnet: true
   ```

2. **Kiểm tra balance trước khi đặt lệnh**
   ```python
   balance = requests.get(f"{backend_url}/api/binance/balance/USDT").json()
   ```

3. **Luôn set Stop Loss và Take Profit**
   ```python
   self._place_stop_loss(symbol, side, quantity, stop_price)
   self._place_take_profit(symbol, side, quantity, take_profit)
   ```

4. **Log tất cả các lỗi**
   ```python
   logger.error(f"Order failed: {e}")
   ```

5. **Implement retry logic với exponential backoff**
   ```python
   import time
   for attempt in range(3):
       try:
           response = requests.post(...)
           break
       except Exception as e:
           wait_time = 2 ** attempt
           time.sleep(wait_time)
   ```

## Tham Khảo

- [Binance Connector Java Documentation](https://github.com/binance/binance-connector-java)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
