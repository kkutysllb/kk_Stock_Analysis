#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表数据生成器
为前端提供各种图表的数据格式
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json

# 添加路径以正确导入模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models.quantitative_models import ChartData, ChartPoint, PerformanceMetrics


class ChartGenerator:
    """图表数据生成器"""
    
    def __init__(self):
        self.chart_colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff9800',
            'info': '#17a2b8',
            'purple': '#9467bd',
            'pink': '#e377c2',
            'teal': '#17a2b8',
            'cyan': '#6f42c1'
        }
    
    def generate_performance_chart(
        self,
        returns_data: List[float],
        dates: List[date],
        benchmark_returns: Optional[List[float]] = None,
        title: str = "策略绩效对比"
    ) -> Dict[str, Any]:
        """
        生成绩效对比图表
        适用于ECharts的配置格式
        """
        
        # 计算累计收益率
        cumulative_returns = []
        cumulative_value = 1.0
        
        for return_rate in returns_data:
            cumulative_value *= (1 + return_rate)
            cumulative_returns.append(cumulative_value)
        
        # 基准数据
        benchmark_cumulative = []
        if benchmark_returns:
            benchmark_value = 1.0
            for return_rate in benchmark_returns:
                benchmark_value *= (1 + return_rate)
                benchmark_cumulative.append(benchmark_value)
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center',
                'textStyle': {
                    'fontSize': 16,
                    'fontWeight': 'bold'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross',
                    'crossStyle': {
                        'color': '#999'
                    }
                },
                'formatter': """function(params) {
                    var result = params[0].name + '<br/>';
                    params.forEach(function(item) {
                        result += item.marker + item.seriesName + ': ' + 
                                (item.value * 100).toFixed(2) + '%<br/>';
                    });
                    return result;
                }"""
            },
            'legend': {
                'data': ['策略收益', '基准收益'],
                'bottom': 10
            },
            'xAxis': {
                'type': 'category',
                'data': [d.strftime('%Y-%m-%d') for d in dates],
                'axisPointer': {
                    'type': 'shadow'
                }
            },
            'yAxis': {
                'type': 'value',
                'name': '累计收益率',
                'axisLabel': {
                    'formatter': '{value}%'
                }
            },
            'series': [
                {
                    'name': '策略收益',
                    'type': 'line',
                    'smooth': True,
                    'data': [(r - 1) * 100 for r in cumulative_returns],
                    'itemStyle': {
                        'color': self.chart_colors['primary']
                    },
                    'lineStyle': {
                        'width': 2
                    }
                }
            ]
        }
        
        # 添加基准数据
        if benchmark_returns:
            chart_config['series'].append({
                'name': '基准收益',
                'type': 'line',
                'smooth': True,
                'data': [(r - 1) * 100 for r in benchmark_cumulative],
                'itemStyle': {
                    'color': self.chart_colors['secondary']
                },
                'lineStyle': {
                    'width': 2,
                    'type': 'dashed'
                }
            })
        
        return chart_config
    
    def generate_drawdown_chart(
        self,
        returns_data: List[float],
        dates: List[date],
        title: str = "策略回撤分析"
    ) -> Dict[str, Any]:
        """生成回撤图表"""
        
        # 计算回撤
        cumulative_returns = []
        peak = 1.0
        drawdowns = []
        
        for return_rate in returns_data:
            cumulative_value = cumulative_returns[-1] * (1 + return_rate) if cumulative_returns else 1 + return_rate
            cumulative_returns.append(cumulative_value)
            
            if cumulative_value > peak:
                peak = cumulative_value
            
            drawdown = (cumulative_value - peak) / peak
            drawdowns.append(drawdown * 100)  # 转换为百分比
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center',
                'textStyle': {
                    'fontSize': 16,
                    'fontWeight': 'bold'
                }
            },
            'tooltip': {
                'trigger': 'axis',
                'formatter': """function(params) {
                    return params[0].name + '<br/>' + 
                           params[0].marker + '回撤: ' + 
                           params[0].value.toFixed(2) + '%';
                }"""
            },
            'xAxis': {
                'type': 'category',
                'data': [d.strftime('%Y-%m-%d') for d in dates]
            },
            'yAxis': {
                'type': 'value',
                'name': '回撤(%)',
                'max': 0,
                'axisLabel': {
                    'formatter': '{value}%'
                }
            },
            'series': [{
                'name': '回撤',
                'type': 'line',
                'data': drawdowns,
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0,
                        'y': 0,
                        'x2': 0,
                        'y2': 1,
                        'colorStops': [{
                            'offset': 0,
                            'color': 'rgba(214, 39, 40, 0.3)'
                        }, {
                            'offset': 1,
                            'color': 'rgba(214, 39, 40, 0.1)'
                        }]
                    }
                },
                'lineStyle': {
                    'color': self.chart_colors['danger'],
                    'width': 2
                },
                'itemStyle': {
                    'color': self.chart_colors['danger']
                }
            }]
        }
        
        return chart_config
    
    def generate_position_pie_chart(
        self,
        positions: List[Dict[str, Any]],
        title: str = "持仓分布"
    ) -> Dict[str, Any]:
        """生成持仓分布饼图"""
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center',
                'textStyle': {
                    'fontSize': 16,
                    'fontWeight': 'bold'
                }
            },
            'tooltip': {
                'trigger': 'item',
                'formatter': '{b}: {c}% ({d}%)'
            },
            'legend': {
                'orient': 'vertical',
                'left': 'left'
            },
            'series': [{
                'name': '持仓权重',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'avoidLabelOverlap': False,
                'label': {
                    'show': False,
                    'position': 'center'
                },
                'emphasis': {
                    'label': {
                        'show': True,
                        'fontSize': '20',
                        'fontWeight': 'bold'
                    }
                },
                'labelLine': {
                    'show': False
                },
                'data': [
                    {
                        'value': pos['weight'] * 100,
                        'name': f"{pos['stock_name']}({pos['stock_code']})"
                    }
                    for pos in positions
                ]
            }]
        }
        
        return chart_config
    
    def generate_trade_analysis_chart(
        self,
        trade_data: List[Dict[str, Any]],
        title: str = "交易分析"
    ) -> Dict[str, Any]:
        """生成交易分析图表"""
        
        # 按月统计交易次数和盈亏
        monthly_stats = {}
        
        for trade in trade_data:
            trade_date = datetime.strptime(trade['date'], '%Y-%m-%d')
            month_key = trade_date.strftime('%Y-%m')
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'trades': 0,
                    'profit': 0,
                    'loss': 0,
                    'win_count': 0
                }
            
            monthly_stats[month_key]['trades'] += 1
            
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                monthly_stats[month_key]['profit'] += pnl
                monthly_stats[month_key]['win_count'] += 1
            else:
                monthly_stats[month_key]['loss'] += abs(pnl)
        
        months = sorted(monthly_stats.keys())
        trade_counts = [monthly_stats[m]['trades'] for m in months]
        win_rates = [monthly_stats[m]['win_count'] / monthly_stats[m]['trades'] * 100 
                    if monthly_stats[m]['trades'] > 0 else 0 for m in months]
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross',
                    'crossStyle': {
                        'color': '#999'
                    }
                }
            },
            'legend': {
                'data': ['交易次数', '胜率'],
                'bottom': 10
            },
            'xAxis': {
                'type': 'category',
                'data': months,
                'axisPointer': {
                    'type': 'shadow'
                }
            },
            'yAxis': [
                {
                    'type': 'value',
                    'name': '交易次数',
                    'position': 'left'
                },
                {
                    'type': 'value',
                    'name': '胜率(%)',
                    'position': 'right',
                    'axisLabel': {
                        'formatter': '{value}%'
                    }
                }
            ],
            'series': [
                {
                    'name': '交易次数',
                    'type': 'bar',
                    'data': trade_counts,
                    'itemStyle': {
                        'color': self.chart_colors['primary']
                    }
                },
                {
                    'name': '胜率',
                    'type': 'line',
                    'yAxisIndex': 1,
                    'data': win_rates,
                    'itemStyle': {
                        'color': self.chart_colors['success']
                    }
                }
            ]
        }
        
        return chart_config
    
    def generate_risk_metrics_radar(
        self,
        metrics: PerformanceMetrics,
        benchmark_metrics: Optional[PerformanceMetrics] = None,
        title: str = "风险指标雷达图"
    ) -> Dict[str, Any]:
        """生成风险指标雷达图"""
        
        # 定义指标映射和最大值
        indicators = [
            {'name': '年化收益', 'max': 50},
            {'name': '夏普比率', 'max': 3},
            {'name': '胜率', 'max': 100},
            {'name': '卡马比率', 'max': 3},
            {'name': '索提诺比率', 'max': 3},
            {'name': '回撤控制', 'max': 100}  # 100 - 最大回撤%
        ]
        
        # 策略数据
        strategy_data = [
            metrics.annual_return * 100,
            metrics.sharpe_ratio,
            metrics.win_rate * 100,
            metrics.calmar_ratio,
            metrics.sortino_ratio,
            100 - abs(metrics.max_drawdown) * 100
        ]
        
        series_data = [{
            'value': strategy_data,
            'name': '策略表现'
        }]
        
        # 基准数据
        if benchmark_metrics:
            benchmark_data = [
                benchmark_metrics.annual_return * 100,
                benchmark_metrics.sharpe_ratio,
                benchmark_metrics.win_rate * 100,
                benchmark_metrics.calmar_ratio,
                benchmark_metrics.sortino_ratio,
                100 - abs(benchmark_metrics.max_drawdown) * 100
            ]
            series_data.append({
                'value': benchmark_data,
                'name': '基准表现'
            })
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'item'
            },
            'legend': {
                'data': ['策略表现', '基准表现'] if benchmark_metrics else ['策略表现'],
                'bottom': 10
            },
            'radar': {
                'indicator': indicators,
                'name': {
                    'textStyle': {
                        'color': '#666'
                    }
                },
                'splitArea': {
                    'areaStyle': {
                        'color': ['rgba(114, 172, 209, 0.2)',
                                'rgba(114, 172, 209, 0.4)',
                                'rgba(114, 172, 209, 0.6)',
                                'rgba(114, 172, 209, 0.8)',
                                'rgba(114, 172, 209, 1)']
                    }
                },
                'splitLine': {
                    'lineStyle': {
                        'color': 'rgba(114, 172, 209, 0.6)'
                    }
                }
            },
            'series': [{
                'name': '风险指标',
                'type': 'radar',
                'data': series_data
            }]
        }
        
        return chart_config
    
    def generate_correlation_heatmap(
        self,
        correlation_matrix: List[List[float]],
        labels: List[str],
        title: str = "相关性热力图"
    ) -> Dict[str, Any]:
        """生成相关性热力图"""
        
        # 转换数据格式
        heatmap_data = []
        for i, row in enumerate(correlation_matrix):
            for j, value in enumerate(row):
                heatmap_data.append([j, i, round(value, 3)])
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center'
            },
            'tooltip': {
                'position': 'top',
                'formatter': """function(params) {
                    return labels[params.data[0]] + ' vs ' + 
                           labels[params.data[1]] + '<br/>相关系数: ' + 
                           params.data[2];
                }"""
            },
            'xAxis': {
                'type': 'category',
                'data': labels,
                'splitArea': {
                    'show': True
                }
            },
            'yAxis': {
                'type': 'category',
                'data': labels,
                'splitArea': {
                    'show': True
                }
            },
            'visualMap': {
                'min': -1,
                'max': 1,
                'calculable': True,
                'orient': 'horizontal',
                'left': 'center',
                'bottom': '10%',
                'inRange': {
                    'color': ['#313695', '#4575b4', '#74add1', '#abd9e9', 
                             '#e0f3f8', '#ffffcc', '#fee090', '#fdae61', 
                             '#f46d43', '#d73027', '#a50026']
                }
            },
            'series': [{
                'name': '相关系数',
                'type': 'heatmap',
                'data': heatmap_data,
                'label': {
                    'show': True,
                    'formatter': '{c}'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        }
        
        return chart_config
    
    def generate_multi_strategy_comparison(
        self,
        strategies_data: Dict[str, Dict[str, List[float]]],
        title: str = "多策略对比"
    ) -> Dict[str, Any]:
        """生成多策略对比图表"""
        
        # 获取所有策略名称
        strategy_names = list(strategies_data.keys())
        
        # 假设所有策略的时间序列长度相同
        first_strategy = list(strategies_data.values())[0]
        dates = first_strategy.get('dates', [])
        
        series_data = []
        colors = list(self.chart_colors.values())
        
        for i, (strategy_name, data) in enumerate(strategies_data.items()):
            returns = data.get('returns', [])
            
            # 计算累计收益
            cumulative_returns = []
            cumulative_value = 1.0
            
            for return_rate in returns:
                cumulative_value *= (1 + return_rate)
                cumulative_returns.append((cumulative_value - 1) * 100)
            
            series_data.append({
                'name': strategy_name,
                'type': 'line',
                'smooth': True,
                'data': cumulative_returns,
                'itemStyle': {
                    'color': colors[i % len(colors)]
                }
            })
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross'
                }
            },
            'legend': {
                'data': strategy_names,
                'bottom': 10
            },
            'xAxis': {
                'type': 'category',
                'data': dates
            },
            'yAxis': {
                'type': 'value',
                'name': '累计收益率(%)',
                'axisLabel': {
                    'formatter': '{value}%'
                }
            },
            'series': series_data
        }
        
        return chart_config
    
    def generate_rolling_metrics_chart(
        self,
        rolling_data: Dict[str, List[float]],
        dates: List[str],
        title: str = "滚动指标分析"
    ) -> Dict[str, Any]:
        """生成滚动指标图表"""
        
        chart_config = {
            'title': {
                'text': title,
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {
                    'type': 'cross'
                }
            },
            'legend': {
                'data': list(rolling_data.keys()),
                'bottom': 10
            },
            'xAxis': {
                'type': 'category',
                'data': dates
            },
            'yAxis': {
                'type': 'value',
                'name': '指标值'
            },
            'series': []
        }
        
        colors = list(self.chart_colors.values())
        
        for i, (metric_name, values) in enumerate(rolling_data.items()):
            chart_config['series'].append({
                'name': metric_name,
                'type': 'line',
                'smooth': True,
                'data': values,
                'itemStyle': {
                    'color': colors[i % len(colors)]
                }
            })
        
        return chart_config


