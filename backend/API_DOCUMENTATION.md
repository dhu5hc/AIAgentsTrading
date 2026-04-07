# 🚀 API Documentation - Kỷ Luật Tuyệt Đối Framework

**Base URL:** `http://localhost:8080/api/discipline`

---

## 📋 Table of Contents

1. [Core Validation Endpoint](#core-validation-endpoint)
2. [Account Status Endpoints](#account-status-endpoints)
3. [Trade Result Endpoints](#trade-result-endpoints)
4. [Session Management](#session-management)
5. [Error Responses](#error-responses)
6. [Examples](#examples)

---

## Core Validation Endpoint

### POST /api/discipline/validate

**Description:** Primary endpoint to validate a trade signal against all discipline rules

**Request Body:**
```json
{
  "signal": {
    "symbol": "BTC/USDT",
    "type": "BUY",
    "price": 32000.00,
    "confidence": 0.75,
    "strategy": "RSI_Oversold",
    "stopLoss": 31000.00,
    "takeProfit": 33500.00,
    "positionSize": 1.5
  },
  "config": {
    "accountId": "trader-001",
    "minConfidenceThreshold": 0.60,
    "stopLossRequired": true,
    "minStopLossPercentage": 0.01,
    "maxStopLossPercentage": 0.10,
    "maxRiskPerTrade": 0.02,
    "maxDailyRisk": 0.05,
    "accountBalance": 10000.00,
    "maxOrdersInPeriod": 3,
    "fomoDetectionWindowSeconds": 300,
    "fomoThreshold": 0.70,
    "consecutiveLossesTriggerBreak": 3,
    "dailyProfitLoss": -150.00,
    "currentConsecutiveLosses": 0,
    "sessionStatus": "ACTIVE"
  }
}
```

**Success Response (200):**
```json
{
  "isValid": true,
  "symbol": "BTC/USDT",
  "violations": [],
  "warnings": [
    {
      "rule": "STOP_LOSS_REQUIRED",
      "severity": "MEDIUM",
      "message": "⚠️ STOP LOSS TOO LOOSE | SL: 3.12% | Maximum: 10.00%",
      "vietnameseMessage": "⚠️ SL quá xa! Risk quá lớn cho một lệnh",
      "details": {
        "slPercentage": 0.0312,
        "maximumSL": 0.10,
        "price": 32000.00,
        "stopLoss": 31000.00
      }
    }
  ],
  "feedback": "✅ VALIDATION PASSED - Ready to Trade!\n\n⚠️ WARNINGS:\n..."
}
```

**Failed Response (200 with isValid: false):**
```json
{
  "isValid": false,
  "symbol": "BTC/USDT",
  "violations": [
    {
      "rule": "CONFIDENCE_CHECK",
      "severity": "CRITICAL",
      "message": "❌ CONFIDENCE CHECK FAILED | Confidence: 45.0% | Required: 60.0%",
      "vietnameseMessage": "❌ Bạn chưa đủ tự tin để trade! Confidence phải ≥ 60%",
      "details": {
        "actualConfidence": 0.45,
        "requiredThreshold": 0.60,
        "deficiency": 0.15
      }
    },
    {
      "rule": "STOP_LOSS_REQUIRED",
      "severity": "CRITICAL",
      "message": "❌ STOP LOSS MISSING | No SL set!",
      "vietnameseMessage": "❌ Bạn đã đặt SL/TP chưa? Không được trade mà không có SL!",
      "details": {
        "stopLoss": null,
        "symbol": "BTC/USDT",
        "price": 32000.00
      }
    }
  ],
  "warnings": [],
  "feedback": "❌ VALIDATION FAILED - Trade BLOCKED\n\nVIOLATIONS:\n..."
}
```

---

## Account Status Endpoints

### GET /api/discipline/status/{accountId}

**Description:** Get current trading session status and discipline config

**Parameters:**
- `accountId` (path): Account identifier

**Response (200):**
```json
{
  "accountId": "trader-001",
  "sessionStatus": "ACTIVE",
  "consecutiveLosses": 1,
  "dailyProfitLoss": -150.50,
  "dailyRiskUsed": 0.0151,
  "accountBalance": 9849.50,
  "minConfidenceThreshold": 0.60,
  "maxRiskPerTrade": 0.02,
  "breakEndsAt": null,
  "isInBreak": false,
  "isLocked": false
}
```

### GET /api/discipline/report/{accountId}

**Description:** Generate detailed discipline report

**Parameters:**
- `accountId` (path): Account identifier

**Response (200):**
```json
{
  "accountId": "trader-001",
  "sessionStatus": "ACTIVE",
  "consecutiveLosses": 1,
  "dailyProfitLoss": -150.50,
  "dailyRiskUsed": 0.0151,
  "accountBalance": 9849.50,
  "minConfidenceThreshold": 0.60,
  "maxRiskPerTrade": 0.02,
  "breakEndsAt": null,
  "isInBreak": false,
  "isLocked": false
}
```

---

## Trade Result Endpoints

### POST /api/discipline/record-win

**Description:** Record a winning trade result

**Request Body:**
```json
{
  "accountId": "trader-001",
  "amount": 250.50
}
```

**Response (200):**
```json
"Win recorded successfully"
```

**Effects:**
- ✅ Consecutive losses reset to 0
- ✅ Daily P&L: +250.50
- ✅ Account balance increased

---

### POST /api/discipline/record-loss

**Description:** Record a losing trade result

**Request Body:**
```json
{
  "accountId": "trader-001",
  "amount": 150.50
}
```

**Response (200):**
```json
"Loss recorded - check if break period triggered"
```

**Effects:**
- ❌ Consecutive losses incremented
- ❌ Daily P&L: -150.50
- ❌ If consecutive losses >= 3: Auto-triggers break period

---

## Session Management

### POST /api/discipline/break

**Description:** Manually initiate a break period

**Request Body:**
```json
{
  "accountId": "trader-001"
}
```

**Response (200):**
```json
"Break period initiated - until 2026-04-07T15:30:00"
```

**Effects:**
- ⏸️ Session status: BREAK
- ⏸️ Trading disabled for 30 minutes
- ⏸️ All orders will be rejected during break

---

### POST /api/discipline/resume

**Description:** Resume trading after break period

**Request Body:**
```json
{
  "accountId": "trader-001"
}
```

**Response (200):**
```json
"Trading resumed - stay disciplined!"
```

**Effects:**
- ▶️ Session status: ACTIVE
- ▶️ Consecutive losses reset
- ▶️ Ready to trade again

---

### POST /api/discipline/lock

**Description:** Manually lock account (admin only)

**Request Body:**
```json
{
  "accountId": "trader-001",
  "reason": "Multiple critical rule violations detected"
}
```

**Response (403 Forbidden):**
```json
"Account locked: Multiple critical rule violations detected"
```

**Effects:**
- 🔒 Session status: LOCKED
- 🔒 ALL trading blocked
- 🔒 Manual intervention required to unlock

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request body",
  "message": "Signal symbol is required"
}
```

### 403 Forbidden
```json
{
  "error": "Account locked",
  "message": "Account is locked: Consecutive losses (Rule 4: Thua → nghỉ)"
}
```

### 404 Not Found
```json
{
  "error": "Account not found",
  "message": "Account 'trader-001' does not exist"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Failed to validate trade signal"
}
```

---

## Examples

### Example 1: Valid Trade with Warnings

**Request:**
```bash
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "ETH/USDT",
      "type": "BUY",
      "price": 1900,
      "confidence": 0.75,
      "stopLoss": 1850,
      "takeProfit": 1950,
      "positionSize": 2.0
    },
    "config": {
      "accountId": "trader-001",
      "minConfidenceThreshold": 0.60,
      "maxRiskPerTrade": 0.02,
      "accountBalance": 10000
    }
  }'
```

**Response:**
```json
{
  "isValid": true,
  "violations": [],
  "warnings": [
    {
      "rule": "STOP_LOSS_REQUIRED",
      "severity": "MEDIUM",
      "message": "⚠️ STOP LOSS TOO TIGHT | SL: 2.63% | Minimum: 1.00%",
      "vietnameseMessage": "⚠️ SL quá gần entry point! Dễ bị stop out bởi noise"
    }
  ],
  "feedback": "✅ VALIDATION PASSED - Ready to Trade!\n\n⚠️ WARNINGS:..."
}
```

---

### Example 2: Blocked - Missing Stop Loss

**Request:**
```bash
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "XRP/USDT",
      "type": "SELL",
      "price": 0.50,
      "confidence": 0.80,
      "stopLoss": null,
      "takeProfit": 0.48
    },
    "config": {
      "accountId": "trader-001",
      "minConfidenceThreshold": 0.60,
      "stopLossRequired": true
    }
  }'
```

**Response:**
```json
{
  "isValid": false,
  "violations": [
    {
      "rule": "STOP_LOSS_REQUIRED",
      "severity": "CRITICAL",
      "message": "❌ STOP LOSS MISSING | No SL set!",
      "vietnameseMessage": "❌ Bạn đã đặt SL/TP chưa? Không được trade mà không có SL!"
    }
  ],
  "feedback": "❌ VALIDATION FAILED - Trade BLOCKED\n..."
}
```

---

### Example 3: Auto-Break Triggered

**Sequence of calls:**

**Step 1: Record 1st loss**
```bash
curl -X POST http://localhost:8080/api/discipline/record-loss \
  -H "Content-Type: application/json" \
  -d '{"accountId": "trader-001", "amount": 100}'

# Response: "Loss recorded - check if break period triggered"
# Consecutive losses: 1
```

**Step 2: Record 2nd loss**
```bash
curl -X POST http://localhost:8080/api/discipline/record-loss \
  -H "Content-Type: application/json" \
  -d '{"accountId": "trader-001", "amount": 150}'

# Response: "Loss recorded - check if break period triggered"
# Consecutive losses: 2
```

**Step 3: Record 3rd loss (BREAKS ACCOUNT)**
```bash
curl -X POST http://localhost:8080/api/discipline/record-loss \
  -H "Content-Type: application/json" \
  -d '{"accountId": "trader-001", "amount": 200}'

# System auto-initiates break!
# Response: "Loss recorded - check if break period triggered"
# Consecutive losses: 3 → AUTO-BREAK
# Session status: BREAK (30 minutes)
```

**Step 4: Try to place order during break**
```bash
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{...signal...}'

# Response:
{
  "isValid": false,
  "violations": [
    {
      "rule": "BREAK_AFTER_LOSS",
      "severity": "CRITICAL",
      "message": "❌ ACCOUNT ON BREAK | Break continues until: 2026-04-07T15:30:00",
      "vietnameseMessage": "❌ Bạn đang trong kỳ nghỉ! Cần xả stress trước tiếp tục"
    }
  ]
}
```

**Step 5: Resume after break ends**
```bash
curl -X POST http://localhost:8080/api/discipline/resume \
  -H "Content-Type: application/json" \
  -d '{"accountId": "trader-001"}'

# Response: "Trading resumed - stay disciplined!"
# Session status: ACTIVE
# Consecutive losses: reset to 0
```

---

### Example 4: FOMO Detection

**Request with multiple rapid orders:**
```bash
# Order 1
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{...signal 1...}'
# Response: isValid=true (1st order)

# Order 2 (within 5 min)
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{...signal 2...}'
# Response: isValid=true (2nd order)

# Order 3 (within 5 min)
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{...signal 3...}'
# Response: isValid=true (3rd order)

# Order 4 (within 5 min) → FOMO DETECTED
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  -d '{...signal 4...}'

# Response:
{
  "isValid": true,
  "warnings": [
    {
      "rule": "CONFIDENCE_CHECK",
      "severity": "HIGH",
      "message": "⚠️ FOMO DETECTED | Orders in last 5 min: 4 | FOMO Score: 85%",
      "vietnameseMessage": "⚠️ Bạn đang fomo! Quá nhiều lệnh trong thời gian ngắn"
    }
  ]
}
```

---

## Integration with Frontend

### React Component Example

```javascript
const validateTrade = async (signal, config) => {
  try {
    const response = await fetch('http://localhost:8080/api/discipline/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signal, config })
    });
    
    const result = await response.json();
    
    if (!result.isValid) {
      // Show violations - BLOCK trade
      showError(result.violations.map(v => v.vietnameseMessage).join('\n'));
      return false;
    }
    
    if (result.warnings.length > 0) {
      // Show warnings - ASK for confirmation
      const confirmed = await showWarning({
        title: "⚠️ Cảnh báo",
        message: result.warnings.map(w => w.vietnameseMessage).join('\n'),
        buttons: ['Tiếp tục', 'Huỷ']
      });
      
      if (!confirmed) return false;
    }
    
    // Trade is valid!
    return true;
    
  } catch (error) {
    console.error('Validation error:', error);
    return false;
  }
};
```

---

## Testing with cURL

```bash
# Test 1: Valid trade
curl -X POST http://localhost:8080/api/discipline/validate \
  -H "Content-Type: application/json" \
  --data @valid_trade.json | jq .

# Test 2: Get account status
curl -X GET http://localhost:8080/api/discipline/status/trader-001 | jq .

# Test 3: Record a loss
curl -X POST http://localhost:8080/api/discipline/record-loss \
  -H "Content-Type: application/json" \
  -d '{"accountId": "trader-001", "amount": 100}' | jq .

# Test 4: Get report
curl -X GET http://localhost:8080/api/discipline/report/trader-001 | jq .
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 400 | Bad Request - Invalid input |
| 403 | Forbidden - Trading blocked/account locked |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Error - Server error |

