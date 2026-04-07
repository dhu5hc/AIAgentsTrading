# 🎯 Framework "Kỷ Luật Tuyệt Đối" - Complete Implementation Guide

**Absolute Discipline Framework for AI Trading System**

---

## 📚 Documentation Files

This implementation includes 4 comprehensive guides:

1. **[DISCIPLINE_FRAMEWORK.md](./DISCIPLINE_FRAMEWORK.md)** - Core concepts and rules
2. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - REST API reference
3. **[CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md)** - Configuration & customization
4. **[discipline_client.py](./discipline_client.py)** - Python client helper

---

## 🚀 Quick Start

### 1. Build the Backend

```bash
cd backend
./gradlew clean build
```

### 2. Run the Application

```bash
# Using Docker
docker-compose up

# Or run directly
java -jar build/libs/trading-orchestrator-1.0.0.jar
```

### 3. Verify API is Running

```bash
curl http://localhost:8080/api/discipline/status/test-trader
```

---

## 🎮 The 4 Rules

### Rule 1: "Không chắc → không trade"
**If uncertain → don't trade**

```
Condition: Confidence < 60%
Action: BLOCK trade immediately
Message: "Bạn chưa đủ tự tin để trade!"
```

### Rule 2: "Không có SL → không trade"
**If no stop loss → don't trade**

```
Condition: Stop Loss is null or 0
Action: BLOCK trade immediately
Message: "Bạn đã đặt SL/TP chưa? Không được trade mà không có SL!"
```

### Rule 3: "Sai → cắt ngay"
**If wrong → exit immediately**

```
Condition: SL too tight/too loose (< 1% or > 10%)
Action: WARN user or BLOCK depending on severity
Message: "SL quá gần! Dễ bị stop out" / "SL quá xa! Risk quá lớn"
```

### Rule 4: "Thua → nghỉ"
**If lost → take a break**

```
Condition: 3 consecutive losses
Action: LOCK account for 30 minutes (auto-break)
Message: "Bạn đang trong kỳ nghỉ! Cần xả stress"
```

---

## 🔄 Full Request/Response Cycle

### Step 1: Analysis Agent Generates Signal

```json
{
  "symbol": "BTC/USDT",
  "type": "BUY",
  "price": 32000,
  "confidence": 0.75,
  "stopLoss": 31000,
  "takeProfit": 33000,
  "positionSize": 1.5
}
```

### Step 2: Validate Against Rules

```bash
POST /api/discipline/validate
```

```json
{
  "signal": { ... },
  "config": {
    "accountId": "trader-001",
    "minConfidenceThreshold": 0.60,
    "maxRiskPerTrade": 0.02,
    "accountBalance": 10000
  }
}
```

### Step 3: Get Validation Result

```json
{
  "isValid": true,
  "violations": [],
  "warnings": [],
  "feedback": "✅ VALIDATION PASSED - Ready to Trade!"
}
```

### Step 4: Execute (if valid)

- Send to Execution Agent via Kafka
- Execute the trade
- Monitor the position

### Step 5: Record Result

When trade closes:

```bash
# If profitable
POST /api/discipline/record-win
{"accountId": "trader-001", "amount": 250.50}

# If loss
POST /api/discipline/record-loss
{"accountId": "trader-001", "amount": 150.00}

# If 3 losses → Auto-break triggered
# Account locked for 30 minutes
```

### Step 6: Check Status

```bash
GET /api/discipline/status/trader-001
```

```json
{
  "sessionStatus": "BREAK",
  "consecutiveLosses": 3,
  "breakEndsAt": "2026-04-07T15:30:00",
  "isInBreak": true,
  "isLocked": false
}
```

---

## 📊 Real-World Scenarios

### Scenario 1: Low Confidence Signal (BLOCKED)

```
Analysis Agent generates signal:
- BTC/USDT BUY at $32,000
- Confidence: 45% (below 60% threshold)
- SL: $31,000, TP: $33,000

System Response:
❌ BLOCKED - "Bạn chưa đủ tự tin để trade!"
Result: Signal REJECTED, no trade executed
```

### Scenario 2: Missing Stop Loss (BLOCKED)

```
Trader tries to place order:
- ETH/USDT SELL at $1,900
- Confidence: 75% ✅
- SL: NOT SET ❌
- TP: $1,850

System Response:
❌ BLOCKED - "Bạn đã đặt SL/TP chưa?"
Result: Order REJECTED, must set SL first
```

### Scenario 3: FOMO Detected (WARNING)

```
Trader places orders rapidly:
- 14:00 - Order 1: BTC BUY ✅
- 14:02 - Order 2: ETH SELL ✅
- 14:04 - Order 3: XRP BUY ✅
- 14:05 - Order 4: ADA SELL ⚠️ FOMO!

System Response:
⚠️ WARNING - "Bạn đang fomo! Quá nhiều lệnh"
Result: Order allowed but warning shown
```

