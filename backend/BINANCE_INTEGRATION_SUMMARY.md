# Binance API Integration - Summary of Changes

## Overview

Backend đã được tích hợp **Binance Connector Java** v3.5.0 để kết nối trực tiếp tới Binance REST API. Execution Agent và Monitoring Agent sẽ gọi các HTTP endpoints từ backend thay vì kết nối trực tiếp tới Binance.

---

## Files Modified

### 1. Backend - `build.gradle.kts`

**Added Dependencies:**
```kotlin
// Binance Connector Java
implementation("com.binance.connector:binance-connector-java:3.5.0")

// JSON parsing
implementation("org.json:json:20231013")

// OkHttp for HTTP requests
implementation("com.squareup.okhttp3:okhttp:4.11.0")
```

### 2. Backend - `application.yml`

**Added Binance Configuration:**
```yaml
binance:
  api-key: ${BINANCE_API_KEY:}
  api-secret: ${BINANCE_API_SECRET:}
  testnet: ${BINANCE_TESTNET:true}
```

---

## Files Created

### 1. Backend - `BinanceApiClient.java`

**Location:** `src/main/java/com/trading/orchestrator/service/BinanceApiClient.java`

**Features:**
- ✅ Connect to Binance REST API using Binance Connector Java
- ✅ Place LIMIT orders
- ✅ Place MARKET orders
- ✅ Place orders with Stop Loss
- ✅ Cancel orders
- ✅ Get order information
- ✅ Get open orders
- ✅ Get account information
- ✅ Get asset balance
- ✅ Get current ticker price
- ✅ Get 24h price statistics
- ✅ Get trade history

**Key Methods:**
```java
public JSONObject placeLimitOrder(String symbol, String side, String quantity, String price)
public JSONObject placeMarketOrder(String symbol, String side, String quantity)
public JSONObject placeOrderWithStopLoss(String symbol, String side, String quantity, String price, String stopPrice)
public JSONObject cancelOrder(String symbol, Long orderId)
public JSONObject getOrder(String symbol, Long orderId)
public JSONObject getOpenOrders(String symbol)
public JSONObject getAccountInfo()
public JSONObject getBalance(String asset)
public JSONObject getTicker(String symbol)
public JSONObject get24hStats(String symbol)
public JSONObject getTradeHistory(String symbol, Integer limit)
```

### 2. Backend - `BinanceController.java`

**Location:** `src/main/java/com/trading/orchestrator/controller/BinanceController.java`

**REST Endpoints:**

#### Market Data
- `GET /api/binance/ticker/{symbol}` - Get current price
- `GET /api/binance/stats24h/{symbol}` - Get 24h statistics

#### Account
- `GET /api/binance/account` - Get account information
- `GET /api/binance/balance/{asset}` - Get asset balance

#### Trading
- `POST /api/binance/order/limit` - Place limit order
- `POST /api/binance/order/market` - Place market order
- `POST /api/binance/order/stop-loss` - Place order with stop loss
- `GET /api/binance/orders/open/{symbol}` - Get open orders
- `GET /api/binance/order/{symbol}/{orderId}` - Get order details
- `DELETE /api/binance/order/{symbol}/{orderId}` - Cancel order

#### Trade History
- `GET /api/binance/trades/{symbol}` - Get trade history

### 3. Python Agents - `execution_agent.py`

**Changes:**
- ✅ Removed direct Binance Python SDK usage
- ✅ Added HTTP REST API calls to backend
- ✅ Implemented `_execute_live_order()` using backend API
- ✅ Implemented `_calculate_quantity()` based on account balance
- ✅ Implemented `_place_stop_loss()` using backend API
- ✅ Implemented `_place_take_profit()` using backend API
- ✅ Added `backend_url` configuration parameter

**Key Changes:**
```python
# Before: Direct Binance client
self.binance_client = BinanceClient(api_key, api_secret)

# After: HTTP requests to backend
requests.post(f"{backend_url}/api/binance/order/market", params={...})
```

### 4. Python Agents - `monitoring_agent.py`

**Changes:**
- ✅ Added HTTP REST API calls to backend
- ✅ Implemented real portfolio value calculation from Binance account
- ✅ Enhanced alert checking with account status from Binance
- ✅ Added trade history retrieval
- ✅ Added `backend_url` configuration parameter

**Key Improvements:**
```python
# Calculate actual portfolio value from Binance
response = requests.get(f"{backend_url}/api/binance/account")
account = response.json()
for balance in account.get('balances', []):
    # Sum all asset values in USDT
```

---

## Configuration

### Environment Variables

```bash
# Binance API Keys
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"

# Use Binance Testnet (recommended for development)
export BINANCE_TESTNET=true

# Backend URL for Python agents
export BACKEND_URL="http://localhost:8080"
```

### Python Agent Configuration

```python
config = {
    'backend_url': 'http://localhost:8080',  # NEW
    'paper_trading': True,  # UPDATED: Now simulates paper trading
    'kafka': {...},
    'redis': {...}
}
```

---

## Architecture

