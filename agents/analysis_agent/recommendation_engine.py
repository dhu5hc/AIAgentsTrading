"""
Recommendation Engine - Đưa ra khuyên dựa trên behavior analytics
"""
import json
import logging
from typing import Dict, List
from enum import Enum
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Loại khuyên"""
    POSITION_SIZE_ADJUSTMENT = "POSITION_SIZE_ADJUSTMENT"
    STRATEGY_ADJUSTMENT = "STRATEGY_ADJUSTMENT"
    TIME_MANAGEMENT = "TIME_MANAGEMENT"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    DISCIPLINE_REMINDER = "DISCIPLINE_REMINDER"
    BREAK_RECOMMENDATION = "BREAK_RECOMMENDATION"


class RecommendationEngine:
    """Đưa ra khuyên dựa trên behavior analytics"""
    
    def __init__(self):
        self.min_trades_for_analysis = 10
        
    def generate_recommendations(self, 
                                trading_history: Dict,
                                psychological_metrics: Dict,
                                current_market_conditions: Dict) -> List[Dict]:
        """Tạo danh sách khuyên chi tiết"""
        
        if trading_history.get('total_trades', 0) < self.min_trades_for_analysis:
            return self._generate_beginner_recommendations()
        
        recommendations = []
        
        # Phân tích từ rủi ro tâm lý
        recommendations.extend(self._generate_psychological_recommendations(psychological_metrics))
        
        # Phân tích từ lịch sử giao dịch
        recommendations.extend(self._generate_behavior_recommendations(trading_history))
        
        # Phân tích từ điều kiện thị trường hiện tại
        recommendations.extend(self._generate_market_timing_recommendations(
            trading_history, current_market_conditions))
        
        # Ranking khuyên theo priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations
    
    def _generate_beginner_recommendations(self) -> List[Dict]:
        """Khuyên cho trader mới"""
        return [
            {
                'type': RecommendationType.DISCIPLINE_REMINDER,
                'title': 'Xây dựng lịch sử giao dịch',
                'description': 'Hãy hoàn thành ít nhất 10 giao dịch để hệ thống có thể phân tích hành vi',
                'priority': 10,
                'action': 'CONTINUE_TRADING'
            }
        ]
    
    def _generate_psychological_recommendations(self, psych_metrics: Dict) -> List[Dict]:
        """Khuyên dựa trên metrics tâm lý"""
        recommendations = []
        
        # FOMO recommendations
        if psych_metrics['fomo_score'] > 0.6:
            recommendations.append({
                'type': RecommendationType.STRATEGY_ADJUSTMENT,
                'title': 'Chế độ Anti-FOMO',
                'description': 'Bạn có xu hướng vào thị trường khi nó "nóng". Hãy:',
                'details': [
                    '1. Tắt TradingView tín hiệu hoặc notifications',
                    '2. Set trading hours cố định (ví dụ: 9-11am, 3-5pm)',
                    '3. Chỉ trade khi có "setup rõ ràng" theo plan'
                ],
                'priority': 9,
                'action': 'SET_TRADING_SCHEDULE'
            })
        
        # Revenge Trading recommendations
        if psych_metrics['revenge_trading_score'] > 0.6:
            recommendations.append({
                'type': RecommendationType.TIME_MANAGEMENT,
                'title': 'Stop & Rest Protocol',
                'description': 'Phát hiện xu hướng "revenge trading" sau loss',
                'details': [
                    '1. Sau mỗi loss ngay lập tức, rest 30-60 phút',
                    '2. Set daily max losses limit (ví dụ: -$100)',
                    '3. Khi đạt max loss → đóng terminal ngay',
                    '4. Review tại sao loss, không re-trade ngay'
                ],
                'priority': 10,
                'action': 'SET_LOSS_LIMIT'
            })
        
        # Overconfidence recommendations
        if psych_metrics['overconfidence_score'] > 0.6:
            recommendations.append({
                'type': RecommendationType.RISK_MANAGEMENT,
                'title': 'Anti-Overconfidence Rules',
                'description': 'Sau win streak, bạn có xu hướng rủi ro cao hơn',
                'details': [
                    '1. Set FIXED lot size, không được thay đổi',
                    '2. Mỗi 3 consecutive wins → tighten SL 10%',
                    '3. Sau 5 consecutive wins → rest 1 tradeday',
                    '4. Review trade plan weekly'
                ],
                'priority': 8,
                'action': 'SET_FIXED_LOT'
            })
        
        # Risk Aversion recommendations
        if psych_metrics['risk_aversion_score'] > 0.6:
            recommendations.append({
                'type': RecommendationType.STRATEGY_ADJUSTMENT,
                'title': 'Kiểm soát Exit Fear',
                'description': 'Bạn có xu hướng exit quá sớm before TP',
                'details': [
                    '1. Set TP cách xa entry tối thiểu 1:2 RR',
                    '2. Khi entry, "lock" TP tại một vị trí cố định',
                    '3. Chỉ move SL, không được move TP xuống',
                    '4. Để TP "tự chạy" - không touch trong lúc trade'
                ],
                'priority': 8,
                'action': 'SET_FIXED_TP'
            })
        
        # Impatience recommendations
        if psych_metrics['impatience_score'] > 0.6:
            recommendations.append({
                'type': RecommendationType.TIME_MANAGEMENT,
                'title': 'Slow Down Protocol',
                'description': 'Bạn trade quá nhanh/nhập nhằng. Tăng timeframe',
                'details': [
                    f'1. Đổi từ timeframe hiện tại sang timeframe lớn hơn',
                    '2. Target: average 2-3 trades/day, không 10+',
                    '3. Set daily trade limit (ví dụ: 5 trades/day)',
                    '4. Mỗi trade, pause 5 phút trước setup tiếp theo'
                ],
                'priority': 7,
                'action': 'INCREASE_TIMEFRAME'
            })
        
        return recommendations
    
    def _generate_behavior_recommendations(self, history: Dict) -> List[Dict]:
        """Khuyên dựa trên hành vi giao dịch"""
        recommendations = []
        
        # Win rate analysis
        win_rate = history.get('win_rate', 0)
        if win_rate < 40:
            recommendations.append({
                'type': RecommendationType.STRATEGY_ADJUSTMENT,
                'title': 'Cải thiện Win Rate',
                'description': f'Win rate của bạn là {win_rate:.1f}% - dưới 45% là nguy hiểm',
                'details': [
                    '1. Review các trade thua: tại sao fail?',
                    '2. Cải thiện entry: chờ confirmation, không rush',
                    '3. Tighten SL: lỗ sẽ nhỏ hơn',
                    '4. Xem xét thay đổi strategy hoàn toàn'
                ],
                'priority': 10,
                'action': 'REVIEW_STRATEGY'
            })
        
        # Drawdown analysis
        drawdown = history.get('drawdown_analysis', {}).get('drawdown_percentage', 0)
        if drawdown > 20:
            recommendations.append({
                'type': RecommendationType.RISK_MANAGEMENT,
                'title': 'Giảm Drawdown',
                'description': f'Drawdown của bạn là {drawdown:.1f}% - quá cao!',
                'details': [
                    '1. Giảm lot size ngay 30%',
                    '2. Tighten SL 20-30%',
                    '3. Chỉ take high-probability setups',
                    '4. Tính toán risk/trade = $X only'
                ],
                'priority': 9,
                'action': 'REDUCE_POSITION_SIZE'
            })
        
        # Discipline violations
        violations = history.get('discipline_violations', {})
        no_sl_trades = violations.get('no_sl_trades', 0)
        total_trades = history.get('total_trades', 1)
        no_sl_pct = (no_sl_trades / total_trades * 100) if total_trades > 0 else 0
        
        if no_sl_pct > 5:
            recommendations.append({
                'type': RecommendationType.DISCIPLINE_REMINDER,
                'title': 'LUÔN SET STOP LOSS',
                'description': f'{no_sl_pct:.1f}% trade của bạn không có SL. Đây là violation nghiêm trọng!',
                'details': [
                    '1. Quy tắc tuyệt đối: KHÔNG TRADE NẾU KHÔNG CÓ SL',
                    '2. SL phải được set TRƯỚC khi entry',
                    '3. SL = max loss bạn chấp nhận',
                    '4. Không được move SL "out" sau entry'
                ],
                'priority': 10,
                'action': 'MANDATORY_SL'
            })
        
        no_tp_trades = violations.get('no_tp_trades', 0)
        no_tp_pct = (no_tp_trades / total_trades * 100) if total_trades > 0 else 0
        
        if no_tp_pct > 5:
            recommendations.append({
                'type': RecommendationType.DISCIPLINE_REMINDER,
                'title': 'LUÔN SET TAKE PROFIT',
                'description': f'{no_tp_pct:.1f}% trade của bạn không có TP. Set clear exit target!',
                'details': [
                    '1. Quy tắc: Mỗi trade có TP cụ thể',
                    '2. TP = profit target hoặc technical level',
                    '3. Khi đạt TP → close 50% hoặc trail SL',
                    '4. Chỉ trail nếu trend còn strong'
                ],
                'priority': 9,
                'action': 'MANDATORY_TP'
            })
        
        oversized = violations.get('oversized_positions', 0)
        oversized_pct = (oversized / total_trades * 100) if total_trades > 0 else 0
        
        if oversized_pct > 10:
            recommendations.append({
                'type': RecommendationType.RISK_MANAGEMENT,
                'title': 'Position Sizing Issue',
                'description': f'{oversized_pct:.1f}% trades vượt quá 2% account risk',
                'details': [
                    '1. Công thức: Risk = account * 1-2%',
                    '2. Từ risk tính ngược lot size',
                    '3. Lot size = Risk / (entry - SL) / pip value',
                    '4. Không bao giờ vượt giới hạn'
                ],
                'priority': 9,
                'action': 'RECALCULATE_LOT'
            })
        
        # Symbol focus
        symbols = history.get('symbol_patterns', {}).get('favorite_symbols', {})
        if len(symbols) > 5:
            recommendations.append({
                'type': RecommendationType.STRATEGY_ADJUSTMENT,
                'title': 'Focus on Best Symbols',
                'description': 'Bạn trade quá nhiều symbols khác nhau',
                'details': [
                    '1. Chỉ focus trên TOP 3 symbols tốt nhất',
                    '2. Mỗi symbol: learn deep (levels, patterns)',
                    '3. Học kết hợp: correlations, zones',
                    '4. Giảm symbols → tăng win rate'
                ],
                'priority': 7,
                'action': 'FOCUS_SYMBOLS'
            })
        
        return recommendations
    
    def _generate_market_timing_recommendations(self, 
                                              history: Dict,
                                              market_conditions: Dict) -> List[Dict]:
        """Khuyên dựa trên market timing"""
        recommendations = []
        
        # Time pattern analysis
        time_patterns = history.get('time_patterns', {})
        
        # Peak trading hours - trader nên know best time
        peak_hours = time_patterns.get('peak_trading_hours', {})
        if peak_hours:
            best_hour = max(peak_hours.items(), key=lambda x: x[1])[0]
            recommendations.append({
                'type': RecommendationType.TIME_MANAGEMENT,
                'title': 'Optimize Trading Hours',
                'description': f'Bạn trade tốt nhất vào {best_hour}:00',
                'details': [
                    f'1. Focus trading vào {best_hour}:00 (peak performance)',
                    '2. Ngoài giờ peak → quality over quantity',
                    '3. Set alarm trước peak hours 15 phút',
                    '4. Off-peak hours: nên tính toán kỹ hơn'
                ],
                'priority': 6,
                'action': 'SET_PEAK_HOURS'
            })
        
        # Market volatility - high volatility = FOMO risk
        if market_conditions.get('volatility', 'NORMAL') == 'HIGH':
            recommendations.append({
                'type': RecommendationType.DISCIPLINE_REMINDER,
                'title': 'HIGH Volatility Protocol',
                'description': 'Hiện tại thị trường rất volatile',
                'details': [
                    '1. GIẢM lot size 50% (half size)',
                    '2. Tighten SL hơn',
                    '3. Chỉ take HIGH quality setups',
                    '4. TRÁNH scalping, position trade only'
                ],
                'priority': 8,
                'action': 'REDUCE_LOT_HIGH_VOL'
            })
        
        return recommendations
    
    def rank_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Xếp hạng khuyên theo priority và urgency"""
        # Group by type
        grouped = {}
        for rec in recommendations:
            rec_type = rec['type'].value
            if rec_type not in grouped:
                grouped[rec_type] = []
            grouped[rec_type].append(rec)
        
        # Sort within each group
        for rec_type in grouped:
            grouped[rec_type].sort(key=lambda x: x['priority'], reverse=True)
        
        # Flatten
        ranked = []
        for rec_type in sorted(grouped.keys()):
            ranked.extend(grouped[rec_type])
        
        return ranked
    
    def format_recommendations_for_ui(self, recommendations: List[Dict]) -> str:
        """Format khuyên cho UI display"""
        if not recommendations:
            return "Không có khuyên - Hành vi giao dịch tốt!"
        
        output = "📊 BEHAVIOR ANALYTICS - RECOMMENDATIONS\n"
        output += "=" * 50 + "\n\n"
        
        for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
            priority_icon = "🔴" if rec['priority'] >= 9 else "🟡" if rec['priority'] >= 7 else "🟢"
            
            output += f"{priority_icon} [{i}] {rec['title']}\n"
            output += f"Type: {rec['type'].value}\n"
            output += f"Description: {rec['description']}\n"
            
            if 'details' in rec and rec['details']:
                output += "Action Items:\n"
                for detail in rec['details']:
                    output += f"  • {detail}\n"
            
            output += f"Priority: {rec['priority']}/10\n"
            output += "-" * 50 + "\n"
        
        return output
