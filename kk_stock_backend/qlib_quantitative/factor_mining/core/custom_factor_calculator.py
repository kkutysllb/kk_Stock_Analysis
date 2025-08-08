#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义因子计算器 - 动量、波动率、量价背离因子
实现配置文件中定义的自定义衍生因子计算
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings('ignore')

class CustomFactorCalculator:
    """
    自定义因子计算器
    
    主要功能：
    1. 动量因子计算
    2. 波动率因子计算  
    3. 量价背离因子计算
    4. 复合技术因子计算
    """
    
    def __init__(self):
        """初始化计算器"""
        pass
    
    def calculate_momentum_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算动量因子
        
        Args:
            data: 包含OHLCV和技术指标的数据
            
        Returns:
            动量因子DataFrame
        """
        result = pd.DataFrame(index=data.index)
        
        try:
            # 1. 增强动量因子（短期MA vs 长期MA）
            ma_5 = data['close'].rolling(5).mean()
            ma_20 = data['close'].rolling(20).mean()
            # 防止除零和无穷大值
            result['enhanced_momentum'] = np.where(
                (ma_5 > 0) & (ma_20 > 0), 
                data['close'] / ma_5 - data['close'] / ma_20,
                0.0
            )
            
            # 2. 价格动量因子（不同周期）
            result['price_momentum_1d'] = data['close'].pct_change(1).fillna(0.0)
            result['price_momentum_5d'] = data['close'].pct_change(5).fillna(0.0)
            result['price_momentum_20d'] = data['close'].pct_change(20).fillna(0.0)
            
            # 3. 成交量动量 - 防止除零
            vol_mean_20 = data['vol'].rolling(20).mean()
            result['volume_momentum'] = np.where(
                vol_mean_20 > 0,
                data['vol'] / vol_mean_20,
                1.0
            )
            
            # 4. 相对强度动量 - 防止除零
            close_mean_252 = data['close'].rolling(252).mean()
            result['relative_strength'] = np.where(
                close_mean_252 > 0,
                (data['close'] / close_mean_252) - 1,
                0.0
            )
            
            # 5. 价格加速度（二阶动量）
            returns = data['close'].pct_change().fillna(0.0)
            result['price_acceleration'] = returns - returns.shift(1)
            result['price_acceleration'] = result['price_acceleration'].fillna(0.0)
            
            # 清理无穷大值和极值
            result = self._clean_factor_data(result)
            
        except Exception as e:
            warnings.warn(f"动量因子计算失败: {e}")
            # 返回零填充的DataFrame
            for col in ['enhanced_momentum', 'price_momentum_1d', 'price_momentum_5d', 
                       'price_momentum_20d', 'volume_momentum', 'relative_strength', 'price_acceleration']:
                result[col] = 0.0
        
        return result
    
    def calculate_volatility_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算波动率因子
        
        Args:
            data: 包含OHLCV的数据
            
        Returns:
            波动率因子DataFrame
        """
        result = pd.DataFrame(index=data.index)
        
        try:
            returns = data['close'].pct_change().fillna(0.0)
            
            # 1. 波动率动量因子（核心因子）
            result['volatility_momentum'] = returns.rolling(20).std().fillna(0.0)
            
            # 2. 不同周期的价格波动率
            result['price_volatility_5d'] = returns.rolling(5).std().fillna(0.0)
            result['price_volatility_20d'] = returns.rolling(20).std().fillna(0.0)
            result['price_volatility_60d'] = returns.rolling(60).std().fillna(0.0)
            
            # 3. 高低价波动率（日内波动）- 防止除零
            result['high_low_volatility'] = np.where(
                data['close'] > 0,
                (data['high'] - data['low']) / data['close'],
                0.0
            )
            
            # 4. 成交量波动率
            volume_returns = data['vol'].pct_change().fillna(0.0)
            result['volume_volatility'] = volume_returns.rolling(20).std().fillna(0.0)
            
            # 5. 波动率比率（短期vs长期）- 防止除零
            vol_5 = returns.rolling(5).std().fillna(0.0)
            vol_20 = returns.rolling(20).std().fillna(0.0)
            result['volatility_ratio'] = np.where(
                vol_20 > 0,
                vol_5 / vol_20,
                1.0
            )
            
            # 6. GARCH波动率（简化版）
            result['garch_volatility'] = self._calculate_garch_volatility(returns)
            
            # 7. 波动率偏度和峰度 - 使用更安全的计算
            result['volatility_skew'] = returns.rolling(60).apply(
                lambda x: x.skew() if len(x) >= 10 and x.std() > 0 else 0.0
            ).fillna(0.0)
            result['volatility_kurtosis'] = returns.rolling(60).apply(
                lambda x: x.kurtosis() if len(x) >= 10 and x.std() > 0 else 0.0
            ).fillna(0.0)
            
            # 清理无穷大值和极值
            result = self._clean_factor_data(result)
            
        except Exception as e:
            warnings.warn(f"波动率因子计算失败: {e}")
            # 返回零填充的DataFrame
            for col in ['volatility_momentum', 'price_volatility_5d', 'price_volatility_20d', 
                       'price_volatility_60d', 'high_low_volatility', 'volume_volatility',
                       'volatility_ratio', 'garch_volatility', 'volatility_skew', 'volatility_kurtosis']:
                result[col] = 0.0
        
        return result
    
    def calculate_price_volume_divergence_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算量价背离因子
        
        Args:
            data: 包含OHLCV的数据
            
        Returns:
            量价背离因子DataFrame
        """
        result = pd.DataFrame(index=data.index)
        
        try:
            # 1. 量价背离因子（10日）- 核心因子
            price_change_10d = data['close'].pct_change(10).fillna(0.0)
            volume_change_10d = data['vol'].pct_change(10).fillna(0.0)
            
            # 计算滚动排名
            price_rank = price_change_10d.rolling(252).rank(pct=True).fillna(0.5)
            volume_rank = volume_change_10d.rolling(252).rank(pct=True).fillna(0.5)
            result['pv_divergence_10d'] = price_rank - volume_rank
            
            # 2. 量价相关性（不同窗口）
            returns = data['close'].pct_change().fillna(0.0)
            volume_change = data['vol'].pct_change().fillna(0.0)
            result['pv_correlation_10d'] = returns.rolling(10).corr(volume_change).fillna(0.0)
            result['pv_correlation_20d'] = returns.rolling(20).corr(volume_change).fillna(0.0)
            
            # 3. 量价趋势指标
            result['volume_price_trend'] = returns * data['vol']
            
            # 4. OBV背离指标
            result['obv_divergence'] = self._calculate_obv_divergence(data)
            
            # 5. 价量同步指标
            result['price_volume_sync'] = self._calculate_pv_sync(data)
            
            # 6. 相对成交量 - 防止除零
            vol_mean_60 = data['vol'].rolling(60).mean()
            result['relative_volume'] = np.where(
                vol_mean_60 > 0,
                data['vol'] / vol_mean_60,
                1.0
            )
            
            # 7. 量价强度
            result['volume_price_strength'] = (data['close'] - data['open']) * data['vol']
            
            # 清理无穷大值和极值
            result = self._clean_factor_data(result)
            
        except Exception as e:
            warnings.warn(f"量价背离因子计算失败: {e}")
            # 返回零填充的DataFrame
            for col in ['pv_divergence_10d', 'pv_correlation_10d', 'pv_correlation_20d',
                       'volume_price_trend', 'obv_divergence', 'price_volume_sync',
                       'relative_volume', 'volume_price_strength']:
                result[col] = 0.0
        
        return result
    
    def calculate_composite_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算复合技术因子
        
        Args:
            data: 包含技术指标的数据
            
        Returns:
            复合因子DataFrame
        """
        result = pd.DataFrame(index=data.index)
        
        try:
            # 1. RSI背离
            # 检查是否有任何RSI字段可用
            rsi_available = any(field in data.columns for field in ['rsi_bfq_12', 'rsi_bfq_6', 'rsi_bfq_24', 'rsi_hfq_12', 'rsi_qfq_12'])
            if rsi_available:
                result['rsi_divergence'] = self._calculate_rsi_divergence(data)
            else:
                result['rsi_divergence'] = 0.0
            
            # 2. MACD动量
            if 'macd_dif_bfq' in data.columns:
                result['macd_momentum'] = data['macd_dif_bfq'].pct_change().fillna(0.0)
            else:
                result['macd_momentum'] = 0.0
            
            # 3. 布林带位置 - 防止除零
            if all(col in data.columns for col in ['boll_lower_bfq', 'boll_upper_bfq']):
                bollinger_width = data['boll_upper_bfq'] - data['boll_lower_bfq']
                result['bollinger_position'] = np.where(
                    bollinger_width > 0,
                    (data['close'] - data['boll_lower_bfq']) / bollinger_width,
                    0.5  # 如果布林带宽度为0，设为中性值
                )
            else:
                result['bollinger_position'] = 0.5
            
            # 4. KDJ背离
            if all(col in data.columns for col in ['kdj_k_bfq', 'kdj_d_bfq']):
                result['kdj_divergence'] = data['kdj_k_bfq'] - data['kdj_d_bfq']
            else:
                result['kdj_divergence'] = 0.0
            
            # 5. 技术指标动量 - 防止除零
            if 'ema_bfq_20' in data.columns:
                result['ema_momentum'] = np.where(
                    data['ema_bfq_20'] > 0,
                    data['close'] / data['ema_bfq_20'] - 1,
                    0.0
                )
            else:
                result['ema_momentum'] = 0.0
            
            # 清理无穷大值和极值
            result = self._clean_factor_data(result)
            
        except Exception as e:
            warnings.warn(f"复合技术因子计算失败: {e}")
            # 返回零填充的DataFrame
            for col in ['rsi_divergence', 'macd_momentum', 'bollinger_position', 'kdj_divergence', 'ema_momentum']:
                result[col] = 0.0
            
        return result
    
    def _calculate_garch_volatility(self, returns: pd.Series, window: int = 60) -> pd.Series:
        """计算简化GARCH波动率"""
        def garch_vol(x):
            try:
                if len(x) < 10 or x.std() == 0:
                    return 0.0
                # 简化的GARCH(1,1)
                variance = x.var()
                if variance <= 0 or not np.isfinite(variance):
                    return 0.0
                    
                alpha, beta = 0.1, 0.85
                garch_var = variance
                for ret in x:
                    if np.isfinite(ret):
                        garch_var = variance * (1 - alpha - beta) + alpha * ret**2 + beta * garch_var
                        # 确保方差为正且有限
                        if garch_var <= 0 or not np.isfinite(garch_var):
                            garch_var = variance
                
                result = np.sqrt(garch_var) if garch_var > 0 else 0.0
                return result if np.isfinite(result) else 0.0
            except:
                return 0.0
        
        return returns.rolling(window).apply(garch_vol).fillna(0.0)
    
    def _calculate_obv_divergence(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """计算OBV背离指标"""
        # 计算OBV
        price_change = data['close'].diff()
        obv = (data['vol'] * np.sign(price_change)).cumsum()
        
        # 计算价格和OBV的趋势
        def trend_slope(x):
            if len(x) < 5:
                return np.nan
            return stats.linregress(range(len(x)), x)[0]
        
        price_trend = data['close'].rolling(window).apply(trend_slope)
        obv_trend = obv.rolling(window).apply(trend_slope)
        
        # 背离：价格和OBV趋势方向不一致
        return (np.sign(price_trend) != np.sign(obv_trend)).astype(int)
    
    def _calculate_pv_sync(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """计算价量同步指标"""
        returns = data['close'].pct_change()
        volume_change = data['vol'].pct_change()
        
        # 计算同步指标：价格上涨时成交量也放大的程度
        sync_signal = np.where(
            (returns > 0) & (volume_change > 0), 1,  # 价涨量增
            np.where((returns < 0) & (volume_change < 0), 1,  # 价跌量缩
                    -1)  # 背离
        )
        
        return pd.Series(sync_signal, index=data.index).rolling(window).mean()
    
    def _calculate_rsi_divergence(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """计算RSI背离指标"""
        # 寻找可用的RSI字段（优先使用12日RSI）
        rsi_field = None
        for field in ['rsi_bfq_12', 'rsi_bfq_6', 'rsi_bfq_24', 'rsi_hfq_12', 'rsi_qfq_12']:
            if field in data.columns:
                rsi_field = field
                break
        
        if rsi_field is None:
            return pd.Series(np.nan, index=data.index)
        
        def trend_slope(x):
            if len(x) < 5:
                return np.nan
            return stats.linregress(range(len(x)), x)[0]
        
        price_trend = data['close'].rolling(window).apply(trend_slope)
        rsi_trend = data[rsi_field].rolling(window).apply(trend_slope)
        
        # 背离：价格和RSI趋势方向不一致
        return (np.sign(price_trend) != np.sign(rsi_trend)).astype(int)
    
    def calculate_all_custom_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有自定义因子
        
        Args:
            data: 包含OHLCV和技术指标的完整数据
            
        Returns:
            所有自定义因子的DataFrame
        """
        all_factors = pd.DataFrame(index=data.index)
        
        # 计算各类自定义因子
        momentum_factors = self.calculate_momentum_factors(data)
        volatility_factors = self.calculate_volatility_factors(data)
        pv_factors = self.calculate_price_volume_divergence_factors(data)
        composite_factors = self.calculate_composite_factors(data)
        
        # 合并所有因子
        all_factors = pd.concat([
            all_factors, 
            momentum_factors, 
            volatility_factors, 
            pv_factors, 
            composite_factors
        ], axis=1)
        
        return all_factors
    
    def _clean_factor_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理因子数据，处理无穷大值和极值
        
        Args:
            df: 因子数据DataFrame
            
        Returns:
            清理后的DataFrame
        """
        try:
            for col in df.columns:
                # 1. 替换无穷大值为NaN
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                
                # 2. 处理极值（超出合理范围的值）
                # 对于因子值，使用更保守的范围
                safe_max = 1e10
                safe_min = -1e10
                
                # 将超出安全范围的值设为NaN
                df.loc[df[col] > safe_max, col] = np.nan
                df.loc[df[col] < safe_min, col] = np.nan
                
                # 3. 填充NaN值
                if pd.isna(df[col]).all():
                    # 如果整列都是无效值，用0填充
                    df[col] = 0.0
                elif pd.isna(df[col]).any():
                    # 有部分无效值，用中位数填充
                    median_value = df[col].median()
                    if pd.isna(median_value):
                        median_value = 0.0
                    df[col] = df[col].fillna(median_value)
                
                # 4. 最终检查数据类型
                if not pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            return df
            
        except Exception as e:
            warnings.warn(f"因子数据清理失败: {e}")
            # 如果清理失败，至少确保没有无穷大值
            for col in df.columns:
                if col in df.columns:
                    df[col] = df[col].replace([np.inf, -np.inf], 0.0).fillna(0.0)
            return df


def example_usage():
    """使用示例"""
    # 模拟数据
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    n = len(dates)
    
    data = pd.DataFrame({
        'close': 100 + np.cumsum(np.random.randn(n) * 0.02),
        'open': 100 + np.cumsum(np.random.randn(n) * 0.02),
        'high': 100 + np.cumsum(np.random.randn(n) * 0.02),
        'low': 100 + np.cumsum(np.random.randn(n) * 0.02),
        'vol': np.random.exponential(1000000, n),
        'rsi_bfq_14': np.random.uniform(20, 80, n),
        'macd_dif_bfq': np.random.randn(n),
        'boll_lower_bfq': 95 + np.cumsum(np.random.randn(n) * 0.015),
        'boll_upper_bfq': 105 + np.cumsum(np.random.randn(n) * 0.015),
    }, index=dates)
    
    # 计算自定义因子
    calculator = CustomFactorCalculator()
    custom_factors = calculator.calculate_all_custom_factors(data)
    
    print("计算完成的自定义因子:")
    print(f"因子数量: {len(custom_factors.columns)}")
    print(f"数据形状: {custom_factors.shape}")
    print("\n因子列表:")
    for i, col in enumerate(custom_factors.columns, 1):
        print(f"{i:2d}. {col}")

if __name__ == "__main__":
    example_usage()