#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子挖掘可视化引擎
提供因子分析结果的图表可视化功能
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings

# 设置中文字体和样式
plt.style.use('seaborn-v0_8')
# 尝试多种中文字体
try:
    import matplotlib.font_manager as fm
    # 查找系统中可用的中文字体
    fonts = [f.name for f in fm.fontManager.ttflist if 'chinese' in f.name.lower() or 'simhei' in f.name.lower() or 'simsun' in f.name.lower()]
    if fonts:
        plt.rcParams['font.sans-serif'] = fonts[:1] + ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
    else:
        # 如果没有找到中文字体，使用系统默认字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']

plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class VisualizationEngine:
    """
    因子挖掘可视化引擎
    
    主要功能：
    1. 因子IC分析图表
    2. 因子分布和相关性图表
    3. 模型性能可视化
    4. 策略回测结果图表
    5. 综合分析仪表板
    """
    
    def __init__(self, output_dir: str = "results/factor_mining/charts"):
        """
        初始化可视化引擎
        
        Args:
            output_dir: 图表输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置图表样式
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        self.figsize_large = (15, 10)
        self.figsize_medium = (12, 8)
        self.figsize_small = (10, 6)
    
    def plot_factor_ic_analysis(self, ic_results: Dict[str, pd.DataFrame], 
                              save_path: str = None) -> str:
        """
        绘制因子IC分析图表
        
        Args:
            ic_results: IC分析结果，格式: {period: ic_df}
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize_large)
        fig.suptitle('Factor IC Analysis Report', fontsize=16, fontweight='bold')
        
        # 1. IC均值分布
        ax1 = axes[0, 0]
        ic_means = []
        periods = []
        
        for period, ic_df in ic_results.items():
            if not ic_df.empty:
                ic_means.extend(ic_df['ic_mean'].values)
                periods.extend([f'{period}天'] * len(ic_df))
        
        if ic_means:
            ic_data = pd.DataFrame({'IC均值': ic_means, '周期': periods})
            sns.boxplot(data=ic_data, x='周期', y='IC均值', ax=ax1)
            ax1.set_title('IC Mean Distribution by Period')
            ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        # 2. IC信息比率排名
        ax2 = axes[0, 1]
        for period, ic_df in ic_results.items():
            if not ic_df.empty and len(ic_df) > 0:
                top_factors = ic_df.nlargest(10, 'ic_ir')
                ax2.barh(range(len(top_factors)), top_factors['ic_ir'].values, 
                        label=f'{period}天', alpha=0.7)
                break  # 只显示一个周期的top因子
        
        ax2.set_title('Top 10 Factor Information Ratio')
        ax2.set_xlabel('IC Information Ratio')
        
        # 3. IC稳定性分析
        ax3 = axes[1, 0]
        for period, ic_df in ic_results.items():
            if not ic_df.empty:
                ax3.scatter(ic_df['ic_std'], ic_df['ic_mean'], 
                          label=f'{period}天', alpha=0.6, s=50)
        
        ax3.set_xlabel('IC Standard Deviation')
        ax3.set_ylabel('IC Mean')
        ax3.set_title('IC Stability Analysis (Mean vs Std)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 显著性因子统计
        ax4 = axes[1, 1]
        significance_stats = []
        period_names = []
        
        for period, ic_df in ic_results.items():
            if not ic_df.empty:
                significant_count = len(ic_df[ic_df['significance'] == True])
                total_count = len(ic_df)
                significance_stats.append(significant_count / total_count * 100)
                period_names.append(f'{period}天')
        
        if significance_stats:
            bars = ax4.bar(period_names, significance_stats, color=self.colors['success'])
            ax4.set_title('Significant Factors by Period')
            ax4.set_ylabel('Significant Factor Ratio (%)')
            
            # 添加数值标签
            for bar, value in zip(bars, significance_stats):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{value:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = os.path.join(self.output_dir, f'factor_ic_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def plot_factor_correlation_heatmap(self, factor_data: pd.DataFrame, 
                                      top_factors: List[str] = None,
                                      save_path: str = None) -> str:
        """
        绘制因子相关性热力图
        
        Args:
            factor_data: 因子数据
            top_factors: 重点分析的因子列表
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        if top_factors:
            # 只分析重点因子
            available_factors = [f for f in top_factors if f in factor_data.columns]
            if available_factors:
                data_subset = factor_data[available_factors]
            else:
                data_subset = factor_data.select_dtypes(include=[np.number])
        else:
            # 选择数值型列
            data_subset = factor_data.select_dtypes(include=[np.number])
        
        # 限制因子数量以提高可读性
        if len(data_subset.columns) > 50:
            # 计算相关性并选择最相关的因子
            corr_with_first = data_subset.corrwith(data_subset.iloc[:, 0]).abs()
            top_corr_factors = corr_with_first.nlargest(50).index
            data_subset = data_subset[top_corr_factors]
        
        # 计算相关性矩阵
        correlation_matrix = data_subset.corr()
        
        # 创建图表
        fig, ax = plt.subplots(figsize=self.figsize_large)
        
        # 绘制热力图
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
        sns.heatmap(correlation_matrix, 
                   mask=mask,
                   annot=False,
                   cmap='RdBu_r',
                   center=0,
                   square=True,
                   linewidths=0.1,
                   ax=ax)
        
        ax.set_title('因子相关性热力图', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        if save_path is None:
            save_path = os.path.join(self.output_dir, f'factor_correlation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def plot_model_performance(self, model_results: List[Dict], 
                             save_path: str = None) -> str:
        """
        绘制模型性能对比图表
        
        Args:
            model_results: 模型结果列表
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        if not model_results:
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=self.figsize_large)
        fig.suptitle('模型性能对比分析', fontsize=16, fontweight='bold')
        
        # 准备数据
        model_names = [result['model_name'] for result in model_results]
        train_r2 = [result['train_metrics'].get('r2_score', 0) for result in model_results]
        val_r2 = [result['val_metrics'].get('r2_score', 0) for result in model_results]
        train_mse = [result['train_metrics'].get('mse', 0) for result in model_results]
        val_mse = [result['val_metrics'].get('mse', 0) for result in model_results]
        
        # 1. R²得分对比
        ax1 = axes[0, 0]
        x = np.arange(len(model_names))
        width = 0.35
        
        ax1.bar(x - width/2, train_r2, width, label='训练集', color=self.colors['primary'])
        ax1.bar(x + width/2, val_r2, width, label='验证集', color=self.colors['secondary'])
        
        ax1.set_ylabel('R² 得分')
        ax1.set_title('模型R²得分对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(model_names, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. MSE对比
        ax2 = axes[0, 1]
        ax2.bar(x - width/2, train_mse, width, label='训练集', color=self.colors['success'])
        ax2.bar(x + width/2, val_mse, width, label='验证集', color=self.colors['warning'])
        
        ax2.set_ylabel('MSE')
        ax2.set_title('模型MSE对比')
        ax2.set_xticks(x)
        ax2.set_xticklabels(model_names, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 训练时间对比
        ax3 = axes[1, 0]
        training_times = [result.get('training_time', 0) for result in model_results]
        bars = ax3.bar(model_names, training_times, color=self.colors['info'])
        
        ax3.set_ylabel('训练时间 (秒)')
        ax3.set_title('模型训练时间对比')
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
        
        # 添加数值标签
        for bar, time in zip(bars, training_times):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(training_times)*0.01,
                    f'{time:.1f}s', ha='center', va='bottom')
        
        # 4. 综合性能雷达图
        ax4 = axes[1, 1]
        
        # 准备雷达图数据
        if len(model_results) > 0:
            best_model = max(model_results, key=lambda x: x['val_metrics'].get('r2_score', 0))
            
            metrics = ['R²得分', 'IC均值', '稳定性', '速度']
            values = [
                best_model['val_metrics'].get('r2_score', 0),
                abs(best_model['val_metrics'].get('ic', 0)),
                1 - best_model['val_metrics'].get('mse', 1),  # 稳定性 = 1 - 相对MSE
                min(1.0, 60 / max(best_model.get('training_time', 60), 1))  # 速度评分
            ]
            
            # 标准化到0-1范围
            values = [min(1.0, max(0.0, v)) for v in values]
            
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            values += values[:1]  # 闭合图形
            angles += angles[:1]
            
            ax4.plot(angles, values, 'o-', linewidth=2, color=self.colors['primary'])
            ax4.fill(angles, values, alpha=0.25, color=self.colors['primary'])
            ax4.set_xticks(angles[:-1])
            ax4.set_xticklabels(metrics)
            ax4.set_ylim(0, 1)
            ax4.set_title(f'最佳模型综合性能\n({best_model["model_name"]})')
            ax4.grid(True)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = os.path.join(self.output_dir, f'model_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def plot_factor_returns_analysis(self, factor_data: pd.DataFrame, 
                                   returns_data: pd.DataFrame,
                                   top_factors: List[str] = None,
                                   save_path: str = None) -> str:
        """
        绘制因子收益分析图表
        
        Args:
            factor_data: 因子数据
            returns_data: 收益率数据
            top_factors: 重点分析的因子
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        if top_factors is None:
            # 自动选择最相关的因子
            numeric_factors = factor_data.select_dtypes(include=[np.number]).columns
            if len(numeric_factors) > 20:
                # 随机选择20个因子进行展示
                top_factors = np.random.choice(numeric_factors, 20, replace=False).tolist()
            else:
                top_factors = numeric_factors.tolist()
        
        fig, axes = plt.subplots(2, 2, figsize=self.figsize_large)
        fig.suptitle('因子收益分析', fontsize=16, fontweight='bold')
        
        # 1. 因子与收益率散点图
        ax1 = axes[0, 0]
        if len(top_factors) > 0 and top_factors[0] in factor_data.columns:
            factor_col = top_factors[0]
            return_col = returns_data.columns[0] if len(returns_data.columns) > 0 else None
            
            if return_col:
                # 合并数据
                merged_data = pd.concat([factor_data[factor_col], returns_data[return_col]], axis=1).dropna()
                
                if not merged_data.empty:
                    ax1.scatter(merged_data.iloc[:, 0], merged_data.iloc[:, 1], 
                              alpha=0.6, s=20, color=self.colors['primary'])
                    
                    # 添加趋势线
                    z = np.polyfit(merged_data.iloc[:, 0], merged_data.iloc[:, 1], 1)
                    p = np.poly1d(z)
                    ax1.plot(merged_data.iloc[:, 0].sort_values(), 
                           p(merged_data.iloc[:, 0].sort_values()), 
                           "r--", alpha=0.8, linewidth=2)
                    
                    corr = merged_data.iloc[:, 0].corr(merged_data.iloc[:, 1])
                    ax1.set_title(f'{factor_col} vs 收益率\n相关系数: {corr:.3f}')
                    ax1.set_xlabel(factor_col)
                    ax1.set_ylabel('收益率')
        
        # 2. 因子分位数收益分析
        ax2 = axes[0, 1]
        if len(top_factors) > 0 and top_factors[0] in factor_data.columns:
            factor_col = top_factors[0]
            return_col = returns_data.columns[0] if len(returns_data.columns) > 0 else None
            
            if return_col:
                merged_data = pd.concat([factor_data[factor_col], returns_data[return_col]], axis=1).dropna()
                
                if not merged_data.empty:
                    # 按因子值分位数分组
                    merged_data['quantile'] = pd.qcut(merged_data.iloc[:, 0], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
                    quantile_returns = merged_data.groupby('quantile')[return_col].mean()
                    
                    bars = ax2.bar(quantile_returns.index, quantile_returns.values, 
                                  color=self.colors['secondary'])
                    ax2.set_title(f'{factor_col} 分位数收益')
                    ax2.set_ylabel('平均收益率')
                    ax2.set_xlabel('因子分位数')
                    
                    # 添加数值标签
                    for bar, value in zip(bars, quantile_returns.values):
                        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                f'{value:.4f}', ha='center', va='bottom')
        
        # 3. 多因子收益相关性
        ax3 = axes[1, 0]
        correlation_data = []
        factor_names = []
        
        for factor in top_factors[:10]:  # 限制显示数量
            if factor in factor_data.columns:
                return_col = returns_data.columns[0] if len(returns_data.columns) > 0 else None
                if return_col:
                    merged_data = pd.concat([factor_data[factor], returns_data[return_col]], axis=1).dropna()
                    if not merged_data.empty:
                        corr = merged_data.iloc[:, 0].corr(merged_data.iloc[:, 1])
                        correlation_data.append(abs(corr))
                        factor_names.append(factor)
        
        if correlation_data:
            bars = ax3.barh(factor_names, correlation_data, color=self.colors['success'])
            ax3.set_title('因子与收益率相关性排名')
            ax3.set_xlabel('|相关系数|')
            
            # 添加数值标签
            for bar, value in zip(bars, correlation_data):
                ax3.text(bar.get_width() + max(correlation_data)*0.01, bar.get_y() + bar.get_height()/2,
                        f'{value:.3f}', ha='left', va='center')
        
        # 4. 收益率时序图
        ax4 = axes[1, 1]
        if not returns_data.empty:
            returns_data.plot(ax=ax4, alpha=0.7)
            ax4.set_title('收益率时序变化')
            ax4.set_ylabel('收益率')
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = os.path.join(self.output_dir, f'factor_returns_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def create_comprehensive_dashboard(self, analysis_results: Dict[str, Any],
                                     save_path: str = None) -> str:
        """
        创建综合分析仪表板
        
        Args:
            analysis_results: 完整的分析结果
            save_path: 保存路径
            
        Returns:
            图表文件路径
        """
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # 主标题
        fig.suptitle('因子挖掘综合分析仪表板', fontsize=20, fontweight='bold', y=0.95)
        
        # 1. 因子数量统计 (左上角)
        ax1 = fig.add_subplot(gs[0, 0])
        factor_stats = analysis_results.get('factor_stats', {})
        categories = ['总因子', '有效因子', '显著因子', '优质因子']
        counts = [
            factor_stats.get('total_factors', 0),
            factor_stats.get('valid_factors', 0), 
            factor_stats.get('significant_factors', 0),
            factor_stats.get('quality_factors', 0)
        ]
        
        bars = ax1.bar(categories, counts, color=[self.colors['primary'], self.colors['success'], 
                                                self.colors['warning'], self.colors['danger']])
        ax1.set_title('因子统计概览')
        ax1.set_ylabel('数量')
        
        # 添加数值标签
        for bar, count in zip(bars, counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    str(count), ha='center', va='bottom')
        
        # 2. IC分布直方图
        ax2 = fig.add_subplot(gs[0, 1:3])
        ic_data = analysis_results.get('ic_analysis', {})
        if ic_data:
            all_ics = []
            for period_data in ic_data.values():
                if isinstance(period_data, pd.DataFrame) and not period_data.empty:
                    all_ics.extend(period_data['ic_mean'].values)
            
            if all_ics:
                ax2.hist(all_ics, bins=30, alpha=0.7, color=self.colors['primary'], edgecolor='black')
                ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7)
                ax2.set_title('因子IC值分布')
                ax2.set_xlabel('IC均值')
                ax2.set_ylabel('频次')
        
        # 3. 模型性能对比
        ax3 = fig.add_subplot(gs[0, 3])
        model_results = analysis_results.get('model_results', [])
        if model_results:
            model_names = [result['model_name'][:8] for result in model_results[:5]]  # 截短名称
            r2_scores = [result['val_metrics'].get('r2_score', 0) for result in model_results[:5]]
            
            bars = ax3.bar(model_names, r2_scores, color=self.colors['secondary'])
            ax3.set_title('模型R²得分')
            ax3.set_ylabel('R²')
            plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
        
        # 4. Top因子热力图
        ax4 = fig.add_subplot(gs[1, :2])
        top_factors_data = analysis_results.get('top_factors', pd.DataFrame())
        if not top_factors_data.empty:
            # 选择前15个因子
            display_data = top_factors_data.head(15)[['ic_mean', 'ic_ir', 'sharpe_ratio']]
            sns.heatmap(display_data.T, annot=True, cmap='RdYlGn', center=0, 
                       ax=ax4, cbar_kws={'shrink': 0.5})
            ax4.set_title('Top 15因子关键指标热力图')
        
        # 5. 收益分析
        ax5 = fig.add_subplot(gs[1, 2:])
        returns_analysis = analysis_results.get('returns_analysis', {})
        if returns_analysis:
            periods = list(returns_analysis.keys())
            returns = [returns_analysis[p].get('mean_return', 0) for p in periods]
            
            ax5.plot(periods, returns, marker='o', linewidth=2, markersize=8, color=self.colors['success'])
            ax5.set_title('不同周期平均收益率')
            ax5.set_xlabel('预测周期')
            ax5.set_ylabel('平均收益率')
            ax5.grid(True, alpha=0.3)
        
        # 6. 策略绩效时序图
        ax6 = fig.add_subplot(gs[2, :])
        strategy_results = analysis_results.get('strategy_results', {})
        if strategy_results and 'portfolio_returns' in strategy_results:
            returns_series = strategy_results['portfolio_returns']
            cumulative_returns = (1 + returns_series).cumprod()
            
            ax6.plot(cumulative_returns.index, cumulative_returns.values, 
                    linewidth=2, color=self.colors['primary'], label='策略累计收益')
            
            # 基准对比
            if 'benchmark_returns' in strategy_results:
                benchmark_cumulative = (1 + strategy_results['benchmark_returns']).cumprod()
                ax6.plot(benchmark_cumulative.index, benchmark_cumulative.values,
                        linewidth=2, color=self.colors['secondary'], label='基准累计收益')
            
            ax6.set_title('策略绩效表现')
            ax6.set_ylabel('累计收益')
            ax6.legend()
            ax6.grid(True, alpha=0.3)
        
        # 7. 风险指标雷达图
        ax7 = fig.add_subplot(gs[3, :2], projection='polar')
        risk_metrics = analysis_results.get('risk_metrics', {})
        if risk_metrics:
            metrics = ['夏普比率', '最大回撤', '胜率', '盈亏比', '波动率']
            values = [
                risk_metrics.get('sharpe_ratio', 0) / 3,  # 标准化
                1 - risk_metrics.get('max_drawdown', 0),  # 转换为正向指标
                risk_metrics.get('win_rate', 0),
                min(1.0, risk_metrics.get('profit_loss_ratio', 0) / 2),
                1 - risk_metrics.get('volatility', 0)  # 转换为正向指标
            ]
            
            # 确保值在0-1范围内
            values = [max(0, min(1, v)) for v in values]
            
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]
            
            ax7.plot(angles, values, 'o-', linewidth=2, color=self.colors['danger'])
            ax7.fill(angles, values, alpha=0.25, color=self.colors['danger'])
            ax7.set_xticks(angles[:-1])
            ax7.set_xticklabels(metrics)
            ax7.set_ylim(0, 1)
            ax7.set_title('风险收益指标')
        
        # 8. 关键统计信息
        ax8 = fig.add_subplot(gs[3, 2:])
        ax8.axis('off')
        
        # 准备统计信息文本
        stats_text = "关键统计信息\n" + "="*20 + "\n\n"
        
        if factor_stats:
            stats_text += f"• 总因子数量: {factor_stats.get('total_factors', 'N/A')}\n"
            stats_text += f"• 有效因子数量: {factor_stats.get('valid_factors', 'N/A')}\n"
            stats_text += f"• 因子有效率: {factor_stats.get('effectiveness_rate', 'N/A'):.1%}\n\n"
        
        if model_results:
            best_model = max(model_results, key=lambda x: x['val_metrics'].get('r2_score', 0))
            stats_text += f"• 最佳模型: {best_model['model_name']}\n"
            stats_text += f"• 最佳R²得分: {best_model['val_metrics'].get('r2_score', 0):.4f}\n"
            stats_text += f"• 训练时间: {best_model.get('training_time', 0):.1f}秒\n\n"
        
        if risk_metrics:
            stats_text += f"• 策略夏普比率: {risk_metrics.get('sharpe_ratio', 'N/A'):.2f}\n"
            stats_text += f"• 最大回撤: {risk_metrics.get('max_drawdown', 'N/A'):.2%}\n"
            stats_text += f"• 年化收益率: {risk_metrics.get('annual_return', 'N/A'):.2%}\n"
        
        ax8.text(0.05, 0.95, stats_text, transform=ax8.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        if save_path is None:
            save_path = os.path.join(self.output_dir, f'comprehensive_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path


if __name__ == "__main__":
    # 测试代码
    print("🚀 测试可视化引擎...")
    
    viz_engine = VisualizationEngine()
    print("✅ 可视化引擎初始化成功")