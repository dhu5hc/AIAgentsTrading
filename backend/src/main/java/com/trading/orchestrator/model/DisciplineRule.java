package com.trading.orchestrator.model;

/**
 * Enum representing the 4 Absolute Discipline Rules
 * The iron laws of trading psychology and behavior
 */
public enum DisciplineRule {
    CONFIDENCE_CHECK(
        "Không chắc → không trade",
        "You must have at least 60% confidence before trading"
    ),
    STOP_LOSS_REQUIRED(
        "Không có SL → không trade",
        "Stop loss must be set before placing any order"
    ),
    QUICK_EXIT_ON_LOSS(
        "Sai → cắt ngay",
        "Exit immediately when stop loss is hit - no hesitation"
    ),
    BREAK_AFTER_LOSS(
        "Thua → nghỉ",
        "Take a break after N consecutive losses (emotional recovery)"
    );

    private final String vietnameseName;
    private final String description;

    DisciplineRule(String vietnameseName, String description) {
        this.vietnameseName = vietnameseName;
        this.description = description;
    }

    public String getVietnameseName() {
        return vietnameseName;
    }

    public String getDescription() {
        return description;
    }
}
