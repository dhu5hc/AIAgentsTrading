# 🎯 Framework "Kỷ Luật Tuyệt Đối" (Absolute Discipline Framework)

## Tổng Quan

Hệ thống Rule Engine được xây dựng để thực thi **4 quy tắc cơ bản của giao dịch có kỷ luật**:

```
1. "Không chắc → không trade"       → Confidence Check
2. "Không có SL → không trade"      → Stop Loss Required  
3. "Sai → cắt ngay"                 → Quick Exit on Loss
4. "Thua → nghỉ"                    → Break After Losses
```

---

## 🏗️ Kiến Trúc Hệ Thống

### Core Components

#### 1. **DisciplineRule Enum**
- Định nghĩa 4 quy tắc cơ bản
- Năm các mô tả bằng tiếng Việt

```java
DisciplineRule.CONFIDENCE_CHECK         // Không chắc → không trade
DisciplineRule.STOP_LOSS_REQUIRED       // Không có SL → không trade  
DisciplineRule.QUICK_EXIT_ON_LOSS       // Sai → cắt ngay
DisciplineRule.BREAK_AFTER_LOSS         // Thua → nghỉ
```

#### 2. **TradingDisciplineConfig**
Cấu hình các giới hạn rủi ro và ngưỡng cho tài khoản:

| Tham số | Default | Ý nghĩa |
|---------|---------|---------|
| `minConfidenceThreshold` | 0.60 (60%) | Độ tự tin tối thiểu |
| `stopLossRequired` | true | Bắt buộc phải set SL |
| `minStopLossPercentage` | 0.01 (1%) | SL tối thiểu cách entry |
| `maxStopLossPercentage` | 0.10 (10%) | SL tối đa cách entry |
| `maxRiskPerTrade` | 0.02 (2%) | Rủi ro tối đa mỗi lệnh |
| `maxDailyRisk` | 0.05 (5%) | Rủi ro tối đa mỗi ngày |
| `fomoThreshold` | 0.70 (70%) | Ngưỡng phát hiện FOMO |
| `consecutiveLossesTriggerBreak` | 3 | Số lệnh thua liên tiếp |

#### 3. **DisciplineRuleEngine**
Engine chính validate tất cả các rule:

```java
ValidationResult validateTrade(TradingSignal signal, TradingDisciplineConfig config)
```

**Quy trình kiểm tra:**
1. ✅ **Confidence Check** - Đủ tự tin không?
2. ✅ **Stop Loss Check** - Đã set SL chưa?
3. ✅ **SL Validity** - SL hợp lý không? (không quá tight/loose)
4. ✅ **Risk Limits** - Rủi ro trong giới hạn không?
5. ✅ **FOMO Detection** - Đang bị FOMO không?
6. ✅ **Account Status** - Account còn active không?

#### 4. **RuleViolation Model**
Lưu trữ mọi lần vi phạm:

```java
@Entity
public class RuleViolation {
    private DisciplineRule violatedRule;
    private ViolationSeverity severity;      // LOW, MEDIUM, HIGH, CRITICAL
    private ViolationStatus status;          // WARNED, PREVENTED, LOCKED
    private String violationMessage;
    private String violationData;           // JSON data
}
```

**Severity Levels:**
- `LOW` - Cảnh báo nhẹ
- `MEDIUM` - Cảnh báo trung bình  
- `HIGH` - Cảnh báo nguy hiểm
- `CRITICAL` - Ngăn chặn ngay lập tức

**Status:**
- `WARNED` - Đã cảnh báo, chờ user xác nhận
- `PREVENTED` - Đã ngăn chặn lệnh
- `LOCKED` - Account bị khoá

---

## ⚠️ Cảnh Báo & Ngăn Chặn

### Cảnh Báo (Warnings)

Hệ thống sẽ **cảnh báo** nhưng vẫn cho phép trade nếu user xác nhận:

