"""
Trading History Analyzer - Phân tích lịch sử giao dịch để hiểu hành vi trader
"""
import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingHistoryAnalyzer:
    """Phân tích lịch sử giao dịch và mô hình hành vi"""
    
    def __init__(self, redis_client, timeframe_days: int = 30):
        self.redis_client = redis_client
        self.timeframe_days = timeframe_days
        
    def analyze_trading_history(self, user_id: str) -> Dict:
        """Phân tích toàn bộ lịch sử giao dịch của user"""
        try:
            # Lấy lịch sử giao dịch từ Redis/DB
            trades = self._fetch_user_trades(user_id)
            
            if not trades:
                logger.warning(f"No trades found for user {user_id}")
                return self._empty_analysis()
            
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            analysis = {
                'user_id': user_id,
                'total_trades': len(df),
                'win_rate': self._calculate_win_rate(df),
                'avg_profit_per_trade': self._calculate_avg_profit(df),
                'drawdown_analysis': self._calculate_drawdown(df),
                'time_patterns': self._analyze_time_patterns(df),
                'symbol_patterns': self._analyze_symbol_patterns(df),
                'lot_size_patterns': self._analyze_lot_size_patterns(df),
                'entry_exit_patterns': self._analyze_entry_exit_patterns(df),
                'discipline_violations': self._detect_discipline_violations(df),
                'recovery_time': self._analyze_recovery_time(df),
                'profit_taking_behavior': self._analyze_profit_taking(df),
                'stop_loss_behavior': self._analyze_stop_loss_behavior(df),
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing trading history: {e}")
            return self._empty_analysis()
    
    def _fetch_user_trades(self, user_id: str) -> List[Dict]:
        """Lấy lịch sử giao dịch từ Redis"""
        try:
            trades_key = f"trades:{user_id}:*"
            # Mocked data - trong production sẽ query từ database
            return self.redis_client.get(f"trades:{user_id}") or []
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    def _calculate_win_rate(self, df: pd.DataFrame) -> float:
        """Tính win rate"""
        if len(df) == 0:
            return 0.0
        
        winning_trades = len(df[df['profit'] > 0])
        return (winning_trades / len(df)) * 100
    
    def _calculate_avg_profit(self, df: pd.DataFrame) -> float:
        """Tính trung bình lợi nhuận"""
        if len(df) == 0:
            return 0.0
        return df['profit'].mean()
    
    def _calculate_drawdown(self, df: pd.DataFrame) -> Dict:
        """Tính drawdown analysis"""
        if len(df) == 0:
            return {'max_drawdown': 0, 'current_drawdown': 0, 'drawdown_percentage': 0}
        
        # Tính cumulative profit
        df['cumulative_profit'] = df['profit'].cumsum()
        
        # Max drawdown
        running_max = df['cumulative_profit'].expanding().max()
        drawdown = running_max - df['cumulative_profit']
        max_drawdown = drawdown.max()
        
        return {
            'max_drawdown': float(max_drawdown),
            'current_drawdown': float(drawdown.iloc[-1]) if len(drawdown) > 0 else 0,
            'drawdown_percentage': float((max_drawdown / max(abs(running_max.max()), 1)) * 100)
        }
    
    def _analyze_time_patterns(self, df: pd.DataFrame) -> Dict:
        """Phân tích mô hình thời gian - trader thường trade lúc nào?"""
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        return {
            'peak_trading_hours': df['hour'].value_counts().head(3).to_dict(),
            'peak_trading_days': df['day_of_week'].value_counts().head(3).to_dict(),
            'trades_per_day': len(df) / max((df['timestamp'].max() - df['timestamp'].min()).days, 1),
            'average_trade_duration_hours': self._calculate_avg_trade_duration(df)
        }
    
    def _calculate_avg_trade_duration(self, df: pd.DataFrame) -> float:
        """Tính duration trung bình của một trade"""
        if 'entry_time' not in df.columns or 'exit_time' not in df.columns:
            return 0.0
        
        df['duration'] = pd.to_datetime(df['exit_time']) - pd.to_datetime(df['entry_time'])
        return df['duration'].mean().total_seconds() / 3600  # Convert to hours
    
    def _analyze_symbol_patterns(self, df: pd.DataFrame) -> Dict:
        """Phân tích trader thường trade symbol nào?"""
        return {
            'favorite_symbols': df['symbol'].value_counts().head(5).to_dict(),
            'symbol_win_rates': df.groupby('symbol')['profit'].apply(
                lambda x: (len(x[x > 0]) / len(x) * 100) if len(x) > 0 else 0
            ).to_dict(),
            'avg_profit_by_symbol': df.groupby('symbol')['profit'].mean().to_dict()
        }
    
    def _analyze_lot_size_patterns(self, df: pd.DataFrame) -> Dict:
        """Phân tích mô hình lot size - trader có ngớn lot khi profit hay loss?"""
        return {
            'avg_lot_size': float(df['lot_size'].mean()),
            'min_lot_size': float(df['lot_size'].min()),
            'max_lot_size': float(df['lot_size'].max()),
            'lot_size_after_win': self._analyze_lot_size_after_outcome(df, 'win'),
            'lot_size_after_loss': self._analyze_lot_size_after_outcome(df, 'loss'),
            'lot_size_trend': self._detect_lot_size_trend(df)
        }
    
    def _analyze_lot_size_after_outcome(self, df: pd.DataFrame, outcome: str) -> float:
        """Phân tích lot size sau khi win/loss - phát hiện revenge trading"""
        if len(df) < 2:
            return 0.0
        
        if outcome == 'win':
            wins_idx = df[df['profit'] > 0].index
        else:
            wins_idx = df[df['profit'] < 0].index
        
        after_outcomes = []
        for idx in wins_idx:
            next_idx = idx + 1
            if next_idx < len(df):
                after_outcomes.append(df.iloc[next_idx]['lot_size'])
        
        return float(np.mean(after_outcomes)) if after_outcomes else 0.0
    
    def _detect_lot_size_trend(self, df: pd.DataFrame) -> str:
        """Phát hiện xu hướng lot size"""
        if len(df) < 2:
            return "INSUFFICIENT_DATA"
        
        avg_first_half = df.iloc[:len(df)//2]['lot_size'].mean()
        avg_second_half = df.iloc[len(df)//2:]['lot_size'].mean()
        
        if avg_second_half > avg_first_half * 1.2:
            return "INCREASING"  # Lot size ngày càng lớn - nguy hiểm!
        elif avg_second_half < avg_first_half * 0.8:
            return "DECREASING"  # Lot size ngày càng nhỏ
        else:
            return "STABLE"
    
    def _analyze_entry_exit_patterns(self, df: pd.DataFrame) -> Dict:
        """Phân tích mô hình entry/exit"""
        return {
            'entry_patterns': {
                'avg_entry_price_deviation': self._calculate_entry_deviation(df),
                'entry_at_resistance': self._count_entries_at_resistance(df),
                'entry_at_support': self._count_entries_at_support(df),
            },
            'exit_patterns': {
                'avg_profit_on_winners': self._calculate_avg_take_profit(df),
                'max_profit_reached_but_exited_early': self._count_early_tp_exits(df),
                'sl_hit_vs_manual_exit': self._analyze_sl_exits(df)
            }
        }
    
    def _calculate_entry_deviation(self, df: pd.DataFrame) -> float:
        """Tính độ lệch entry từ price hiện tại"""
        if 'entry_price' not in df.columns or 'market_price_at_entry' not in df.columns:
            return 0.0
        
        df['deviation'] = abs(df['entry_price'] - df['market_price_at_entry']) / df['market_price_at_entry']
        return float(df['deviation'].mean() * 100)  # Convert to percentage
    
    def _count_entries_at_resistance(self, df: pd.DataFrame) -> int:
        """Đếm số lần entry ở resistance"""
        # Mocked - trong production sẽ tính từ technical analysis
        return 0
    
    def _count_entries_at_support(self, df: pd.DataFrame) -> int:
        """Đếm số lần entry ở support"""
        return 0
    
    def _calculate_avg_take_profit(self, df: pd.DataFrame) -> float:
        """Tính trung bình take profit trên winning trades"""
        winning = df[df['profit'] > 0]
        if len(winning) == 0:
            return 0.0
        return float(winning['profit'].mean())
    
    def _count_early_tp_exits(self, df: pd.DataFrame) -> int:
        """Đếm số lần exit sớm trước khi đạt max profit"""
        # Mocked
        return 0
    
    def _analyze_sl_exits(self, df: pd.DataFrame) -> Dict:
        """Phân tích % exit by SL vs manual"""
        if len(df) == 0:
            return {'sl_percentage': 0, 'manual_exit_percentage': 0}
        
        sl_hits = len(df[df.get('exit_reason', '') == 'STOP_LOSS'])
        return {
            'sl_percentage': (sl_hits / len(df) * 100) if len(df) > 0 else 0,
            'manual_exit_percentage': ((len(df) - sl_hits) / len(df) * 100) if len(df) > 0 else 0
        }
    
    def _detect_discipline_violations(self, df: pd.DataFrame) -> Dict:
        """Phát hiện vi phạm kỷ luật"""
        violations = {
            'no_sl_trades': 0,
            'no_tp_trades': 0,
            'oversized_positions': 0,
            'revenge_trades': 0,
            'fomo_entries': 0
        }
        
        # Phát hiện trade không có SL
        violations['no_sl_trades'] = len(df[df['stop_loss'].isna() | (df['stop_loss'] == 0)])
        
        # Phát hiện trade không có TP
        violations['no_tp_trades'] = len(df[df['take_profit'].isna() | (df['take_profit'] == 0)])
        
        # Phát hiện oversized positions (lot size > 2% account)
        violations['oversized_positions'] = len(df[df['risk_percentage'] > 2])
        
        # Phát hiện revenge trading (lot size tăng sau loss)
        revenge_trades = 0
        for i in range(1, len(df)):
            if df.iloc[i-1]['profit'] < 0 and df.iloc[i]['lot_size'] > df.iloc[i-1]['lot_size'] * 1.5:
                revenge_trades += 1
        violations['revenge_trades'] = revenge_trades
        
        return violations
    
    def _analyze_recovery_time(self, df: pd.DataFrame) -> Dict:
        """Phân tích thời gian recovery sau loss"""
        losses = df[df['profit'] < 0]
        
        if len(losses) == 0:
            return {'avg_recovery_time_hours': 0, 'max_recovery_time_hours': 0}
        
        recovery_times = []
        for idx in losses.index:
            losses_after = df[df.index > idx]
            if len(losses_after) > 0:
                recovery_trade = losses_after[losses_after['cumulative_profit'] > df.loc[idx, 'cumulative_profit']].index[0] if len(losses_after[losses_after['cumulative_profit'] > df.loc[idx, 'cumulative_profit']]) > 0 else None
                if recovery_trade:
                    recovery_time = (df.loc[recovery_trade, 'timestamp'] - df.loc[idx, 'timestamp']).total_seconds() / 3600
                    recovery_times.append(recovery_time)
        
        return {
            'avg_recovery_time_hours': float(np.mean(recovery_times)) if recovery_times else 0,
            'max_recovery_time_hours': float(np.max(recovery_times)) if recovery_times else 0
        }
    
    def _analyze_profit_taking(self, df: pd.DataFrame) -> Dict:
        """Phân tích hành vi take profit"""
        winning_trades = df[df['profit'] > 0]
        
        if len(winning_trades) == 0:
            return {'avg_take_profit': 0, 'tp_consistency': 0}
        
        return {
            'avg_take_profit': float(winning_trades['profit'].mean()),
            'tp_consistency': float(winning_trades['profit'].std()),  # Thấp = consistent, cao = inconsistent
            'avg_tp_hit_percentage': self._calculate_tp_hit_rate(df)
        }
    
    def _calculate_tp_hit_rate(self, df: pd.DataFrame) -> float:
        """Tính % trades đạt đúng TP"""
        if 'exit_reason' not in df.columns:
            return 0.0
        tp_hits = len(df[df['exit_reason'] == 'TAKE_PROFIT'])
        return (tp_hits / len(df) * 100) if len(df) > 0 else 0.0
    
    def _analyze_stop_loss_behavior(self, df: pd.DataFrame) -> Dict:
        """Phân tích hành vi stop loss"""
        sl_hit = df[df['exit_reason'] == 'STOP_LOSS']
        
        return {
            'total_sl_hits': len(sl_hit),
            'avg_sl_loss': float(sl_hit['profit'].mean()) if len(sl_hit) > 0 else 0,
            'sl_consistency': float(sl_hit['profit'].std()) if len(sl_hit) > 0 else 0,
            'manual_exit_on_losses': len(df[(df['profit'] < 0) & (df['exit_reason'] != 'STOP_LOSS')])
        }
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'total_trades': 0,
            'win_rate': 0,
            'avg_profit_per_trade': 0,
            'drawdown_analysis': {},
            'time_patterns': {},
            'symbol_patterns': {},
            'lot_size_patterns': {},
            'entry_exit_patterns': {},
            'discipline_violations': {},
            'recovery_time': {}
        }
