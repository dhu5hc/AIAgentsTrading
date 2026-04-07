# ⚙️ Configuration Guide - Kỷ Luật Tuyệt Đối Framework

## Quick Reference

| Setting | Default | Min | Max | Notes |
|---------|---------|-----|-----|-------|
| **Confidence** |  |  |  | |
| `minConfidenceThreshold` | 0.60 | 0.30 | 1.00 | Rule 1: No trade if < threshold |
| **Stop Loss** |  |  |  | |
| `stopLossRequired` | true | - | - | Rule 2: Must always set SL |
| `minStopLossPercentage` | 0.01 | 0.005 | 0.05 | Minimum 1% from entry (avoid tight) |
| `maxStopLossPercentage` | 0.10 | 0.05 | 0.50 | Maximum 10% from entry (avoid loose) |
| **Risk Management** |  |  |  | |
| `maxRiskPerTrade` | 0.02 | 0.01 | 0.10 | Risk per trade = 2% of account |
| `maxDailyRisk` | 0.05 | 0.02 | 0.20 | Max daily loss = 5% of account |
| `accountBalance` | 10000 | - | - | Current account balance |
| **FOMO Detection** |  |  |  | |
| `maxOrdersInPeriod` | 3 | 1 | 10 | Max 3 orders in window |
| `fomoDetectionWindowSeconds` | 300 | 60 | 3600 | 5-minute window |
| `fomoThreshold` | 0.70 | 0.50 | 1.00 | Alert if FOMO > 70% |
| **Break Rules** |  |  |  | |
| `consecutiveLossesTriggerBreak` | 3 | 1 | 10 | After 3 losses → auto-break |

---

## Configuration Files

### 1. application.yml

```yaml
spring:
  application:
    name: ai-trading-orchestrator

# ============ DISCIPLINE FRAMEWORK CONFIG ============
trading:
  discipline:
    # Rule 1: Confidence Requirement
    minConfidenceThreshold: 0.60
    
    # Rule 2 & 3: Stop Loss Configuration
    stopLossRequired: true
    minStopLossPercentage: 0.01      # 1% minimum SL distance
    maxStopLossPercentage: 0.10      # 10% maximum SL distance
    
    # Rule 3 & 4: Risk Management
    maxRiskPerTrade: 0.02            # 2% risk per trade
    maxDailyRisk: 0.05               # 5% risk per day
    accountBalance: 10000.0
    
    # FOMO Detection (Pre-Rule 1)
    fomoDetectionWindowSeconds: 300  # 5 minutes
    maxOrdersInPeriod: 3
    fomoThreshold: 0.70              # 70% likelihood
    
    # Rule 4: Break After Loss
    consecutiveLossesTriggerBreak: 3
    breakDurationMinutes: 30
```

### 2. discipline-config.properties

```properties
# ===== CONFIDENCE RULES =====
discipline.minConfidenceThreshold=0.60

# ===== STOP LOSS RULES =====
discipline.stopLossRequired=true
discipline.minStopLossPercentage=0.01
discipline.maxStopLossPercentage=0.10

# ===== RISK MANAGEMENT =====
discipline.maxRiskPerTrade=0.02
discipline.maxDailyRisk=0.05
discipline.accountBalance=10000.0

# ===== FOMO DETECTION =====
discipline.fomoDetectionWindowSeconds=300
discipline.maxOrdersInPeriod=3
discipline.fomoThreshold=0.70

# ===== BREAK SETTINGS =====
discipline.consecutiveLossesTriggerBreak=3
discipline.breakDurationMinutes=30
```

---

## Trader Profiles

### Conservative Trader (Risk-Averse)

```yaml
discipline:
  minConfidenceThreshold: 0.75          # Require 75% confidence
  maxRiskPerTrade: 0.01                 # 1% risk per trade (tight)
  maxDailyRisk: 0.03                    # 3% daily limit (tight)
  minStopLossPercentage: 0.015          # At least 1.5% SL
  maxStopLossPercentage: 0.05           # Max 5% SL
  fomoThreshold: 0.60                   # Low FOMO tolerance
  consecutiveLossesTriggerBreak: 2      # Break after 2 losses
```