```
⚠️ CONFIDENCE CHECK FAILED
Confidence: 45.0% < Required: 60.0%
→ User có thể vẫn trade nhưng phải xác nhận

⚠️ FOMO DETECTED  
Orders in last 5 min: 5 | FOMO Score: 85%
→ Cảnh báo bị FOMO, nên dừng lại

⚠️ STOP LOSS TOO TIGHT
SL: 0.50% < Minimum: 1.00%
→ SL quá gần, dễ bị stop out bởi noise
```

### Ngăn Chặn (Blocks)

Hệ thống sẽ **ngăn chặn** trade nếu vi phạm quy tắc cơ bản:

```
❌ STOP LOSS MISSING
No SL set!
→ KHÔNG ĐƯỢC TRADE - Bắt buộc phải set SL

❌ RISK PER TRADE EXCEEDED
Risk: 3.50% > Max: 2.00% | Amount: $350
→ KHÔNG ĐƯỢC TRADE - Vượt quá risk limit

❌ ACCOUNT ON BREAK
Break continues until: 2026-04-07 15:30:00
→ KHÔNG ĐƯỢC TRADE - Đang trong kỳ nghỉ

❌ ACCOUNT LOCKED
Reason: Consecutive losses (Rule 4: Thua → nghỉ)
→ KHÔNG ĐƯỢC TRADE - Account bị khoá
```

---

## 📊 Cách Hoạt Động Chi Tiết

### 1. Confidence Check (Không chắc → không trade)

```java
if (confidence < minConfidenceThreshold) {
    // BLOCK: Không đủ tự tin
    violation(DisciplineRule.CONFIDENCE_CHECK, CRITICAL);
}
```

**Khi nào trigger:**
- Confidence < 60%
- Signal từ strategy không đủ chắc chắn

**Hành động:**
- ❌ BLOCK trade
- Thông báo: "Bạn chưa đủ tự tin để trade!"

---

### 2. Stop Loss Required (Không có SL → không trade)

```java
if (stopLoss == null || stopLoss == 0.0) {
    // BLOCK: Chưa set SL
    violation(DisciplineRule.STOP_LOSS_REQUIRED, CRITICAL);
}
```

**Khi nào trigger:**
- Stop Loss = null hoặc 0
- User quên set SL

**Hành động:**
- ❌ BLOCK trade
- Thông báo: "Bạn đã đặt SL/TP chưa?"

---

### 3. Stop Loss Validity (Sai → cắt ngay)

```java
double slDistance = Math.abs(price - stopLoss) / price;

if (slDistance < minSL) {
    // WARN: SL quá gần
    warning("SL quá tight, dễ bị stop out");
}

if (slDistance > maxSL) {
    // WARN: SL quá xa
    warning("Risk quá lớn cho một lệnh");
}
```

**Khi nào trigger:**
- SL < 1% cách entry (quá tight)
- SL > 10% cách entry (quá loose)

**Hành động:**
- ⚠️ WARN user
- Cho phép trade nhưng hiển thị cảnh báo

---

### 4. Risk Limits (Rủi ro vượt quá)

```java
double riskAmount = positionSize * Math.abs(price - stopLoss);
double riskPercentage = riskAmount / accountBalance;

if (riskPercentage > maxRiskPerTrade) {
    // BLOCK: Risk quá lớn
    violation("Risk: 3.5% > Max: 2.0%", CRITICAL);
}

if (dailyRisk + riskPercentage > maxDailyRisk) {
    // WARN: Daily risk nearly exhausted
    warning("Daily risk sắp hết");
}
```

**Khi nào trigger:**
- Risk per trade > 2%
- Daily risk > 5%

**Hành động:**
- ❌ BLOCK nếu vượt per-trade limit
- ⚠️ WARN nếu gần hết daily limit

---

### 5. FOMO Detection (Bạn đang fomo)

```java
// Count orders in last 5 minutes
long recentOrders = countOrdersInLast(Duration.ofMinutes(5));
double fomoLikelihood = recentOrders / maxOrdersInPeriod;

if (fomoLikelihood > fomoThreshold) {
    // WARN: FOMO detected
    warning("Bạn đang fomo! " + recentOrders + " lệnh trong 5 phút");
}
```