### Scenario 4: Automatic Break (AUTO-LOCKED)

```
Timeline:
15:00 - Trade 1: LOSS -$100 (Consecutive: 1)
15:15 - Trade 2: LOSS -$150 (Consecutive: 2)
15:30 - Trade 3: LOSS -$200 (Consecutive: 3) ⚠️

15:30 - System auto-locks account
        ❌ ACCOUNT ON BREAK until 16:00

15:45 - Trader tries to trade
        Result: ❌ ORDER BLOCKED
        Message: "Account on break until 16:00"

16:00+ - Trader can resume
        POST /api/discipline/resume
        ✅ Account active again
```

---

## 💻 Integration Points

### From Analysis Agent (Python)

```python
from discipline_client import DisciplineClient

client = DisciplineClient("http://localhost:8080/api/discipline")

# Validate before sending to execution
signal = {
    "symbol": "BTC/USDT",
    "type": "BUY",
    "confidence": 0.75,
    ...
}

config = {
    "accountId": "trader-001",
    "minConfidenceThreshold": 0.60,
    ...
}

result = client.validate_trade(signal, config)

if result['isValid']:
    # Send to execution agent
    send_to_kafka(signal)
else:
    # Reject signal
    log_rejection(result['violations'])
```

### From Execution Agent (Kafka Consumer)

```java
@KafkaListener(topics = "execution-orders")
public void handleOrder(TradingSignal signal) {
    // Signal already validated by discipline engine
    
    // Execute order
    Order order = executeOrder(signal);
    
    // Track result
    if (order.isProfitable()) {
        tradingService.recordTradeResult(accountId, profit);
    } else {
        tradingService.recordTradeResult(accountId, -loss);
    }
}
```

### From Monitoring Agent

```python
# Monitor account discipline status
status = client.get_account_status("trader-001")

if status['isInBreak']:
    alert("Account on break - emotional recovery needed")
    
if status['isLocked']:
    alert("Account locked - manual review required")
    
if status['consecutiveLosses'] >= 2:
    warn(f"Warning: {status['consecutiveLosses']} losses - break coming soon")
```

---

## 📈 Metrics & Monitoring

### Key Metrics

```
1. Violation Rate
   - Violations per day
   - Most common violation types
   
2. Break Frequency
   - How often auto-breaks triggered
   - Break duration effectiveness
   
3. Trade Success Rate
   - Win rate (with discipline)
   - ROI improvement
   
4. FOMO Patterns
   - FOMO detection accuracy
   - User behavior changes after warning
```

### Dashboard Queries

```sql
-- Daily violations
SELECT 
  DATE(detected_at) as date,
  violated_rule,
  COUNT(*) as count
FROM rule_violations
WHERE DATE(detected_at) = CURRENT_DATE
GROUP BY DATE(detected_at), violated_rule;

-- Break effectiveness
SELECT
  account_id,
  session_status,
  COUNT(*) as count,
  AVG(daily_profit_loss) as avg_daily_pl
FROM trading_discipline_config
GROUP BY account_id, session_status;

-- Consecutive losses distribution
SELECT
  current_consecutive_losses,
  COUNT(*) as accounts
FROM trading_discipline_config
GROUP BY current_consecutive_losses
ORDER BY current_consecutive_losses DESC;
```

---

## 🔧 Configuration by Trader Type

### Day Trader

```yaml
minConfidenceThreshold: 0.55        # Lower - more opportunities
maxRiskPerTrade: 0.03               # Higher - multiple trades
minStopLossPercentage: 0.005        # Tight SL for scalping
maxStopLossPercentage: 0.05         # Loose SL limit
fomoDetectionWindowSeconds: 60      # Short window
```

### Swing Trader

```yaml
minConfidenceThreshold: 0.70        # Higher - fewer trades
maxRiskPerTrade: 0.02               # Standard risk
minStopLossPercentage: 0.02         # Normal SL
maxStopLossPercentage: 0.10         # Higher upper limit
fomoDetectionWindowSeconds: 300     # Normal window
```

### Conservative Trader

```yaml
minConfidenceThreshold: 0.80        # Very high
maxRiskPerTrade: 0.01               # Very low risk
minStopLossPercentage: 0.015        # Tight SL
maxStopLossPercentage: 0.05         # Strict upper limit
fomoDetectionWindowSeconds: 600     # Long window
```

---

## 🐳 Docker Deployment

### docker-compose.yml Integration