# 图表配置工具类
class ChartConfigBuilder:
    """图表配置构建器"""
    
    @staticmethod
    def create_responsive_config() -> Dict[str, Any]:
        """创建响应式图表配置"""
        return {
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '3%',
                'containLabel': True
            },
            'animation': True,
            'animationDuration': 1000,
            'animationEasing': 'cubicOut'
        }
    
    @staticmethod
    def create_dark_theme_config() -> Dict[str, Any]:
        """创建暗色主题配置"""
        return {
            'backgroundColor': '#1e1e1e',
            'textStyle': {
                'color': '#fff'
            },
            'title': {
                'textStyle': {
                    'color': '#fff'
                }
            },
            'legend': {
                'textStyle': {
                    'color': '#fff'
                }
            },
            'xAxis': {
                'axisLine': {
                    'lineStyle': {
                        'color': '#fff'
                    }
                },
                'axisLabel': {
                    'textStyle': {
                        'color': '#fff'
                    }
                }
            },
            'yAxis': {
                'axisLine': {
                    'lineStyle': {
                        'color': '#fff'
                    }
                },
                'axisLabel': {
                    'textStyle': {
                        'color': '#fff'
                    }
                }
            }
        }
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """合并多个配置"""
        result = {}
        for config in configs:
            result.update(config)
        return result