**Khi nào trigger:**
- > 3 lệnh trong 5 phút
- FOMO score > 70%

**Hành động:**
- ⚠️ WARN user
- "Bạn đang fomo! Quá nhiều lệnh trong thời gian ngắn"

---

### 6. Thua → Nghỉ (Break After Losses)

```java
// Record loss
consecutiveLosses++;
dailyProfitLoss -= lossAmount;

if (consecutiveLosses >= 3) {
    // Initiate 30-minute break
    sessionStatus = BREAK;
    breakEndsAt = now().plusMinutes(30);
}

// Prevent trading during break
if (sessionStatus == BREAK && now().isBefore(breakEndsAt)) {
    violation("Account on break until: " + breakEndsAt, CRITICAL);
}
```

**Khi nào trigger:**
- 3 lệnh thua liên tiếp
- Hệ thống sẽ tự động ban trading

**Hành động:**
- ⏸️ LOCK trading cho 30 phút
- ❌ BLOCK tất cả trade orders
- Thông báo: "Bạn đang trong kỳ nghỉ! Cần xả stress trước tiếp tục"
- Khi hết thời gian: User phải là call resume API để tiếp tục

---

## 🔗 REST API Endpoints

### 1. Validate Trade

```
POST /api/discipline/validate

Body:
{
  "signal": {
    "symbol": "BTC/USDT",
    "type": "BUY",
    "price": 32000,
    "confidence": 0.55,
    "stopLoss": 31000,
    "takeProfit": 33000,
    "positionSize": 1.5
  },
  "config": {
    "accountId": "trader-001",
    "minConfidenceThreshold": 0.60,
    "maxRiskPerTrade": 0.02,
    "accountBalance": 10000
  }
}

Response:
{
  "isValid": false,
  "violations": [
    {
      "rule": "CONFIDENCE_CHECK",
      "severity": "CRITICAL",
      "message": "Confidence: 55.0% < Required: 60.0%",
      "vietnameseMessage": "Bạn chưa đủ tự tin để trade!"
    }
  ],
  "warnings": [
    {
      "rule": "STOP_LOSS_REQUIRED",
      "severity": "MEDIUM",
      "message": "SL quá gần entry point",
      "vietnameseMessage": "SL quá gần! Dễ bị stop out"
    }
  ],
  "feedback": "❌ VALIDATION FAILED\n\nVIOLATIONS:\nConfidence: 55.0% < 60.0%..."
}
```

### 2. Get Account Status

```
GET /api/discipline/status/{accountId}

Response:
{
  "accountId": "trader-001",
  "sessionStatus": "ACTIVE",
  "consecutiveLosses": 1,
  "dailyProfitLoss": -150.50,
  "dailyRiskUsed": 0.015,
  "accountBalance": 10000,
  "minConfidenceThreshold": 0.60,
  "maxRiskPerTrade": 0.02,
  "isInBreak": false,
  "isLocked": false
}
```

### 3. Record Trade Win

```
POST /api/discipline/record-win

Body:
{
  "accountId": "trader-001",
  "amount": 250.50
}

Response:
"Win recorded successfully"

Effect:
- Consecutive losses reset to 0
- Daily P&L updated: +250.50
- Account balance increased
```

### 4. Record Trade Loss

```
POST /api/discipline/record-loss

Body:
{
  "accountId": "trader-001",
  "amount": 150.50
}

Response:
"Loss recorded - check if break period triggered"

Effect:
- Consecutive losses: 1 → 2
- Daily P&L updated: -150.50
- If consecutive losses >= 3: AUTO-LOCK account for 30 min
```

### 5. Initiate Break Period

```
POST /api/discipline/break

Body:
{
  "accountId": "trader-001"
}

Response:
"Break period initiated - until 2026-04-07 15:30:00"

Effect:
- Session status: BREAK
- Trading disabled for 30 minutes
- Automatic unlock when time expires
```

