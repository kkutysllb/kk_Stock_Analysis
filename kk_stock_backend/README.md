# 🚀 KK股票量化分析系统

一个基于MongoDB的股票量化分析多端项目，专注于股指期货、ETF、股票和宏观数据的采集与分析。

## 📁 项目结构

```
kk_StockQuant_Analysis/
├── analysis/                # 核心分析模块 🆕
│   ├── dow_theory/         # 道氏理论分析引擎
│   │   ├── core/           # 核心分析引擎
│   │   ├── analyzers/      # 各类分析器
│   │   ├── models/         # 数据模型定义
│   │   └── utils/          # 工具类
│   └── chan_theory/        # 缠论分析引擎
├── api/                     # API接口层
│   ├── routers/            # API路由
│   │   ├── dow_theory_analysis.py  # 道氏理论分析API
│   │   └── chan_theory_analysis.py # 缠论分析API
│   └── main.py             # API服务入口
├── backtrader_strategies/   # 量化策略模块
├── qlib_quantitative/       # Qlib量化框架集成
├── data_collector/          # 数据采集模块
├── tests/                   # 统一测试模块
├── docs/                    # 项目文档
└── frontend/                # 前端应用（独立仓库）
```

## ✨ 主要特性

### 🔄 数据采集系统
- **股指期货数据**: K线数据、持仓排名、基本信息
- **ETF数据**: 基本信息、日线数据、成交量分析
- **股票数据**: 基本信息、K线数据、技术指标
- **宏观数据**: CPI、货币供应量、利率等经济指标

### 📊 数据分析系统
- **道氏理论分析**: 多时间周期趋势分析、123法则、2B法则、增强技术分析 🆕
- **缠论分析**: 笔段识别、分型分析、多级别结构分析 🆕
- **市场分析**: 大盘综合分析、板块分析、龙虎榜分析
- **ETF分析**: 成交量变化分析、相关性分析
- **期货分析**: 持仓变化分析、贴升水分析
- **技术分析**: 移动平均线、RSI、MACD等技术指标
- **宏观分析**: 经济趋势分析

### 🧪 统一测试模块
- **系统连接测试**: 网络、API、数据库连接检查
- **功能测试**: 各模块功能完整性验证
- **数据验证**: 数据采集和分析结果验证
- **统一运行器**: 支持单个、分类、批量测试执行

### 📅 智能交易日历
- **Tushare集成**: 基于Tushare API获取真实交易日历
- **本地缓存**: 数据库存储交易日历，减少API调用
- **智能判断**: 准确识别交易日、休市日、节假日
- **增量更新**: 只在交易日执行数据更新

### 🔄 自动化增量更新
- **交易日检测**: 自动识别交易日，跳过非交易日
- **智能调度**: 避免重复更新，检测进程冲突
- **分级任务**: 关键数据优先，可选数据补充
- **错误处理**: 超时控制、失败重试、状态监控

## 🚀 快速开始

### 1. 环境准备
```bash
# 激活conda环境
conda activate kk_stock

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export TUSHARE_TOKEN=你的Tushare令牌
```

### 2. 数据库启动
```bash
# 启动MongoDB集群
cd database
docker-compose up -d
```

### 3. 数据采集
```bash
# 采集所有数据
python data_collector/main_collector.py --task all

# 采集特定数据
python data_collector/main_collector.py --task stock_kline --days 30
```

### 4. 数据分析
```bash
# 执行市场分析
python data_analysis/main_analyzer.py --task market_report

# 执行所有分析
python data_analysis/main_analyzer.py --task all_analysis --days 30
```

### 5. 系统测试
```bash
# 查看所有可用测试
python tests/run_tests.py --list

# 运行连接测试
python tests/run_tests.py --test connection

# 运行所有测试
python tests/run_tests.py --all
```

### 6. 交易日历管理
```bash
# 更新交易日历（首次使用）
python trading_calendar_manager.py --update 20250101 20251231

# 查看交易日历状态
python trading_calendar_manager.py --stats

# 显示最近交易日历
python trading_calendar_manager.py --show 14

# 检查特定日期是否为交易日
python trading_calendar_manager.py --check 20250623
```

