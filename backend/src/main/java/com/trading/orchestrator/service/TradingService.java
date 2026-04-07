package com.trading.orchestrator.service;

import com.trading.orchestrator.model.TradingSignal;
import com.trading.orchestrator.model.TradingDisciplineConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

@Service
@Slf4j
@RequiredArgsConstructor
public class TradingService {
    
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final DisciplineRuleEngine disciplineRuleEngine;
    private final AtomicBoolean tradingActive = new AtomicBoolean(false);
    
    // Kafka topics
    private static final String TOPIC_MARKET_DATA = "market-data";
    private static final String TOPIC_ANALYSIS = "analysis-results";
    private static final String TOPIC_SIGNALS = "trading-signals";
    private static final String TOPIC_EXECUTION = "execution-orders";
    
    public List<TradingSignal> getRecentSignals(String symbol, int limit) {
        log.info("Getting recent signals for symbol: {}, limit: {}", symbol, limit);
        // TODO: Implement database query
        return new ArrayList<>();
    }
    
    public TradingSignal approveSignal(Long signalId) {
        log.info("Approving signal: {}", signalId);
        
        // TODO: Fetch signal from DB by signalId
        TradingSignal signal = new TradingSignal();
        
        // Get or create discipline config for the account
        TradingDisciplineConfig config = getTradingDisciplineConfig("default-account");
        
        // Validate against discipline rules
        ValidationResult validationResult = disciplineRuleEngine.validateTrade(signal, config);
        
        if (!validationResult.isValid()) {
            log.error("❌ Signal validation FAILED | Violations: {}", 
                validationResult.getViolations().size());
            
            // Reject the signal due to discipline violations
            signal.setStatus(TradingSignal.SignalStatus.REJECTED);
            
            // Lock account if critical violations detected
            long criticalCount = validationResult.getViolations().stream()
                .filter(v -> v.getSeverity() == com.trading.orchestrator.model.RuleViolation.ViolationSeverity.CRITICAL)
                .count();
            
            if (criticalCount > 0) {
                disciplineRuleEngine.lockAccount(config, 
                    "Multiple critical rule violations detected");
            }
            
            return signal;
        }
        
        // Validation passed - proceed with execution
        log.info("✅ Signal validation PASSED | Sending to execution agent");
        signal.setStatus(TradingSignal.SignalStatus.APPROVED);
        
        kafkaTemplate.send("execution-orders", Map.of(
            "signalId", signalId,
            "action", "execute",
            "signal", signal
        ));
        
        return signal;
    }
    
    public TradingSignal rejectSignal(Long signalId) {
        log.info("Rejecting signal: {}", signalId);
        // TODO: Implement rejection logic
        return new TradingSignal();
    }
    
    public Map<String, Object> getPortfolio() {
        log.info("Getting portfolio information");
        // TODO: Implement portfolio retrieval
        return Map.of(
            "totalValue", 10000.0,
            "cash", 5000.0,
            "positions", new ArrayList<>()
        );
    }
    
    public Map<String, Object> getPerformance() {
        log.info("Getting performance metrics");
        return Map.of(
            "totalReturn", 5.2,
            "winRate", 65.0,
            "profitFactor", 1.8,
            "sharpeRatio", 1.5,
            "maxDrawdown", -8.5
        );
    }
    
    public void startTrading() {
        if (tradingActive.compareAndSet(false, true)) {
            log.info("🚀 Starting trading system...");
            kafkaTemplate.send("system-control", Map.of("action", "start"));
        } else {
            log.warn("Trading system is already running");
        }
    }
    
    public void stopTrading() {
        if (tradingActive.compareAndSet(true, false)) {
            log.info("⏹️ Stopping trading system...");
            kafkaTemplate.send("system-control", Map.of("action", "stop"));
        } else {
            log.warn("Trading system is not running");
        }
    }
    
    public Map<String, Object> getSystemStatus() {
        return Map.of(
            "tradingActive", tradingActive.get(),
            "agents", Map.of(
                "dataAgent", "RUNNING",
                "analysisAgent", "RUNNING",
                "strategyAgent", "RUNNING",
                "riskAgent", "RUNNING",
                "executionAgent", "RUNNING",
                "monitoringAgent", "RUNNING"
            ),
            "lastUpdate", new Date()
        );
    }
    
    // ========== DISCIPLINE INTEGRATION METHODS ==========
    
    /**
     * Get or create trading discipline config for account
     * In production, fetch from database
     */
    private TradingDisciplineConfig getTradingDisciplineConfig(String accountId) {
        // TODO: Implement database call
        // For now, return default config
        return TradingDisciplineConfig.builder()
            .accountId(accountId)
            .minConfidenceThreshold(0.60)
            .stopLossRequired(true)
            .maxRiskPerTrade(0.02)
            .maxDailyRisk(0.05)
            .accountBalance(10000.0)
            .build();
    }
    
    /**
     * Record an executed trade result
     */
    public void recordTradeResult(String accountId, double profitLoss) {
        TradingDisciplineConfig config = getTradingDisciplineConfig(accountId);
        
        if (profitLoss > 0) {
            disciplineRuleEngine.recordWin(null, config, profitLoss);
            log.info("✅ Trade WIN recorded: +${}", profitLoss);
        } else {
            disciplineRuleEngine.recordLoss(null, config, Math.abs(profitLoss));
            log.warn("❌ Trade LOSS recorded: -${}", Math.abs(profitLoss));
        }
    }
    
    /**
     * Get current discipline status for account
     */
    public Map<String, Object> getDisciplineStatus(String accountId) {
        TradingDisciplineConfig config = getTradingDisciplineConfig(accountId);
        return disciplineRuleEngine.generateDisciplineReport(config);
    }
}
