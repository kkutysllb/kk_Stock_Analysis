#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtrader策略配置文件
定义策略的全局配置参数
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DatabaseConfig:
    """
    数据库配置
    """
    host: str = "127.0.0.1"
    port: int = 27017
    database: str = "quant_analysis"
    username: str = "root"
    password: str = "example"
    auth_source: str = "admin"
    
    # 集合名称 - 基于实际数据库结构
    factor_collection: str = "stock_factor_pro"  # 主要因子数据集合
    basic_collection: str = "infrastructure_stock_basic"        # 股票基本信息集合
    
    # 财务数据集合
    financial_indicator_collection: str = "stock_fina_indicator"  # 财务指标数据
    balance_sheet_collection: str = "stock_balance_sheet"         # 资产负债表数据
    income_statement_collection: str = "stock_income"             # 利润表数据
    cash_flow_collection: str = "stock_cash_flow"                 # 现金流量表数据
    
    # 高优先级集合 - 量化策略必需
    index_daily_collection: str = "index_daily"                   # 指数日线数据
    index_weight_collection: str = "index_weight"                 # 指数权重数据
    money_flow_collection: str = "stock_money_flow"               # 资金流向数据
    dividend_collection: str = "stock_dividend"                   # 分红送股数据
    trading_calendar_collection: str = "infrastructure_trading_calendar"  # 交易日历
    
    # 策略特殊集合
    margin_detail_collection: str = "margin_detail"               # 融资融券明细
    limit_list_collection: str = "limit_list_daily"               # 涨跌停数据
    
    # 连接配置
    connect_timeout: int = 30000
    server_selection_timeout: int = 30000
    max_pool_size: int = 100
    
    # 字段映射配置
    field_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        """初始化字段映射 - 基于数据库因子综合报告的全量真实字段映射"""
        if self.field_mapping is None:
            self.field_mapping = {
                # ==================== 基础市场数据字段 ====================
                'stock_code': 'ts_code',
                'trade_date': 'trade_date',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'vol',
                'amount': 'amount',
                'pre_close': 'pre_close',
                'change': 'change',
                'pct_chg': 'pct_chg',
                'adj_factor': 'adj_factor',
                
                # ==================== 复权价格数据 ====================
                # 后复权价格
                'open_hfq': 'open_hfq',
                'high_hfq': 'high_hfq',
                'low_hfq': 'low_hfq',
                'close_hfq': 'close_hfq',
                
                # 前复权价格
                'open_qfq': 'open_qfq',
                'high_qfq': 'high_qfq',
                'low_qfq': 'low_qfq',
                'close_qfq': 'close_qfq',
                
                # ==================== 市值和估值指标 ====================
                'total_mv': 'total_mv',                # 总市值(万元)
                'circ_mv': 'circ_mv',                  # 流通市值(万元)
                'pe': 'pe',                            # 市盈率
                'pe_ttm': 'pe_ttm',                    # 市盈率TTM
                'pb': 'pb',                            # 市净率
                'ps': 'ps',                            # 市销率
                'ps_ttm': 'ps_ttm',                    # 市销率TTM
                'dv_ratio': 'dv_ratio',                # 股息率
                'dv_ttm': 'dv_ttm',                    # 股息率TTM
                'total_share': 'total_share',          # 总股本
                'float_share': 'float_share',          # 流通股本
                'free_share': 'free_share',            # 自由流通股本
                
                # ==================== 成交量和流动性指标 ====================
                'turnover_rate': 'turnover_rate',      # 换手率
                'turnover_rate_f': 'turnover_rate_f',  # 换手率(自由流通股)
                'volume_ratio': 'volume_ratio',        # 量比
                
                # ==================== 移动平均线系列 ====================
                # 简单移动平均(SMA) - 不复权
                'ma5': 'ma_bfq_5',
                'ma10': 'ma_bfq_10',
                'ma20': 'ma_bfq_20',
                'ma30': 'ma_bfq_30',
                'ma60': 'ma_bfq_60',
                'ma90': 'ma_bfq_90',
                # 注意: ma_bfq_120字段在数据库中不存在，暂时移除
                # 'ma120': 'ma_bfq_120',  
                'ma250': 'ma_bfq_250',
                
                # 简单移动平均(SMA) - 后复权
                'ma5_hfq': 'ma_hfq_5',
                'ma10_hfq': 'ma_hfq_10',
                'ma20_hfq': 'ma_hfq_20',
                'ma30_hfq': 'ma_hfq_30',
                'ma60_hfq': 'ma_hfq_60',
                'ma90_hfq': 'ma_hfq_90',
                'ma250_hfq': 'ma_hfq_250',
                
                # 简单移动平均(SMA) - 前复权
                'ma5_qfq': 'ma_qfq_5',
                'ma10_qfq': 'ma_qfq_10',
                'ma20_qfq': 'ma_qfq_20',
                'ma30_qfq': 'ma_qfq_30',
                'ma60_qfq': 'ma_qfq_60',
                'ma90_qfq': 'ma_qfq_90',
                'ma250_qfq': 'ma_qfq_250',
                
                # 指数移动平均(EMA) - 不复权
                'ema5': 'ema_bfq_5',
                'ema10': 'ema_bfq_10',
                'ema20': 'ema_bfq_20',
                'ema30': 'ema_bfq_30',
                'ema60': 'ema_bfq_60',
                'ema90': 'ema_bfq_90',
                'ema250': 'ema_bfq_250',
                
                # 指数移动平均(EMA) - 后复权
                'ema5_hfq': 'ema_hfq_5',
                'ema10_hfq': 'ema_hfq_10',
                'ema20_hfq': 'ema_hfq_20',
                'ema30_hfq': 'ema_hfq_30',
                'ema60_hfq': 'ema_hfq_60',
                'ema90_hfq': 'ema_hfq_90',
                'ema250_hfq': 'ema_hfq_250',
                
                # 指数移动平均(EMA) - 前复权
                'ema5_qfq': 'ema_qfq_5',
                'ema10_qfq': 'ema_qfq_10',
                'ema20_qfq': 'ema_qfq_20',
                'ema30_qfq': 'ema_qfq_30',
                'ema60_qfq': 'ema_qfq_60',
                'ema90_qfq': 'ema_qfq_90',
                'ema250_qfq': 'ema_qfq_250',
                
                # EXPMA指数移动平均
                'expma12': 'expma_12_bfq',
                'expma50': 'expma_50_bfq',
                'expma12_hfq': 'expma_12_hfq',
                'expma50_hfq': 'expma_50_hfq',
                'expma12_qfq': 'expma_12_qfq',
                'expma50_qfq': 'expma_50_qfq',
                
                # ==================== RSI相对强弱指标系列 ====================
                'rsi6': 'rsi_bfq_6',
                'rsi12': 'rsi_bfq_12',
                'rsi24': 'rsi_bfq_24',
                'rsi6_hfq': 'rsi_hfq_6',
                'rsi12_hfq': 'rsi_hfq_12',
                'rsi24_hfq': 'rsi_hfq_24',
                'rsi6_qfq': 'rsi_qfq_6',
                'rsi12_qfq': 'rsi_qfq_12',
                'rsi24_qfq': 'rsi_qfq_24',
                
                # ==================== MACD指标系列 ====================
                'macd_dif': 'macd_dif_bfq',
                'macd_dea': 'macd_dea_bfq', 
                'macd_macd': 'macd_bfq',
                'macd_dif_hfq': 'macd_dif_hfq',
                'macd_dea_hfq': 'macd_dea_hfq', 
                'macd_macd_hfq': 'macd_hfq',
                'macd_dif_qfq': 'macd_dif_qfq',
                'macd_dea_qfq': 'macd_dea_qfq', 
                'macd_macd_qfq': 'macd_qfq',
                
                # ==================== 布林带指标系列 ====================
                'boll_upper': 'boll_upper_bfq',
                'boll_mid': 'boll_mid_bfq',
                'boll_lower': 'boll_lower_bfq',
                'boll_upper_hfq': 'boll_upper_hfq',
                'boll_mid_hfq': 'boll_mid_hfq',
                'boll_lower_hfq': 'boll_lower_hfq',
                'boll_upper_qfq': 'boll_upper_qfq',
                'boll_mid_qfq': 'boll_mid_qfq',
                'boll_lower_qfq': 'boll_lower_qfq',
                
                # ==================== KDJ随机指标系列 ====================
                'kdj_k': 'kdj_k_bfq',
                'kdj_d': 'kdj_d_bfq',
                'kdj_j': 'kdj_bfq',
                'kdj_k_hfq': 'kdj_k_hfq',
                'kdj_d_hfq': 'kdj_d_hfq',
                'kdj_j_hfq': 'kdj_hfq',
                'kdj_k_qfq': 'kdj_k_qfq',
                'kdj_d_qfq': 'kdj_d_qfq',
                'kdj_j_qfq': 'kdj_qfq',
                
                # ==================== 威廉指标系列 ====================
                'wr': 'wr_bfq',
                'wr1': 'wr1_bfq',
                'wr_hfq': 'wr_hfq',
                'wr1_hfq': 'wr1_hfq',
                'wr_qfq': 'wr_qfq',
                'wr1_qfq': 'wr1_qfq',
                
                # ==================== BIAS乖离率指标系列 ====================
                'bias1': 'bias1_bfq',
                'bias2': 'bias2_bfq', 
                'bias3': 'bias3_bfq',
                'bias1_hfq': 'bias1_hfq',
                'bias2_hfq': 'bias2_hfq', 
                'bias3_hfq': 'bias3_hfq',
                'bias1_qfq': 'bias1_qfq',
                'bias2_qfq': 'bias2_qfq', 
                'bias3_qfq': 'bias3_qfq',
                
                # ==================== DMI趋向指标系列 ====================
                'dmi_pdi': 'dmi_pdi_bfq',
                'dmi_mdi': 'dmi_mdi_bfq',
                'dmi_adx': 'dmi_adx_bfq',
                'dmi_adxr': 'dmi_adxr_bfq',
                'dmi_pdi_hfq': 'dmi_pdi_hfq',
                'dmi_mdi_hfq': 'dmi_mdi_hfq',
                'dmi_adx_hfq': 'dmi_adx_hfq',
                'dmi_adxr_hfq': 'dmi_adxr_hfq',
                'dmi_pdi_qfq': 'dmi_pdi_qfq',
                'dmi_mdi_qfq': 'dmi_mdi_qfq',
                'dmi_adx_qfq': 'dmi_adx_qfq',
                'dmi_adxr_qfq': 'dmi_adxr_qfq',
                
                # ==================== BRAR人气意愿指标系列 ====================
                'brar_ar': 'brar_ar_bfq',
                'brar_br': 'brar_br_bfq',
                'brar_ar_hfq': 'brar_ar_hfq',
                'brar_br_hfq': 'brar_br_hfq',
                'brar_ar_qfq': 'brar_ar_qfq',
                'brar_br_qfq': 'brar_br_qfq',
                
                # ==================== CCI商品通道指数系列 ====================
                'cci': 'cci_bfq',
                'cci_hfq': 'cci_hfq',
                'cci_qfq': 'cci_qfq',
                
                # ==================== ATR真实波幅指标系列 ====================
                'atr': 'atr_bfq',
                'atr_hfq': 'atr_hfq',
                'atr_qfq': 'atr_qfq',
                
                # ==================== ROC变动率指标系列 ====================
                'roc': 'roc_bfq',
                'roc_hfq': 'roc_hfq',
                'roc_qfq': 'roc_qfq',
                
                # ==================== MTM动量指标系列 ====================
                'mtm': 'mtm_bfq',
                'mtm_hfq': 'mtm_hfq',
                'mtm_qfq': 'mtm_qfq',
                
                # ==================== PSY心理线指标系列 ====================
                'psy': 'psy_bfq',
                'psy_hfq': 'psy_hfq',
                'psy_qfq': 'psy_qfq',
                'psyma': 'psyma_bfq',
                'psyma_hfq': 'psyma_hfq',
                'psyma_qfq': 'psyma_qfq',
                
                # ==================== OBV累积能量指标系列 ====================
                'obv': 'obv_bfq',
                'obv_hfq': 'obv_hfq',
                'obv_qfq': 'obv_qfq',
                
                # ==================== EMV简易波动指标系列 ====================
                'emv': 'emv_bfq',
                'emv_hfq': 'emv_hfq',
                'emv_qfq': 'emv_qfq',
                
                # ==================== MFI资金流量指标系列 ====================
                'mfi': 'mfi_bfq',
                'mfi_hfq': 'mfi_hfq',
                'mfi_qfq': 'mfi_qfq',
                
                # ==================== VR成交量变异率系列 ====================
                'vr': 'vr_bfq',
                'vr_hfq': 'vr_hfq',
                'vr_qfq': 'vr_qfq',
                
                # ==================== MASS梅斯线指标系列 ====================
                'mass': 'mass_bfq',
                'mass_hfq': 'mass_hfq',
                'mass_qfq': 'mass_qfq',
                'ma_mass': 'ma_mass_bfq',
                'ma_mass_hfq': 'ma_mass_hfq',
                'ma_mass_qfq': 'ma_mass_qfq',
                
                # ==================== CR指标系列 ====================
                'cr': 'cr_bfq',
                'cr_hfq': 'cr_hfq',
                'cr_qfq': 'cr_qfq',
                
                # ==================== ASI振动升降指标系列 ====================
                'asi': 'asi_bfq',
                'asit': 'asit_bfq',
                'asi_hfq': 'asi_hfq',
                'asit_hfq': 'asit_hfq',
                'asi_qfq': 'asi_qfq',
                'asit_qfq': 'asit_qfq',
                
                # ==================== TRIX三重指数平滑平均系列 ====================
                'trix': 'trix_bfq',
                'trix_hfq': 'trix_hfq',
                'trix_qfq': 'trix_qfq',
                
                # ==================== DPO去趋势价格震荡指标系列 ====================
                'dpo': 'dpo_bfq',
                'dpo_hfq': 'dpo_hfq',
                'dpo_qfq': 'dpo_qfq',
                
                # ==================== BBI多空指标系列 ====================
                'bbi': 'bbi_bfq',
                'bbi_hfq': 'bbi_hfq',
                'bbi_qfq': 'bbi_qfq',
                
                # ==================== DFMA动态平均指标系列 ====================
                'dfma_dif': 'dfma_dif_bfq',
                'dfma_difma': 'dfma_difma_bfq',
                'dfma_dif_hfq': 'dfma_dif_hfq',
                'dfma_difma_hfq': 'dfma_difma_hfq',
                'dfma_dif_qfq': 'dfma_dif_qfq',
                'dfma_difma_qfq': 'dfma_difma_qfq',
                
                # ==================== KTN肯特纳通道系列 ====================
                'ktn_upper': 'ktn_upper_bfq',
                'ktn_mid': 'ktn_mid_bfq',
                'ktn_down': 'ktn_down_bfq',
                'ktn_upper_hfq': 'ktn_upper_hfq',
                'ktn_mid_hfq': 'ktn_mid_hfq',
                'ktn_down_hfq': 'ktn_down_hfq',
                'ktn_upper_qfq': 'ktn_upper_qfq',
                'ktn_mid_qfq': 'ktn_mid_qfq',
                'ktn_down_qfq': 'ktn_down_qfq',
                
                # ==================== TAQ抛物线指标系列 ====================
                'taq_up': 'taq_up_bfq',
                'taq_mid': 'taq_mid_bfq',
                'taq_down': 'taq_down_bfq',
                'taq_up_hfq': 'taq_up_hfq',
                'taq_mid_hfq': 'taq_mid_hfq',
                'taq_down_hfq': 'taq_down_hfq',
                'taq_up_qfq': 'taq_up_qfq',
                'taq_mid_qfq': 'taq_mid_qfq',
                'taq_down_qfq': 'taq_down_qfq',
                
                # ==================== XSII小时四度空间指标系列 ====================
                'xsii_td1': 'xsii_td1_bfq',
                'xsii_td2': 'xsii_td2_bfq',
                'xsii_td3': 'xsii_td3_bfq',
                'xsii_td4': 'xsii_td4_bfq',
                'xsii_td1_hfq': 'xsii_td1_hfq',
                'xsii_td2_hfq': 'xsii_td2_hfq',
                'xsii_td3_hfq': 'xsii_td3_hfq',
                'xsii_td4_hfq': 'xsii_td4_hfq',
                'xsii_td1_qfq': 'xsii_td1_qfq',
                'xsii_td2_qfq': 'xsii_td2_qfq',
                'xsii_td3_qfq': 'xsii_td3_qfq',
                'xsii_td4_qfq': 'xsii_td4_qfq',
                
                # ==================== 涨跌统计指标 ====================
                'updays': 'updays',                    # 上涨天数
                'downdays': 'downdays',                # 下跌天数
                'topdays': 'topdays',                  # 触顶天数
                'lowdays': 'lowdays',                  # 触底天数
                
                # ==================== 财务指标字段映射 (来自stock_fina_indicator集合) ====================
                # 每股指标
                'eps': 'eps',                          # 每股收益
                'diluted2_eps': 'diluted2_eps',        # 稀释每股收益
                'dt_eps': 'dt_eps',                    # 扣非每股收益
                'bvps': 'bps',                         # 每股净资产
                'cfps': 'cfps',                        # 每股现金流
                'ocfps': 'ocfps',                      # 每股经营现金流
                'revenue_ps': 'revenue_ps',            # 每股营收
                'total_revenue_ps': 'total_revenue_ps', # 每股营业总收入
                'capital_rese_ps': 'capital_rese_ps',  # 每股资本公积
                'surplus_rese_ps': 'surplus_rese_ps',  # 每股盈余公积
                'undist_profit_ps': 'undist_profit_ps', # 每股未分配利润
                'retainedps': 'retainedps',            # 每股留存收益
                
                # 盈利能力指标
                'roe': 'roe',                          # 净资产收益率
                'roe_waa': 'roe_waa',                  # 加权平均净资产收益率
                'roe_dt': 'roe_dt',                    # 扣非净资产收益率
                'roe_avg': 'roe_avg',                  # 平均净资产收益率
                'roe_yearly': 'roe_yearly',            # 年化净资产收益率
                'roa_dp': 'roa_dp',                    # 总资产报酬率
                'roa_yearly': 'roa_yearly',            # 年化总资产收益率
                'netprofit_margin': 'netprofit_margin', # 销售净利率
                # 注意: grossprofit_margin字段在数据库中不存在，暂时移除
                # 'grossprofit_margin': 'grossprofit_margin', # 销售毛利率
                'profit_to_gr': 'profit_to_gr',        # 净利润/营业总收入
                'profit_to_op': 'profit_to_op',        # 净利润/营业利润
                
                # 营运能力指标
                'assets_turn': 'assets_turn',          # 资产周转率
                'total_fa_trun': 'total_fa_trun',      # 固定资产周转率
                
                # 偿债能力指标
                'debt_to_assets': 'debt_to_assets',    # 资产负债率
                'debt_to_eqt': 'debt_to_eqt',          # 产权比率
                'eqt_to_debt': 'eqt_to_debt',          # 权益乘数
                'assets_to_eqt': 'assets_to_eqt',      # 资产权益比
                # 注意: current_ratio, quick_ratio字段在数据库中不存在，暂时移除
                # 'current_ratio': 'current_ratio',    # 流动比率
                # 'quick_ratio': 'quick_ratio',        # 速动比率
                'ocf_to_debt': 'ocf_to_debt',          # 经营现金流量对负债比率
                'op_to_debt': 'op_to_debt',            # 营业利润对负债比率
                
                # 现金流指标
                'ocf_to_profit': 'ocf_to_profit',      # 经营现金净流量对净利润比率
                'ocf_to_opincome': 'ocf_to_opincome',  # 经营现金净流量对营业收入比率
                'ocf_to_or': 'ocf_to_or',              # 经营现金净流量营业收入比
                
                # 成长能力指标
                'revenue_yoy': 'or_yoy',               # 营业收入同比增长率
                'profit_yoy': 'netprofit_yoy',         # 净利润同比增长率
                'dt_netprofit_yoy': 'dt_netprofit_yoy', # 扣非净利润同比增长率
                'eps_yoy': 'basic_eps_yoy',            # 每股收益同比增长率
                'dt_eps_yoy': 'dt_eps_yoy',            # 扣非每股收益同比增长率
                'bps_yoy': 'bps_yoy',                  # 每股净资产同比增长率
                'cfps_yoy': 'cfps_yoy',                # 每股经营现金流同比增长率
                'roe_yoy': 'roe_yoy',                  # ROE同比变化
                'assets_yoy': 'assets_yoy',            # 资产同比增长率
                'equity_yoy': 'equity_yoy',            # 股东权益同比增长率
                'ebt_yoy': 'ebt_yoy',                  # 利润总额同比增长率
                'op_yoy': 'op_yoy',                    # 营业利润同比增长率
                'ocf_yoy': 'ocf_yoy',                  # 经营现金流同比增长率
                
                # 季度指标
                'q_eps': 'q_eps',                      # 单季每股收益
                'q_roe': 'q_roe',                      # 单季ROE
                'q_dt_roe': 'q_dt_roe',                # 单季扣非ROE
                'q_netprofit_margin': 'q_netprofit_margin', # 单季销售净利率
                'q_netprofit_yoy': 'q_netprofit_yoy',  # 单季净利润同比
                'q_netprofit_qoq': 'q_netprofit_qoq',  # 单季净利润环比
                'q_profit_yoy': 'q_profit_yoy',        # 单季利润同比
                'q_profit_qoq': 'q_profit_qoq',        # 单季利润环比
                'q_profit_to_gr': 'q_profit_to_gr',    # 单季净利润/营业总收入
                'q_dtprofit': 'q_dtprofit',            # 单季扣非净利润
                'q_dtprofit_to_profit': 'q_dtprofit_to_profit', # 单季扣非净利润/净利润
                'q_opincome': 'q_opincome',            # 单季营业收入
                'q_investincome': 'q_investincome',    # 单季投资收益
                'q_investincome_to_ebt': 'q_investincome_to_ebt', # 单季投资收益/利润总额
                'q_opincome_to_ebt': 'q_opincome_to_ebt', # 单季营业收入/利润总额
                
                # 其他财务指标
                'op_income': 'op_income',              # 营业收入
                'profit_dedt': 'profit_dedt',          # 利润总额
                'retained_earnings': 'retained_earnings', # 留存收益
                'fixed_assets': 'fixed_assets',        # 固定资产
                'non_op_profit': 'non_op_profit',      # 营业外收支净额
                'valuechange_income': 'valuechange_income', # 公允价值变动收益
                'investincome_of_ebt': 'investincome_of_ebt', # 投资收益/利润总额
                'opincome_of_ebt': 'opincome_of_ebt',  # 营业收入/利润总额
                'n_op_profit_of_ebt': 'n_op_profit_of_ebt', # 营业外收支净额/利润总额
                'dtprofit_to_profit': 'dtprofit_to_profit', # 扣非净利润/净利润
                'nop_to_ebt': 'nop_to_ebt',            # 营业外收支净额/利润总额
                'op_of_gr': 'op_of_gr',                # 营业利润/营业总收入
                'op_to_ebt': 'op_to_ebt',              # 营业利润/利润总额
                # 注意: adminexp_of_gr字段在数据库中不存在，暂时移除
                # 'adminexp_of_gr': 'adminexp_of_gr',  # 管理费用/营业总收入
                'extra_item': 'extra_item',            # 非经常性损益
                'npta': 'npta',                        # 总资产净利润
                'dp_assets_to_eqt': 'dp_assets_to_eqt', # 带息负债/全部投入资本
                
                # ==================== 市值和估值指标 (重复确认) ====================
                'pe_ttm': 'pe_ttm',                    # 市盈率TTM
                'pb': 'pb',                            # 市净率
                'ps_ttm': 'ps_ttm',                    # 市销率TTM
                # 注意: pcf_ratio字段在数据库中不存在，暂时移除
                # 'pcf_ratio': 'pcf_ratio',            # 市现率
                'market_cap': 'circ_mv',               # 流通市值(万元)
                'total_market_cap': 'total_mv',        # 总市值(万元)
                'free_share': 'free_share',            # 自由流通股本
                'total_share': 'total_share',          # 总股本
                
                # ==================== 资产负债表字段映射 (来自stock_balance_sheet集合) ====================
                'bs_ann_date': 'ann_date',             # 公告日期
                'bs_end_date': 'end_date',             # 报告期
                'bs_f_ann_date': 'f_ann_date',         # 首次公告日期
                'bs_comp_type': 'comp_type',           # 公司类型
                'bs_report_type': 'report_type',       # 报表类型
                'bond_payable': 'bond_payable',        # 应付债券
                'cap_rese': 'cap_rese',                # 资本公积金
                'cash_reser_cb': 'cash_reser_cb',      # 央行准备金
                'cb_borr': 'cb_borr',                  # 向央行借款
                'decr_in_disbur': 'decr_in_disbur',    # 拆出资金净减少额
                'defer_tax_assets': 'defer_tax_assets', # 递延所得税资产
                'depos': 'depos',                      # 客户资金存款
                'depos_in_oth_bfi': 'depos_in_oth_bfi', # 存放同业款项
                'depos_oth_bfi': 'depos_oth_bfi',      # 同业存放款项
                'deriv_assets': 'deriv_assets',        # 衍生金融资产
                'deriv_liab': 'deriv_liab',            # 衍生金融负债
                'estimated_liab': 'estimated_liab',    # 预计负债
                'fix_assets': 'fix_assets',            # 固定资产
                'goodwill': 'goodwill',                # 商誉
                'intan_assets': 'intan_assets',        # 无形资产
                'invest_real_estate': 'invest_real_estate', # 投资性房地产
                'loan_oth_bank': 'loan_oth_bank',      # 同业借款
                'loanto_oth_bank_fi': 'loanto_oth_bank_fi', # 拆借给同业
                'oth_assets': 'oth_assets',            # 其他资产
                'oth_comp_income': 'oth_comp_income',  # 其他综合收益
                'oth_eqt_tools': 'oth_eqt_tools',      # 其他权益工具
                'oth_eqt_tools_p_shr': 'oth_eqt_tools_p_shr', # 其他权益工具-优先股
                'oth_liab': 'oth_liab',                # 其他负债
                'payroll_payable': 'payroll_payable',  # 应付职工薪酬
                'prec_metals': 'prec_metals',          # 贵金属
                'pur_resale_fa': 'pur_resale_fa',      # 买入返售金融资产
                'sold_for_repur_fa': 'sold_for_repur_fa', # 卖出回购金融资产
                'surplus_rese': 'surplus_rese',        # 盈余公积
                'taxes_payable': 'taxes_payable',      # 应交税费
                'bs_total_assets': 'total_assets',     # 资产总计
                'bs_total_liab': 'total_liab',         # 负债总计
                'bs_total_share': 'total_share',       # 实收资本
                'trad_asset': 'trad_asset',            # 交易性金融资产
                'trading_fl': 'trading_fl',            # 交易性金融负债
                'undistr_porfit': 'undistr_porfit',    # 未分配利润
                
                # ==================== 指数日线数据字段映射 (来自index_daily集合) ====================
                'idx_open': 'open',                    # 指数开盘价
                'idx_high': 'high',                    # 指数最高价
                'idx_low': 'low',                      # 指数最低价
                'idx_close': 'close',                  # 指数收盘价
                'idx_pre_close': 'pre_close',          # 指数前收盘价
                'idx_change': 'change',                # 指数涨跌额
                'idx_pct_chg': 'pct_chg',              # 指数涨跌幅
                'idx_vol': 'vol',                      # 指数成交量
                'idx_amount': 'amount',                # 指数成交额
                
                # ==================== 指数权重数据字段映射 (来自index_weight集合) ====================
                'index_code': 'index_code',            # 指数代码
                'con_code': 'con_code',                # 成分股代码
                'weight': 'weight',                    # 权重
                'idx_trade_date': 'trade_date',        # 指数交易日期
                
                # ==================== 资金流向数据字段映射 (来自stock_money_flow集合) ====================
                'buy_sm_amount': 'buy_sm_amount',      # 小单买入金额
                'buy_sm_vol': 'buy_sm_vol',            # 小单买入量
                'buy_md_amount': 'buy_md_amount',      # 中单买入金额
                'buy_md_vol': 'buy_md_vol',            # 中单买入量
                'buy_lg_amount': 'buy_lg_amount',      # 大单买入金额
                'buy_lg_vol': 'buy_lg_vol',            # 大单买入量
                'buy_elg_amount': 'buy_elg_amount',    # 特大单买入金额
                'buy_elg_vol': 'buy_elg_vol',          # 特大单买入量
                'sell_sm_amount': 'sell_sm_amount',    # 小单卖出金额
                'sell_sm_vol': 'sell_sm_vol',          # 小单卖出量
                'sell_md_amount': 'sell_md_amount',    # 中单卖出金额
                'sell_md_vol': 'sell_md_vol',          # 中单卖出量
                'sell_lg_amount': 'sell_lg_amount',    # 大单卖出金额
                'sell_lg_vol': 'sell_lg_vol',          # 大单卖出量
                'sell_elg_amount': 'sell_elg_amount',  # 特大单卖出金额
                'sell_elg_vol': 'sell_elg_vol',        # 特大单卖出量
                'net_mf_amount': 'net_mf_amount',      # 净流入金额
                'net_mf_vol': 'net_mf_vol',            # 净流入量
                
                # ==================== 分红送股数据字段映射 (来自stock_dividend集合) ====================
                'div_ann_date': 'ann_date',            # 分红公告日期
                'div_end_date': 'end_date',            # 分红截止日期
                'cash_div': 'cash_div',                # 现金分红
                'cash_div_tax': 'cash_div_tax',        # 现金分红税后
                'stk_div': 'stk_div',                  # 股票股利
                'div_proc': 'div_proc',                # 分红进度
                
                # ==================== 交易日历数据字段映射 (来自infrastructure_trading_calendar集合) ====================
                'cal_date': 'cal_date',                # 日历日期
                'exchange': 'exchange',                # 交易所
                'is_open': 'is_open',                  # 是否开市
                
                # ==================== 融资融券数据字段映射 (来自margin_detail集合) ====================
                'rzye': 'rzye',                        # 融资余额
                'rzmre': 'rzmre',                      # 融资买入额
                'rzche': 'rzche',                      # 融资偿还额
                'rqye': 'rqye',                        # 融券余额
                'rqmcl': 'rqmcl',                      # 融券卖出量
                'rqchl': 'rqchl',                      # 融券偿还量
                
                # ==================== 涨跌停数据字段映射 (来自limit_list_daily集合) ====================
                'limit': 'limit',                      # 涨跌停标识
                'limit_times': 'limit_times',          # 连续涨跌停次数
                'open_times': 'open_times',            # 开板次数
                'first_time': 'first_time',            # 首次涨跌停时间
                'last_time': 'last_time',              # 最后涨跌停时间
                'limit_amount': 'amount',              # 涨跌停成交额
                'fd_amount': 'fd_amount',              # 封单金额
                'float_mv': 'float_mv',                # 流通市值
                'limit_industry': 'industry',          # 涨跌停股票行业
                'strth': 'strth',                      # 涨停强度
            }