### 6. Resume Trading

```
POST /api/discipline/resume

Body:
{
  "accountId": "trader-001"
}

Response:
"Trading resumed - stay disciplined!"

Effect:
- Session status: ACTIVE
- Consecutive losses reset
- Ready to trade again
```

### 7. Lock Account

```
POST /api/discipline/lock

Body:
{
  "accountId": "trader-001",
  "reason": "Multiple critical rule violations"
}

Response:
"Account locked: Multiple critical rule violations"
Status: 403 Forbidden

Effect:
- Session status: LOCKED
- ALL trading blocked
- Manual intervention required to unlock
```

### 8. Get Discipline Report

```
GET /api/discipline/report/{accountId}

Response:
{
  "accountId": "trader-001",
  "sessionStatus": "ACTIVE",
  "consecutiveLosses": 1,
  "dailyProfitLoss": -150.50,
  "dailyRiskUsed": 0.015,
  "accountBalance": 9849.50,
  "minConfidenceThreshold": 0.60,
  "maxRiskPerTrade": 0.02,
  "breakEndsAt": null,
  "isInBreak": false,
  "isLocked": false
}
```

---

## 📈 Request Flow

```
Trading Signal Generated by Analysis Agent
                  ↓
    [POST /api/discipline/validate]
                  ↓
          DisciplineRuleEngine
                  ↓
        ┌─────────┴─────────┐
        ↓                   ↓
   VIOLATIONS         WARNINGS
        ↓                   ↓
    ❌ BLOCK           ⚠️ ALERT
        ↓                   ↓
  Reject Signal      Show to User
        ↓                   ↓
  [POST /api/signals/{id}/reject]  [User Decision]
        ↓                       ↓
    REJECTED              (Confirm/Cancel)
                            ↓
                       ✅ APPROVED
                            ↓
              [POST /api/signals/{id}/approve]
                            ↓
                  Send to Execution Agent
                            ↓
                       Trade Executed
                            ↓
                      [Record Win/Loss]
                            ↓
                  Update Account Status
```

---

## 🎮 Ví Dụ Thực Tế

### Scenario 1: Lack of Confidence

```
1. Analysis Agent generates signal:
   - BTC/USDT, BUY at $32,000
   - Confidence: 45% (< 60% threshold)
   - SL: $31,000, TP: $33,000

2. Validation Result:
   ❌ VIOLATION: CONFIDENCE_CHECK
   Message: "Confidence 45% < Required 60%"
   
3. Result: SIGNAL REJECTED
   Trade is NOT executed
   User is notified to wait for stronger signal
```

### Scenario 2: Missing Stop Loss

```
1. User tries to place order:
   - ETH/USDT, SELL at $1,900
   - Confidence: 75% ✅
   - SL: NOT SET ❌
   - TP: $1,850

2. Validation Result:
   ❌ VIOLATION: STOP_LOSS_REQUIRED
   Message: "Bạn đã đặt SL/TP chưa? KHÔNG ĐƯỢC TRADE MÀ KHÔNG CÓ SL!"
   
3. Result: ORDER REJECTED
   System blocks the trade
   User must set SL before resubmitting
```

### Scenario 3: FOMO Detection

```
1. User places 4 orders in 3 minutes:
   - Order 1: BTC BUY at 15:01
   - Order 2: ETH SELL at 15:02
   - Order 3: XRP BUY at 15:03
   - Order 4: ADA SELL at 15:04

2. System detects FOMO:
   ⚠️ WARNING: FOMO_DETECTED
   Message: "4 orders in last 5 minutes | FOMO Score: 90%"
   
3. Result:
   ⚠️ ALERT displayed to user
   Trade is still allowed (WARNING level)
   But user sees: "Bạn đang fomo! Quá nhiều lệnh"
```

### Scenario 4: Auto-Break After 3 Losses

