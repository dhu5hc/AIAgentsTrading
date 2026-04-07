package com.trading.orchestrator.controller;

import com.trading.orchestrator.service.BinanceApiClient;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.json.JSONObject;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Binance API Controller
 * Cung cấp các endpoints để interact với Binance API
 */
@Slf4j
@RestController
@RequestMapping("/api/binance")
@RequiredArgsConstructor
@Tag(name = "Binance API", description = "Binance Market và Trading APIs")
public class BinanceController {

    private final BinanceApiClient binanceApiClient;

    // ==================== MARKET DATA ====================

    @GetMapping("/ticker/{symbol}")
    @Operation(summary = "Lấy thông tin giá hiện tại của một cặp")
    public ResponseEntity<?> getTicker(@PathVariable String symbol) {
        try {
            JSONObject result = binanceApiClient.getTicker(symbol);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/stats24h/{symbol}")
    @Operation(summary = "Lấy thông tin thay đổi giá trong 24h")
    public ResponseEntity<?> get24hStats(@PathVariable String symbol) {
        try {
            JSONObject result = binanceApiClient.get24hStats(symbol);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    // ==================== ACCOUNT ====================

    @GetMapping("/account")
    @Operation(summary = "Lấy thông tin tài khoản")
    public ResponseEntity<?> getAccountInfo() {
        try {
            JSONObject result = binanceApiClient.getAccountInfo();
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/balance/{asset}")
    @Operation(summary = "Lấy balance của một asset")
    public ResponseEntity<?> getBalance(@PathVariable String asset) {
        try {
            JSONObject result = binanceApiClient.getBalance(asset);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    // ==================== ORDERS ====================

    @PostMapping("/order/limit")
    @Operation(summary = "Đặt lệnh LIMIT")
    public ResponseEntity<?> placeLimitOrder(
            @RequestParam String symbol,
            @RequestParam String side,
            @RequestParam String quantity,
            @RequestParam String price) {
        try {
            JSONObject result = binanceApiClient.placeLimitOrder(symbol, side, quantity, price);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            log.error("Error placing limit order", e);
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @PostMapping("/order/market")
    @Operation(summary = "Đặt lệnh MARKET")
    public ResponseEntity<?> placeMarketOrder(
            @RequestParam String symbol,
            @RequestParam String side,
            @RequestParam String quantity) {
        try {
            JSONObject result = binanceApiClient.placeMarketOrder(symbol, side, quantity);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            log.error("Error placing market order", e);
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @PostMapping("/order/stop-loss")
    @Operation(summary = "Đặt lệnh với Stop Loss")
    public ResponseEntity<?> placeOrderWithStopLoss(
            @RequestParam String symbol,
            @RequestParam String side,
            @RequestParam String quantity,
            @RequestParam String price,
            @RequestParam String stopPrice) {
        try {
            JSONObject result = binanceApiClient.placeOrderWithStopLoss(symbol, side, quantity, price, stopPrice);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            log.error("Error placing order with stop loss", e);
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/orders/open/{symbol}")
    @Operation(summary = "Lấy tất cả lệnh mở")
    public ResponseEntity<?> getOpenOrders(@PathVariable String symbol) {
        try {
            JSONObject result = binanceApiClient.getOpenOrders(symbol);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/order/{symbol}/{orderId}")
    @Operation(summary = "Lấy thông tin chi tiết lệnh")
    public ResponseEntity<?> getOrder(
            @PathVariable String symbol,
            @PathVariable Long orderId) {
        try {
            JSONObject result = binanceApiClient.getOrder(symbol, orderId);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    @DeleteMapping("/order/{symbol}/{orderId}")
    @Operation(summary = "Hủy lệnh")
    public ResponseEntity<?> cancelOrder(
            @PathVariable String symbol,
            @PathVariable Long orderId) {
        try {
            JSONObject result = binanceApiClient.cancelOrder(symbol, orderId);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            log.error("Error cancelling order", e);
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }

    // ==================== TRADE HISTORY ====================

    @GetMapping("/trades/{symbol}")
    @Operation(summary = "Lấy trade history")
    public ResponseEntity<?> getTradeHistory(
            @PathVariable String symbol,
            @RequestParam(required = false) Integer limit) {
        try {
            JSONObject result = binanceApiClient.getTradeHistory(symbol, limit != null ? limit : 10);
            return ResponseEntity.ok(result.toMap());
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Error: " + e.getMessage());
        }
    }
}