### 7. 增量更新调度
```bash
# 检查数据采集状态
cd data_collector
python main_collector.py --status

# 智能自动增量采集（推荐）
python main_collector.py --auto

# 只采集每日更新的数据
python main_collector.py --frequency daily

# 高效并行采集日线数据
python main_collector.py --frequency daily --parallel-groups --workers 5
```

### 8. 定时任务设置（macOS）
> **⚠️ 注意**：`daily_update_scheduler.py` 和 `run_daily_update.sh` 已废弃，建议直接使用 `main_collector.py` 进行数据采集。

```bash
# 推荐的每日数据采集命令（可用于定时任务）
cd data_collector && python main_collector.py --frequency daily

# 或使用智能自动采集
cd data_collector && python main_collector.py --auto

# 传统定时任务管理（已过时，不推荐使用）
./manage_cron.sh status    # 查看状态
./manage_cron.sh logs      # 查看日志
./manage_cron.sh test      # 测试执行
./manage_cron.sh enable    # 启用任务
./manage_cron.sh disable   # 禁用任务
```

**定时任务特性**：
- 🎯 **智能执行**: 只在交易日进行数据更新
- 🔄 **自动化**: 无需人工干预的定时执行
- 📊 **可监控**: 详细的日志和状态检查
- 🛠️ **易管理**: 简单的命令行管理工具

## 🧪 测试系统

### 统一测试管理
所有测试脚本统一放置在 `tests/` 目录下，提供一致的测试体验：

```bash
# 统一测试运行器使用方法
python tests/run_tests.py [选项]

# 常用命令
python tests/run_tests.py --list                    # 列出所有测试
python tests/run_tests.py --test connection         # 运行连接测试
python tests/run_tests.py --category etf            # 运行ETF相关测试
python tests/run_tests.py --all                     # 运行所有测试
```

### 测试分类
- **连接测试**: 网络、API、数据库连接验证
- **ETF测试**: ETF数据采集和分析功能测试
- **期货测试**: 期货数据采集和分析功能测试
- **市场测试**: 市场分析功能测试
- **分析测试**: 综合分析功能测试

## 📊 数据统计

当前系统包含：
- **24个数据集合** 有数据
- **107,336条记录** 总计
- **支持品种**: 股指期货(IF/IH/IC/IM)、主要ETF、A股、宏观指标

## 🔧 系统架构

### 数据流向
```
数据源(Tushare) → 数据采集器 → MongoDB → 数据分析器 → 分析结果
```

### 模块分离
- **数据采集**: 专注于数据获取和存储，不包含分析逻辑
- **数据分析**: 专门从数据库读取数据进行分析
- **测试验证**: 统一的测试框架验证系统功能

## 📚 详细文档

- [数据分析模块说明](data_analysis/README.md)
- [测试模块说明](tests/README.md)
- [交易日历与增量更新使用说明](docs/交易日历与增量更新使用说明.md) 🆕
- [macOS定时任务设置说明](docs/macOS定时任务设置说明.md) 🆕
- [Tushare数据采集说明](docs/Tushare数据采集说明.md)
- [MongoDB集群部署指导](docs/macOS_MongoDB集群部署指导.md)
- [股指期货数据采集与分析使用说明](docs/股指期货数据采集与分析使用说明.md)

## 🛠️ 技术栈

- **数据库**: MongoDB (副本集集群)
- **数据源**: Tushare Pro API
- **后端**: Python + FastAPI
- **前端**: Vue.js + uni-app
- **容器化**: Docker + Docker Compose
- **测试**: 统一测试框架

## 📈 核心功能亮点

### 市场分析 🆕
- **大盘综合分析**: 成交量环比、资金流向、市场情绪
- **板块分析**: TOP10成交量差异板块、资金流入流出
- **龙虎榜分析**: 个股异动识别、环比差异分析

### 期货分析
- **持仓分析**: 机构持仓变化、龙虎榜排名
- **贴升水分析**: 期限结构、套利机会识别

### ETF分析
- **成交量分析**: 热门ETF追踪、异动识别
- **相关性分析**: ETF间相关性计算

## 💡 使用建议

