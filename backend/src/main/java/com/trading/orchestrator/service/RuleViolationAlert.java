package com.trading.orchestrator.service;

import com.trading.orchestrator.model.DisciplineRule;
import com.trading.orchestrator.model.RuleViolation;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.Map;

/**
 * Alert for a rule violation - used during validation
 */
@Data
@Builder
@AllArgsConstructor
public class RuleViolationAlert {
    private DisciplineRule rule;
    private RuleViolation.ViolationSeverity severity;
    private String message;
    private String vietnameseMessage;
    private Map<String, Object> details;
    
    @Override
    public String toString() {
        return "\n" + message + 
               "\n📝 " + vietnameseMessage +
               "\nDetails: " + details;
    }
}
