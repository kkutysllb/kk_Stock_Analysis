<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="800px"
    :before-close="handleClose"
    class="strategy-detail-modal"
  >
    <template #header>
      <div class="dialog-header-content">
        <span class="dialog-title">{{ dialogTitle }}</span>
        <div class="header-actions">
          <AskAIComponent :data-context="aiDataContext" />
        </div>
      </div>
    </template>
    <div class="strategy-detail-content">
      <!-- 策略说明区域 -->
      <div class="strategy-description">
        <h3 class="section-title">
          <component :is="templateIcon" class="section-icon" />
          策略核心思想
        </h3>
        <div class="strategy-philosophy">
          <p class="philosophy-text">{{ strategyPhilosophy }}</p>
          <div class="key-principles">
            <div class="principle-item" v-for="principle in keyPrinciples" :key="principle.title">
              <div class="principle-icon">
                <component :is="principle.icon" />
              </div>
              <div class="principle-content">
                <h4>{{ principle.title }}</h4>
                <p>{{ principle.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 参数设置区域 -->
      <div class="parameter-settings">
        <h3 class="section-title">
          <component :is="CogIcon" class="section-icon" />
          策略参数设置
        </h3>
        <el-form :model="parameters" label-width="140px" class="parameter-form">
          <!-- 价值股策略参数 -->
          <template v-if="strategyTemplate?.strategy_type === 'value'">
            <el-row :gutter="20">
              <!-- 基础估值参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">估值筛选</h4>
                <el-form-item label="PE上限:">
                  <el-input-number 
                    v-model="parameters.pe_max" 
                    :min="5" 
                    :max="100" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">市盈率 < {{ parameters.pe_max }}</span>
                </el-form-item>
                <el-form-item label="PB上限:">
                  <el-input-number 
                    v-model="parameters.pb_max" 
                    :min="0.5" 
                    :max="10" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">市净率 < {{ parameters.pb_max }}</span>
                </el-form-item>
              </el-col>

              <!-- 盈利能力参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">盈利能力</h4>
                <el-form-item label="ROE下限:">
                  <el-input-number 
                    v-model="parameters.roe_min" 
                    :min="0" 
                    :max="50" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">净资产收益率 > {{ parameters.roe_min }}%</span>
                </el-form-item>
                <el-form-item label="利润增长:">
                  <el-input-number 
                    v-model="parameters.profit_growth_min" 
                    :min="-50" 
                    :max="100" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">利润增长率 > {{ parameters.profit_growth_min }}%</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 财务健康参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">财务健康</h4>
                <el-form-item label="流动比率:">
                  <el-input-number 
                    v-model="parameters.current_ratio_min" 
                    :min="0.5" 
                    :max="5" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">流动比率 > {{ parameters.current_ratio_min }}</span>
                </el-form-item>
                <el-form-item label="负债率上限:">
                  <el-input-number 
                    v-model="parameters.debt_ratio_max" 
                    :min="0" 
                    :max="90" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">资产负债率 < {{ parameters.debt_ratio_max }}%</span>
                </el-form-item>
              </el-col>

              <!-- 规模筛选参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">规模筛选</h4>
                <el-form-item label="市值下限:">
                  <el-input-number 
                    v-model="parameters.market_cap_min" 
                    :min="1" 
                    :max="1000" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">总市值 > {{ parameters.market_cap_min }}亿</span>
                </el-form-item>
                <el-form-item label="评分下限:">
                  <el-input-number 
                    v-model="parameters.total_score_min" 
                    :min="0" 
                    :max="100" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">综合评分 > {{ parameters.total_score_min }}</span>
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 成长股策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'growth'">
            <el-row :gutter="20">
              <!-- 成长性指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">🚀 成长性指标</h4>
                <el-form-item label="EPS增长率下限:">
                  <el-input-number 
                    v-model="parameters.eps_growth_min" 
                    :min="0" 
                    :max="100" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">连续三年EPS增长率 > {{ parameters.eps_growth_min }}%</span>
                </el-form-item>
                <el-form-item label="营收增长率下限:">
                  <el-input-number 
                    v-model="parameters.revenue_growth_min" 
                    :min="0" 
                    :max="100" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">连续三年营收增长率 > {{ parameters.revenue_growth_min }}%</span>
                </el-form-item>
                <el-form-item label="PEG上限:">
                  <el-input-number 
                    v-model="parameters.peg_max" 
                    :min="0.1" 
                    :max="3" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">PEG < {{ parameters.peg_max }}</span>
                </el-form-item>
              </el-col>

              <!-- 盈利能力指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">💰 盈利能力</h4>
                <el-form-item label="ROIC下限:">
                  <el-input-number 
                    v-model="parameters.roic_min" 
                    :min="0" 
                    :max="50" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">投入资本回报率 > {{ parameters.roic_min }}%</span>
                </el-form-item>
                <el-form-item label="毛利率下限:">
                  <el-input-number 
                    v-model="parameters.gross_margin_min" 
                    :min="0" 
                    :max="90" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">毛利率 > {{ parameters.gross_margin_min }}%</span>
                </el-form-item>
                <el-form-item label="净利率下限:">
                  <el-input-number 
                    v-model="parameters.net_margin_min" 
                    :min="0" 
                    :max="50" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">净利率 > {{ parameters.net_margin_min }}%</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 财务安全性 -->
              <el-col :span="12">
                <h4 class="param-group-title">🛡️ 财务安全</h4>
                <el-form-item label="资产负债率上限:">
                  <el-input-number 
                    v-model="parameters.debt_ratio_max" 
                    :min="0" 
                    :max="90" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">资产负债率 < {{ parameters.debt_ratio_max }}%</span>
                </el-form-item>
                <el-form-item label="速动比率下限:">
                  <el-input-number 
                    v-model="parameters.quick_ratio_min" 
                    :min="0.1" 
                    :max="5" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">速动比率 > {{ parameters.quick_ratio_min }}</span>
                </el-form-item>
                <el-form-item label="研发费用率下限:">
                  <el-input-number 
                    v-model="parameters.rd_rate_min" 
                    :min="0" 
                    :max="30" 
                    :step="0.5"
                    controls-position="right"
                  />
                  <span class="param-hint">研发费用率 > {{ parameters.rd_rate_min }}%</span>
                </el-form-item>
              </el-col>

              <!-- 估值与规模 -->
              <el-col :span="12">
                <h4 class="param-group-title">📊 估值规模</h4>
                <el-form-item label="PE上限:">
                  <el-input-number 
                    v-model="parameters.pe_max" 
                    :min="5" 
                    :max="100" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">市盈率 < {{ parameters.pe_max }}</span>
                </el-form-item>
                <el-form-item label="PB上限:">
                  <el-input-number 
                    v-model="parameters.pb_max" 
                    :min="0.5" 
                    :max="20" 
                    :step="0.5"
                    controls-position="right"
                  />
                  <span class="param-hint">市净率 < {{ parameters.pb_max }}</span>
                </el-form-item>
                <el-form-item label="市值下限:">
                  <el-input-number 
                    v-model="parameters.market_cap_min" 
                    :min="1" 
                    :max="1000" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">总市值 > {{ parameters.market_cap_min }}亿</span>
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 高股息策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'dividend'">
            <el-row :gutter="20">
              <!-- 核心股息指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">💰 核心股息指标</h4>
                <el-form-item label="股息率下限:">
                  <el-input-number 
                    v-model="parameters.dividend_yield_min" 
                    :min="1" 
                    :max="10" 
                    :step="0.5"
                    controls-position="right"
                  />
                  <span class="param-hint">股息率 > {{ parameters.dividend_yield_min }}%（核心筛选条件）</span>
                </el-form-item>
                <el-form-item label="股息支付率下限:">
                  <el-input-number 
                    v-model="parameters.payout_ratio_min" 
                    :min="20" 
                    :max="80" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">股息支付率 > {{ parameters.payout_ratio_min }}%（近3年平均）</span>
                </el-form-item>
                <el-form-item label="分红募资比下限:">
                  <el-input-number 
                    v-model="parameters.dividend_fundraising_ratio_min" 
                    :min="30" 
                    :max="200" 
                    :step="10"
                    controls-position="right"
                  />
                  <span class="param-hint">分红募资比 > {{ parameters.dividend_fundraising_ratio_min }}%（分红超过融资）</span>
                </el-form-item>
                <el-form-item label="净现金水平下限:">
                  <el-input-number 
                    v-model="parameters.net_cash_min" 
                    :min="0" 
                    :max="100000" 
                    :step="1000"
                    controls-position="right"
                  />
                  <span class="param-hint">净现金 > {{ parameters.net_cash_min }}万元</span>
                </el-form-item>
              </el-col>

              <!-- 财务健康指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">📈 财务健康</h4>
                <el-form-item label="ROE下限:">
                  <el-input-number 
                    v-model="parameters.roe_min" 
                    :min="0" 
                    :max="30" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">净资产收益率 > {{ parameters.roe_min }}%</span>
                </el-form-item>
                <el-form-item label="资产负债率上限:">
                  <el-input-number 
                    v-model="parameters.debt_ratio_max" 
                    :min="50" 
                    :max="90" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">资产负债率 < {{ parameters.debt_ratio_max }}%</span>
                </el-form-item>
                <el-form-item label="净利润率下限:">
                  <el-input-number 
                    v-model="parameters.net_profit_margin_min" 
                    :min="-10" 
                    :max="20" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">净利润率 > {{ parameters.net_profit_margin_min }}%</span>
                </el-form-item>
                <el-form-item label="市值下限:">
                  <el-input-number 
                    v-model="parameters.market_cap_min" 
                    :min="5" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">总市值 > {{ parameters.market_cap_min }}亿</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 策略说明 -->
              <el-col :span="24">
                <div class="strategy-note">
                  <h4>💡 高股息策略说明</h4>
                  <p>基于多维度指标筛选，<strong>发现优质分红股票</strong>：</p>
                  <ul>
                    <li><strong>核心条件</strong>：股息率 ≥ {{ parameters.dividend_yield_min }}%（基于EPS和40%分红率估算）</li>
                    <li><strong>基本要求</strong>：每股收益 > 0、总市值 ≥ 10亿</li>
                    <li><strong>风险控制</strong>：排除ST股票</li>
                    <li><strong>额外指标</strong>：分红募资比、净现金水平、股息支付率等</li>
                    <li><strong>评分权重</strong>：优先考虑股息率，兼顾现金状况和盈利能力</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </template>

          <!-- 动量突破策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'momentum'">
            <el-row :gutter="20">
              <!-- 动量指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">📈 动量指标</h4>
                <el-form-item label="过去N日收益率:">
                  <el-input-number 
                    v-model="parameters.period_days" 
                    :min="20" 
                    :max="252" 
                    :step="10"
                    controls-position="right"
                  />
                  <span class="param-hint">计算过去{{ parameters.period_days }}日收益率</span>
                </el-form-item>
                <el-form-item label="RPS阈值:">
                  <el-input-number 
                    v-model="parameters.rps_threshold" 
                    :min="60" 
                    :max="95" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">相对强度 > {{ parameters.rps_threshold }}</span>
                </el-form-item>
                <el-form-item label="量比下限:">
                  <el-input-number 
                    v-model="parameters.volume_ratio_min" 
                    :min="1.0" 
                    :max="5.0" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">量比 > {{ parameters.volume_ratio_min }}</span>
                </el-form-item>
              </el-col>

              <!-- 技术指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">⚡ 技术指标</h4>
                <el-form-item label="RSI下限:">
                  <el-input-number 
                    v-model="parameters.rsi_min" 
                    :min="30" 
                    :max="70" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">RSI > {{ parameters.rsi_min }}</span>
                </el-form-item>
                <el-form-item label="RSI上限:">
                  <el-input-number 
                    v-model="parameters.rsi_max" 
                    :min="60" 
                    :max="90" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">RSI < {{ parameters.rsi_max }}</span>
                </el-form-item>
                <el-form-item label="MACD金叉:">
                  <el-switch
                    v-model="parameters.require_macd_golden"
                    active-text="要求"
                    inactive-text="不要求"
                  />
                  <span class="param-hint">{{ parameters.require_macd_golden ? '要求MACD金叉' : '不要求MACD金叉' }}</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 均线突破 -->
              <el-col :span="12">
                <h4 class="param-group-title">📊 均线突破</h4>
                <el-form-item label="EMA(20)>EMA(50):">
                  <el-switch
                    v-model="parameters.require_ema_breakthrough"
                    active-text="要求"
                    inactive-text="不要求"
                  />
                  <span class="param-hint">{{ parameters.require_ema_breakthrough ? '要求快线在慢线之上' : '不要求均线排列' }}</span>
                </el-form-item>
                <el-form-item label="收盘价站上20日线:">
                  <el-switch
                    v-model="parameters.require_above_ma20"
                    active-text="要求"
                    inactive-text="不要求"
                  />
                  <span class="param-hint">{{ parameters.require_above_ma20 ? '要求价格站上20日线' : '不要求站上20日线' }}</span>
                </el-form-item>
              </el-col>

              <!-- 筛选条件 -->
              <el-col :span="12">
                <h4 class="param-group-title">🎯 筛选条件</h4>
                <el-form-item label="市值下限:">
                  <el-input-number 
                    v-model="parameters.market_cap_min" 
                    :min="1" 
                    :max="1000" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">总市值 > {{ parameters.market_cap_min }}亿</span>
                </el-form-item>
                <el-form-item label="涨跌幅下限:">
                  <el-input-number 
                    v-model="parameters.pct_chg_min" 
                    :min="-10" 
                    :max="10" 
                    :step="0.5"
                    controls-position="right"
                  />
                  <span class="param-hint">涨跌幅 > {{ parameters.pct_chg_min }}%</span>
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 技术突破策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'technical'">
            <el-row :gutter="20">
              <!-- RSI动能指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">⚡ RSI动能指标</h4>
                <el-form-item label="RSI下限:">
                  <el-input-number 
                    v-model="parameters.rsi_min" 
                    :min="30" 
                    :max="70" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">RSI > {{ parameters.rsi_min }}（确保动能充足）</span>
                </el-form-item>
                <el-form-item label="RSI上限:">
                  <el-input-number 
                    v-model="parameters.rsi_max" 
                    :min="60" 
                    :max="90" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">RSI < {{ parameters.rsi_max }}（避免超买）</span>
                </el-form-item>
                <el-form-item label="量比下限:">
                  <el-input-number 
                    v-model="parameters.volume_ratio_min" 
                    :min="1.0" 
                    :max="5.0" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">量比 > {{ parameters.volume_ratio_min }}（成交量放大）</span>
                </el-form-item>
              </el-col>

              <!-- MACD和均线指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">📊 MACD&均线指标</h4>
                <el-form-item label="MACD金叉要求:">
                  <el-switch
                    v-model="parameters.macd_requirement"
                    active-text="要求"
                    inactive-text="不要求"
                  />
                  <span class="param-hint">{{ parameters.macd_requirement ? '要求MACD DIF>DEA且柱状线>0' : '不要求MACD金叉' }}</span>
                </el-form-item>
                <el-form-item label="均线多头排列:">
                  <el-switch
                    v-model="parameters.ma_alignment"
                    active-text="要求"
                    inactive-text="不要求"
                  />
                  <span class="param-hint">{{ parameters.ma_alignment ? '要求5日>10日>20日均线' : '仅要求站上20日线' }}</span>
                </el-form-item>
                <el-form-item label="布林带位置:">
                  <el-select 
                    v-model="parameters.bollinger_position" 
                    placeholder="选择布林带位置要求"
                    class="param-select"
                  >
                    <el-option label="突破上轨优先" value="upper"></el-option>
                    <el-option label="中轨之上即可" value="middle"></el-option>
                    <el-option label="任意位置" value="any"></el-option>
                  </el-select>
                  <span class="param-hint">布林带位置影响评分权重</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 策略说明 -->
              <el-col :span="24">
                <div class="strategy-note">
                  <h4>📈 技术突破策略说明</h4>
                  <p>基于多重技术指标确认的<strong>技术突破选股</strong>：</p>
                  <ul>
                    <li><strong>RSI动能</strong>：RSI在{{ parameters.rsi_min }}-{{ parameters.rsi_max }}区间，确保动能充足但避免超买</li>
                    <li><strong>MACD确认</strong>：{{ parameters.macd_requirement ? 'DIF上穿DEA且柱状线为正，确认上涨动能' : '不强制要求MACD金叉' }}</li>
                    <li><strong>均线系统</strong>：{{ parameters.ma_alignment ? '短期均线多头排列，趋势向上明确' : '股价站上20日均线即可' }}</li>
                    <li><strong>成交量确认</strong>：量比>{{ parameters.volume_ratio_min }}倍，确保突破有效性</li>
                    <li><strong>布林带位置</strong>：{{ parameters.bollinger_position === 'upper' ? '突破上轨加分更高' : parameters.bollinger_position === 'middle' ? '中轨之上即可' : '任意位置' }}</li>
                    <li><strong>评分体系</strong>：综合6个维度评分，>70分为强突破信号</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </template>

          <!-- 超跌反弹策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'oversold'">
            <el-row :gutter="20">
              <!-- 超跌状态指标 -->
              <el-col :span="12">
                <h4 class="param-group-title">📉 超跌状态指标</h4>
                <el-form-item label="RSI下限:">
                  <el-input-number 
                    v-model="parameters.rsi_min" 
                    :min="10" 
                    :max="25" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">RSI > {{ parameters.rsi_min }}（避免极端情况）</span>
                </el-form-item>
                <el-form-item label="RSI上限:">
                  <el-input-number 
                    v-model="parameters.rsi_max" 
                    :min="30" 
                    :max="45" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">RSI < {{ parameters.rsi_max }}（确保超跌状态）</span>
                </el-form-item>
                <el-form-item label="量比下限:">
                  <el-input-number 
                    v-model="parameters.volume_ratio_min" 
                    :min="1.0" 
                    :max="3.0" 
                    :step="0.1"
                    controls-position="right"
                  />
                  <span class="param-hint">量比 > {{ parameters.volume_ratio_min }}（成交量放大）</span>
                </el-form-item>
              </el-col>

              <!-- 估值安全边际 -->
              <el-col :span="12">
                <h4 class="param-group-title">🛡️ 估值安全边际</h4>
                <el-form-item label="PE上限:">
                  <el-input-number 
                    v-model="parameters.pe_max" 
                    :min="20" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">PE < {{ parameters.pe_max }}（避免高估值）</span>
                </el-form-item>
                <el-form-item label="PB上限:">
                  <el-input-number 
                    v-model="parameters.pb_max" 
                    :min="3" 
                    :max="15" 
                    :step="0.5"
                    controls-position="right"
                  />
                  <span class="param-hint">PB < {{ parameters.pb_max }}（估值合理）</span>
                </el-form-item>
                <el-form-item label="连续下跌天数:">
                  <el-input-number 
                    v-model="parameters.decline_days" 
                    :min="1" 
                    :max="10" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">连续下跌 ≥ {{ parameters.decline_days }}天</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 策略说明 -->
              <el-col :span="24">
                <div class="strategy-note">
                  <h4>🔄 超跌反弹策略说明</h4>
                  <p>基于多维度超跌识别的<strong>反弹机会选股</strong>：</p>
                  <ul>
                    <li><strong>超跌确认</strong>：RSI在{{ parameters.rsi_min }}-{{ parameters.rsi_max }}区间，确保深度调整</li>
                    <li><strong>技术位支撑</strong>：股价低于20日和60日均线，处于技术性超跌</li>
                    <li><strong>成交量放大</strong>：量比>{{ parameters.volume_ratio_min }}倍，确认资金开始关注</li>
                    <li><strong>估值保护</strong>：PE<{{ parameters.pe_max }}，PB<{{ parameters.pb_max }}，提供安全边际</li>
                    <li><strong>反弹信号</strong>：当日止跌企稳或小幅反弹，确认反弹动能</li>
                    <li><strong>评分体系</strong>：综合5个维度评分，>55分为强反弹信号</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </template>

          <!-- 连板龙头策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'limit_up'">
            <el-row :gutter="20">
              <!-- 连板条件设置 -->
              <el-col :span="12">
                <h4 class="param-group-title">🔥 连板条件设置</h4>
                <el-form-item label="最小连板次数:">
                  <el-input-number 
                    v-model="parameters.min_limit_times" 
                    :min="2" 
                    :max="5" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">连板次数 ≥ {{ parameters.min_limit_times }}（建议2-3连板）</span>
                </el-form-item>
                <el-form-item label="最大连板次数:">
                  <el-input-number 
                    v-model="parameters.max_limit_times" 
                    :min="6" 
                    :max="15" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">连板次数 ≤ {{ parameters.max_limit_times }}（避免过高风险）</span>
                </el-form-item>
                <el-form-item label="最大开板次数:">
                  <el-input-number 
                    v-model="parameters.max_open_times" 
                    :min="0" 
                    :max="5" 
                    :step="1"
                    controls-position="right"
                  />
                  <span class="param-hint">开板次数 ≤ {{ parameters.max_open_times }}（确保封板稳定）</span>
                </el-form-item>
              </el-col>

              <!-- 成交活跃度控制 -->
              <el-col :span="12">
                <h4 class="param-group-title">📊 成交活跃度控制</h4>
                <el-form-item label="最小换手率:">
                  <el-input-number 
                    v-model="parameters.min_turnover" 
                    :min="3" 
                    :max="15" 
                    :step="0.5"
                    controls-position="right"
                  />
                  <span class="param-hint">换手率 ≥ {{ parameters.min_turnover }}%（确保活跃度）</span>
                </el-form-item>
                <el-form-item label="最大换手率:">
                  <el-input-number 
                    v-model="parameters.max_turnover" 
                    :min="20" 
                    :max="50" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">换手率 ≤ {{ parameters.max_turnover }}%（避免过度炒作）</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 策略说明 -->
              <el-col :span="24">
                <div class="strategy-note">
                  <h4>🚀 连板龙头策略说明</h4>
                  <p>基于真实涨跌停数据的<strong>连板龙头选股</strong>：</p>
                  <ul>
                    <li><strong>连板筛选</strong>：{{ parameters.min_limit_times }}-{{ parameters.max_limit_times }}连板区间，避免过高风险</li>
                    <li><strong>封板质量</strong>：开板次数≤{{ parameters.max_open_times }}次，确保封板稳定</li>
                    <li><strong>成交活跃</strong>：换手率{{ parameters.min_turnover }}-{{ parameters.max_turnover }}%，流动性适中</li>
                    <li><strong>板块协同</strong>：关注板块涨停股数量，选择热点板块龙头</li>
                    <li><strong>市值适中</strong>：中等市值优先，兼顾流动性和成长性</li>
                    <li><strong>评分体系</strong>：综合5个维度评分，>70分为强龙头信号</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </template>

          <!-- 资金追踪策略参数 -->
          <template v-else-if="strategyTemplate?.strategy_type === 'fund_flow'">
            <el-row :gutter="20">
              <!-- 融资交易参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">🎯 融资交易参数</h4>
                <el-form-item label="融资买入趋势下限:">
                  <el-input-number 
                    v-model="parameters.margin_buy_trend_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">融资买入趋势 ≥ {{ parameters.margin_buy_trend_min }}%</span>
                </el-form-item>
                <el-form-item label="融资余额增长下限:">
                  <el-input-number 
                    v-model="parameters.margin_balance_growth_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">融资余额增长 ≥ {{ parameters.margin_balance_growth_min }}%</span>
                </el-form-item>
                <el-form-item label="两融活跃度下限:">
                  <el-input-number 
                    v-model="parameters.margin_activity_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">两融活跃度 ≥ {{ parameters.margin_activity_min }}%</span>
                </el-form-item>
                <el-form-item label="融券趋势下限:">
                  <el-input-number 
                    v-model="parameters.short_sell_trend_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">融券趋势 ≥ {{ parameters.short_sell_trend_min }}%</span>
                </el-form-item>
              </el-col>

              <!-- 资金流向参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">💰 资金流向参数</h4>
                <el-form-item label="大单净流入下限:">
                  <el-input-number 
                    v-model="parameters.large_order_inflow_min" 
                    :min="-10000" 
                    :max="50000" 
                    :step="1000"
                    controls-position="right"
                  />
                  <span class="param-hint">大单净流入 ≥ {{ parameters.large_order_inflow_min }}万元</span>
                </el-form-item>
                <el-form-item label="超大单净流入下限:">
                  <el-input-number 
                    v-model="parameters.super_large_inflow_min" 
                    :min="-10000" 
                    :max="50000" 
                    :step="1000"
                    controls-position="right"
                  />
                  <span class="param-hint">超大单净流入 ≥ {{ parameters.super_large_inflow_min }}万元</span>
                </el-form-item>
                <el-form-item label="资金连续性下限:">
                  <el-input-number 
                    v-model="parameters.fund_continuity_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">资金流入连续性 ≥ {{ parameters.fund_continuity_min }}%</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 机构参与参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">🏛️ 机构参与参数</h4>
                <el-form-item label="机构资金占比下限:">
                  <el-input-number 
                    v-model="parameters.institutional_ratio_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">机构资金占比 ≥ {{ parameters.institutional_ratio_min }}%</span>
                </el-form-item>
                <el-form-item label="行业资金排名上限:">
                  <el-input-number 
                    v-model="parameters.industry_rank_max" 
                    :min="1" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">行业资金排名 ≤ {{ parameters.industry_rank_max }}</span>
                </el-form-item>
                <el-form-item label="行业资金强度下限:">
                  <el-input-number 
                    v-model="parameters.industry_strength_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">行业资金强度 ≥ {{ parameters.industry_strength_min }}%</span>
                </el-form-item>
              </el-col>

              <!-- 综合评分参数 -->
              <el-col :span="12">
                <h4 class="param-group-title">📊 综合评分参数</h4>
                <el-form-item label="追踪评分下限:">
                  <el-input-number 
                    v-model="parameters.fund_tracking_score_min" 
                    :min="0" 
                    :max="100" 
                    :step="5"
                    controls-position="right"
                  />
                  <span class="param-hint">资金追踪评分 ≥ {{ parameters.fund_tracking_score_min }}分</span>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <!-- 策略说明 -->
              <el-col :span="24">
                <div class="strategy-note">
                  <h4>👁️ 资金趋势跟踪策略说明</h4>
                  <p>基于<strong>两融数据、资金流向和行业轮动</strong>的多维度资金趋势跟踪：</p>
                  <ul>
                    <li><strong>融资交易分析</strong>：融资买入趋势≥{{ parameters.margin_buy_trend_min }}%，融资余额增长≥{{ parameters.margin_balance_growth_min }}%，两融活跃度≥{{ parameters.margin_activity_min }}%</li>
                    <li><strong>资金流向监控</strong>：大单净流入≥{{ parameters.large_order_inflow_min }}万元，超大单净流入≥{{ parameters.super_large_inflow_min }}万元，连续性≥{{ parameters.fund_continuity_min }}%</li>
                    <li><strong>机构参与度</strong>：机构资金占比≥{{ parameters.institutional_ratio_min }}%，行业排名≤{{ parameters.industry_rank_max }}，"聪明钱"持续关注</li>
                    <li><strong>行业资金配置</strong>：行业资金强度≥{{ parameters.industry_strength_min }}%，捕捉行业轮动机会</li>
                    <li><strong>综合评分</strong>：多维度加权评分，≥{{ parameters.fund_tracking_score_min }}分为强趋势信号</li>
                    <li><strong>策略核心</strong>：通过真实两融数据和资金流向，识别主力资金关注的投资标的</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </template>
        </el-form>
      </div>

      <!-- 权重配置区域 -->
      <div class="weight-settings">
        <h3 class="section-title">
          <component :is="ScaleIcon" class="section-icon" />
          评分权重配置
        </h3>
        <div class="weight-form">
          <div class="weight-item" v-for="weight in weights" :key="weight.key">
            <div class="weight-label">
              <span>{{ weight.label }}</span>
              <span class="weight-value">{{ weight.value }}%</span>
            </div>
            <el-slider 
              v-model="weight.value" 
              :min="0" 
              :max="50" 
              :step="5"
              @change="normalizeWeights"
              class="weight-slider"
            />
          </div>
          <div class="weight-total">
            总权重: {{ totalWeight }}% 
            <span :class="{ 'weight-error': totalWeight !== 100 }">(应为100%)</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="resetToDefault">恢复默认</el-button>
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Cog6ToothIcon as CogIcon, 
  ScaleIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  BoltIcon,
  CurrencyDollarIcon,
  ArrowPathIcon,
  FireIcon,
  ShieldCheckIcon,
  InformationCircleIcon,
  EyeIcon
} from '@heroicons/vue/24/outline'
import AskAIComponent from './AskAIComponent.vue'

// Props
interface Props {
  modelValue: boolean
  strategyTemplate: any
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save-settings': [templateId: string, parameters: any]
}>()

// 响应式数据
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 策略图标映射
const templateIcons: Record<string, any> = {
  'value': ScaleIcon,
  'growth': ArrowTrendingUpIcon,
  'momentum': BoltIcon,
  'dividend': CurrencyDollarIcon,
  'technical': ChartBarIcon,
  'oversold': ArrowPathIcon,
  'limit_up': FireIcon,
  'fund_flow': EyeIcon
}

// 策略核心思想配置
const strategyConfigs: Record<string, any> = {
  'value': {
    philosophy: '巴菲特式价值投资理念：寻找"便宜的好公司"。通过深度分析企业基本面，发现被市场低估但具有持续盈利能力和成长潜力的优质企业。注重企业的内在价值，以合理或更低的价格买入并长期持有。',
    principles: [
      {
        title: '盈利能力优先',
        description: 'ROE > 10%，选择具有持续稳定盈利能力的企业',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '财务健康稳健',
        description: '低负债率、强现金流，确保企业财务安全',
        icon: ShieldCheckIcon
      },
      {
        title: '合理估值买入',
        description: 'PE < 25, PB < 3，以合理价格买入优质股票',
        icon: CurrencyDollarIcon
      },
      {
        title: '稳定增长预期',
        description: '关注业绩稳定增长，避免周期性和高风险股票',
        icon: ArrowTrendingUpIcon
      }
    ]
  },
  'growth': {
    philosophy: '高质量成长股投资策略：基于彼得·林奇和菲利普·费雪的成长投资理念，寻找具备超强盈利能力、持续高增长、合理估值的优质企业。通过严格的量化筛选标准，发现真正的"成长股之王"，追求长期稳健的超额收益。',
    principles: [
      {
        title: '稳健增长引擎',
        description: 'EPS增长>10%或营收增长>8%，确保持续成长动力',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '优质盈利能力',
        description: 'ROIC>6%，毛利率>15%，净利率>5%，具备盈利优势',
        icon: CurrencyDollarIcon
      },
      {
        title: '合理估值区间',
        description: 'PEG<2，灵活估值标准，平衡成长性与安全性',
        icon: ShieldCheckIcon
      },
      {
        title: '创新驱动发展',
        description: '研发费用率>2%，持续创新投入，构建长期护城河',
        icon: BoltIcon
      }
    ]
  },
  'dividend': {
    philosophy: '新版高股息策略：基于多维度分红质量筛选，寻找真正优质的分红股票。要求分红募资比>100%、股息支付率近3年>40%、股息率近一年>3%、净现金水平>0。通过严格的分红质量评估，发现真正回馈股东的优质企业。',
    principles: [
      {
        title: '分红超过融资',
        description: '分红募资比>100%，公司真正回馈股东而非圈钱',
        icon: CurrencyDollarIcon
      },
      {
        title: '持续分红能力',
        description: '股息支付率近3年>40%，具备稳定的分红实力',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '吸引力股息率',
        description: '股息率近一年>3%，提供有竞争力的现金回报',
        icon: InformationCircleIcon
      },
      {
        title: '现金流健康',
        description: '净现金水平>0，确保良好的现金状况支撑分红',
        icon: ShieldCheckIcon
      }
    ]
  },
  'momentum': {
    philosophy: '动量突破策略：基于技术分析和量化指标，捕捉股价突破关键阻力位的强势股票。通过多维度技术指标组合，识别具备持续上涨动能的个股，在趋势确立初期介入，获取趋势性收益。',
    principles: [
      {
        title: '趋势动量确认',
        description: '过去60日收益率前20%，RPS≥80，确保相对强势',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '技术指标共振',
        description: 'RSI(50-70)，MACD金叉，多指标确认突破有效性',
        icon: BoltIcon
      },
      {
        title: '均线系统支撑',
        description: 'EMA(20)>EMA(50)，价格站上20日线，趋势向上',
        icon: ChartBarIcon
      },
      {
        title: '成交量放大',
        description: '量比>1.5倍，突破伴随成交量放大，确保资金认可',
        icon: FireIcon
      }
    ]
  },
  'technical': {
    philosophy: '技术突破策略：基于多重技术指标确认的突破性选股策略。通过RSI动能、MACD金叉、均线排列、布林带位置、成交量配合等六个维度的综合分析，识别技术面强势突破的个股。注重多指标共振确认，避免假突破，在趋势初期捕捉最佳介入时机。',
    principles: [
      {
        title: 'RSI动能确认',
        description: 'RSI在50-80区间，确保动能充足但避免超买风险',
        icon: BoltIcon
      },
      {
        title: 'MACD金叉验证',
        description: 'DIF上穿DEA且柱状线为正，确认上涨动能启动',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '均线多头排列',
        description: '5日>10日>20日均线，趋势向上结构清晰',
        icon: ChartBarIcon
      },
      {
        title: '布林带位置优化',
        description: '价格在中轨之上，突破上轨获得更高评分',
        icon: InformationCircleIcon
      },
      {
        title: '成交量放大确认',
        description: '量比>1.5倍，突破伴随成交量放大确保有效性',
        icon: FireIcon
      },
      {
        title: '综合评分筛选',
        description: '六维度评分系统，>70分为强突破信号',
        icon: ScaleIcon
      }
    ]
  },
  'oversold': {
    philosophy: '超跌反弹策略：基于多维度超跌识别和反弹确认的选股策略。通过RSI超跌区域、成交量放大、估值合理性、技术位支撑等维度筛选，寻找深度调整后具备反弹潜力的优质股票。注重安全边际和反弹确认信号，在市场恐慌中发现价值机会。',
    principles: [
      {
        title: '超跌状态确认',
        description: 'RSI<35，股价低于20日和60日均线，确保超跌状态',
        icon: ArrowPathIcon
      },
      {
        title: '成交量放大验证',
        description: '量比>1.3倍，反弹伴随成交量放大，确认资金关注',
        icon: FireIcon
      },
      {
        title: '估值安全边际',
        description: 'PE<50，PB<8，确保合理估值提供安全保护',
        icon: ShieldCheckIcon
      },
      {
        title: '技术位支撑',
        description: '重要均线支撑位附近，历史低点区域反弹概率高',
        icon: ChartBarIcon
      },
      {
        title: '反弹信号确认',
        description: '当日止跌企稳或小幅反弹，确认反弹动能启动',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '综合评分筛选',
        description: '五维度评分系统，>55分为强反弹信号',
        icon: ScaleIcon
      }
    ]
  },
  'limit_up': {
    philosophy: '连板龙头策略：基于真实涨跌停数据的连板龙头选股策略。通过连板次数、封板强度、板块热度、市值规模、换手率等多维度分析，识别具备持续上涨潜力的连板龙头股。注重封板质量和板块协同效应，在强势行情中捕捉龙头机会。',
    principles: [
      {
        title: '连板次数确认',
        description: '2-6连板为最优区间，过高连板风险增大',
        icon: FireIcon
      },
      {
        title: '封板强度验证',
        description: '开板次数少，封板稳定，确保上涨动能持续',
        icon: ShieldCheckIcon
      },
      {
        title: '板块热度评估',
        description: '所属板块涨停股数量多，板块整体强势',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '市值规模筛选',
        description: '中等市值股票流动性好，易于操作',
        icon: CurrencyDollarIcon
      },
      {
        title: '换手率适中',
        description: '8-20%换手率，避免过度炒作',
        icon: ChartBarIcon
      },
      {
        title: '综合评分筛选',
        description: '五维度评分系统，>70分为强龙头信号',
        icon: ScaleIcon
      }
    ]
  },
  'fund_flow': {
    philosophy: '资金趋势跟踪策略：基于真实两融数据、资金流向和行业轮动的多维度资金趋势跟踪策略。通过深度分析融资买入趋势、融资余额增长、两融活跃度、大单资金流入、机构参与度和行业资金配置，识别主力资金关注的优质投资标的。利用真实的两融交易数据，追踪"聪明钱"的足迹，发现市场先知先觉的投资机会。',
    principles: [
      {
        title: '融资买入趋势分析',
        description: '融资买入趋势≥50%，主力资金通过融资积极布局',
        icon: ArrowTrendingUpIcon
      },
      {
        title: '融资余额增长监控',  
        description: '融资余额增长≥50%，资金持续流入，市场信心增强',
        icon: CurrencyDollarIcon
      },
      {
        title: '两融活跃度评估',
        description: '两融活跃度≥30%，交易活跃，资金关注度高',
        icon: FireIcon
      },
      {
        title: '大单资金流入',
        description: '大单和超大单持续净流入，机构资金积极布局',
        icon: EyeIcon
      },
      {
        title: '行业资金轮动',
        description: '行业资金排名靠前，捕捉行业轮动机会',
        icon: ChartBarIcon
      },
      {
        title: '综合趋势评分',
        description: '多维度评分系统，>20分为强资金趋势信号',
        icon: ScaleIcon
      }
    ]
  }
}

// 计算属性
const dialogTitle = computed(() => {
  return props.strategyTemplate ? `${props.strategyTemplate.name} - 策略详情` : '策略详情'
})

const templateIcon = computed(() => {
  const strategyType = props.strategyTemplate?.strategy_type || 'value'
  return templateIcons[strategyType] || ChartBarIcon
})

const strategyPhilosophy = computed(() => {
  const strategyType = props.strategyTemplate?.strategy_type || 'value'
  return strategyConfigs[strategyType]?.philosophy || '暂无策略说明'
})

const keyPrinciples = computed(() => {
  const strategyType = props.strategyTemplate?.strategy_type || 'value'
  return strategyConfigs[strategyType]?.principles || []
})

// 策略默认参数配置
const defaultParameters: Record<string, any> = {
  'value': {
    pe_max: 25,
    pb_max: 3,
    roe_min: 10,
    profit_growth_min: 5,
    current_ratio_min: 1.2,
    debt_ratio_max: 60,
    market_cap_min: 10,
    total_score_min: 70
  },
  'growth': {
    eps_growth_min: 10,          // EPS增长率下限 (降低)
    revenue_growth_min: 8,       // 营收增长率下限 (降低)
    peg_max: 2.0,               // PEG上限 (放宽)
    roic_min: 6,                // ROIC下限 (降低)
    gross_margin_min: 15,       // 毛利率下限 (降低)
    net_margin_min: 5,          // 净利率下限 (降低)
    debt_ratio_max: 80,         // 资产负债率上限 (放宽)
    quick_ratio_min: 0.5,       // 速动比率下限 (降低)
    rd_rate_min: 2,             // 研发费用率下限 (降低)
    pe_max: 50,                 // PE上限 (放宽)
    pb_max: 8,                  // PB上限 (放宽)
    market_cap_min: 5,          // 市值下限 (降低)
    total_score_min: 60         // 评分下限 (降低)
  },
  'momentum': {
    period_days: 60,            // 过去N日收益率计算周期
    rps_threshold: 80,          // RPS相对强度阈值
    rsi_min: 50,               // RSI下限
    rsi_max: 70,               // RSI上限
    volume_ratio_min: 1.5,     // 量比下限
    require_macd_golden: true,  // 是否要求MACD金叉
    require_ema_breakthrough: true,  // 是否要求EMA突破
    require_above_ma20: true,   // 是否要求站上20日线
    market_cap_min: 10,        // 市值下限(亿)
    pct_chg_min: 0             // 涨跌幅下限(%)
  },
  'dividend': {
    dividend_yield_min: 2.0,           // 股息率下限(%) - 核心条件
    payout_ratio_min: 20.0,            // 股息支付率下限(%) - 固定假设值
    dividend_fundraising_ratio_min: 30.0,  // 分红募资比下限(%) - 实际计算
    net_cash_min: -1000000.0,          // 净现金水平下限(万元) - 不限制
    roe_min: 0,                        // ROE下限(%) - 确保盈利
    debt_ratio_max: 80,                // 资产负债率上限(%)
    net_profit_margin_min: 0,          // 净利润率下限(%)
    market_cap_min: 10,                // 市值下限(亿)
    total_score_min: 0                 // 评分下限 - 不限制
  },
  'technical': {
    rsi_min: 45.0,                    // RSI下限(%) - 确保动能充足（放宽）
    rsi_max: 85.0,                    // RSI上限(%) - 避免超买（放宽）
    volume_ratio_min: 1.2,            // 量比下限 - 确保成交量放大（放宽）
    macd_requirement: false,           // 是否要求MACD金叉（默认不要求）
    ma_alignment: false,               // 是否要求均线多头排列（默认不要求）
    bollinger_position: 'upper'        // 布林带位置要求
  },
  'oversold': {
    rsi_min: 15.0,                    // RSI下限(%) - 避免极端情况
    rsi_max: 35.0,                    // RSI上限(%) - 超跌区域
    volume_ratio_min: 1.3,            // 量比下限 - 成交量放大
    pe_max: 50.0,                     // PE上限 - 避免高估值
    pb_max: 8.0,                      // PB上限 - 避免高估值
    decline_days: 3                   // 连续下跌天数要求
  },
  'limit_up': {
    min_limit_times: 2,               // 最小连板次数
    max_limit_times: 10,              // 最大连板次数
    max_open_times: 3,                // 最大开板次数
    min_turnover: 5.0,                // 最小换手率(%)
    max_turnover: 30.0                // 最大换手率(%)
  },
  'fund_flow': {
    margin_buy_trend_min: 50,         // 融资买入趋势下限(%)
    margin_balance_growth_min: 50,    // 融资余额增长下限(%)
    margin_activity_min: 30,          // 两融活跃度下限(%)
    short_sell_trend_min: 50,         // 融券趋势下限(%)
    large_order_inflow_min: 0,        // 大单净流入下限(万元)
    super_large_inflow_min: 0,        // 超大单净流入下限(万元)
    fund_continuity_min: 40,          // 资金流入连续性下限(%)
    institutional_ratio_min: 20,      // 机构资金占比下限(%)
    industry_rank_max: 50,            // 行业资金排名上限
    industry_strength_min: 0,         // 行业资金强度下限(%)
    fund_tracking_score_min: 20       // 资金追踪综合评分下限
  }
}

// 策略权重配置
const defaultWeights: Record<string, any[]> = {
  'value': [
    { key: 'roe_weight', label: 'ROE权重', value: 40 },
    { key: 'cash_flow_weight', label: '现金流权重', value: 20 },
    { key: 'debt_weight', label: '负债权重', value: 20 },
    { key: 'growth_weight', label: '增长权重', value: 10 },
    { key: 'valuation_weight', label: '估值权重', value: 10 }
  ],
  'growth': [
    { key: 'eps_growth_weight', label: 'EPS增长权重', value: 25 },
    { key: 'revenue_growth_weight', label: '营收增长权重', value: 20 },
    { key: 'roic_weight', label: 'ROIC权重', value: 25 },
    { key: 'profitability_weight', label: '盈利能力权重', value: 20 },
    { key: 'innovation_weight', label: '创新投入权重', value: 10 }
  ],
  'momentum': [
    { key: 'volume_ratio_weight', label: '量比权重', value: 25 },
    { key: 'rsi_weight', label: 'RSI权重', value: 15 },
    { key: 'macd_weight', label: 'MACD权重', value: 20 },
    { key: 'price_momentum_weight', label: '价格动量权重', value: 15 },
    { key: 'breakthrough_weight', label: '突破信号权重', value: 15 },
    { key: 'rps_weight', label: '相对强度权重', value: 10 }
  ],
  'dividend': [
    { key: 'dividend_yield_weight', label: '股息率权重', value: 30 },
    { key: 'payout_ratio_weight', label: '股息支付率权重', value: 20 },
    { key: 'dividend_fundraising_ratio_weight', label: '分红募资比权重', value: 20 },
    { key: 'net_cash_weight', label: '净现金水平权重', value: 15 },
    { key: 'profitability_weight', label: '盈利能力权重', value: 10 },
    { key: 'financial_safety_weight', label: '财务安全权重', value: 5 }
  ],
  'technical': [
    { key: 'bollinger_weight', label: '布林带位置权重', value: 25 },
    { key: 'ma_alignment_weight', label: '均线排列权重', value: 20 },
    { key: 'macd_weight', label: 'MACD强度权重', value: 20 },
    { key: 'rsi_weight', label: 'RSI动能权重', value: 15 },
    { key: 'volume_weight', label: '成交量权重', value: 15 },
    { key: 'momentum_weight', label: '价格动量权重', value: 5 }
  ],
  'oversold': [
    { key: 'rsi_weight', label: 'RSI超跌权重', value: 25 },
    { key: 'volume_weight', label: '量比权重', value: 20 },
    { key: 'valuation_weight', label: '估值权重', value: 15 },
    { key: 'rebound_signal_weight', label: '反弹信号权重', value: 15 },
    { key: 'turnover_weight', label: '换手率权重', value: 25 }
  ],
  'limit_up': [
    { key: 'limit_times_weight', label: '连板次数权重', value: 30 },
    { key: 'seal_strength_weight', label: '封板强度权重', value: 25 },
    { key: 'sector_heat_weight', label: '板块热度权重', value: 20 },
    { key: 'market_cap_weight', label: '市值权重', value: 15 },
    { key: 'turnover_weight', label: '换手率权重', value: 10 }
  ],
  'fund_flow': [
    { key: 'margin_trading_weight', label: '融资交易权重', value: 30 },
    { key: 'fund_flow_weight', label: '资金流向权重', value: 30 },
    { key: 'institutional_weight', label: '机构参与权重', value: 25 },
    { key: 'industry_rotation_weight', label: '行业轮动权重', value: 15 }
  ]
}

// 参数设置
const parameters = reactive<Record<string, any>>({})

// 权重配置 - 修复初始化问题
const weights = reactive<Array<{ key: string; label: string; value: number }>>([])

const totalWeight = computed(() => {
  return weights.reduce((sum, weight) => sum + weight.value, 0)
})

// AI数据上下文
const aiDataContext = computed(() => {
  const strategy = props.strategyTemplate
  const strategyType = strategy?.strategy_type || 'value'
  const strategyName = strategy?.name || '未知策略'
  
  // 获取当前策略的核心思想和配置
  const strategyConfig = strategyConfigs[strategyType] || strategyConfigs['value']
  
  // 构建详细的策略分析摘要
  const parametersSummary = Object.entries(parameters).map(([key, value]) => 
    `- ${key}: ${value}`
  ).join('\n')
  
  const weightsSummary = weights.map(weight => 
    `- ${weight.label}: ${weight.value}%`
  ).join('\n')
  
  const principlesSummary = strategyConfig.principles?.map((principle: any, index: number) => 
    `${index + 1}. **${principle.title}**: ${principle.description}`
  ).join('\n') || ''
  
  const summary = `投资策略详细配置分析：

## 策略基本信息
- **策略名称**: ${strategyName}
- **策略类型**: ${strategyType}
- **策略哲学**: ${strategyConfig.philosophy}

## 核心投资原则
${principlesSummary}

## 当前参数配置
${parametersSummary || '- 暂无参数配置'}

## 权重分布设置
${weightsSummary || '- 暂无权重配置'}
- **权重总和**: ${totalWeight.value}%

## 分析要点
- 配置参数数量：${Object.keys(parameters).length}个
- 权重指标数量：${weights.length}个
- 权重配置状态：${totalWeight.value === 100 ? '✅ 权重平衡' : '⚠️ 权重需调整'}
- 策略类型特征：基于${strategyType}投资理念的专业选股策略

请基于以上策略配置信息，从投资逻辑合理性、参数设置优化、权重分配均衡性、市场适用性、风险控制等角度进行专业分析，并提供改进建议。`

  return {
    type: 'strategy_config',
    name: `${strategyName}策略配置`,  // name用于AI组件检测数据变化
    title: '投资策略配置分析',
    summary: summary,
    data: {
      strategyType: strategyType,
      strategyName: strategyName,
      parameters: parameters,
      weights: weights,
      totalWeight: totalWeight.value,
      philosophy: strategyConfig.philosophy,
      principles: strategyConfig.principles
    }
  }
})

// 方法
const handleClose = () => {
  visible.value = false
}

const normalizeWeights = () => {
  // 可以添加权重归一化逻辑
  if (totalWeight.value > 100) {
    ElMessage.warning('权重总和不能超过100%，请调整')
  }
}

const resetToDefault = () => {
  const strategyType = props.strategyTemplate?.strategy_type || 'value'
  
  // 恢复默认参数
  Object.assign(parameters, defaultParameters[strategyType] || defaultParameters['value'])
  
  // 恢复默认权重
  weights.length = 0
  const defaultWeightsForType = defaultWeights[strategyType] || defaultWeights['value']
  weights.push(...defaultWeightsForType)
  
  ElMessage.success('已恢复默认设置')
}

const saveSettings = () => {
  if (totalWeight.value !== 100) {
    ElMessage.error('权重总和必须为100%，请调整后再保存')
    return
  }
  
  const settings = {
    parameters: { ...parameters },
    weights: weights.reduce((acc, weight) => {
      acc[weight.key] = weight.value
      return acc
    }, {} as Record<string, number>)
  }
  
  emit('save-settings', props.strategyTemplate?.id, settings)
  ElMessage.success('策略参数已保存')
  visible.value = false
}

// 初始化数据的函数
const initializeData = (strategyType: string) => {
  // 加载对应策略的默认参数
  const defaultParams = defaultParameters[strategyType] || defaultParameters['value']
  Object.keys(parameters).forEach(key => delete parameters[key])
  Object.assign(parameters, defaultParams)
  
  // 加载对应策略的默认权重
  weights.length = 0
  const defaultWeightsForType = defaultWeights[strategyType] || defaultWeights['value']
  weights.push(...defaultWeightsForType)
  
  // console.log('初始化策略数据:', strategyType, {
  //   parameters: parameters,
  //   weights: weights,
  //   totalWeight: totalWeight.value
  // })
}

// 监听策略模板变化，加载对应的默认参数
watch(() => props.strategyTemplate, (newTemplate) => {
  if (newTemplate) {
    const strategyType = newTemplate.strategy_type || 'value'
    initializeData(strategyType)
  }
}, { immediate: true })

// 监听弹窗显示状态，确保数据正确初始化
watch(() => props.modelValue, (isVisible) => {
  if (isVisible && props.strategyTemplate) {
    const strategyType = props.strategyTemplate.strategy_type || 'value'
    initializeData(strategyType)
  }
})
</script>

<style scoped>
.strategy-detail-modal {
  --el-dialog-padding-primary: 0;
}

/* 对话框头部样式 */
.dialog-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0 var(--spacing-lg);
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.strategy-detail-content {
  padding: var(--spacing-lg);
  max-height: 70vh;
  overflow-y: auto;
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 2px solid var(--border-primary);
}

.section-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-primary);
}