@dataclass
class BacktestConfig:
    """
    回测配置
    """
    # 基本配置
    initial_cash: float = 1000000.0  # 初始资金100万
    start_date: str = "2020-01-01"
    end_date: str = "2023-12-31"
    
    # 交易费用
    commission_rate: float = 0.0001  # 万一手续费
    stamp_tax_rate: float = 0.001    # 千一印花税（仅卖出）
    min_commission: float = 5.0      # 最低手续费5元
    
    # 滑点设置
    slippage_rate: float = 0.001     # 千一滑点
    
    # 数据配置
    data_frequency: str = "daily"     # daily, minute, tick
    benchmark: str = "000300.SH"      # 沪深300作为基准
    
    # 输出配置
    output_dir: str = "./results"
    save_trades: bool = True
    save_positions: bool = True
    save_performance: bool = True
    
    # 并行配置
    max_workers: int = 4
    enable_multiprocessing: bool = False


@dataclass
class StrategyConfig:
    """
    策略通用配置
    """
    # 基本参数
    max_positions: int = 20          # 最大持仓数量
    rebalance_frequency: int = 5     # 调仓频率（交易日）
    min_position_value: float = 10000.0  # 最小持仓价值
    
    # 风险控制
    max_single_position: float = 0.1     # 单只股票最大权重10%
    max_sector_weight: float = 0.3       # 单个行业最大权重30%
    stop_loss_pct: float = -0.06         # 止损比例-6%
    take_profit_pct: float = 0.12        # 止盈比例12%
    max_drawdown_limit: float = -0.20    # 最大回撤限制-20%
    
    # 选股过滤
    min_market_cap: float = 50e8         # 最小市值50亿
    max_market_cap: float = 5000e8       # 最大市值5000亿
    min_turnover: float = 0.01           # 最小换手率1%
    max_turnover: float = 0.20           # 最大换手率20%
    min_price: float = 5.0               # 最小股价5元
    max_price: float = 200.0             # 最大股价200元
    
    # 排除条件
    exclude_st: bool = True              # 排除ST股票
    exclude_new_stock_days: int = 60     # 排除上市60天内新股
    exclude_suspended: bool = True       # 排除停牌股票
    
    # 行业配置
    allowed_industries: List[str] = None # 允许的行业，None表示不限制
    excluded_industries: List[str] = None # 排除的行业


