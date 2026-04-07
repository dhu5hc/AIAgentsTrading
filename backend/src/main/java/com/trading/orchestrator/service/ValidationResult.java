package com.trading.orchestrator.service;

import com.trading.orchestrator.model.TradingSignal;
import com.trading.orchestrator.model.TradingDisciplineConfig;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.List;

/**
 * Result of validation against discipline rules
 */
@Data
@Builder
@AllArgsConstructor
public class ValidationResult {
    
    /**
     * The signal being validated
     */
    private TradingSignal signal;
    
    /**
     * The config used for validation
     */
    private TradingDisciplineConfig config;
    
    /**
     * Is the signal valid (no violations)?
     */
    private boolean valid;
    
    /**
     * Critical violations that prevent trade execution
     */
    private List<RuleViolationAlert> violations;
    
    /**
     * Warnings that should be shown but may allow trade with user confirmation
     */
    private List<RuleViolationAlert> warnings;
    
    /**
     * Generate feedback message for UI/user
     */
    public String generateFeedback() {
        StringBuilder sb = new StringBuilder();
        
        if (valid) {
            sb.append("✅ VALIDATION PASSED - Ready to Trade!\n");
            if (!warnings.isEmpty()) {
                sb.append("\n⚠️ WARNINGS:\n");
                warnings.forEach(w -> sb.append(w.toString()).append("\n"));
            }
        } else {
            sb.append("❌ VALIDATION FAILED - Trade BLOCKED\n\n");
            sb.append("VIOLATIONS:\n");
            violations.forEach(v -> sb.append(v.toString()).append("\n"));
            
            if (!warnings.isEmpty()) {
                sb.append("\n⚠️ WARNINGS:\n");
                warnings.forEach(w -> sb.append(w.toString()).append("\n"));
            }
        }
        
        return sb.toString();
    }
}