/* 策略说明样式 */
.strategy-description {
  margin-bottom: var(--spacing-xl);
}

.philosophy-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--accent-primary);
}

.key-principles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
}

.principle-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--gradient-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-base);
}

.principle-item:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 12px rgba(0, 255, 255, 0.1);
}

.principle-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-primary);
  border-radius: var(--radius-md);
  color: white;
  flex-shrink: 0;
}

.principle-icon svg {
  width: 20px;
  height: 20px;
}

.principle-content h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.principle-content p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* 参数设置样式 */
.parameter-settings {
  margin-bottom: var(--spacing-xl);
}

.param-group-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-primary);
  margin-bottom: var(--spacing-md);
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-primary);
}

.parameter-form {
  background: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
}

.param-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: var(--spacing-sm);
  font-style: italic;
}

/* 权重设置样式 */
.weight-settings {
  margin-bottom: var(--spacing-lg);
}

.weight-form {
  background: var(--bg-secondary);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-primary);
}

.weight-item {
  margin-bottom: var(--spacing-lg);
}

.weight-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.weight-value {
  font-weight: 600;
  color: var(--accent-primary);
}

.weight-slider {
  margin-bottom: var(--spacing-sm);
}

.weight-total {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-primary);
  font-weight: 600;
  text-align: center;
}

