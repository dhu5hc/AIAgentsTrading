package com.trading.orchestrator.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "rule_violations")
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuleViolation {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    /**
     * Liên kết đến trading signal
     */
    @ManyToOne
    @JoinColumn(name = "signal_id", nullable = false)
    private TradingSignal signal;
    
    /**
     * Rule nào bị vi phạm
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DisciplineRule violatedRule;
    
    /**
     * Mô tả chi tiết vi phạm
     */
    @Column(columnDefinition = "TEXT")
    private String violationMessage;
    
    /**
     * Mức độ nghiêm trọng: LOW, MEDIUM, HIGH, CRITICAL
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ViolationSeverity severity;
    
    /**
     * Trạng thái: WARNED, PREVENTED, LOCKED
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ViolationStatus status;
    
    /**
     * Dữ liệu liên quan đến vi phạm (JSON)
     */
    @Column(columnDefinition = "TEXT")
    private String violationData;
    
    /**
     * Thời điểm phát hiện vi phạm
     */
    @Column(nullable = false)
    private LocalDateTime detectedAt;
    
    /**
     * Thời điểm user được cảnh báo
     */
    private LocalDateTime warnedAt;
    
    /**
     * Thời điểm hệ thống ngăn chặn
     */
    private LocalDateTime preventedAt;
    
    public enum ViolationSeverity {
        LOW,              // Cảnh báo nhẹ
        MEDIUM,           // Cảnh báo trung bình
        HIGH,             // Nguy hiểm
        CRITICAL          // Ngăn chặn ngay lập tức
    }
    
    public enum ViolationStatus {
        WARNED,           // Đã cảnh báo, chờ user xác nhận
        PREVENTED,        // Đã ngăn chặn lệnh
        LOCKED            // Tài khoản bị khoá, không được trade
    }
}
