```mermaid
graph TB
    subgraph "AI Trading Agents (Python)"
        AA["📊 Analysis Agent"]
        DA["📈 Data Agent"]
        SA["🎯 Strategy Agent"]
        EA["⚙️ Execution Agent"]
        MA["📡 Monitoring Agent"]
    end

    subgraph "Kỷ Luật Tuyệt Đối Framework (Java)"
        TradingController["TradingController"]
        DisciplineController["🔐 DisciplineController"]
        TradingService["TradingService"]
        DRuleEngine["🎯 DisciplineRuleEngine"]
        
        subgraph "Rules Engine"
            R1["Rule 1: Confidence Check<br/>Không chắc → không trade"]
            R2["Rule 2: Stop Loss Required<br/>Không có SL → không trade"]
            R3["Rule 3: SL Validity<br/>Sai → cắt ngay"]
            R4["Rule 4: Break After Loss<br/>Thua → nghỉ"]
            FOMO["FOMO Detection"]
        end
        
        subgraph "Models"
            DSignal["TradingSignal"]
            DConfig["TradingDisciplineConfig"]
            RViolation["RuleViolation"]
            VResult["ValidationResult"]
        end
    end

    subgraph "Database"
        DB_Signals["trading_signals"]
        DB_Config["trading_discipline_config"]
        DB_Violations["rule_violations"]
    end

    subgraph "Message Queue (Kafka)"
        K_Analysis["analysis-results"]
        K_Signals["trading-signals"]
        K_Execution["execution-orders"]
        K_Results["trade-results"]
    end

    %% Data Flow
    DA -->|Market Data| K_Analysis
    AA -->|Generate Signals| K_Signals
    
    %% Validation Flow
    K_Signals -->|Signal| DisciplineController
    DisciplineController -->|Validate| DRuleEngine
    
    %% Rule Checks
    DRuleEngine --> R1
    DRuleEngine --> R2
    DRuleEngine --> R3
    DRuleEngine --> R4
    DRuleEngine --> FOMO
    
    %% Validation Result
    R1 --> VResult
    R2 --> VResult
    R3 --> VResult
    R4 --> VResult
    FOMO --> VResult
    
    %% If Valid
    VResult -->|Valid ✅| K_Execution
    
    %% If Invalid
    VResult -->|Invalid ❌| TradingService
    TradingService -->|Reject| TradingController
    
    %% Execution
    K_Execution -->|Execute Order| EA
    
    %% Track Result
    EA -->|Win/Loss| K_Results
    K_Results -->|Record Result| TradingService
    
    %% Update Account Status
    TradingService -->|Update Config| DRuleEngine
    
    %% Monitoring
    DRuleEngine -->|Status| MA
    
    %% Database
    DSignal --> DB_Signals
    DConfig --> DB_Config
    RViolation --> DB_Violations
    
    style DRuleEngine fill:#ff6b6b,color:#fff
    style R1 fill:#ff8787,color:#fff
    style R2 fill:#ff8787,color:#fff
    style R3 fill:#ff8787,color:#fff
    style R4 fill:#ff8787,color:#fff
    style FOMO fill:#ff8787,color:#fff
    style DisciplineController fill:#ff6b6b,color:#fff
    style VResult fill:#fcc419,color:#000
```

## Architecture Overview

```mermaid
sequenceDiagram
    participant Agent as Analysis Agent
    participant API as Discipline API
    participant Engine as Rule Engine
    participant Exec as Execution Agent
    participant Monitor as Monitoring Agent

    Agent->>API: 1. POST /validate (signal + config)
    API->>Engine: 2. validateTrade()
    
    par Rule Checks
        Engine->>Engine: Check Confidence
        Engine->>Engine: Check Stop Loss
        Engine->>Engine: Check Risk Limits
        Engine->>Engine: Check FOMO
        Engine->>Engine: Check Account Status
    end
    
    alt Valid ✅
        Engine-->>API: ValidationResult (valid=true)
        API->>Exec: 3. Send to Kafka (execution-orders)
        Exec->>Exec: 4. Execute Trade
        Exec-->>Exec: 5. Track P&L
    else Invalid ❌
        Engine-->>API: ValidationResult (valid=false)
        API-->>Agent: Reject with reasons
        Agent->>Monitor: Log rejection
    end
    
    alt Trade Profitable
        Exec->>API: 6. POST /record-win
        API->>Engine: Record win
    else Trade Loss
        Exec->>API: 6. POST /record-loss
        API->>Engine: Record loss
        
        alt 3+ Consecutive Losses?
            Engine->>Engine: Auto-break for 30 min
            Engine-->>Monitor: Account on break
        end
    end
    
    Monitor->>API: GET /status
    API-->>Monitor: Account Info
```

## Rule Enforcement Flow