.weight-error {
  color: var(--text-danger);
}

/* 对话框底部样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategy-detail-content {
    padding: var(--spacing-md);
  }
  
  .key-principles {
    grid-template-columns: 1fr;
  }
  
  .parameter-form .el-row {
    flex-direction: column;
  }
  
  .parameter-form .el-col {
    width: 100%;
    margin-bottom: var(--spacing-md);
  }
}

/* Element Plus 组件样式覆盖 */
:deep(.el-form-item) {
  margin-bottom: var(--spacing-md);
}

:deep(.el-input-number) {
  width: 120px;
}

:deep(.el-slider__runway) {
  background-color: var(--border-primary);
}

:deep(.el-slider__bar) {
  background-color: var(--accent-primary);
}

:deep(.el-slider__button) {
  border-color: var(--accent-primary);
}

.strategy-note {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 16px;
  margin: 16px 0;
}

.strategy-note h4 {
  color: var(--accent-primary);
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.strategy-note p {
  color: var(--text-primary);
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.strategy-note ul {
  margin: 0;
  padding-left: 20px;
}

.strategy-note li {
  color: var(--text-secondary);
  margin-bottom: 6px;
  line-height: 1.5;
}

.strategy-note strong {
  color: var(--accent-primary);
  font-weight: 600;
}
</style>