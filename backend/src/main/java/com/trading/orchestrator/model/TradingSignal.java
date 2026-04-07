package com.trading.orchestrator.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "trading_signals")
public class TradingSignal {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String symbol;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SignalType type; // BUY, SELL, HOLD
    
    @Column(nullable = false)
    private Double price;
    
    @Column(nullable = false)
    private Double confidence; // 0.0 to 1.0
    
    private String strategy;
    
    @Column(columnDefinition = "TEXT")
    private String reasoning;
    
    private Double stopLoss;
    private Double takeProfit;
    private Double positionSize;
    
    @Enumerated(EnumType.STRING)
    private SignalStatus status; // PENDING, APPROVED, REJECTED, EXECUTED
    
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    private LocalDateTime executedAt;
    
    public enum SignalType {
        BUY, SELL, HOLD
    }
    
    public enum SignalStatus {
        PENDING, APPROVED, REJECTED, EXECUTED, CANCELLED
    }
}