```
Timeline:
15:00 - Trade 1: LOSS -$100 (Consecutive: 1)
15:15 - Trade 2: LOSS -$150 (Consecutive: 2)
15:30 - Trade 3: LOSS -$200 (Consecutive: 3) ← AUTOMATIC BREAK!

15:30 - System automatically locks account
        ❌ ACCOUNT ON BREAK
        Available after: 16:00

15:50 - User tries to place order
        Result: ❌ BLOCKED
        Message: "Account on break until 16:00"

16:00 - Break period ends
        User can resume by calling: POST /api/discipline/resume

16:01 - User resumes trading
        ✅ Consecutive losses reset
        Ready to trade again
```

---

## 🔧 Cấu Hình

### Trong `application.yml`

```yaml
trading:
  discipline:
    # Confidence requirements
    minConfidenceThreshold: 0.60
    
    # Stop Loss settings
    stopLossRequired: true
    minStopLossPercentage: 0.01
    maxStopLossPercentage: 0.10
    
    # Risk management
    maxRiskPerTrade: 0.02
    maxDailyRisk: 0.05
    accountBalance: 10000.0
    
    # FOMO detection
    fomoDetectionWindowSeconds: 300
    maxOrdersInPeriod: 3
    fomoThreshold: 0.70
    
    # Break rules
    consecutiveLossesTriggerBreak: 3
    breakDurationMinutes: 30
```

---

## 📊 Database Schema

```sql
-- Trading discipline configurations
CREATE TABLE trading_discipline_config (
    id BIGINT PRIMARY KEY,
    account_id VARCHAR(100) NOT NULL UNIQUE,
    min_confidence_threshold DOUBLE DEFAULT 0.60,
    stop_loss_required BOOLEAN DEFAULT TRUE,
    max_risk_per_trade DOUBLE DEFAULT 0.02,
    max_daily_risk DOUBLE DEFAULT 0.05,
    current_consecutive_losses INT DEFAULT 0,
    daily_profit_loss DOUBLE DEFAULT 0.0,
    session_status VARCHAR(50) DEFAULT 'ACTIVE',
    break_ends_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Rule violation tracking
CREATE TABLE rule_violations (
    id BIGINT PRIMARY KEY,
    signal_id BIGINT NOT NULL,
    violated_rule VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    violation_message TEXT,
    detected_at TIMESTAMP,
    prevented_at TIMESTAMP
);
```

---

## 🚀 Tích Hợp với Execution Agent

Execution Agent sẽ nhận về signal từ orchestrator **CHỈ KHI** signal đã passed validation:

```java
// Execution Agent
@KafkaListener(topics = "execution-orders")
public void handleExecutionOrder(Map<String, Object> message) {
    Long signalId = (Long) message.get("signalId");
    TradingSignal signal = (TradingSignal) message.get("signal");
    
    // Signal là đã được validate by DisciplineRuleEngine
    // → Có thể execute với confidence
    
    executeOrder(signal);
    
    // Track result
    if (orderProfit > 0) {
        tradingService.recordTradeResult(accountId, orderProfit);
    } else {
        tradingService.recordTradeResult(accountId, -orderLoss);
    }
}
```

---

## ✅ Advantages

✅ **Loại bỏ FOMO** - Phát hiện và cảnh báo giao dịch vô tư  
✅ **Bắt buộc Stop Loss** - Không bao giờ trade mà không có SL  
✅ **Quản lý rủi ro** - Giới hạn rủi ro trên mỗi lệnh và mỗi ngày  
✅ **Tự động nghỉ** - Tự động khoá account sau losses liên tiếp  
✅ **Tự động phục hồi** - Hỗ trợ xả stress trước khi tiếp tục trade  
✅ **Audit trail** - Lưu trữ tất cả vi phạm và cảnh báo  

---

## 🎯 Next Steps

1. ✅ Integrate with TradingService
2. ✅ Create REST API endpoints
3. ⏳ Create database repositories
4. ⏳ Add WebSocket real-time alerts
5. ⏳ Create trader dashboard
6. ⏳ Add ML-based patterns for FOMO detection
