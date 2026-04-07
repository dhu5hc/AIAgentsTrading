# KAFKA vs ORCHESTRATOR - QUICK REFERENCE GUIDE

## TL;DR - One Sentence Each

| Component | Purpose | Use When |
|-----------|---------|----------|
| **KAFKA** | Async event streaming between agents | Broadcasting data, fire-and-forget, high frequency |
| **ORCHESTRATOR** | Sync API for validation & rules | Blocking decision, state change, database update |

---

## The Mental Model

```
KAFKA         = Nervous System (signals flowing)
ORCHESTRATOR  = Brain (decision making)
```

- **Kafka**: "Hey everyone, market price changed!"
- **Orchestrator**: "Wait, is it OK to trade right now?"
- **Kafka**: "OK, order executed, publishing result"
- **Orchestrator**: "Recorded. Account state updated."

---

## Quick Decision Guide

### Use KAFKA when:
- ✅ Broadcasting data to multiple subscribers
- ✅ Fire-and-forget notifications OK
- ✅ High-frequency streaming (market data)
- ✅ Agents don't need to wait for confirmation
- ✅ Order doesn't matter much (happened already)
- ✅ Historical replay might be useful

### Use REST API (Orchestrator) when:
- ✅ Need immediate sync response
- ✅ Must block if conditions aren't met
- ✅ Updating centralized state (account, balance)
- ✅ Business rules enforcement
- ✅ Database persistence required
- ✅ Audit trail / compliance needed

---

## Execution Agent Flow (Actual Code)

```python
# STEP 1: Listen to Kafka (async)
for signal in kafka_consumer.consume('trading-signals'):
    
    # STEP 2: Validate with Orchestrator (sync)
    validation = requests.post(
        'http://orchestrator:8080/api/discipline/validate',
        json={'signal': signal, 'config': config}
    )
    
    if not validation['isValid']:
        # Block the trade
        continue
    
    # STEP 3: Execute trade
    order = place_order(signal)
    
    # STEP 4: Record in Orchestrator (sync)
    requests.post(
        'http://orchestrator:8080/api/discipline/record-win',
        json={'accountId': account, 'amount': profit}
    )
    
    # STEP 5: Publish result to Kafka (async)
    kafka_producer.send('execution-results', order)
```

---

## Network Calls Cheat Sheet

### Kafka (Topic-based, Async)
```python
# PUBLISH (Agent → Topic)
producer.send('topic-name', message)

# CONSUME (Topic → Agent)
for msg in consumer:
    handle(msg)

# Topics in trading system:
market-data              # Data Agent publishes
analysis-results         # Analysis Agent publishes
trading-signals          # Strategy Agent publishes
execution-results        # Execution Agent publishes
```

### REST API (Request-Response, Sync)
```python
# VALIDATE BEFORE TRADING
response = requests.post(
    '/api/discipline/validate',
    json={'signal': signal, 'config': config}
)
# Response: {"isValid": true/false, "violations": [...]}

# CHECK ACCOUNT STATUS
status = requests.get(
    '/api/discipline/status/user_123'
)
# Response: {"isLocked": false, "dailyPnL": 100, ...}

# RECORD RESULT
response = requests.post(
    '/api/discipline/record-win',
    json={'accountId': 'user_123', 'amount': 125.50}
)
# Response: {"status": "recorded"}
```

---

## Characteristics Comparison

| Aspect | Kafka | Orchestrator |
|--------|-------|------|
| **Communication** | Async (fire-and-forget) | Sync (request-response) |
| **Latency** | ~100-200ms | ~10-50ms |
| **Throughput** | Millions/sec | 1K-10K/sec |
| **Coupling** | Loose | Tight (by design) |
| **State** | Stateless | Stateful (DB) |
| **Persistence** | 7-30 days | Permanent (DB) |
| **Failure Mode** | Message loss | Clear error response |
| **Use For** | Data flow | Business logic |

---

## Layered Architecture

```
┌────────────────────────────────────┐
│   ORCHESTRATOR LAYER               │
│   (Control, validation, rules)      │
│   - Discipline engine               │
│   - Account state machine           │
│   - Database persistence            │
└────────┬──────────────┬─────────────┘
         │ REST API     │
         │ (sync)       │
┌────────▼──────────────▼─────────────┐
│   AGENT LAYER                       │
│   (Business logic)                  │
│   - Data, Analysis, Strategy, Exec  │
└────────┬────────────────────────────┘
         │ Kafka
         │ (async)
│        
└────────▼──────────────────────────────┐
         │   INFRASTRUCTURE LAYER       │
         │   - Kafka (messaging)        │
         │   - Redis (cache)            │
         │   - PostgreSQL (persistence) │
         │   - Binance (exchange)       │
         └─────────────────────────────┘
```

---

## Real Example: Execute Trade

```
t=0ms   Strategy Agent generates signal
        └─ Publish to Kafka 'trading-signals'

t=100ms Execution Agent receives from Kafka
        └─ signal = {symbol: BTCUSDT, qty: 0.5, price: 45000, SL: 44000, TP: 46000}

t=120ms Execution Agent calls Orchestrator (sync REST)
        ├─ POST /api/discipline/validate
        ├─ Checks: SL set? TP set? Position size? Daily loss?
        └─ Response: {"isValid": true}

t=150ms Start executing order on Binance
        ├─ Place main order: BUY 0.5 @ 45000
        ├─ Place SL: SELL 0.5 @ 44000
        └─ Place TP: SELL 0.5 @ 46000

t=200ms Order filled
        └─ Got: filled_price=44999, commission=2.25

t=220ms Call Orchestrator to record (sync REST)
        ├─ POST /api/discipline/record-win
        ├─ Amount: 125.50 profit
        └─ Response: {"status": "recorded"}

t=240ms Publish result to Kafka
        ├─ 'execution-results' topic
        ├─ Monitoring Agent gets it → update portfolio
        ├─ Risk Agent gets it → check correlation
        └─ Strategy Agent gets it → adjust next signal

✅ Total: ~240ms, compliant, trackable!
```