### Moderate Trader (Balanced)

```yaml
discipline:
  minConfidenceThreshold: 0.60          # Standard 60%
  maxRiskPerTrade: 0.02                 # 2% risk per trade
  maxDailyRisk: 0.05                    # 5% daily limit
  minStopLossPercentage: 0.01           # 1% minimum SL
  maxStopLossPercentage: 0.10           # 10% maximum SL
  fomoThreshold: 0.70                   # Standard FOMO threshold
  consecutiveLossesTriggerBreak: 3      # Break after 3 losses
```

### Aggressive Trader (Risk-Seeking)

```yaml
discipline:
  minConfidenceThreshold: 0.50          # Lower confidence requirement
  maxRiskPerTrade: 0.05                 # 5% risk per trade (loose)
  maxDailyRisk: 0.10                    # 10% daily limit (loose)
  minStopLossPercentage: 0.005          # 0.5% minimum SL
  maxStopLossPercentage: 0.20           # 20% maximum SL
  fomoThreshold: 0.85                   # High FOMO tolerance
  consecutiveLossesTriggerBreak: 5      # Break after 5 losses
```

---

## Environment Variables

```bash
# Set in Docker container or system environment

# Discipline Rules
export DISCIPLINE_MIN_CONFIDENCE=0.60
export DISCIPLINE_STOP_LOSS_REQUIRED=true
export DISCIPLINE_MIN_SL_PCT=0.01
export DISCIPLINE_MAX_SL_PCT=0.10

# Risk Management
export DISCIPLINE_MAX_RISK_PER_TRADE=0.02
export DISCIPLINE_MAX_DAILY_RISK=0.05
export DISCIPLINE_ACCOUNT_BALANCE=10000

# FOMO Detection
export DISCIPLINE_FOMO_WINDOW_SECONDS=300
export DISCIPLINE_MAX_ORDERS_IN_PERIOD=3
export DISCIPLINE_FOMO_THRESHOLD=0.70

# Break Settings
export DISCIPLINE_CONSECUTIVE_LOSSES=3
export DISCIPLINE_BREAK_DURATION_MINUTES=30
```

---

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  trading-orchestrator:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      # Discipline Framework
      DISCIPLINE_MIN_CONFIDENCE: 0.60
      DISCIPLINE_STOP_LOSS_REQUIRED: "true"
      DISCIPLINE_MIN_SL_PCT: 0.01
      DISCIPLINE_MAX_SL_PCT: 0.10
      DISCIPLINE_MAX_RISK_PER_TRADE: 0.02
      DISCIPLINE_MAX_DAILY_RISK: 0.05
      DISCIPLINE_ACCOUNT_BALANCE: 10000
      DISCIPLINE_FOMO_WINDOW_SECONDS: 300
      DISCIPLINE_MAX_ORDERS_IN_PERIOD: 3
      DISCIPLINE_FOMO_THRESHOLD: 0.70
      DISCIPLINE_CONSECUTIVE_LOSSES: 3
      DISCIPLINE_BREAK_DURATION_MINUTES: 30
      
      # Database
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/trading_db
      SPRING_DATASOURCE_USERNAME: trading_user
      SPRING_DATASOURCE_PASSWORD: trading_pass
      
      # Kafka
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      
      # Redis
      REDIS_HOST: redis
      REDIS_PORT: 6379
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - kafka
      - redis
```

---

## Per-Account Configuration

Each trader can have custom configuration:

```sql
INSERT INTO trading_discipline_config (
  account_id,
  min_confidence_threshold,
  stop_loss_required,
  min_stop_loss_percentage,
  max_stop_loss_percentage,
  max_risk_per_trade,
  max_daily_risk,
  account_balance,
  max_orders_in_period,
  fomo_detection_window_seconds,
  fomo_threshold,
  consecutive_losses_trigger_break,
  created_at,
  updated_at
) VALUES (
  'trader-aggressive-001',
  0.50,
  true,
  0.005,
  0.20,
  0.05,
  0.10,
  50000.0,
  5,
  300,
  0.85,
  5,
  NOW(),
  NOW()
);
```

---

## Testing Different Configs

### Test Scenario 1: Rule 1 Violation

```bash
# Setup: minConfidenceThreshold = 0.60

curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "BTC/USDT",
      "type": "BUY",
      "confidence": 0.45,
      "stopLoss": 31000,
      "price": 32000
    },
    "config": {
      "minConfidenceThreshold": 0.60
    }
  }'

# Expected: isValid=false, violation=CONFIDENCE_CHECK
```

### Test Scenario 2: Rule 2 Violation

```bash
# Setup: stopLossRequired = true

curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "ETH/USDT",
      "type": "SELL",
      "confidence": 0.80,
      "stopLoss": null,
      "price": 1900
    },
    "config": {
      "stopLossRequired": true
    }
  }'

# Expected: isValid=false, violation=STOP_LOSS_REQUIRED
```

### Test Scenario 3: Rule 4 & Break

```bash
# Record 3 consecutive losses

curl -X POST http://localhost:8080/api/discipline/record-loss \
  -d '{"accountId": "test-trader", "amount": 100}'

curl -X POST http://localhost:8080/api/discipline/record-loss \
  -d '{"accountId": "test-trader", "amount": 150}'

curl -X POST http://localhost:8080/api/discipline/record-loss \
  -d '{"accountId": "test-trader", "amount": 200}'

# Check status
curl -X GET http://localhost:8080/api/discipline/status/test-trader

# Expected: sessionStatus=BREAK, isInBreak=true
```

---

## Deployment Checklist

- [ ] Set `minConfidenceThreshold` to appropriate level (default: 0.60)
- [ ] Ensure `stopLossRequired = true` (mandatory for risk management)
- [ ] Configure `maxRiskPerTrade` based on account size
- [ ] Set `maxDailyRisk` to limit daily losses
- [ ] Adjust FOMO detection for trading style
- [ ] Set `consecutiveLossesTriggerBreak` (default: 3)
- [ ] Configure database for rule_violations tracking
- [ ] Set up Redis for real-time break/lock status
- [ ] Configure alerts/notifications for violations
- [ ] Test with conservative profile first
- [ ] Gradually increase risk tolerance as traders gain experience

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Daily Violation Rate**
   - How many violations per day?
   - Which rules violated most?

2. **Break Frequency**
   - How often do traders trigger auto-breaks?
   - Are breaks helping?

3. **Win Rate**
   - Are disciplined traders more profitable?
   - ROI improvement?

4. **FOMO Incidents**
   - How often is FOMO detected?
   - Is FOMO warning effective?

### Alert Examples

```
🚨 High Violation Alert
- Account: trader-001
- Violations today: 12
- Most common: FOMO (7 times)
- Recommendation: Increase minConfidenceThreshold

⏸️ Break Initiated
- Account: trader-002
- Consecutive losses: 3
- Break until: 2026-04-07 16:00
- Reason: Rule 4 Compliance

🔒 Account Locked
- Account: trader-003
- Reason: 5 critical violations in 1 hour
- Action: Manual review required
```

---

## Customization Examples

### For Scalpers (Fast Trading)

```yaml
discipline:
  minConfidenceThreshold: 0.55
  maxRiskPerTrade: 0.015              # Smaller risk per trade
  maxDailyRisk: 0.08
  minStopLossPercentage: 0.003        # Tight SL for scalps
  maxStopLossPercentage: 0.05
  fomoDetectionWindowSeconds: 120     # Shorter window (2 min)
  maxOrdersInPeriod: 10               # Allow more orders
  consecutiveLossesTriggerBreak: 5    # More losses allowed
```

### For Swing Traders (Slower Trading)

```yaml
discipline:
  minConfidenceThreshold: 0.70
  maxRiskPerTrade: 0.03               # Larger risk per trade
  maxDailyRisk: 0.08
  minStopLossPercentage: 0.02
  maxStopLossPercentage: 0.15
  fomoDetectionWindowSeconds: 900     # Longer window (15 min)
  maxOrdersInPeriod: 2                # Few orders
  consecutiveLossesTriggerBreak: 2    # Fewer losses allowed
```

