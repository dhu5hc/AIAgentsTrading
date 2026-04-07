package com.trading.orchestrator.service;

import com.trading.orchestrator.model.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

/**
 * The Absolute Discipline Rule Engine
 * Enforces the 4 core trading discipline rules:
 * 1. "Không chắc → không trade" - Confidence must be >= threshold
 * 2. "Không có SL → không trade" - Stop loss must be set
 * 3. "Sai → cắt ngay" - Exit on stop loss immediately
 * 4. "Thua → nghỉ" - Take a break after consecutive losses
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class DisciplineRuleEngine {
    
    // Simulated repositories - in real app, use JPA repositories
    private final Map<String, TradingDisciplineConfig> configCache = new HashMap<>();
    private final List<RuleViolation> violations = new ArrayList<>();
    
    /**
     * Main validation method - runs before EVERY trade
     */
    public ValidationResult validateTrade(TradingSignal signal, TradingDisciplineConfig config) {
        log.info("=== Starting Discipline Validation for {} ===", signal.getSymbol());
        
        ValidationResult result = ValidationResult.builder()
            .signal(signal)
            .config(config)
            .isValid(true)
            .violations(new ArrayList<>())
            .warnings(new ArrayList<>())
            .build();
        
        // Rule 1: Confidence Check
        checkConfidence(signal, config, result);
        
        // Rule 2: Stop Loss Required
        checkStopLossRequired(signal, config, result);
        
        // Rule 3: Stop Loss Validity (not too tight, not too loose)
        checkStopLossValidity(signal, config, result);
        
        // Rule 4: Risk Management
        checkRiskLimits(signal, config, result);
        
        // Rule 5: FOMO Detection
        checkFomoDetection(signal, config, result);
        
        // Rule 6: Account Status (Break/Lock)
        checkAccountStatus(signal, config, result);
        
        // Determine final validation status
        result.setValid(result.getViolations().isEmpty());
        
        log.info("Validation Result: Valid={}, Violations={}, Warnings={}", 
            result.isValid(), result.getViolations().size(), result.getWarnings().size());
        
        return result;
    }
    
    /**
     * Rule 1: "Không chắc → không trade"
     * Confidence must meet minimum threshold
     */
    private void checkConfidence(TradingSignal signal, TradingDisciplineConfig config, ValidationResult result) {
        double confidence = signal.getConfidence() != null ? signal.getConfidence() : 0.0;
        double threshold = config.getMinConfidenceThreshold();
        
        log.debug("Confidence Check: {} >= {}?", confidence, threshold);
        
        if (confidence < threshold) {
            String message = String.format(
                "❌ CONFIDENCE CHECK FAILED | Confidence: %.1f%% | Required: %.1f%%",
                confidence * 100, threshold * 100
            );
            
            RuleViolationAlert violation = RuleViolationAlert.builder()
                .rule(DisciplineRule.CONFIDENCE_CHECK)
                .severity(RuleViolation.ViolationSeverity.CRITICAL)
                .message(message)
                .vietnameseMessage("Bạn chưa đủ tự tin để trade! Confidence phải ≥ " + (int)(threshold * 100) + "%")
                .details(Map.of(
                    "actualConfidence", confidence,
                    "requiredThreshold", threshold,
                    "deficiency", threshold - confidence
                ))
                .build();
            
            result.getViolations().add(violation);
        }
    }
    
    /**
     * Rule 2: "Không có SL → không trade"
     * Stop loss MUST be set
     */
    private void checkStopLossRequired(TradingSignal signal, TradingDisciplineConfig config, ValidationResult result) {
        if (!config.getStopLossRequired()) {
            return; // Config allows trades without SL
        }
        
        Double stopLoss = signal.getStopLoss();
        
        log.debug("Stop Loss Check: Set? {}", stopLoss != null);
        
        if (stopLoss == null || stopLoss == 0.0) {
            String message = "❌ STOP LOSS MISSING | No SL set!";
            
            RuleViolationAlert violation = RuleViolationAlert.builder()
                .rule(DisciplineRule.STOP_LOSS_REQUIRED)
                .severity(RuleViolation.ViolationSeverity.CRITICAL)
                .message(message)
                .vietnameseMessage("❌ Bạn đã đặt SL/TP chưa? Không được trade mà không có SL!")
                .details(Map.of(
                    "stopLoss", stopLoss,
                    "symbol", signal.getSymbol(),
                    "price", signal.getPrice()
                ))
                .build();
            
            result.getViolations().add(violation);
        }
    }
    
    /**
     * Rule 3: "Sai → cắt ngay" - Validate SL distance
     * SL should be reasonable (not too tight, not too loose)
     */
    private void checkStopLossValidity(TradingSignal signal, TradingDisciplineConfig config, ValidationResult result) {
        Double stopLoss = signal.getStopLoss();
        Double price = signal.getPrice();
        
        if (stopLoss == null || price == null || stopLoss == 0.0) {
            return; // Already handled by checkStopLossRequired
        }
        
        double slDistance = Math.abs(price - stopLoss) / price;
        double minSL = config.getMinStopLossPercentage();
        double maxSL = config.getMaxStopLossPercentage();
        
        log.debug("SL Validity Check: {} %% (min: {} %%, max: {} %%)", slDistance * 100, minSL * 100, maxSL * 100);
        
        // SL too tight (tighter than minimum)
        if (slDistance < minSL) {
            String message = String.format(
                "⚠️ STOP LOSS TOO TIGHT | SL: %.2f%% | Minimum: %.2f%%",
                slDistance * 100, minSL * 100
            );
            
            RuleViolationAlert warning = RuleViolationAlert.builder()
                .rule(DisciplineRule.STOP_LOSS_REQUIRED)
                .severity(RuleViolation.ViolationSeverity.MEDIUM)
                .message(message)
                .vietnameseMessage("⚠️ SL quá gần entry point! Dễ bị stop out bởi noise")
                .details(Map.of(
                    "slPercentage", slDistance,
                    "minimumSL", minSL,
                    "price", price,
                    "stopLoss", stopLoss
                ))
                .build();
            
            result.getWarnings().add(warning);
        }
        
        // SL too loose (farther than maximum)
        if (slDistance > maxSL) {
            String message = String.format(
                "⚠️ STOP LOSS TOO LOOSE | SL: %.2f%% | Maximum: %.2f%%",
                slDistance * 100, maxSL * 100
            );
            
            RuleViolationAlert warning = RuleViolationAlert.builder()
                .rule(DisciplineRule.STOP_LOSS_REQUIRED)
                .severity(RuleViolation.ViolationSeverity.HIGH)
                .message(message)
                .vietnameseMessage("⚠️ SL quá xa! Risk quá lớn cho một lệnh")
                .details(Map.of(
                    "slPercentage", slDistance,
                    "maximumSL", maxSL,
                    "price", price,
                    "stopLoss", stopLoss
                ))
                .build();
            
            result.getViolations().add(warning);
        }
    }
    
    /**
     * Rule 4: Risk Management - Volume/Position Size Check
     * "Khối lượng vượt quá giới hạn rủi ro chấp nhận được"
     */
    private void checkRiskLimits(TradingSignal signal, TradingDisciplineConfig config, ValidationResult result) {
        Double positionSize = signal.getPositionSize();
        Double stopLoss = signal.getStopLoss();
        Double price = signal.getPrice();
        Double accountBalance = config.getAccountBalance();
        
        if (positionSize == null || positionSize == 0.0 || stopLoss == null || price == null) {
            return; // Can't calculate risk without these
        }
        
        // Calculate risk in dollars
        double riskDistance = Math.abs(price - stopLoss);
        double riskAmount = positionSize * riskDistance;
        double riskPercentage = riskAmount / accountBalance;
        
        double maxRiskPerTrade = config.getMaxRiskPerTrade();
        double maxDailyRisk = config.getMaxDailyRisk();
        
        log.debug("Risk Check: Trade Risk %.2f%% (max: %.2f%%), Daily Risk: %.2f%% (max: %.2f%%)",
            riskPercentage * 100, maxRiskPerTrade * 100,
            config.getDailyProfitLoss() * 100, maxDailyRisk * 100);
        
        // Per-trade risk check
        if (riskPercentage > maxRiskPerTrade) {
            String message = String.format(
                "❌ RISK PER TRADE EXCEEDED | Risk: %.2f%% | Max: %.2f%% | Amount: $%.2f",
                riskPercentage * 100, maxRiskPerTrade * 100, riskAmount
            );
            
            RuleViolationAlert violation = RuleViolationAlert.builder()
                .rule(DisciplineRule.STOP_LOSS_REQUIRED)
                .severity(RuleViolation.ViolationSeverity.CRITICAL)
                .message(message)
                .vietnameseMessage("❌ Khối lượng vượt quá giới hạn rủi ro chấp nhận được!")
                .details(Map.of(
                    "riskPercentage", riskPercentage,
                    "maxRiskPerTrade", maxRiskPerTrade,
                    "riskAmount", riskAmount,
                    "positionSize", positionSize,
                    "accountBalance", accountBalance
                ))
                .build();
            
            result.getViolations().add(violation);
        }
        
        // Daily risk check
        double projectedDailyRisk = Math.abs(config.getDailyProfitLoss()) + riskPercentage;
        if (projectedDailyRisk > maxDailyRisk) {
            String message = String.format(
                "⚠️ DAILY RISK LIMIT APPROACHING | Current: %.2f%% | Max: %.2f%%",
                projectedDailyRisk * 100, maxDailyRisk * 100
            );
            
            RuleViolationAlert warning = RuleViolationAlert.builder()
                .rule(DisciplineRule.BREAK_AFTER_LOSS)
                .severity(RuleViolation.ViolationSeverity.HIGH)
                .message(message)
                .vietnameseMessage("⚠️ Đã cạn kiệt daily risk limit!")
                .details(Map.of(
                    "projectedDailyRisk", projectedDailyRisk,
                    "maxDailyRisk", maxDailyRisk,
                    "currentDailyLoss", config.getDailyProfitLoss()
                ))
                .build();
            
            result.getWarnings().add(warning);
        }
    }
    
    /**
     * Rule 5: FOMO Detection
     * "Bạn đang fomo" - Detect rapid trading behavior
     */
    private void checkFomoDetection(TradingSignal signal, TradingDisciplineConfig config, ValidationResult result) {
        long windowSeconds = config.getFomoDetectionWindowSeconds();
        int maxOrdersInPeriod = config.getMaxOrdersInPeriod();
        
        // Simulated: count orders in last 5 minutes
        LocalDateTime windowStart = LocalDateTime.now().minusSeconds(windowSeconds);
        long recentOrdersCount = violations.stream()
            .filter(v -> v.getDetectedAt().isAfter(windowStart))
            .count();
        
        double fomoLikelihood = (double) recentOrdersCount / maxOrdersInPeriod;
        if (fomoLikelihood > 1.0) fomoLikelihood = 1.0;
        
        log.debug("FOMO Check: {} orders in {} seconds | Likelihood: {}", 
            recentOrdersCount, windowSeconds, fomoLikelihood);
        
        if (fomoLikelihood > config.getFomoThreshold()) {
            String message = String.format(
                "⚠️ FOMO DETECTED | Orders in last %d min: %d | FOMO Score: %.1f%%",
                windowSeconds / 60, recentOrdersCount, fomoLikelihood * 100
            );
            
            RuleViolationAlert warning = RuleViolationAlert.builder()
                .rule(DisciplineRule.CONFIDENCE_CHECK)
                .severity(RuleViolation.ViolationSeverity.HIGH)
                .message(message)
                .vietnameseMessage("⚠️ Bạn đang fomo! Quá nhiều lệnh trong thời gian ngắn")
                .details(Map.of(
                    "recentOrdersCount", recentOrdersCount,
                    "windowSeconds", windowSeconds,
                    "fomoLikelihood", fomoLikelihood,
                    "threshold", config.getFomoThreshold()
                ))
                .build();
            
            result.getWarnings().add(warning);
        }
    }
    
    /**
     * Rule 6: Account Status Check
     * "Thua → nghỉ" - Check if account is on break or locked
     */
    private void checkAccountStatus(TradingSignal signal, TradingDisciplineConfig config, ValidationResult result) {
        if (config.isInBreak()) {
            String message = String.format(
                "❌ ACCOUNT ON BREAK | Break continues until: %s",
                config.getBreakEndsAt()
            );
            
            RuleViolationAlert violation = RuleViolationAlert.builder()
                .rule(DisciplineRule.BREAK_AFTER_LOSS)
                .severity(RuleViolation.ViolationSeverity.CRITICAL)
                .message(message)
                .vietnameseMessage("❌ Bạn đang trong kỳ nghỉ! Cần xả stress trước tiếp tục")
                .details(Map.of(
                    "breakEndsAt", config.getBreakEndsAt(),
                    "reason", "Consecutive losses - emotional recovery needed"
                ))
                .build();
            
            result.getViolations().add(violation);
        }
        
        if (config.isLocked()) {
            String message = String.format(
                "❌ ACCOUNT LOCKED | Reason: %s",
                config.getLockReason()
            );
            
            RuleViolationAlert violation = RuleViolationAlert.builder()
                .rule(DisciplineRule.STOP_LOSS_REQUIRED)
                .severity(RuleViolation.ViolationSeverity.CRITICAL)
                .message(message)
                .vietnameseMessage("❌ Tài khoản bị khoá do vi phạm rule!")
                .details(Map.of(
                    "lockReason", config.getLockReason(),
                    "lockedAt", config.getStatusChangedAt()
                ))
                .build();
            
            result.getViolations().add(violation);
        }
    }
    
    /**
     * Apply a loss - update consecutive losses counter
     * If exceeds threshold, trigger break period
     */
    public void recordLoss(TradingSignal signal, TradingDisciplineConfig config, double lossAmount) {
        config.setCurrentConsecutiveLosses(config.getCurrentConsecutiveLosses() + 1);
        config.setDailyProfitLoss(config.getDailyProfitLoss() - lossAmount);
        
        log.warn("Loss recorded | Consecutive Losses: {} | Daily Loss: {}", 
            config.getCurrentConsecutiveLosses(), config.getDailyProfitLoss());
        
        if (config.getCurrentConsecutiveLosses() >= config.getConsecutiveLossesTriggerBreak()) {
            initiateBreakPeriod(config);
        }
    }
    
    /**
     * Apply a win - reset consecutive losses counter
     */
    public void recordWin(TradingSignal signal, TradingDisciplineConfig config, double winAmount) {
        config.setCurrentConsecutiveLosses(0);
        config.setDailyProfitLoss(config.getDailyProfitLoss() + winAmount);
        config.setAccountBalance(config.getAccountBalance() + winAmount);
        
        log.info("Win recorded | Consecutive Losses Reset | Daily Profit: {}", config.getDailyProfitLoss());
    }
    
    /**
     * Initiate a break period after consecutive losses
     */
    public void initiateBreakPeriod(TradingDisciplineConfig config) {
        int breakDurationMinutes = 30; // Default 30 minutes
        LocalDateTime breakEndsAt = LocalDateTime.now().plusMinutes(breakDurationMinutes);
        
        config.setSessionStatus(TradingDisciplineConfig.TradingSessionStatus.BREAK);
        config.setBreakEndsAt(breakEndsAt);
        config.setStatusChangedAt(LocalDateTime.now());
        config.setLockReason("Consecutive losses (Rule 4: Thua → nghỉ)");
        
        log.warn("⏸️ BREAK PERIOD INITIATED | Duration: {} minutes | Ends: {}", 
            breakDurationMinutes, breakEndsAt);
    }
    
    /**
     * Lock trading account due to rule violations
     */
    public void lockAccount(TradingDisciplineConfig config, String reason) {
        config.setSessionStatus(TradingDisciplineConfig.TradingSessionStatus.LOCKED);
        config.setStatusChangedAt(LocalDateTime.now());
        config.setLockReason(reason);
        
        log.error("🔒 ACCOUNT LOCKED | Reason: {}", reason);
    }
    
    /**
     * Resume trading after break period
     */
    public void resumeTrading(TradingDisciplineConfig config) {
        config.setSessionStatus(TradingDisciplineConfig.TradingSessionStatus.ACTIVE);
        config.setCurrentConsecutiveLosses(0);
        config.setStatusChangedAt(LocalDateTime.now());
        config.setBreakEndsAt(null);
        config.setLockReason(null);
        
        log.info("▶️ RESUME TRADING | Account status reset");
    }
    
    /**
     * Get activity report
     */
    public Map<String, Object> generateDisciplineReport(TradingDisciplineConfig config) {
        return Map.ofEntries(
            Map.entry("accountId", config.getAccountId()),
            Map.entry("sessionStatus", config.getSessionStatus()),
            Map.entry("consecutiveLosses", config.getCurrentConsecutiveLosses()),
            Map.entry("dailyProfitLoss", config.getDailyProfitLoss()),
            Map.entry("dailyRiskUsed", config.getDailyProfitLoss() / config.getAccountBalance()),
            Map.entry("accountBalance", config.getAccountBalance()),
            Map.entry("minConfidenceThreshold", config.getMinConfidenceThreshold()),
            Map.entry("maxRiskPerTrade", config.getMaxRiskPerTrade()),
            Map.entry("breakEndsAt", config.getBreakEndsAt()),
            Map.entry("isInBreak", config.isInBreak()),
            Map.entry("isLocked", config.isLocked())
        );
    }
}
