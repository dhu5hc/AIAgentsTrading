package com.trading.orchestrator.service;

import com.binance.connector.client.SpotClient;
import com.binance.connector.client.exceptions.BinanceClientException;
import com.binance.connector.client.exceptions.BinanceConnectorException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.json.JSONObject;
import java.util.*;

/**
 * Binance API Client Service
 * Kết nối với Binance REST API để thực thi lệnh trading và lấy thông tin markets
 */
@Slf4j
@Service
public class BinanceApiClient {

    private final SpotClient spotClient;
    private final String apiKey;
    private final String apiSecret;
    private final boolean testnet;

    public BinanceApiClient(
            @Value("${binance.api-key}") String apiKey,
            @Value("${binance.api-secret}") String apiSecret,
            @Value("${binance.testnet:false}") boolean testnet) {
        this.apiKey = apiKey;
        this.apiSecret = apiSecret;
        this.testnet = testnet;
        this.spotClient = new SpotClient.Builder()
                .baseUrl(testnet ? "https://testnet.binance.vision" : "https://api.binance.com")
                .apiKey(apiKey)
                .secretKey(apiSecret)
                .build();
    }

    /**
     * Đặt lệnh LIMIT
     */
    public JSONObject placeLimitOrder(String symbol, String side, String quantity, String price) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            parameters.put("side", side.toUpperCase()); // BUY or SELL
            parameters.put("type", "LIMIT");
            parameters.put("timeInForce", "GTC");
            parameters.put("quantity", quantity);
            parameters.put("price", price);

            String response = spotClient.createOrder(parameters);
            log.info("Limit order placed: {}", response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to place limit order: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to place limit order: " + e.getMessage());
        }
    }

    /**
     * Đặt lệnh MARKET
     */
    public JSONObject placeMarketOrder(String symbol, String side, String quantity) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            parameters.put("side", side.toUpperCase());
            parameters.put("type", "MARKET");
            parameters.put("quantity", quantity);

            String response = spotClient.createOrder(parameters);
            log.info("Market order placed: {}", response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to place market order: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to place market order: " + e.getMessage());
        }
    }

    /**
     * Đặt lệnh với Stop Loss và Take Profit
     */
    public JSONObject placeOrderWithStopLoss(String symbol, String side, String quantity, 
                                             String price, String stopPrice) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            parameters.put("side", side.toUpperCase());
            parameters.put("type", "LIMIT");
            parameters.put("timeInForce", "GTC");
            parameters.put("quantity", quantity);
            parameters.put("price", price);
            parameters.put("stopPrice", stopPrice);

            String response = spotClient.createOrder(parameters);
            log.info("Order with stop loss placed: {}", response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to place order with stop loss: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to place order with stop loss: " + e.getMessage());
        }
    }

    /**
     * Hủy lệnh
     */
    public JSONObject cancelOrder(String symbol, Long orderId) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            parameters.put("orderId", orderId);

            String response = spotClient.cancelOrder(parameters);
            log.info("Order cancelled: {}", response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to cancel order: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to cancel order: " + e.getMessage());
        }
    }

    /**
     * Lấy thông tin lệnh
     */
    public JSONObject getOrder(String symbol, Long orderId) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            parameters.put("orderId", orderId);

            String response = spotClient.getOrder(parameters);
            log.info("Order info retrieved: {}", response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get order: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get order: " + e.getMessage());
        }
    }

    /**
     * Lấy tất cả lệnh mở
     */
    public JSONObject getOpenOrders(String symbol) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);

            String response = spotClient.getOpenOrders(parameters);
            log.info("Open orders retrieved for {}: {}", symbol, response);
            return new JSONObject("{\"orders\":" + response + "}");
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get open orders: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get open orders: " + e.getMessage());
        }
    }

    /**
     * Lấy thông tin tài khoản
     */
    public JSONObject getAccountInfo() {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            String response = spotClient.account(parameters);
            log.info("Account info retrieved");
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get account info: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get account info: " + e.getMessage());
        }
    }

    /**
     * Lấy balance của từng asset
     */
    public JSONObject getBalance(String asset) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            String response = spotClient.account(parameters);
            JSONObject accountInfo = new JSONObject(response);
            JSONObject result = new JSONObject();
            result.put("asset", asset);
            result.put("balance", 0);
            result.put("locked", 0);

            if (accountInfo.has("balances")) {
                accountInfo.getJSONArray("balances").forEach(item -> {
                    JSONObject balance = (JSONObject) item;
                    if (balance.getString("asset").equals(asset)) {
                        result.put("balance", balance.getDouble("free"));
                        result.put("locked", balance.getDouble("locked"));
                    }
                });
            }
            return result;
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get balance: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get balance: " + e.getMessage());
        }
    }

    /**
     * Lấy tick hiện tại
     */
    public JSONObject getTicker(String symbol) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            String response = spotClient.ticketPrice(parameters);
            log.info("Ticker retrieved for {}: {}", symbol, response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get ticker: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get ticker: " + e.getMessage());
        }
    }

    /**
     * Lấy 24h price change
     */
    public JSONObject get24hStats(String symbol) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            String response = spotClient.ticker24h(parameters);
            log.info("24h stats retrieved for {}: {}", symbol, response);
            return new JSONObject(response);
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get 24h stats: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get 24h stats: " + e.getMessage());
        }
    }

    /**
     * Lấy trade history
     */
    public JSONObject getTradeHistory(String symbol, Integer limit) {
        try {
            LinkedHashMap<String, Object> parameters = new LinkedHashMap<>();
            parameters.put("symbol", symbol);
            if (limit != null) {
                parameters.put("limit", limit);
            }
            String response = spotClient.myTrades(parameters);
            log.info("Trade history retrieved for {}: {}", symbol, response);
            return new JSONObject("{\"trades\":" + response + "}");
        } catch (BinanceClientException e) {
            log.error("Binance Client Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get trade history: " + e.getMessage());
        } catch (BinanceConnectorException e) {
            log.error("Binance Connector Exception: {}", e.getMessage());
            throw new RuntimeException("Failed to get trade history: " + e.getMessage());
        }
    }
}
