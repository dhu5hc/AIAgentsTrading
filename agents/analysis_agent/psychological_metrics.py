"""
Psychological Metrics - Phát hiện các chỉ số tâm lý trong giao dịch
FOMO Detection, Revenge Trading, Overconfidence, Risk Aversion, Impatience
"""
import json
import logging
from typing import Dict, List
from enum import Enum
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PsychologicalRiskLevel(Enum):
    """Mức độ rủi ro tâm lý"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PsychologicalMetrics:
    """Phát hiện các rủi ro tâm lý trong hành vi giao dịch"""
    
    def __init__(self):
        self.fomo_threshold = 0.7  # Threshold để phát hiện FOMO
        self.revenge_threshold = 1.5  # Lot size increase after loss
        self.overconfidence_threshold = 3  # Win streak threshold
        
    def analyze_psychological_state(self, trading_history: Dict, current_signals: List[Dict]) -> Dict:
        """Phân tích trạng thái tâm lý hiện tại của trader"""
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'fomo_score': self._calculate_fomo_score(trading_history, current_signals),
            'revenge_trading_score': self._calculate_revenge_trading_score(trading_history),
            'overconfidence_score': self._calculate_overconfidence_score(trading_history),
            'risk_aversion_score': self._calculate_risk_aversion_score(trading_history),
            'impatience_score': self._calculate_impatience_score(trading_history),
            'overall_risk_level': PsychologicalRiskLevel.LOW,
            'warning_flags': [],
            'recommendations': []
        }
        
        # Tính overall risk level
        scores = [
            analysis['fomo_score'],
            analysis['revenge_trading_score'],
            analysis['overconfidence_score']
        ]
        avg_score = np.mean(scores)
        
        if avg_score > 0.75:
            analysis['overall_risk_level'] = PsychologicalRiskLevel.CRITICAL
        elif avg_score > 0.5:
            analysis['overall_risk_level'] = PsychologicalRiskLevel.HIGH
        elif avg_score > 0.25:
            analysis['overall_risk_level'] = PsychologicalRiskLevel.MEDIUM
        else:
            analysis['overall_risk_level'] = PsychologicalRiskLevel.LOW
        
        # Thêm warnings và recommendations
        analysis['warning_flags'] = self._generate_warnings(analysis)
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _calculate_fomo_score(self, trading_history: Dict, current_signals: List[Dict]) -> float:
        """
        Tính FOMO score (Fear Of Missing Out)
        Indicators:
        - Entry ngay sau high volatility
        - Entry sau uptrend mạnh
        - Entry khi giá vừa breakthrough
        - Multiple rapid trades
        """
        score = 0.0
        
        # Check rapid entries (FOMO indicator)
        if 'time_patterns' in trading_history:
            # Nếu trader entry > 5 trades/hour = potential FOMO
            trades_per_hour = trading_history['time_patterns'].get('trades_per_day', 0) * 24
            if trades_per_hour > 5:
                score += min(0.4, (trades_per_hour - 5) / 10)
        
        # Check entry at resistance/breakout
        if 'entry_exit_patterns' in trading_history:
            entry_patterns = trading_history['entry_exit_patterns'].get('entry_patterns', {})
            # Nếu entry deviation cao = entry vào high volatility
            deviation = entry_patterns.get('avg_entry_price_deviation', 0)
            if deviation > 2:  # More than 2% deviation from market price
                score += min(0.3, deviation / 10)
        
        # Check lot size spikes during hot market
        if 'lot_size_patterns' in trading_history:
            lot_trend = trading_history['lot_size_patterns'].get('lot_size_trend', '')
            if lot_trend == "INCREASING":
                score += 0.2
        
        # Check recent win streak -> entering next trade quickly
        if 'discipline_violations' in trading_history:
            # Nếu có many consecutive wins, trader có thể overconfident + FOMO
            pass
        
        return min(1.0, score)
    
    def _calculate_revenge_trading_score(self, trading_history: Dict) -> float:
        """
        Tính Revenge Trading score
        Indicators:
        - Lot size increase sau loss
        - Quick re-entry sau stop loss
        - Higher risk % sau losing streak
        """
        score = 0.0
        
        # Check lot size after loss
        if 'lot_size_patterns' in trading_history:
            lot_after_loss = trading_history['lot_size_patterns'].get('lot_size_after_loss', 0)
            lot_before_loss = trading_history['lot_size_patterns'].get('avg_lot_size', 1)
            
            if lot_after_loss > 0:
                ratio = lot_after_loss / lot_before_loss
                if ratio > self.revenge_threshold:
                    score += min(0.6, (ratio - 1) / 2)
        
        # Check discipline violations - revenge trades detected
        if 'discipline_violations' in trading_history:
            revenge_count = trading_history['discipline_violations'].get('revenge_trades', 0)
            # Calculate percentage
            total_trades = trading_history.get('total_trades', 1)
            revenge_percentage = (revenge_count / total_trades) * 100 if total_trades > 0 else 0
            
            if revenge_percentage > 20:  # More than 20% are revenge trades
                score += min(0.4, revenge_percentage / 100)
        
        return min(1.0, score)
    
    def _calculate_overconfidence_score(self, trading_history: Dict) -> float:
        """
        Tính Overconfidence score
        Indicators:
        - High win rate leading to larger positions
        - Reducing SL after wins
        - Ignoring technical analysis after wins
        """
        score = 0.0
        
        # High win rate
        win_rate = trading_history.get('win_rate', 0)
        if win_rate > 65:  # Suspiciously high
            score += min(0.3, (win_rate - 50) / 50)
        
        # Lot size increasing trend
        if 'lot_size_patterns' in trading_history:
            lot_trend = trading_history['lot_size_patterns'].get('lot_size_trend', '')
            if lot_trend == "INCREASING":
                score += 0.3
        
        # Low stop loss consistency
        if 'stop_loss_behavior' in trading_history:
            sl_consistency = trading_history['stop_loss_behavior'].get('sl_consistency', 0)
            if sl_consistency > 5:  # High variance in SL
                score += 0.2
        
        # Discipline violations
        if 'discipline_violations' in trading_history:
            no_sl_trades = trading_history['discipline_violations'].get('no_sl_trades', 0)
            total_trades = trading_history.get('total_trades', 1)
            no_sl_percentage = (no_sl_trades / total_trades * 100) if total_trades > 0 else 0
            
            if no_sl_percentage > 10:
                score += min(0.3, no_sl_percentage / 100)
        
        return min(1.0, score)
    
    def _calculate_risk_aversion_score(self, trading_history: Dict) -> float:
        """
        Tính Risk Aversion score
        Indicators:
        - Exiting profitable trades too early
        - Small lot sizes despite good win rate
        - Often exiting manually instead of TP
        """
        score = 0.0
        
        # Small lot sizes
        if 'lot_size_patterns' in trading_history:
            avg_lot = trading_history['lot_size_patterns'].get('avg_lot_size', 0)
            if avg_lot < 0.01:  # Very small position
                score += 0.3
        
        # Manual exits instead of TP
        if 'entry_exit_patterns' in trading_history:
            exit_patterns = trading_history['entry_exit_patterns'].get('exit_patterns', {})
            manual_exit_pct = exit_patterns.get('sl_hit_vs_manual_exit', {}).get('manual_exit_on_losses', 0)
            total_trades = trading_history.get('total_trades', 1)
            
            if manual_exit_pct / total_trades > 0.7:
                score += 0.3
        
        # Early TP exits
        early_tp_exits = 0
        if 'entry_exit_patterns' in trading_history:
            early_tp_exits = trading_history['entry_exit_patterns'].get('exit_patterns', {}).get('max_profit_reached_but_exited_early', 0)
            total_trades = trading_history.get('total_trades', 1)
            
            if early_tp_exits / total_trades > 0.3:
                score += 0.3
        
        return min(1.0, score)
    
    def _calculate_impatience_score(self, trading_history: Dict) -> float:
        """
        Tính Impatience score
        Indicators:
        - Short average trade duration
        - Quick entry/exit patterns
        - Many small profit trades
        """
        score = 0.0
        
        # Short trade duration
        if 'time_patterns' in trading_history:
            avg_duration = trading_history['time_patterns'].get('average_trade_duration_hours', 0)
            if avg_duration < 1:  # Less than 1 hour average
                score += 0.4
            elif avg_duration < 5:  # Less than 5 hours
                score += 0.2
        
        # High trade frequency
        if 'time_patterns' in trading_history:
            trades_per_day = trading_history['time_patterns'].get('trades_per_day', 0)
            if trades_per_day > 10:
                score += min(0.3, (trades_per_day - 5) / 20)
        
        # Small avg profit per trade
        avg_profit = trading_history.get('avg_profit_per_trade', 0)
        if avg_profit < 10 and trading_history.get('total_trades', 0) > 10:
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_warnings(self, analysis: Dict) -> List[str]:
        """Tạo danh sách cảnh báo dựa trên scores"""
        warnings = []
        
        if analysis['fomo_score'] > self.fomo_threshold:
            warnings.append("🚨 FOMO DETECTED: Bạn đang vào lệnh khi market nóng quá. Hãy chờ pullback!")
        
        if analysis['revenge_trading_score'] > self.revenge_threshold:
            warnings.append("⚠️ REVENGE TRADING: Bạn có xu hướng tăng lot sau loss. Hãy cắt lỗ và rest!")
        
        if analysis['overconfidence_score'] > 0.7:
            warnings.append("😤 OVERCONFIDENCE: Win streak làm bạn lơ dàng. Tăng SL ngay!")
        
        if analysis['risk_aversion_score'] > 0.7:
            warnings.append("😨 RISK AVERSION: Bạn quá sợ. Hãy để TP chạy!")
        
        if analysis['impatience_score'] > 0.7:
            warnings.append("⏰ IMPATIENCE: Bạn vào ra quá nhanh. Chọn timeframe lớn hơn!")
        
        if analysis['overall_risk_level'] == PsychologicalRiskLevel.CRITICAL:
            warnings.append("🛑 CRITICAL: Trạng thái tâm lý không ổn định. STOP TRADING ngay!")
        
        return warnings
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Tạo khuyên dựa trên analysis"""
        recommendations = []
        
        if analysis['fomo_score'] > 0.5:
            recommendations.append("Đặt Trading Plan TRƯỚC market open. Chỉ trade khi có setup jelas.")
            recommendations.append("Set daily trade limit, stop giữa chừng!")
        
        if analysis['revenge_trading_score'] > 0.5:
            recommendations.append("Kỷ luật: Loss → Rest 1h hoặc 1 ngày trước re-entry")
            recommendations.append("Lot size FIXED sau khi set. Không được thay đổi!")
        
        if analysis['overconfidence_score'] > 0.5:
            recommendations.append("Tighten SL sau mỗi 3 consecutive wins")
            recommendations.append("Review losers weekly, tìm mistakes")
        
        if analysis['risk_aversion_score'] > 0.5:
            recommendations.append("Tăng TP target dần dần. RR minimum 1:2")
            recommendations.append("Chỉ exit manual khi có technical deterioration clear")
        
        if analysis['impatience_score'] > 0.5:
            recommendations.append("Trade timeframe lớn hơn (1h+ thay vì 5m)")
            recommendations.append("Target daily P&L thay vì hourly")
        
        return recommendations
    
    def detect_real_time_psychological_hazards(self, current_trade: Dict, recent_trades: List[Dict]) -> List[str]:
        """Phát hiện các rủi ro tâm lý real-time trước khi đặt lệnh"""
        hazards = []
        
        if not recent_trades:
            return hazards
        
        # Check 1: Recent loss streak + high lot size = Revenge trading
        recent_losses = [t for t in recent_trades[-5:] if t.get('profit', 0) < 0]
        if len(recent_losses) >= 2 and current_trade.get('lot_size', 0) > 0.02:
            hazards.append("Revenge trading detected: Giảm lot size!")
        
        # Check 2: Win streak + no SL + big lot = Overconfidence
        recent_wins = [t for t in recent_trades[-5:] if t.get('profit', 0) > 0]
        if len(recent_wins) >= 3 and current_trade.get('stop_loss') is None:
            hazards.append("Overconfidence hazard: Đặt SL tight!")
        
        # Check 3: Multiple trades trong giờ cuối cùng = FOMO
        last_hour_trades = [t for t in recent_trades if (datetime.now() - pd.to_datetime(t.get('timestamp', datetime.now()))).total_seconds() < 3600]
        if len(last_hour_trades) > 5:
            hazards.append("FOMO hazard: Tạm dừng, rest!")
        
        # Check 4: Previous trade chưa close + muốn open new = Overleverage
        if any(t.get('status') == 'OPEN' for t in recent_trades[-3:]) and len(recent_trades) > 0:
            hazards.append("Overleverage hazard: Close current trade first!")
        
        return hazards