```
Python Agents (Execution, Monitoring, Data, Analysis, Strategy, Risk)
           │
           ├─── HTTP REST API ───┤
           ▼                      ▼
    Backend (Spring Boot)     Swagger UI
    - BinanceController        /swagger-ui.html
    - BinanceApiClient
           │
           └──── Binance Connector Java ────▶ Binance API
                                              (REST/WebSocket)
```

---

## Usage Example

### Execution Agent - Place Order via Backend

```python
from execution_agent import ExecutionAgent

config = {
    'backend_url': 'http://localhost:8080',
    'paper_trading': False,  # Live trading
    'kafka': {'bootstrap_servers': ['localhost:9092']},
    'redis': {'host': 'localhost', 'port': 6379}
}

agent = ExecutionAgent(config)

# Signal to execute
signal = {
    'symbol': 'BTCUSDT',
    'type': 'BUY',
    'price': 45000.0,
    'position_size': 0.01,
    'stop_loss': 44000.0,
    'take_profit': 46000.0
}

# Order will be sent to Binance via backend
result = agent.execute_order(signal)
print(result)  # {'status': 'FILLED', 'order_id': 123456, ...}
```

### Monitoring Agent - Track Account

```python
from monitoring_agent import MonitoringAgent

config = {
    'backend_url': 'http://localhost:8080',
    'kafka': {'bootstrap_servers': ['localhost:9092']},
    'redis': {'host': 'localhost', 'port': 6379}
}

agent = MonitoringAgent(config)

# Portfolio value updated from Binance account
portfolio_value = agent._calculate_portfolio_value()
print(f"Portfolio: ${portfolio_value}")

# Real-time account monitoring
agent.start()
```

---

## API Testing

### 1. Test Connectivity
```bash
curl http://localhost:8080/api/binance/account
```

### 2. Get Bitcoin Price
```bash
curl http://localhost:8080/api/binance/ticker/BTCUSDT
```

### 3. Place Test Order (Paper Trading)
```bash
# Set paper_trading=true in config first
POST http://localhost:8080/api/binance/order/market?symbol=BTCUSDT&side=BUY&quantity=0.001
```

### 4. View API Documentation
```
http://localhost:8080/swagger-ui.html
```

---

## Data Flow

### Order Execution
```
1. Trading Signal │ Strategy Agent generates signal
                  ▼
2. Rule Engine    │ Discipline Agent validates signal
                  ▼
3. Execution      │ Execution Agent formats request
   Agent          ▼
4. Backend API    │ HTTP POST to /api/binance/order/market
                  ▼
5. Binance        │ Binance processes order
   API            ▼
6. Order Result   │ JSON response returned
                  ▼
7. Monitoring     │ Monitoring Agent tracks trade
   Agent
```

### Portfolio Monitoring
```
1. Monitoring     │ Monitoring Agent requests account info
   Agent          ▼
2. Backend API    │ HTTP GET to /api/binance/account
                  ▼
3. Binance        │ Binance returns account data
   API            ▼
4. Calculate      │ Agent sums all asset values
   Value          ▼
5. Prometheus     │ Metrics exposed for monitoring
   Metrics
```

---

## Deployment Notes

### Docker Setup

**Backend Dockerfile:**
```dockerfile
FROM eclipse-temurin:17-jdk-alpine
COPY build/libs/orchestrator.jar /app/
WORKDIR /app
ENV BINANCE_API_KEY=${BINANCE_API_KEY}
ENV BINANCE_API_SECRET=${BINANCE_API_SECRET}
ENV BINANCE_TESTNET=true
CMD ["java", "-jar", "orchestrator.jar"]
```

**Docker Compose:**
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      BINANCE_API_KEY: ${BINANCE_API_KEY}
      BINANCE_API_SECRET: ${BINANCE_API_SECRET}
      BINANCE_TESTNET: true
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      REDIS_HOST: redis

  execution-agent:
    build: ./agents/execution_agent
    environment:
      BACKEND_URL: http://backend:8080
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      - backend
      - kafka
      - redis
```

---

## Next Steps

1. **Build Backend**
   ```bash
   cd backend
   ./gradlew build
   ```

2. **Run Backend**
   ```bash
   ./gradlew bootRun
   ```

3. **Configure API Keys**
   - Create Binance account at https://www.binance.com
   - Generate API keys in Account Settings
   - Set environment variables

4. **Test Endpoints**
   - Visit http://localhost:8080/swagger-ui.html
   - Test market data endpoints
   - Use Testnet for live trading tests

5. **Run Agents**
   ```bash
   python agents/execution_agent/execution_agent.py
   python agents/monitoring_agent/monitoring_agent.py
   ```

---

## Documentation

- **Detailed Guide**: See `BINANCE_API_INTEGRATION.md`
- **API Docs**: http://localhost:8080/swagger-ui.html
- **Binance API**: https://binance-docs.github.io/apidocs/
- **Binance Connector Java**: https://github.com/binance/binance-connector-java

---

## Support

For issues or questions:
1. Check BINANCE_API_INTEGRATION.md for troubleshooting
2. Review Binance API documentation
3. Check logs in backend and agents
4. Test with Binance Testnet first
