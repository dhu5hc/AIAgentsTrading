package com.trading.orchestrator.controller;

import com.trading.orchestrator.model.TradingSignal;
import com.trading.orchestrator.model.TradingDisciplineConfig;
import com.trading.orchestrator.service.DisciplineRuleEngine;
import com.trading.orchestrator.service.ValidationResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * REST API for Absolute Discipline Framework
 * Handles rule validation, account status, and discipline management
 */
@RestController
@RequestMapping("/api/discipline")
@RequiredArgsConstructor
@Slf4j
public class DisciplineController {
    
    private final DisciplineRuleEngine ruleEngine;
    
    /**
     * Main endpoint: Validate a trade signal against discipline rules
     * 
     * POST /api/discipline/validate
     * 
     * Body: {
     *   "signal": { ... },
     *   "config": { ... }
     * }
     */
    @PostMapping("/validate")
    public ResponseEntity<Map<String, Object>> validateTrade(
            @RequestBody DisciplineValidationRequest request) {
        
        log.info("🔍 Validating trade: {}", request.getSignal().getSymbol());
        
        ValidationResult result = ruleEngine.validateTrade(
            request.getSignal(), 
            request.getConfig()
        );
        
        return ResponseEntity.ok(Map.ofEntries(
            Map.entry("isValid", result.isValid()),
            Map.entry("symbol", result.getSignal().getSymbol()),
            Map.entry("violations", result.getViolations().size()),
            Map.entry("warnings", result.getWarnings().size()),
            Map.entry("feedback", result.generateFeedback()),
            Map.entry("violationDetails", result.getViolations()),
            Map.entry("warningDetails", result.getWarnings())
        ));
    }
    
    /**
     * Quick check: Is trading allowed for this account?
     * 
     * GET /api/discipline/status/{accountId}
     */
    @GetMapping("/status/{accountId}")
    public ResponseEntity<Map<String, Object>> getAccountStatus(@PathVariable String accountId) {
        // TODO: Fetch config from database by accountId
        // For now, return dummy data
        
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(accountId)
            .build();
        
        return ResponseEntity.ok(ruleEngine.generateDisciplineReport(config));
    }
    
    /**
     * Record a winning trade
     * 
     * POST /api/discipline/record-win
     */
    @PostMapping("/record-win")
    public ResponseEntity<String> recordWin(
            @RequestBody TradeResultRequest request) {
        
        log.info("✅ Recording win for {}", request.getAccountId());
        
        // TODO: Fetch config from database
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(request.getAccountId())
            .build();
        
        ruleEngine.recordWin(null, config, request.getAmount());
        
        return ResponseEntity.ok("Win recorded successfully");
    }
    
    /**
     * Record a losing trade
     * 
     * POST /api/discipline/record-loss
     */
    @PostMapping("/record-loss")
    public ResponseEntity<String> recordLoss(
            @RequestBody TradeResultRequest request) {
        
        log.warn("❌ Recording loss for {}", request.getAccountId());
        
        // TODO: Fetch config from database
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(request.getAccountId())
            .build();
        
        ruleEngine.recordLoss(null, config, request.getAmount());
        
        return ResponseEntity.ok("Loss recorded - check if break period triggered");
    }
    
    /**
     * Initiate a break period (emotional recovery)
     * 
     * POST /api/discipline/break
     */
    @PostMapping("/break")
    public ResponseEntity<String> initiateBreaK(
            @RequestBody Map<String, String> request) {
        
        String accountId = request.get("accountId");
        log.info("⏸️  Initiating break period for {}", accountId);
        
        // TODO: Fetch config from database
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(accountId)
            .build();
        
        ruleEngine.initiateBreakPeriod(config);
        
        return ResponseEntity.ok("Break period initiated - " + config.getBreakEndsAt());
    }
    
    /**
     * Resume trading after break period
     * 
     * POST /api/discipline/resume
     */
    @PostMapping("/resume")
    public ResponseEntity<String> resumeTrading(
            @RequestBody Map<String, String> request) {
        
        String accountId = request.get("accountId");
        log.info("▶️  Resuming trading for {}", accountId);
        
        // TODO: Fetch config from database
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(accountId)
            .build();
        
        ruleEngine.resumeTrading(config);
        
        return ResponseEntity.ok("Trading resumed - stay disciplined!");
    }
    
    /**
     * Lock account due to violations
     * 
     * POST /api/discipline/lock
     */
    @PostMapping("/lock")
    public ResponseEntity<String> lockAccount(
            @RequestBody Map<String, String> request) {
        
        String accountId = request.get("accountId");
        String reason = request.get("reason");
        
        log.error("🔒 Locking account {} | Reason: {}", accountId, reason);
        
        // TODO: Fetch config from database
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(accountId)
            .build();
        
        ruleEngine.lockAccount(config, reason);
        
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
            .body("Account locked: " + reason);
    }
    
    /**
     * Get discipline report
     * 
     * GET /api/discipline/report/{accountId}
     */
    @GetMapping("/report/{accountId}")
    public ResponseEntity<Map<String, Object>> generateReport(@PathVariable String accountId) {
        // TODO: Fetch config from database
        TradingDisciplineConfig config = TradingDisciplineConfig.builder()
            .accountId(accountId)
            .build();
        
        return ResponseEntity.ok(ruleEngine.generateDisciplineReport(config));
    }
    
    // ========== DTO CLASSES ==========
    
    @lombok.Data
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class DisciplineValidationRequest {
        private TradingSignal signal;
        private TradingDisciplineConfig config;
    }
    
    @lombok.Data
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class TradeResultRequest {
        private String accountId;
        private double amount;
    }
}
