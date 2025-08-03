# 🚀 KK股票量化分析系统

一个专业的跨平台股票量化分析系统，集成了数据采集、技术分析、策略回测、模拟交易和桌面端应用的完整解决方案。基于现代化技术栈构建，专注于为量化投资者提供专业的分析工具和策略验证平台。

## 📁 项目结构

```
kk_Stock_Analysis/
├── kk_stock_backend/        # 🔧 后端服务 (Python + FastAPI)
│   ├── api/                 # API接口层
│   │   ├── routers/         # 路由模块 (20+ API模块)
│   │   ├── middleware/      # 中间件 (缓存、限流、认证)
│   │   ├── simulation/      # 模拟交易系统
│   │   └── main.py          # API服务入口
│   ├── analysis/            # 🧠 核心分析引擎
│   │   ├── dow_theory/      # 道氏理论分析引擎
│   │   └── relative_valuation/ # 相对估值分析
│   ├── backtrader_strategies/ # 📈 量化策略框架
│   │   ├── strategies/      # 策略实现 (4种核心策略)
│   │   ├── backtest/        # 回测引擎
│   │   └── data_feed/       # 数据源适配器
│   ├── qlib_quantitative/   # 🤖 Qlib深度学习框架
│   │   ├── strategies/      # ML策略 (Mario量化等)
│   │   ├── core/            # 核心引擎
│   │   └── scripts/         # 训练脚本
│   ├── tests/               # 🧪 统一测试框架
│   ├── docs/                # 📚 技术文档
│   └── redis/               # 🗄️ Redis缓存配置
└── kk_stock_desktop/        # 🖥️ 桌面端应用 (Electron + Vue3)
    ├── src/
    │   ├── views/           # 页面组件 (10+ 功能页面)
    │   ├── components/      # UI组件 (30+ 专业组件)
    │   ├── api/             # API客户端
    │   ├── stores/          # 状态管理 (Pinia)
    │   └── utils/           # 工具函数
    ├── electron/            # Electron主进程
    └── build/               # 构建配置
```

## ✨ 核心特性

### 🏗️ 系统架构
- **前后端分离**: FastAPI后端 + Electron桌面端
- **微服务设计**: 20+个API模块，功能解耦
- **双数据库架构**: MongoDB集群 + Redis缓存
- **容器化部署**: Docker + Docker Compose
- **智能缓存**: 多层缓存策略，性能优化

### 📊 数据分析引擎
- **道氏理论分析**: 多时间周期趋势分析、123法则、2B法则、增强技术分析
- **相对估值分析**: PE/PB估值模型、行业比较分析
- **技术指标分析**: MACD、RSI、布林带等30+技术指标
- **市场情绪分析**: 龙虎榜、资金流向、成交量分析
- **宏观经济分析**: CPI、货币供应量、利率等经济指标

### 🤖 量化策略框架
- **Backtrader集成**: 专业回测引擎，支持多种策略
- **Qlib深度学习**: Mario量化策略、多因子模型
- **策略库**: 4种核心策略（布林带、多趋势共振、小市值动量等）
- **性能分析**: 夏普比率、最大回撤、年化收益等指标
- **风险管理**: 止损止盈、仓位管理、风险控制

### 💼 模拟交易系统
- **实时模拟**: 基于真实行情的模拟交易
- **账户管理**: 多账户支持、资金管理
- **订单系统**: 限价单、市价单、条件单
- **绩效跟踪**: 实时盈亏、持仓分析
- **风险监控**: 实时风险指标监控

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
# 克隆项目
git clone <repository-url>
cd kk_Stock_Analysis

# 创建并激活conda环境
conda env create -f kk_stock_backend/environment.yml
conda activate kk_stock

# 设置环境变量
export TUSHARE_TOKEN=你的Tushare令牌
export MONGODB_URI=mongodb://localhost:27017
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

### 2. 后端服务启动
```bash
# 启动Redis缓存
cd kk_stock_backend/redis
./deploy_redis.sh

# 启动MongoDB（如果使用Docker）
docker-compose up -d mongodb

# 启动后端API服务
cd kk_stock_backend
python api/main.py
# 或使用脚本
./start_backend.sh
```

