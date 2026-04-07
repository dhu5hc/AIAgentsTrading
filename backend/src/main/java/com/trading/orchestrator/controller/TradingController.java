package com.trading.orchestrator.controller;

import com.trading.orchestrator.model.TradingSignal;
import com.trading.orchestrator.service.TradingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/trading")
@RequiredArgsConstructor
public class TradingController {
    
    private final TradingService tradingService;
    
    @GetMapping("/signals")
    public ResponseEntity<List<TradingSignal>> getSignals(
            @RequestParam(required = false) String symbol,
            @RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(tradingService.getRecentSignals(symbol, limit));
    }
    
    @PostMapping("/signals/{signalId}/approve")
    public ResponseEntity<TradingSignal> approveSignal(@PathVariable Long signalId) {
        return ResponseEntity.ok(tradingService.approveSignal(signalId));
    }
    
    @PostMapping("/signals/{signalId}/reject")
    public ResponseEntity<TradingSignal> rejectSignal(@PathVariable Long signalId) {
        return ResponseEntity.ok(tradingService.rejectSignal(signalId));
    }
    
    @GetMapping("/portfolio")
    public ResponseEntity<Map<String, Object>> getPortfolio() {
        return ResponseEntity.ok(tradingService.getPortfolio());
    }
    
    @GetMapping("/performance")
    public ResponseEntity<Map<String, Object>> getPerformance() {
        return ResponseEntity.ok(tradingService.getPerformance());
    }
    
    @PostMapping("/start")
    public ResponseEntity<String> startTrading() {
        tradingService.startTrading();
        return ResponseEntity.ok("Trading started");
    }
    
    @PostMapping("/stop")
    public ResponseEntity<String> stopTrading() {
        tradingService.stopTrading();
        return ResponseEntity.ok("Trading stopped");
    }
    
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        return ResponseEntity.ok(tradingService.getSystemStatus());
    }
}