```mermaid
graph TD
    Signal["Trading Signal Received"]
    
    Signal --> C1{"Rule 1:<br/>Confidence ≥ 60%?"}
    
    C1 -->|No| BLOCK1["❌ BLOCK<br/>Confidence too low"]
    C1 -->|Yes| C2{"Rule 2:<br/>Stop Loss Set?"}
    
    C2 -->|No| BLOCK2["❌ BLOCK<br/>No SL"]
    C2 -->|Yes| C3{"Rule 3:<br/>SL Valid?<br/>1%-10%"}
    
    C3 -->|Too Tight| WARN3["⚠️ WARN<br/>SL too tight"]
    C3 -->|Too Loose| WARN3
    C3 -->|OK| C4{"Rule 4:<br/>Not On Break?"}
    
    C4 -->|On Break| BLOCK4["❌ BLOCK<br/>Account on break"]
    C4 -->|Active| C5{"FOMO Check:<br/>Not Over 3<br/>Orders/5 min?"}
    
    C5 -->|FOMO| WARN5["⚠️ WARN<br/>FOMO detected"]
    C5 -->|OK| C6{"Risk Check:<br/>Risk ≤ 2%?"}
    
    C6 -->|Exceeded| BLOCK6["❌ BLOCK<br/>Risk too high"]
    C6 -->|OK| PASS["✅ PASS<br/>All rules satisfied"]
    
    BLOCK1 --> REJECT["❌ REJECTED"]
    BLOCK2 --> REJECT
    BLOCK4 --> REJECT
    BLOCK6 --> REJECT
    
    WARN3 --> EXEC["⚠️ ALLOWED<br/>with warnings"]
    WARN5 --> EXEC
    
    PASS --> APPROVE["✅ APPROVED<br/>Execute Order"]
    
    EXEC --> Kafka["Send to<br/>execution-orders"]
    APPROVE --> Kafka
    REJECT --> Revert["Send to<br/>rejected-signals"]
    
    style C1 fill:#ffd93d
    style C2 fill:#ffd93d
    style C3 fill:#ffd93d
    style C4 fill:#ffd93d
    style C5 fill:#ffd93d
    style C6 fill:#ffd93d
    
    style PASS fill:#6bcf7f
    style APPROVE fill:#6bcf7f
    
    style BLOCK1 fill:#ff6b6b
    style BLOCK2 fill:#ff6b6b
    style BLOCK4 fill:#ff6b6b
    style BLOCK6 fill:#ff6b6b
    style REJECT fill:#ff6b6b
    
    style WARN3 fill:#ffa94d
    style WARN5 fill:#ffa94d
    style EXEC fill:#ffa94d
```

## Auto-Break Process

```mermaid
timeline
    title Auto-Break Trigger (3 Consecutive Losses)
    
    15:00 : Trade 1 : LOSS -$100
          : Consecutive Losses: 1
          : Status: ACTIVE
          
    15:15 : Trade 2 : LOSS -$150
          : Consecutive Losses: 2
          : Status: ACTIVE
          
    15:30 : Trade 3 : LOSS -$200
          : Consecutive Losses: 3 ← TRIGGER!
          : AUTO-LOCK activated
          : Break until 16:00
          
    15:30~16:00 : BREAK PERIOD
               : ❌ All orders blocked
               : "Bạn đang trong kỳ nghỉ!"
               : Emotional recovery
               
    16:00 : Break ends
         : Manual: POST /resume
         : Consecutive losses reset
         : Status: ACTIVE
         
    16:05 : User ready
         : Can trade again
         : Fresh start!
```

## Dashboard State Machine

```mermaid
stateDiagram-v2
    [*] --> ACTIVE
    
    ACTIVE --> BREAK: 3 consecutive losses
    ACTIVE --> LOCKED: Critical violation
    ACTIVE --> ACTIVE: Win or normal trade
    
    BREAK --> ACTIVE: 30 min break ends
    BREAK --> BREAK: Try to trade (blocked)
    
    LOCKED --> ACTIVE: Admin unlock
    LOCKED --> LOCKED: Manual unlock needed
    
    note right of ACTIVE
        Normal trading state
        Can place orders
        Monitor rules
    end note
    
    note right of BREAK
        Automatic 30-min break
        Emotional recovery
        All orders blocked
    end note
    
    note right of LOCKED
        Violation or admin action
        Manual intervention needed
        Complete trading freeze
    end note
```

## Integration Architecture

```mermaid
graph LR
    subgraph Agents["🤖 AI Agents (Python)"]
        AA["Analysis<br/>Agent"]
        SA["Strategy<br/>Agent"]
        EA["Execution<br/>Agent"]
    end
    
    subgraph Backend["🔒 Orchestrator Backend (Java)"]
        REST["REST API<br/>Port 8080"]
        TE["Trading<br/>Service"]
        DRE["Discipline<br/>Rule Engine"]
    end
    
    subgraph Infra["📦 Infrastructure"]
        Kafka["Kafka<br/>Message Queue"]
        DB["PostgreSQL<br/>Database"]
        Redis["Redis<br/>Cache"]
    end
    
    AA -->|2. Validate<br/>POST /validate| REST
    REST -->|3. Check| DRE
    DRE -->|4. Return<br/>Result| REST
    
    REST -->|5. Approved<br/>Send Signal| Kafka
    Kafka -->|6. Execute| EA
    EA -->|7. Record<br/>Win/Loss| REST
    
    REST -->|8. Update| TE
    TE -->|9. Persist| DB
    DRE -->|10. Query| DB
    
    TE -->|11. Cache<br/>Status| Redis
    
    style REST fill:#ff6b6b,color:#fff
    style DRE fill:#ff6b6b,color:#fff
    style TE fill:#ff6b6b,color:#fff
```