```yaml
orchestrator:
  environment:
    DISCIPLINE_MIN_CONFIDENCE: 0.60
    DISCIPLINE_STOP_LOSS_REQUIRED: "true"
    DISCIPLINE_MAX_RISK_PER_TRADE: 0.02
    DISCIPLINE_FOMO_THRESHOLD: 0.70
    DISCIPLINE_CONSECUTIVE_LOSSES: 3
  ports:
    - "8080:8080"
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: discipline-config
data:
  minConfidenceThreshold: "0.60"
  stopLossRequired: "true"
  maxRiskPerTrade: "0.02"
  
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  template:
    spec:
      containers:
      - name: orchestrator
        envFrom:
        - configMapRef:
            name: discipline-config
```

---

## ✅ Validation Checklist

- [x] **Core Models Created**
  - [x] DisciplineRule enum
  - [x] TradingDisciplineConfig entity
  - [x] RuleViolation entity

- [x] **Rule Engine Implemented**
  - [x] DisciplineRuleEngine service
  - [x] ValidationResult model
  - [x] RuleViolationAlert model

- [x] **REST APIs Created**
  - [x] POST /validate
  - [x] GET /status
  - [x] POST /record-win
  - [x] POST /record-loss
  - [x] POST /break
  - [x] POST /resume
  - [x] POST /lock
  - [x] GET /report

- [x] **TradingService Integration**
  - [x] Injected DisciplineRuleEngine
  - [x] Updated approveSignal with validation
  - [x] Added recordTradeResult helper
  - [x] Added getDisciplineStatus helper

- [x] **Python Client**
  - [x] DisciplineClient class
  - [x] DisciplineValidator helper
  - [x] Example usage

- [x] **Documentation**
  - [x] Framework overview
  - [x] API documentation
  - [x] Configuration guide
  - [x] Integration examples

---

## 📝 Next Steps

1. **Database Setup**
   - Create repositories for entities
   - Implement JPA queries
   - Set up migrations

2. **Real-time Alerts**
   - WebSocket for live violations
   - Email/SMS notific notifications
   - Dashboard updates

3. **Advanced FOMO Detection**
   - Machine learning models
   - Pattern recognition
   - Behavioral analytics

4. **Trader Dashboard**
   - Account statistics
   - Violation history
   - Performance tracking

5. **Agent Integration**
   - Update Analysis Agent to use client
   - Update Execution Agent to record results
   - Update Strategy Agent to follow rules

---

## 🎓 Training Traders

### Onboarding Flow

```
1. Start with CONSERVATIVE profile
   - High confidence threshold (0.70+)
   - Low risk limits (1-2% per trade)
   - Frequent breaks

2. Monitor performance
   - Track violation rate
   - Analyze break patterns
   - Review P&L

3. Gradually increase difficulty
   - Lower confidence requirement
   - Increase risk limits
   - Extend break periods

4. Customize to trading style
   - Scalper: Short windows, high orders
   - Swing: Normal settings
   - Long-term: High thresholds
```

---

## 🆘 Troubleshooting

### Account Locked - How to Unlock?

```
1. Check reason: GET /api/discipline/status/{accountId}
2. Review violations: GET /api/discipline/report/{accountId}
3. Manual unlock: POST /api/discipline/lock (admin only)
4. Or wait for auto-recovery (1 hour)
```

### Why is my signal blocked?

```
Reasons:
1. Confidence too low (< 60%) → Wait for higher-confidence signal
2. No SL set → Set stop loss before retry
3. Risk too high → Reduce position size
4. On break period → Wait 30 minutes, then resume
5. Account locked → Contact admin
```

### FOMO warning - what to do?

```
1. STOP placing orders immediately
2. Step away from keyboard
3. Review recent trades
4. Wait 5+ minutes before next trade
5. Resume when calm and focused
```

---

## 📞 Support

For issues or questions:

1. Check DISCIPLINE_FRAMEWORK.md for concepts
2. Check API_DOCUMENTATION.md for endpoints
3. Check CONFIGURATION_GUIDE.md for settings
4. Check discipline_client.py for Python examples
5. Review server logs for detailed errors

---

## 📊 Sample Configuration Files

### For Testing

```bash
# Test with loose rules
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d @test_loose_rules.json

# Test with strict rules
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d @test_strict_rules.json
```

---

## 🎯 Success Metrics

After implementing Kỷ Luật Tuyệt Đối:

✅ **Expected Improvements**
- ✓ Reduced FOMO-driven losses (30-50% reduction)
- ✓ Consistent stop loss adherence (99%+)
- ✓ Better emotional control (measurable)
- ✓ Higher win rate (10-15% improvement)
- ✓ Better daily risk management (< 5% daily loss)

---

## 📚 References

- Trading Psychology: "Thinking, Fast and Slow" by Daniel Kahneman
- Risk Management: "The Disciplined Trader" by Mark Douglas
- Behavioral Finance: "Behavioral Finance and Wealth Management"

---

**Built with ❤️ for Disciplined Traders**

*Remember: "Discipline is doing what you hate to do, but nonetheless doing it like you love it." - Mike Tyson*
