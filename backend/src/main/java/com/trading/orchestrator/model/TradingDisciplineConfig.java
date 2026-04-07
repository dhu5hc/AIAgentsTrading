package com.trading.orchestrator.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

/**
 * Configuration cho Absolute Discipline Framework
 * Quản lý các giới hạn rủi ro, FOMO detection, và session management
 */
@Data
@Entity
@Table(name = "trading_discipline_config")
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradingDisciplineConfig {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    /**
     * Định danh trader/account
     */
    @Column(nullable = false, unique = true)
    private String accountId;
    
    // ========== CONFIDENCE RULES ==========
    /**
     * Ngưỡng confidence tối thiểu để được phép trade (0.0 - 1.0)
     * Default: 0.60 (60%)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double minConfidenceThreshold = 0.60;
    
    // ========== STOP LOSS RULES ==========
    /**
     * Bắt buộc phải set Stop Loss
     * Default: true
     */
    @Column(nullable = false)
    @Builder.Default
    private Boolean stopLossRequired = true;
    
    /**
     * SL phải cách entry tối thiểu bao nhiêu % (để tránh SL quá sâu)
     * Default: 0.01 (1%)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double minStopLossPercentage = 0.01;
    
    /**
     * SL tối đa bao nhiêu % (để tránh SL quá xa)
     * Default: 0.10 (10%)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double maxStopLossPercentage = 0.10;
    
    // ========== RISK MANAGEMENT RULES ==========
    /**
     * Rủi ro tối đa cho một lệnh (% của account)
     * Default: 0.02 (2% risk per trade)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double maxRiskPerTrade = 0.02;
    
    /**
     * Rủi ro tối đa mỗi ngày (% của account)
     * Default: 0.05 (5% daily risk)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double maxDailyRisk = 0.05;
    
    /**
     * Account balance hiện tại (để tính toán rủi ro)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double accountBalance = 10000.0;
    
    // ========== FOMO DETECTION ==========
    /**
     * Phát hiện FOMO nếu có ngắt lệnh rapid trong khoảng thời gian ngắn
     * Số lệnh tối đa trong thời kỳ (default: 3 lệnh)
     */
    @Column(nullable = false)
    @Builder.Default
    private Integer maxOrdersInPeriod = 3;
    
    /**
     * Thời kỳ kiểm tra FOMO (đơn vị: giây)
     * Default: 300 (5 phút)
     */
    @Column(nullable = false)
    @Builder.Default
    private Long fomoDetectionWindowSeconds = 300L;
    
    /**
     * FOMO likelihood threshold (0.0 - 1.0)
     * Nếu vượt qua, cảnh báo FOMO
     * Default: 0.70
     */
    @Column(nullable = false)
    @Builder.Default
    private Double fomoThreshold = 0.70;
    
    // ========== RECOVERY & BREAK RULES ==========
    /**
     * Số lệnh thua liên tiếp trước khi được yêu cầu nghỉ
     * Default: 3 lệnh thua liên tiếp
     */
    @Column(nullable = false)
    @Builder.Default
    private Integer consecutiveLossesTriggerBreak = 3;
    
    /**
     * Lợi nhuận/lỗ hôm nay (%)
     */
    @Column(nullable = false)
    @Builder.Default
    private Double dailyProfitLoss = 0.0;
    
    /**
     * Tracking consecutive losses
     */
    @Column(nullable = false)
    @Builder.Default
    private Integer currentConsecutiveLosses = 0;
    
    // ========== TRADING SESSION STATUS ==========
    /**
     * Trạng thái trading: ACTIVE, BREAK, LOCKED
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private TradingSessionStatus sessionStatus = TradingSessionStatus.ACTIVE;
    
    /**
     * Lý do khoá trading (nếu LOCKED)
     */
    @Column(columnDefinition = "TEXT")
    private String lockReason;
    
    /**
     * Thời điểm bắt đầu break/lock
     */
    private LocalDateTime statusChangedAt;
    
    /**
     * Thời điểm kết thúc break (nếu có)
     */
    private LocalDateTime breakEndsAt;
    
    // ========== METADATA ==========
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    @Column(nullable = false)
    private LocalDateTime updatedAt;
    
    public enum TradingSessionStatus {
        ACTIVE,        // Bình thường, có thể trade
        BREAK,         // Đang nghỉ sau loss, không được trade
        LOCKED         // Khoá account do vi phạm rule
    }
    
    /**
     * Kiểm tra xem có đang trong break hay không
     */
    public boolean isInBreak() {
        if (sessionStatus == TradingSessionStatus.BREAK && breakEndsAt != null) {
            return LocalDateTime.now().isBefore(breakEndsAt);
        }
        return false;
    }
    
    /**
     * Kiểm tra xem account có bị khoá hay không
     */
    public boolean isLocked() {
        return sessionStatus == TradingSessionStatus.LOCKED;
    }
}
