# 测试模块说明

本目录包含股票量化分析系统的所有测试脚本，统一管理项目的测试功能。

## 📁 目录结构

```
tests/
├── __init__.py                    # 测试模块初始化
├── run_tests.py                   # 统一测试运行脚本
├── README.md                      # 本说明文档
├── test_connection.py             # 系统连接测试
├── test_market_analysis.py        # 市场分析功能测试
├── test_etf_analysis.py           # ETF分析功能测试
├── test_etf_full_analysis.py      # ETF完整分析测试
├── test_futures_simple.py         # 期货基础分析测试
├── test_position_analysis.py      # 持仓分析测试
├── test_position_rank.py          # 持仓排名测试
└── test_contango_analysis.py      # 贴升水分析测试
```

## 🚀 快速开始

### 1. 统一测试运行器

使用 `run_tests.py` 可以方便地运行各种测试：

```bash
# 查看所有可用测试
python tests/run_tests.py --list

# 运行单个测试
python tests/run_tests.py --test connection

# 运行指定类别的测试
python tests/run_tests.py --category etf

# 运行所有测试
python tests/run_tests.py --all
```

### 2. 直接运行测试

也可以直接运行单个测试脚本：

```bash
# 进入tests目录
cd tests

# 运行特定测试
python test_connection.py
python test_market_analysis.py
```

## 📊 测试分类

### 🔗 连接测试
- **test_connection.py**: 系统连接测试
  - 网络连接检查
  - Tushare API连接验证
  - MongoDB数据库连接测试
  - 副本集状态检查

### 📈 市场分析测试
- **test_market_analysis.py**: 市场分析功能测试
  - 大盘综合分析测试
  - 板块成交量和资金流向分析
  - 个股龙虎榜分析测试
  - 市场综合报告生成

### 💰 ETF分析测试
- **test_etf_analysis.py**: ETF分析功能测试
  - ETF基本信息采集
  - ETF日线数据采集
  - ETF成交量分析
  - 热门ETF追踪
  - ETF成交量分析报告生成

- **test_etf_full_analysis.py**: ETF完整分析测试
  - 全面的ETF数据分析
  - ETF相关性分析
  - ETF表现评估

### 📊 期货分析测试
- **test_futures_simple.py**: 期货基础分析测试
  - 股指期货基本信息获取
  - 期货合约信息查询
  - 简单的期货数据分析

- **test_position_analysis.py**: 持仓分析测试
  - 股指期货持仓数据采集
  - 龙虎榜分析功能
  - 持仓变化分析
  - 市场情绪分析

- **test_position_rank.py**: 持仓排名测试
  - 期货持仓排名数据分析
  - 机构持仓统计
  - 持仓变化追踪

- **test_contango_analysis.py**: 贴升水分析测试
  - 期货合约价差分析
  - 贴升水趋势计算
  - 贴升水分析报告生成

## 🛠️ 测试环境要求

### 环境变量
确保设置了以下环境变量：
```bash
TUSHARE_TOKEN=你的Tushare令牌
```

### 数据库连接
- MongoDB服务正常运行
- 数据库连接配置正确
- 必要的数据集合已创建

### 网络连接
- 能够访问互联网
- 能够连接到Tushare API服务器
- DNS解析正常

## 📋 测试结果说明

### 成功标志
- ✅ 表示测试通过
- 📊 显示数据统计信息
- 🎉 表示功能测试完成

### 失败标志
- ❌ 表示测试失败
- ⚠️ 表示警告信息
- 💡 提供修复建议

### 数据验证
测试脚本会验证：
- 数据采集数量
- 数据质量检查
- 分析结果准确性
- 数据库存储状态

## 🔧 故障排除

### 常见问题

1. **导入错误**
   - 确保项目根目录在Python路径中
   - 检查相对导入路径是否正确

2. **数据库连接失败**
   - 检查MongoDB服务是否启动
   - 验证数据库连接配置
   - 确认网络连接正常

3. **API调用失败**
   - 检查Tushare Token是否有效
   - 验证网络连接和DNS解析
   - 确认API调用频率限制

4. **数据不足**
   - 确保基础数据已采集
   - 检查数据时间范围设置
   - 验证数据完整性

### 调试建议

1. **逐步测试**
   ```bash
   # 先测试连接
   python tests/run_tests.py --test connection
   
   # 再测试基础功能
   python tests/run_tests.py --category etf
   ```

2. **查看详细日志**
   - 测试脚本会输出详细的执行信息
   - 注意错误消息和异常堆栈
   - 查看数据库中的实际数据

3. **分类排查**
   - 按功能模块分别测试
   - 隔离问题范围
   - 逐步定位错误原因

## 📚 扩展测试

### 添加新测试
1. 在 `tests/` 目录创建新的测试文件
2. 使用 `test_` 前缀命名
3. 更新 `tests/__init__.py` 中的 `TEST_MODULES` 字典
4. 确保导入路径正确

### 测试最佳实践
- 每个测试应该独立运行
- 提供清晰的成功/失败指示
- 包含数据验证和结果检查
- 添加适当的错误处理和日志输出

---

## 💡 使用提示

1. **定期运行测试**：建议在每次代码更改后运行相关测试
2. **测试环境隔离**：使用独立的测试数据库避免影响生产数据
3. **性能监控**：关注测试执行时间，优化慢速测试
4. **结果分析**：仔细分析测试结果，及时发现潜在问题

通过统一的测试模块，您可以更好地验证系统功能，确保代码质量和数据准确性。 