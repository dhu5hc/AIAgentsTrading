package com.trading.orchestrator.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "market_data")
public class MarketData {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String symbol;
    
    @Column(nullable = false)
    private Double price;
    
    private Double volume;
    private Double high24h;
    private Double low24h;
    private Double change24h;
    private Double changePercent24h;
    
    // Technical indicators
    private Double rsi;
    private Double macd;
    private Double macdSignal;
    private Double ema20;
    private Double ema50;
    private Double ema200;
    private Double bollingerUpper;
    private Double bollingerLower;
    
    // Sentiment
    private Double sentimentScore;
    
    @Column(nullable = false)
    private LocalDateTime timestamp;
    
    @Column(nullable = false)
    private String source; // binance, tradingview, etc.
}
