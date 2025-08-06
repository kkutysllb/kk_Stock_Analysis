#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化配置模块
统一配置中文字体和图表样式
"""

try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

import warnings
warnings.filterwarnings('ignore')

def setup_chinese_fonts():
    """
    设置中文字体配置
    优先使用系统可用的中文字体
    """
    if not HAS_MATPLOTLIB:
        return "默认字体"
        
    import os
    
    # 直接指定字体文件路径
    font_paths = [
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # 系统检测到的字体
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/PingFang.ttc',
        '/Windows/Fonts/simhei.ttf'
    ]
    
    selected_font = None
    selected_path = None
    
    # 检查字体文件是否存在
    for font_path in font_paths:
        if os.path.exists(font_path):
            selected_path = font_path
            if 'Noto' in font_path:
                selected_font = 'Noto Sans CJK SC'
            elif 'DejaVu' in font_path:
                selected_font = 'DejaVu Sans'
            elif 'PingFang' in font_path:
                selected_font = 'PingFang SC'
            elif 'simhei' in font_path:
                selected_font = 'SimHei'
            break
    
    if selected_path:
        # 添加字体到matplotlib
        try:
            from matplotlib.font_manager import FontProperties
            prop = FontProperties(fname=selected_path)
        except Exception as e:
            selected_font = 'DejaVu Sans'
    else:
        selected_font = 'DejaVu Sans'
    
    # 配置matplotlib - 使用更兼容的方式
    font_list = [selected_font, 'DejaVu Sans', 'Arial', 'sans-serif']
    
    plt.rcParams['font.sans-serif'] = font_list
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    plt.rcParams['font.size'] = 10
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['figure.figsize'] = (12, 8)
    
    # 强制刷新字体缓存和创建全局字体属性
    try:
        plt.rcParams['font.family'] = 'sans-serif'
        
        # 为matplotlib创建全局字体属性
        if selected_path:
            from matplotlib.font_manager import FontProperties
            global CHINESE_FONT_PROP
            CHINESE_FONT_PROP = FontProperties(fname=selected_path)
        else:
            CHINESE_FONT_PROP = None
            
        pass
    except Exception as e:
        CHINESE_FONT_PROP = None
    
    return selected_font

def get_chinese_font():
    """获取中文字体属性"""
    try:
        return CHINESE_FONT_PROP
    except:
        return None

def setup_plot_style():
    """
    设置图表样式
    """
    if not HAS_MATPLOTLIB:
        return
        
    # 使用seaborn样式
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    
    # matplotlib样式配置
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['legend.frameon'] = True
    plt.rcParams['legend.fancybox'] = True
    plt.rcParams['legend.shadow'] = True

def init_visualization():
    """
    初始化可视化配置
    应在所有需要绘图的模块开始时调用
    """
    if not HAS_MATPLOTLIB:
        return "默认字体"
        
    font_name = setup_chinese_fonts()
    setup_plot_style()
    
    return font_name

# 自动初始化
if __name__ != "__main__":
    init_visualization()