# Quick Start - Binance API Integration

## ⚡ 5-Minute Setup

### Step 1: Configure Binance API Keys

```bash
# Testnet keys (recommended first time)
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
export BINANCE_TESTNET=true

# Or create .env file in backend folder
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
BINANCE_TESTNET=true
```

### Step 2: Build & Run Backend

```bash
cd backend

# Build
./gradlew clean build

# Run
./gradlew bootRun
```

Backend sẽ chạy tại: `http://localhost:8080`

### Step 3: Verify API Connection

```bash
# Test account connection
curl http://localhost:8080/api/binance/account

# Get Bitcoin price
curl http://localhost:8080/api/binance/ticker/BTCUSDT

# View API docs
open http://localhost:8080/swagger-ui.html
```

### Step 4: Configure Python Agents

```python
# execution_agent/execution_agent.py
config = {
    'backend_url': 'http://localhost:8080',  # ← Point to backend
    'paper_trading': True,  # ← Use False for live trading
    'kafka': {'bootstrap_servers': ['localhost:9092']},
    'redis': {'host': 'localhost', 'port': 6379}
}
```

```python
# monitoring_agent/monitoring_agent.py
config = {
    'backend_url': 'http://localhost:8080',  # ← Point to backend
    'kafka': {'bootstrap_servers': ['localhost:9092']},
    'redis': {'host': 'localhost', 'port': 6379}
}
```

### Step 5: Run Agents

```bash
# Terminal 1: Execution Agent
python agents/execution_agent/execution_agent.py

# Terminal 2: Monitoring Agent
python agents/monitoring_agent/monitoring_agent.py
```

---

## 📊 API Endpoints at a Glance

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/binance/ticker/{symbol}` | Get current price |
| GET | `/api/binance/stats24h/{symbol}` | Get 24h change stats |
| GET | `/api/binance/account` | Get account info |
| GET | `/api/binance/balance/{asset}` | Get asset balance |
| POST | `/api/binance/order/market` | Place market order |
| POST | `/api/binance/order/limit` | Place limit order |
| POST | `/api/binance/order/stop-loss` | Place order with SL |
| GET | `/api/binance/orders/open/{symbol}` | Get open orders |
| DELETE | `/api/binance/order/{symbol}/{orderId}` | Cancel order |
| GET | `/api/binance/trades/{symbol}` | Get trade history |

---

## 🔥 Common Commands

### Place Market Buy Order
```bash
curl -X POST \
  "http://localhost:8080/api/binance/order/market" \
  -d "symbol=BTCUSDT" \
  -d "side=BUY" \
  -d "quantity=0.001"
```

### Place Limit Buy with Stop Loss
```bash
curl -X POST \
  "http://localhost:8080/api/binance/order/stop-loss" \
  -d "symbol=BTCUSDT" \
  -d "side=SELL" \
  -d "quantity=0.001" \
  -d "price=44000" \
  -d "stopPrice=43000"
```

### Get Account Balance
```bash
curl http://localhost:8080/api/binance/account | jq '.balances'
```

### Cancel Order
```bash
curl -X DELETE \
  "http://localhost:8080/api/binance/order/BTCUSDT/12345678"
```

---

## 🐛 Troubleshooting

### Backend won't start: "API key error"
```
→ Check BINANCE_API_KEY and BINANCE_API_SECRET are set
→ Verify keys are from Binance API Management page
→ Test with Testnet first (BINANCE_TESTNET=true)
```

### Agent can't connect to backend
```
→ Check backend is running on port 8080
→ Verify backend_url in agent config: 'http://localhost:8080'
→ Test: curl http://localhost:8080/actuator/health
```

### Order placement fails "Insufficient balance"
```
→ Check account balance: curl http://localhost:8080/api/binance/account
→ Calculate required balance for order size
→ Use smaller position size or add balance
```

### "Rate limit exceeded"
```
→ Add delay between API calls
→ Binance: 1200 requests/minute for most endpoints
→ Use import time; time.sleep(0.1)
```

### "Invalid symbol" error
```
→ Always use full symbol: BTCUSDT (not BTC)
→ Check symbol exists on Binance
→ Use GET /api/binance/ticker/SYMBOL to verify
```

---

## 📈 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         Python Trading Agents                       │
│  (Execution, Monitoring, Analysis, Strategy...)     │
└────────────────┬────────────────────────────────────┘
                 │ HTTP REST Calls
                 ▼
┌─────────────────────────────────────────────────────┐
│    Backend (Spring Boot)                            │
│  ┌─────────────────────────────────────────────┐   │
│  │  BinanceController Routes Requests          │   │
│  │  - /api/binance/*                           │   │
│  └────────────────┬────────────────────────────┘   │
│                   ▼                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │  BinanceApiClient (Binance Connector Java)  │   │
│  │  - Handles authentication                    │   │
│  │  - Manages connections                       │   │
│  │  - Processes orders and data                │   │
│  └────────────────┬────────────────────────────┘   │
└────────────────┬─────────────────────────────────────┘
                 │ REST API v3 / WebSocket
                 ▼
        ┌─────────────────────┐
        │   Binance API       │
        │  - Trading          │
        │  - Market Data      │
        │  - Account Info     │
        └─────────────────────┘
```

---

## 🚀 Next Steps

1. **Setup & Test**
   - [ ] Set API keys
   - [ ] Start backend
   - [ ] Test endpoints
   - [ ] Configure agents

2. **Paper Trading**
   - [ ] Set `paper_trading: True`
   - [ ] Test signal flow
   - [ ] Verify order execution
   - [ ] Check monitoring

3. **Testnet Trading**
   - [ ] Create Binance Testnet account
   - [ ] Get Testnet API keys
   - [ ] Set `BINANCE_TESTNET: true`
   - [ ] Place real (but simulated) orders

4. **Live Trading** ⚠️
   - [ ] Thorough testing on Testnet
   - [ ] Implement risk management
   - [ ] Monitor closely
   - [ ] Small initial trades
   - [ ] Set `BINANCE_TESTNET: false`

---

## 💾 File Locations

```
AIAgentsTrading/
├── backend/
│   ├── BINANCE_API_INTEGRATION.md          ← Full documentation
│   ├── BINANCE_INTEGRATION_SUMMARY.md      ← Summary of changes
│   ├── src/main/java/com/trading/
│   │   ├── controller/BinanceController.java       ← REST endpoints
│   │   └── service/BinanceApiClient.java          ← Binance integration
│   ├── src/main/resources/application.yml ← Configuration
│   └── build.gradle.kts                   ← Dependencies
│
├── agents/
│   ├── execution_agent/execution_agent.py  ← Updated to use backend
│   ├── monitoring_agent/monitoring_agent.py ← Updated to use backend
│   └── requirements.txt
```

---

## 📚 Resources

- **Full Guide**: [BINANCE_API_INTEGRATION.md](./BINANCE_API_INTEGRATION.md)
- **Changes Summary**: [BINANCE_INTEGRATION_SUMMARY.md](./BINANCE_INTEGRATION_SUMMARY.md)
- **Binance API Docs**: https://binance-docs.github.io/apidocs/
- **Binance Connector Java**: https://github.com/binance/binance-connector-java
- **Spring Boot**: https://spring.io/projects/spring-boot
- **Swagger UI**: http://localhost:8080/swagger-ui.html (when backend running)

---

## 💬 Questions?

Check these resources in order:
1. Troubleshooting section above
2. BINANCE_API_INTEGRATION.md
3. Binance API documentation
4. Check backend logs: `./gradlew bootRun` output
5. Check agent logs: agent console output