@dataclass
class LoggingConfig:
    """
    日志配置
    """
    log_level: str = "INFO"
    log_dir: str = "./logs"
    max_log_files: int = 30
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    
    # 性能日志
    log_performance_interval: int = 10   # 每10次记录一次性能
    log_trade_details: bool = True
    log_signal_details: bool = True
    
    # 导出配置
    export_format: str = "csv"           # csv, json
    auto_export_interval: int = 100      # 自动导出间隔


class Config:
    """
    主配置类
    整合所有配置项
    """
    
    def __init__(self):
        # 基础配置
        self.strategy_name = "策略"  # 默认策略名称
        self.strategy_type = ""  # 策略类型
        self.database = DatabaseConfig()
        self.backtest = BacktestConfig()
        self.strategy = StrategyConfig()
        self.logging = LoggingConfig()
        
        # 策略特定配置 - 已移除旧的多周期配置类
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """
        从环境变量加载配置
        """
        # 数据库配置
        if os.getenv('MONGO_HOST'):
            self.database.host = os.getenv('MONGO_HOST')
        if os.getenv('MONGO_PORT'):
            self.database.port = int(os.getenv('MONGO_PORT'))
        if os.getenv('MONGO_DATABASE'):
            self.database.database = os.getenv('MONGO_DATABASE')
        if os.getenv('MONGO_USERNAME'):
            self.database.username = os.getenv('MONGO_USERNAME')
        if os.getenv('MONGO_PASSWORD'):
            self.database.password = os.getenv('MONGO_PASSWORD')
        
        # 回测配置
        if os.getenv('INITIAL_CASH'):
            self.backtest.initial_cash = float(os.getenv('INITIAL_CASH'))
        if os.getenv('START_DATE'):
            self.backtest.start_date = os.getenv('START_DATE')
        if os.getenv('END_DATE'):
            self.backtest.end_date = os.getenv('END_DATE')
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            self.logging.log_level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_DIR'):
            self.logging.log_dir = os.getenv('LOG_DIR')
    
    def get_strategy_config(self, strategy_name: str) -> Any:
        """
        获取特定策略的配置
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略配置对象
        """
        strategy_configs = {
            # 旧的多周期配置已移除
            # 现在使用8大策略适配器的配置
        }
        
        return strategy_configs.get(strategy_name.lower())
    
    def update_config(self, config_dict: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config_dict: 配置字典
        """
        for section, values in config_dict.items():
            if hasattr(self, section):
                config_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            配置字典
        """
        return {
            'database': self.database.__dict__,
            'backtest': self.backtest.__dict__,
            'strategy': self.strategy.__dict__,
            'logging': self.logging.__dict__
            # 旧的多周期配置已移除
        }
    
    def validate(self) -> List[str]:
        """
        验证配置的有效性
        
        Returns:
            错误信息列表
        """
        errors = []
        
        # 验证回测配置
        try:
            start_date = datetime.strptime(self.backtest.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(self.backtest.end_date, '%Y-%m-%d')
            if start_date >= end_date:
                errors.append("开始日期必须早于结束日期")
        except ValueError:
            errors.append("日期格式错误，应为YYYY-MM-DD")
        
        # 验证资金配置
        if self.backtest.initial_cash <= 0:
            errors.append("初始资金必须大于0")
        
        # 验证策略配置
        if self.strategy.max_positions <= 0:
            errors.append("最大持仓数量必须大于0")
        
        if self.strategy.max_single_position <= 0 or self.strategy.max_single_position > 1:
            errors.append("单只股票最大权重必须在0-1之间")
        
        # 验证风险参数
        if self.strategy.stop_loss_pct >= 0:
            errors.append("止损比例必须为负数")
        
        if self.strategy.take_profit_pct <= 0:
            errors.append("止盈比例必须为正数")
        
        return errors


# 全局配置实例
config = Config()


# 预定义配置模板 - 简化版本，只保留策略基础配置
CONFIG_TEMPLATES = {
    'conservative': {
        'strategy': {
            'max_positions': 15,
            'stop_loss_pct': -0.10,
            'take_profit_pct': 0.20,
            'max_single_position': 0.08
        }
    },
    'aggressive': {
        'strategy': {
            'max_positions': 30,
            'stop_loss_pct': -0.20,
            'take_profit_pct': 0.40,
            'max_single_position': 0.15
        }
    },
    'balanced': {
        'strategy': {
            'max_positions': 20,
            'stop_loss_pct': -0.06,
            'take_profit_pct': 0.12,
            'max_single_position': 0.10
        }
    }
}


def load_config_template(template_name: str) -> Config:
    """
    加载配置模板
    
    Args:
        template_name: 模板名称 ('conservative', 'aggressive', 'balanced')
        
    Returns:
        配置对象
    """
    if template_name not in CONFIG_TEMPLATES:
        raise ValueError(f"未知的配置模板: {template_name}")
    
    new_config = Config()
    new_config.update_config(CONFIG_TEMPLATES[template_name])
    
    return new_config
