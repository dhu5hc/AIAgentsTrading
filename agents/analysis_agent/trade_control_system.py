"""
Trade Control System - Kiểm soát lệnh dựa trên behavior analytics
Integrate với backend Discipline Rule Engine
"""
import json
import logging
from typing import Dict, List, Tuple
from enum import Enum
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeBlockReason(Enum):
    """Lý do blocking trade"""
    NO_STOP_LOSS = "NO_STOP_LOSS"
    NO_TAKE_PROFIT = "NO_TAKE_PROFIT"
    OVERSIZED_POSITION = "OVERSIZED_POSITION"
    REVENGE_TRADING = "REVENGE_TRADING"
    FOMO_DETECTED = "FOMO_DETECTED"
    DAILY_LOSS_LIMIT_HIT = "DAILY_LOSS_LIMIT_HIT"
    TRADE_LIMIT_EXCEEDED = "TRADE_LIMIT_EXCEEDED"
    IN_RECOVERY_MODE = "IN_RECOVERY_MODE"
    PSYCHOLOGICAL_HAZARD = "PSYCHOLOGICAL_HAZARD"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class TradeApprovalStatus(Enum):
    """Status of trade approval"""
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"


class TradeControlSystem:
    """Kiểm soát lệnh dựa trên behavior"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Default limits
        self.max_daily_loss = self.config.get('max_daily_loss', -100)  # Default -$100
        self.max_trades_per_day = self.config.get('max_trades_per_day', 10)
        self.max_position_risk_percent = self.config.get('max_position_risk_percent', 2)
        self.min_rr_ratio = self.config.get('min_rr_ratio', 1.5)
        self.recovery_cooldown_minutes = self.config.get('recovery_cooldown_minutes', 60)
        
        # State tracking
        self.blocked_trades = []
        self.warnings_history = []
        self.manual_overrides = {}
        
    def validate_trade(self,
                      trade_signal: Dict,
                      user_stats: Dict,
                      behavior_metrics: Dict,
                      psy_metrics: Dict,
                      recent_trades: List[Dict]) -> Tuple[TradeApprovalStatus, List[str], Dict]:
        """
        Validate trade before execution
        Returns: (status, reasons/warnings, trade_control_info)
        """
        
        reasons = []
        warnings = []
        control_info = {
            'validated_at': datetime.now().isoformat(),
            'checks_performed': [],
            'block_reasons': [],
            'warnings': [],
            'adjustments': {}
        }
        
        # Check 1: Stop Loss MUST be set
        sl_check, sl_msg = self._check_stop_loss(trade_signal)
        control_info['checks_performed'].append('stop_loss')
        if not sl_check:
            reasons.append(sl_msg)
            control_info['block_reasons'].append(TradeBlockReason.NO_STOP_LOSS.value)
        
        # Check 2: Take Profit MUST be set
        tp_check, tp_msg = self._check_take_profit(trade_signal)
        control_info['checks_performed'].append('take_profit')
        if not tp_check:
            reasons.append(tp_msg)
            control_info['block_reasons'].append(TradeBlockReason.NO_TAKE_PROFIT.value)
        
        # Check 3: Position size check
        size_check, size_msg, size_adjust = self._check_position_size(
            trade_signal, user_stats)
        control_info['checks_performed'].append('position_size')
        if not size_check:
            reasons.append(size_msg)
            control_info['block_reasons'].append(TradeBlockReason.OVERSIZED_POSITION.value)
        else:
            if size_adjust:
                warnings.append(size_msg)
                control_info['adjustments']['position_size'] = size_adjust
        
        # Check 4: Risk/Reward ratio
        rr_check, rr_msg = self._check_risk_reward_ratio(
            trade_signal, self.min_rr_ratio)
        control_info['checks_performed'].append('risk_reward_ratio')
        if not rr_check:
            warnings.append(rr_msg)
        
        # Check 5: Daily loss limit
        daily_check, daily_msg = self._check_daily_loss_limit(user_stats)
        control_info['checks_performed'].append('daily_loss_limit')
        if not daily_check:
            reasons.append(daily_msg)
            control_info['block_reasons'].append(TradeBlockReason.DAILY_LOSS_LIMIT_HIT.value)
        
        # Check 6: Daily trade limit
        trade_count_check, trade_msg = self._check_trade_count(user_stats, recent_trades)
        control_info['checks_performed'].append('trade_count')
        if not trade_count_check:
            reasons.append(trade_msg)
            control_info['block_reasons'].append(TradeBlockReason.TRADE_LIMIT_EXCEEDED.value)
        
        # Check 7: Revenge trading detection
        revenge_check, revenge_msg, revenge_adjust = self._check_revenge_trading(
            trade_signal, recent_trades, psy_metrics)
        control_info['checks_performed'].append('revenge_trading')
        if not revenge_check:
            warnings.append(revenge_msg)
            control_info['block_reasons'].append(TradeBlockReason.REVENGE_TRADING.value)
            if revenge_adjust:
                control_info['adjustments']['suggested_lot_reduction'] = revenge_adjust
        
        # Check 8: FOMO detection
        fomo_check, fomo_msg = self._check_fomo(
            trade_signal, psy_metrics, recent_trades)
        control_info['checks_performed'].append('fomo_detection')
        if not fomo_check:
            warnings.append(fomo_msg)
            control_info['block_reasons'].append(TradeBlockReason.FOMO_DETECTED.value)
        
        # Check 9: Recovery mode check
        recovery_check, recovery_msg = self._check_recovery_mode(user_stats, recent_trades)
        control_info['checks_performed'].append('recovery_mode')
        if not recovery_check:
            reasons.append(recovery_msg)
            control_info['block_reasons'].append(TradeBlockReason.IN_RECOVERY_MODE.value)
        
        # Check 10: Real-time psychological hazards
        hazard_check, hazard_msgs = self._check_psychological_hazards(
            trade_signal, recent_trades)
        control_info['checks_performed'].append('psychological_hazards')
        if hazard_msgs:
            warnings.extend(hazard_msgs)
        
        # Determine status
        status = TradeApprovalStatus.APPROVED
        if reasons:
            status = TradeApprovalStatus.BLOCKED
        elif warnings:
            status = TradeApprovalStatus.WARNING
        
        control_info['warnings'] = warnings
        
        return status, reasons + warnings, control_info
    
    def _check_stop_loss(self, trade_signal: Dict) -> Tuple[bool, str]:
        """Check if SL is set"""
        sl = trade_signal.get('stop_loss')
        
        if sl is None or sl == 0:
            return False, "❌ NO STOP LOSS SET! Rule 2: 'Không có SL → không trade'"
        
        # Check SL distance
        entry = trade_signal.get('entry_price', 0)
        if entry > 0:
            sl_pct = abs(entry - sl) / entry * 100
            if sl_pct < 0.5:  # SL quá gần
                return False, f"❌ SL quá gần ({sl_pct:.2f}%). Minimum 0.5%"
            if sl_pct > 10:
                return False, f"❌ SL quá xa ({sl_pct:.2f}%). Maximum 10%"
        
        return True, "✓ SL OK"
    
    def _check_take_profit(self, trade_signal: Dict) -> Tuple[bool, str]:
        """Check if TP is set"""
        tp = trade_signal.get('take_profit')
        
        if tp is None or tp == 0:
            return False, "❌ NO TAKE PROFIT SET! Set clear profit target"
        
        return True, "✓ TP OK"
    
    def _check_position_size(self, trade_signal: Dict, user_stats: Dict) -> Tuple[bool, str, dict]:
        """Check if position size is within risk limits"""
        lot_size = trade_signal.get('lot_size', 0)
        
        if lot_size <= 0:
            return False, "❌ Invalid lot size", None
        
        # Calculate risk percentage
        entry = trade_signal.get('entry_price', 0)
        sl = trade_signal.get('stop_loss', 0)
        
        if entry > 0 and sl > 0:
            risk_per_trade = abs(entry - sl) * lot_size
            account_balance = user_stats.get('account_balance', 1000)
            risk_pct = (risk_per_trade / account_balance) * 100
            
            if risk_pct > self.max_position_risk_percent:
                # Calculate suggested lot size
                suggested_lot = (account_balance * self.max_position_risk_percent / 100) / abs(entry - sl)
                reduction = ((suggested_lot / lot_size) - 1) * 100
                
                return False, \
                    f"❌ Position too large! Risk {risk_pct:.2f}% > max {self.max_position_risk_percent}%", \
                    {'suggested_lot': suggested_lot, 'reduction_percentage': reduction}
            
            if risk_pct < 0.1:
                return True, f"⚠️ Position small (risk {risk_pct:.2f}%). Increase if confident", None
        
        return True, f"✓ Position size OK (estimated {risk_pct:.2f}% risk)", None
    
    def _check_risk_reward_ratio(self, trade_signal: Dict, min_rr: float) -> Tuple[bool, str]:
        """Check R:R ratio"""
        entry = trade_signal.get('entry_price', 0)
        sl = trade_signal.get('stop_loss', 0)
        tp = trade_signal.get('take_profit', 0)
        
        if entry > 0 and sl > 0 and tp > 0:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            
            if risk > 0:
                rr = reward / risk
                
                if rr < min_rr:
                    return False, f"⚠️ R:R too low ({rr:.2f}:{1} < {min_rr}:1). Increase TP or tighten SL"
        
        return True, "✓ R:R OK"
    
    def _check_daily_loss_limit(self, user_stats: Dict) -> Tuple[bool, str]:
        """Check if daily loss limit exceeded"""
        daily_pnl = user_stats.get('daily_pnl', 0)
        
        if daily_pnl < self.max_daily_loss:
            return False, f"🛑 Daily loss limit hit! P&L: ${daily_pnl:.2f} <= ${self.max_daily_loss}"
        
        remaining = self.max_daily_loss - daily_pnl
        if remaining < abs(self.max_daily_loss) * 0.2:  # Less than 20% remaining
            return True, f"⚠️ Close to daily loss limit! Remaining: ${remaining:.2f}"
        
        return True, f"✓ Daily loss limit OK (remaining ${remaining:.2f})"
    
    def _check_trade_count(self, user_stats: Dict, recent_trades: List[Dict]) -> Tuple[bool, str]:
        """Check daily trade count limit"""
        # Count trades today
        today_trades = len([t for t in recent_trades if self._is_today(t.get('timestamp'))])
        
        if today_trades >= self.max_trades_per_day:
            return False, f"❌ Daily trade limit ({self.max_trades_per_day}) reached!"
        
        remaining = self.max_trades_per_day - today_trades
        return True, f"✓ Trade count OK ({today_trades}/{self.max_trades_per_day})"
    
    def _check_revenge_trading(self, trade_signal: Dict, recent_trades: List[Dict], 
                               psy_metrics: Dict) -> Tuple[bool, str, dict]:
        """Check for revenge trading pattern"""
        
        if not recent_trades:
            return True, "✓ No revenge trading pattern", None
        
        # Check last trade
        last_trade = recent_trades[-1] if recent_trades else None
        if last_trade and last_trade.get('profit', 0) < 0:  # Last trade was loss
            
            current_lot = trade_signal.get('lot_size', 0)
            last_lot = last_trade.get('lot_size', 0)
            
            if current_lot > last_lot * 1.3:  # Current lot 30% higher than loss
                psy_revenge_score = psy_metrics.get('revenge_trading_score', 0)
                
                if psy_revenge_score > 0.6:
                    suggested_lot = last_lot * 1.0  # Reset to previous level
                    return False, \
                        f"⚠️ REVENGE TRADING PATTERN! Last trade loss, now increasing lot. Take a break!", \
                        {'suggested_lot': suggested_lot, 'reason': 'revenge_detected'}
        
        return True, "✓ No revenge pattern", None
    
    def _check_fomo(self, trade_signal: Dict, psy_metrics: Dict, 
                    recent_trades: List[Dict]) -> Tuple[bool, str]:
        """Check for FOMO"""
        
        fomo_score = psy_metrics.get('fomo_score', 0)
        
        # Check rapid entry
        if len(recent_trades) > 2:
            last_trades = recent_trades[-3:]
            time_diffs = []
            for i in range(1, len(last_trades)):
                t1 = self._parse_timestamp(last_trades[i-1].get('timestamp'))
                t2 = self._parse_timestamp(last_trades[i].get('timestamp'))
                if t1 and t2:
                    diff = (t2 - t1).total_seconds() / 60
                    time_diffs.append(diff)
            
            if time_diffs and min(time_diffs) < 5:  # Less than 5 min between trades
                if fomo_score > 0.6:
                    return False, "⚠️ FOMO DETECTED! Entering too fast. Wait for pullback!"
        
        return True, "✓ No FOMO pattern"
    
    def _check_recovery_mode(self, user_stats: Dict, recent_trades: List[Dict]) -> Tuple[bool, str]:
        """Check if in recovery mode (after certain events)"""
        
        # Check if recent loss streak (3 consecutive losses)
        if len(recent_trades) >= 3:
            recent_3 = recent_trades[-3:]
            if all(t.get('profit', 0) < 0 for t in recent_3):
                # In drawdown, suggest cool-off period
                last_loss_time = self._parse_timestamp(recent_3[-1].get('timestamp'))
                current_time = datetime.now()
                
                if last_loss_time:
                    minutes_since = (current_time - last_loss_time).total_seconds() / 60
                    
                    if minutes_since < self.recovery_cooldown_minutes:
                        remaining = self.recovery_cooldown_minutes - minutes_since
                        return False, f"⚠️ RECOVERY MODE: 3 consecutive losses. Rest {remaining:.0f} more minutes"
        
        return True, "✓ Not in recovery mode"
    
    def _check_psychological_hazards(self, trade_signal: Dict, 
                                     recent_trades: List[Dict]) -> Tuple[bool, List[str]]:
        """Check real-time psychological hazards"""
        hazards = []
        
        # Check 1: No SL set (absolute rule)
        if trade_signal.get('stop_loss') is None or trade_signal.get('stop_loss') == 0:
            hazards.append("🔴 [MANDATORY] SL MUST be set before entry!")
        
        # Check 2: No TP set
        if trade_signal.get('take_profit') is None or trade_signal.get('take_profit') == 0:
            hazards.append("🔴 [MANDATORY] TP MUST be set before entry!")
        
        # Check 3: Scaling into position (multiple entry signals quickly)
        if len(recent_trades) >= 5:
            recent_5_min = [t for t in recent_trades[-5:] 
                           if self._minutes_since(t.get('timestamp')) < 5]
            if len(recent_5_min) > 2:
                hazards.append("⚠️ Rapid entries detected. Slow down!")
        
        return len(hazards) == 0, hazards
    
    def _is_today(self, timestamp) -> bool:
        """Check if timestamp is today"""
        if timestamp is None:
            return False
        
        ts = self._parse_timestamp(timestamp)
        if ts is None:
            return False
        
        return ts.date() == datetime.now().date()
    
    def _parse_timestamp(self, timestamp):
        """Parse timestamp to datetime"""
        try:
            if isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, datetime):
                return timestamp
        except:
            pass
        return None
    
    def _minutes_since(self, timestamp) -> float:
        """Get minutes since timestamp"""
        ts = self._parse_timestamp(timestamp)
        if ts:
            return (datetime.now() - ts).total_seconds() / 60
        return float('inf')
    
    def get_trade_warning_message(self, status: TradeApprovalStatus, 
                                  reasons: List[str]) -> str:
        """Format trade control message for UI"""
        
        if status == TradeApprovalStatus.APPROVED:
            return "✅ Trade APPROVED - Proceed"
        
        elif status == TradeApprovalStatus.BLOCKED:
            msg = "🛑 TRADE BLOCKED - Fix issues:\n"
            for reason in reasons:
                msg += f"• {reason}\n"
            return msg
        
        elif status == TradeApprovalStatus.WARNING:
            msg = "⚠️ WARNINGS - Review before trading:\n"
            for reason in reasons:
                msg += f"• {reason}\n"
            msg += "\n⏱️ [CONFIRM] to proceed at own risk?"
            return msg
        
        elif status == TradeApprovalStatus.NEEDS_CONFIRMATION:
            msg = "❓ NEEDS CONFIRMATION:\n"
            for reason in reasons:
                msg += f"• {reason}\n"
            return msg
        
        return "Unknown status"