### 3. 前端桌面端启动
```bash
# 安装前端依赖
cd kk_stock_desktop
npm install

# 开发模式启动
npm run electron:dev

# 构建桌面应用
npm run electron:build:mac  # macOS
npm run electron:build:win  # Windows
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

## 📊 系统规模

### 数据覆盖
- **66个数据集合**: 涵盖股票、指数、期货、ETF、宏观等
- **20+个API模块**: 完整的数据采集和分析接口
- **4种核心策略**: 专业量化策略实现
- **30+个技术指标**: 全面的技术分析工具

### 支持品种
- **股票市场**: A股全市场、科创板、创业板
- **指数数据**: 上证指数、深证成指、创业板指等
- **期货市场**: 股指期货(IF/IH/IC/IM)、商品期货
- **ETF基金**: 主要ETF产品、行业ETF
- **宏观数据**: CPI、PPI、货币供应量、利率等
- **期权数据**: 股指期权、ETF期权

## 🎯 核心价值

### 🏆 竞争优势
- **专业级分析**: 道氏理论、相对估值等专业分析方法
- **多策略支持**: 传统技术分析 + 机器学习策略
- **跨平台部署**: 支持macOS、Windows、Linux
- **实时性能**: Redis缓存 + 异步处理，毫秒级响应
- **可扩展架构**: 微服务设计，易于功能扩展

### 🎨 用户体验
- **现代化UI**: 基于Element Plus的专业界面设计
- **交互式图表**: ECharts驱动的动态数据可视化
- **智能提示**: AI驱动的分析建议和风险提示
- **一键操作**: 简化的工作流程，提升使用效率
- **离线支持**: 桌面端应用，无需网络依赖

## 🔧 系统架构

### 数据流向
```
数据源(Tushare/AKShare) → API网关 → 缓存层(Redis) → 业务逻辑 → 数据库(MongoDB) → 分析引擎 → 前端展示
```

### 架构特点
- **微服务架构**: 20+个独立API模块，功能解耦
- **分层设计**: 数据层、业务层、表现层清晰分离
- **缓存策略**: 多级缓存，提升系统性能
- **异步处理**: 支持高并发数据处理
- **容错机制**: 完善的错误处理和恢复机制

## 📚 详细文档

- [数据分析模块说明](data_analysis/README.md)
- [测试模块说明](tests/README.md)
- [交易日历与增量更新使用说明](docs/交易日历与增量更新使用说明.md) 🆕
- [macOS定时任务设置说明](docs/macOS定时任务设置说明.md) 🆕
- [Tushare数据采集说明](docs/Tushare数据采集说明.md)
- [MongoDB集群部署指导](docs/macOS_MongoDB集群部署指导.md)
- [股指期货数据采集与分析使用说明](docs/股指期货数据采集与分析使用说明.md)

## 🛠️ 技术栈

### 后端技术栈
- **核心框架**: Python 3.11 + FastAPI + Uvicorn
- **数据库**: MongoDB 集群 + Redis 缓存
- **数据源**: Tushare Pro API + AKShare
- **量化框架**: Backtrader + Qlib + Pandas + NumPy
- **机器学习**: Scikit-learn + XGBoost + Transformers
- **异步处理**: AsyncIO + Motor + Celery
- **认证授权**: JWT + Passlib + BCrypt
- **API文档**: FastAPI自动生成 + Swagger UI

### 前端技术栈
- **桌面框架**: Electron 28.x + TypeScript
- **UI框架**: Vue 3.4 + Composition API
- **组件库**: Element Plus + Tailwind CSS
- **图表库**: ECharts + Vue-ECharts
- **状态管理**: Pinia
- **路由管理**: Vue Router 4
- **构建工具**: Vite + Electron Builder
- **开发工具**: Vue DevTools + TypeScript

### 开发运维
- **容器化**: Docker + Docker Compose
- **版本控制**: Git + GitHub
- **包管理**: Conda + NPM
- **代码质量**: ESLint + Prettier
- **测试框架**: 统一测试运行器
- **文档工具**: Markdown + 自动生成API文档

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

## 💡 最佳实践

### 🔧 部署建议
1. **生产环境**: 建议使用Docker容器化部署
2. **数据库配置**: MongoDB副本集 + Redis集群提升可靠性
3. **缓存策略**: 合理配置Redis缓存过期时间
4. **监控告警**: 配置系统监控和日志告警
5. **备份策略**: 定期备份数据库和配置文件

### 📈 使用建议
1. **数据更新**: 建议每日运行数据采集任务
2. **策略验证**: 使用回测功能验证策略有效性
3. **风险控制**: 设置合理的止损止盈参数
4. **性能监控**: 定期检查系统性能和缓存命中率
5. **版本更新**: 关注项目更新，及时升级新功能

### 🎯 适用场景
- **个人投资者**: 技术分析、策略验证、模拟交易
- **量化团队**: 策略开发、回测分析、风险管理
- **研究机构**: 市场分析、数据挖掘、学术研究
- **金融机构**: 投资决策支持、风险评估

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

## 🔄 版本历程

### v2.0.0 (当前版本) 🚀
**全面重构 - 专业量化分析平台**
- ✅ **桌面端应用**: Electron + Vue3 + TypeScript 专业桌面应用
- ✅ **微服务架构**: 20+个API模块，完整的后端服务体系
- ✅ **量化策略框架**: Backtrader + Qlib 双引擎支持
- ✅ **模拟交易系统**: 完整的模拟交易功能实现
- ✅ **智能缓存系统**: Redis多层缓存，性能大幅提升
- ✅ **道氏理论分析**: 专业的技术分析引擎
- ✅ **相对估值分析**: PE/PB估值模型实现
- ✅ **用户认证系统**: JWT + 多用户支持
- ✅ **API文档系统**: FastAPI自动生成完整API文档

### v1.5.0 
**机器学习集成**
- ✅ Qlib深度学习框架集成
- ✅ Mario量化策略实现
- ✅ 多因子模型支持
- ✅ 策略性能分析优化

### v1.4.0
**技术分析增强**
- ✅ 道氏理论增强分析引擎
- ✅ 123法则和2B法则信号识别
- ✅ MACD技术指标分析
- ✅ 多维度综合评分系统

### v1.3.0
**自动化系统**
- ✅ 智能交易日历系统
- ✅ 自动化数据更新调度
- ✅ macOS定时任务支持
- ✅ 多层容错机制

### v1.0.0 - v1.2.0
**基础框架建设**
- ✅ MongoDB数据库集群
- ✅ 基础数据采集框架
- ✅ 统一测试系统
- ✅ 核心分析模块

---

## 🚀 未来规划

### 📋 开发路线图
- **v2.1.0**: 缠论分析引擎完善
- **v2.2.0**: 更多机器学习策略集成
- **v2.3.0**: 实盘交易接口对接
- **v2.4.0**: 移动端应用开发
- **v2.5.0**: 云端部署和SaaS服务


## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. **Fork** 本项目
2. **创建** 功能分支 (`git checkout -b feature/AmazingFeature`)
3. **提交** 更改 (`git commit -m 'Add some AmazingFeature'`)
4. **推送** 到分支 (`git push origin feature/AmazingFeature`)
5. **创建** Pull Request

### 贡献类型
- 🐛 **Bug修复**: 发现并修复系统问题
- ✨ **新功能**: 添加新的分析功能或策略
- 📚 **文档**: 改进文档和使用说明
- 🎨 **UI/UX**: 优化用户界面和体验
- ⚡ **性能**: 提升系统性能和效率

## 📞 联系我们

- **项目主页**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **功能建议**: [GitHub Discussions]
- **技术交流**: 欢迎加入技术讨论群

## 📄 许可证

本项目采用 **MIT 许可证** - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目的支持：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Electron](https://www.electronjs.org/) - 跨平台桌面应用框架
- [Backtrader](https://www.backtrader.com/) - Python量化回测框架
- [Qlib](https://github.com/microsoft/qlib) - 微软量化投资平台
- [Tushare](https://tushare.pro/) - 金融数据接口

---

⭐ **如果这个项目对您有帮助，请给我们一个Star！** ⭐