---

## Decision Tree (Actual Usage)

```
Question: Should I use Kafka or Orchestrator?

1. Is this HIGH-FREQUENCY data? (market ticks, prices)
   └─ YES → KAFKA ✓
   └─ NO → Continue

2. Do I need IMMEDIATE validation before acting?
   └─ YES → ORCHESTRATOR ✓
   └─ NO → Continue

3. Does this change CENTRAL STATE? (account balance, locked status)
   └─ YES → ORCHESTRATOR ✓
   └─ NO → Continue

4. Will MULTIPLE services care about this?
   └─ YES → KAFKA ✓
   └─ NO → Could be either

DEFAULT: Use BOTH
├─ Kafka for transport (scalable)
└─ REST for validation (correct)
```

---

## Failure Handling

### If Kafka Fails
- Message might be lost (but retry happens)
- Subscriber might miss update
- **Action**: Republish to Kafka, or query state from Orchestrator

### If Orchestrator Fails
- REST calls fail (connection refused, timeout)
- **Action**: Reject trade (safe default), alert monitoring, retry

### If both work but disagreement
- Kafka says "traded" but Orchestrator says "invalid"
- **Solution**: Orchestrator is source of truth (it has database)

---

## Orchestrator Endpoints Cheat Sheet

```bash
# Validate a signal BEFORE executing
POST http://orchestrator:8080/api/discipline/validate
Body: {
  "signal": {
    "symbol": "BTCUSDT",
    "type": "BUY",
    "quantity": 0.5,
    "price": 45000,
    "stopLoss": 44000,
    "takeProfit": 46000
  },
  "config": {
    "accountId": "user_123",
    "maxDailyLoss": -100,
    "maxPositionRiskPercent": 2
  }
}

# Check if account is locked
GET http://orchestrator:8080/api/discipline/status/user_123

# Record a winning trade
POST http://orchestrator:8080/api/discipline/record-win
Body: {"accountId": "user_123", "amount": 125.50}

# Record a losing trade
POST http://orchestrator:8080/api/discipline/record-loss
Body: {"accountId": "user_123", "amount": 50.00}

# Get account balance from Binance
GET http://orchestrator:8080/api/binance/account
```

---

## Environment Configuration

```yaml
# docker-compose.yml
services:
  kafka:
    # Message broker - agents communicate here
    # Topics: market-data, analysis-results, trading-signals, execution-results
    KAFKA_BOOTSTRAP_SERVERS: kafka:29092
  
  orchestrator:
    # REST API + Business logic
    # Validates trades, enforces rules, persists state
    SPRING_PROFILES_ACTIVE: docker
    KAFKA_BOOTSTRAP_SERVERS: kafka:29092  # Can consume Kafka too
    SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/trading_db
  
  execution-agent:
    # Consumes from Kafka, validates with REST, executes
    KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    ORCHESTRATOR_URL: http://orchestrator:8080
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| Trade rejected but unclear why | Orchestrator validation failed | Check `/api/discipline/validate` response for violations |
| Order executed but not recorded | REST call to Orchestrator failed | Retry POST `/api/discipline/record-win` |
| Other agents don't see my result | Kafka publish failed | Check Kafka connectivity |
| Orchestrator reports "account locked" | Rules enforced (intentional) | Check daily P&L, violations, account status |
| High latency (>1 second) | REST API slow or network issue | Check Orchestrator logs, network latency |
| Duplicate trades | Kafka consumer retried | Ensure  idempotent order IDs |

---

## Pro Tips

1. **Always validate with Orchestrator BEFORE executing**
   - Don't trust Kafka for critical decisions
   - REST API is the gatekeeper

2. **Treat Orchestrator as single source of truth**
   - If Orchestrator says "invalid", it IS invalid
   - Database is the real state

3. **Use Kafka for notifications, not decisions**
   - Monitoring can react to Kafka
   - Trading logic must check Orchestrator first

4. **Cache Orchestrator responses locally if needed**
   - Reduce REST calls
   - Fall back to cache on Orchestrator failure

5. **Always handle both success and failure**
   - Kafka: async, so fire-and-forget
   - REST: sync, so check response always

---

## Summary Table

```
╔═══════════════════════════════════════════════════════════╗
║                   KAFKA vs ORCHESTRATOR                  ║
╠═════════════════════════╤═════════════════════════════════╣
║ Kafka                   │ Orchestrator                    ║
├─────────────────────────┼─────────────────────────────────┤
║ Connection: Events      │ Connection: API endpoints       ║
║ Pattern: Pub-Sub        │ Pattern: Request-Response       ║
║ Timing: Async (OK slow) │ Timing: Sync (block if fail)   ║
║ State: Stateless        │ State: Stateful (DB)           ║
║ Used By: All agents     │ Used By: Execution carefully   ║
║                         │                                │
║ Topic-based:            │ Endpoint-based:                │
║  market-data            │  POST /validate                │
║  analysis-results       │  GET /status                   │
║  trading-signals        │  POST /record-win              │
║  execution-results      │  POST /record-loss             │
║                         │  GET /account                  │
╚═════════════════════════╧═════════════════════════════════╝

BEST PRACTICE: Use both!
  Kafka = Transport layer (agents talking)
  Orchestrator = Control layer (rules, validation)
```

