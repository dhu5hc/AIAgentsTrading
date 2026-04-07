```mermaid
graph TB
    subgraph Agents["Python Trading Agents"]
        DA["📊 Data Agent"]
        AA["🔍 Analysis Agent"]
        SA["🎯 Strategy Agent"]
        EA["⚡ Execution Agent"]
        MA["📈 Monitoring Agent"]
        RA["🛡️ Risk Agent"]
    end

    subgraph Backend["Spring Boot Backend"]
        BC["🌐 BinanceController<br/>13 REST Endpoints"]
        BAC["🔌 BinanceApiClient<br/>Binance Connector Java"]
        DS["💾 DisciplineService<br/>Rule Engine"]
    end

    subgraph Kafka["Event Streaming"]
        K1["signals"]
        K2["approved-signals"]
        K3["execution-results"]
        K4["market-data"]
    end

    subgraph External["External Services"]
        BINANCE["🚀 Binance API<br/>REST V3/WebSocket"]
        REDIS["🔴 Redis<br/>Caching & Alerts"]
        PROMETHEUS["📊 Prometheus<br/>Metrics"]
    end

    %% Data flow
    DA -->|market-data| K4
    AA -->|analysis| K1
    SA -->|trading-signals| K1
    RA -->|validation| K2
    
    K1 -->|subscribe| EA
    K2 -->|subscribe| EA
    
    EA -->|HTTP POST<br/>/api/binance/order/*| BC
    EA -->|order-confirm| K3
    
    MA -->|subscribe| K3
    MA -->|HTTP GET<br/>/api/binance/account| BC
    
    BC -->|REST API| BAC
    BAC -->|Place Order<br/>Get Balance<br/>Cancel Order| BINANCE
    
    BINANCE -->|Order Response| BAC
    BAC -->|JSON| BC
    BC -->|JSON Response| EA
    BC -->|Account Data| MA
    
    EA -->|set alerts| REDIS
    MA -->|check alerts| REDIS
    
    BC -->|metrics| PROMETHEUS
    MA -->|metrics| PROMETHEUS
    
    BA["🔐 auth"]
    DS -->|validate| EA
    
    style Agents fill:#e1f5ff
    style Backend fill:#fff3e0
    style Kafka fill:#f3e5f5
    style External fill:#e8f5e9
    style BINANCE fill:#ffebee,color:#c62828
```

This diagram shows:
- **Python Agents** → Send trading signals and orders via Kafka
- **Spring Boot Backend** → Exposes REST API and manages Binance connections
- **BinanceApiClient** → Handles Binance API authentication and communication
- **Binance API** → Executes orders and retrieves market data
- **Event Streaming** → Kafka topics for inter-agent communication
- **External Services** → Redis for caching, Prometheus for metrics