1. **定期数据采集**: 建议每日运行数据采集任务
2. **及时分析**: 数据采集后及时进行分析
3. **测试验证**: 定期运行测试确保系统正常
4. **监控存储**: 注意数据库存储空间和性能

## 🚀 道氏理论增强分析系统

### 核心功能
- **多时间周期分析**: 月线（主要趋势）、周线（次要趋势）、日线（短期波动）
- **道氏法则分析**: 123法则信号识别、2B法则假突破检测
- **增强技术分析**: MACD金叉死叉、均线排列、RSI强度分析
- **综合评分系统**: 多维度信号强度评估和最终推荐
- **风险评估**: 止损位、目标位、建议仓位计算

### 前端组件完善待办 📋

#### 需要新增的展示模块：

1. **增强分析结果展示区域**
   ```vue
   <!-- 新增增强分析展示模块 -->
   <div class="result-section enhanced-analysis-section">
     <h4 class="section-title">增强分析结果</h4>
     <!-- 内容待实现 -->
   </div>
   ```

2. **道氏法则分析展示**
   - **123法则分析卡片**
     - 显示三个条件的满足状态
     - 反转概率百分比展示
     - 信号强度标签（强/中/弱）
   - **2B法则分析卡片**
     - 假突破信号检测
     - 条件满足状态展示
     - 交易信号推荐

3. **MACD信号分析可视化**
   - 金叉死叉信号时间点标注
   - 柱状线趋势方向指示
   - 背离信号警示展示

4. **综合评分可视化**
   - 圆形进度条展示总分
   - 各组件评分权重分布
   - 评分细项展示（MACD、趋势、法则等）

5. **最终建议展示**
   - 操作建议标签（BUY/SELL/HOLD）
   - 信心度百分比
   - 推荐理由列表
   - 风险因子警示

#### 字段映射关系：

| 后端字段 | 前端展示位置 | 展示方式 |
|---------|-------------|----------|
| `enhanced_analysis.rule_123_analysis` | 123法则卡片 | 条件状态 + 概率 |
| `enhanced_analysis.rule_2b_analysis` | 2B法则卡片 | 假突破检测 |
| `enhanced_analysis.macd_signals` | MACD信号区 | 金叉死叉可视化 |
| `enhanced_analysis.comprehensive_score` | 评分圆环 | 总分 + 组件分解 |
| `enhanced_analysis.final_recommendation` | 建议卡片 | 操作 + 理由 + 风险 |

#### 实现优先级：
1. **高优先级**: 最终建议展示（用户最关心）
2. **中优先级**: 道氏法则分析展示（核心功能）
3. **低优先级**: MACD信号可视化、综合评分（辅助功能）

### API接口说明
- **端点**: `GET /dow_theory/analyze/{stock_code}`
- **认证**: JWT Bearer Token
- **参数**: `start_date`, `end_date` (可选)
- **返回**: 包含 `enhanced_analysis` 字段的完整分析结果

## 🔄 更新日志

### v1.4.0 (当前版本) 🆕
- ✅ 道氏理论增强分析引擎完成
- ✅ 123法则和2B法则信号识别
- ✅ MACD金叉死叉和背离信号分析
- ✅ 多维度综合评分系统
- ✅ JSON序列化问题完全解决
- ✅ 增强分析API接口稳定运行
- 🔄 前端组件增强分析展示（待完成）

### v1.3.0
- ✅ 智能交易日历系统集成
- ✅ 基于Tushare API的真实交易日历
- ✅ 自动化增量更新调度器
- ✅ 交易日检测和进程冲突避免
- ✅ 多层容错机制和缓存优化
- ✅ macOS定时任务自动化支持
- ✅ 完善的定时任务管理工具

### v1.2.0
- ✅ 统一测试模块管理
- ✅ 完善的测试运行器
- ✅ 测试脚本导入路径优化
- ✅ 详细的测试文档

### v1.1.0
- ✅ 数据采集与分析完全分离
- ✅ 新增市场分析器
- ✅ 大盘、板块、龙虎榜分析功能

### v1.0.0
- ✅ 基础数据采集和分析框架
- ✅ MongoDB集群部署
- ✅ 股指期货、ETF、股票数据采集

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目采用 MIT 许可证。
