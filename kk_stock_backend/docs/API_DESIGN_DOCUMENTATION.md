# 高并发量化分析API接口设计文档

## 🚀 项目概述

基于当前项目的39个数据集合，设计了一套支持高并发的完整API接口系统，涵盖股票、指数、期货、ETF等全方位数据查询和分析功能。

### 🏗️ 高并发架构特性

- **异步处理**: 基于FastAPI + Motor实现全异步数据库操作
- **Redis缓存**: 多层缓存策略，支持缓存预热和智能失效
- **智能限流**: 令牌桶+滑动窗口算法，支持用户分级限流
- **连接池优化**: MongoDB连接池优化，支持云端+本地双数据库
- **并行查询**: 支持批量并行查询，提升响应速度
- **性能监控**: 实时性能指标监控和慢查询检测

### 📊 数据覆盖范围

| 数据类别 | 集合数量 | 主要内容 |
|---------|---------|----------|
| 🏗️ 基础设施数据 | 10个 | 交易日历、股票基本信息、公司信息、ETF/期货基础信息 |
| 📅 交易日历数据 | 2个 | 股票/期货交易日历、节假日信息 |
| 📈 行情数据 | 9个 | 股票/指数/ETF日线、周线、月线K线数据 |
| 💰 财务数据 | 7个 | 三大报表、财务指标、业绩预告、财务审计 |
| 💸 资金流向数据 | 4个 | 个股、行业、大盘资金流向 |
| 🏦 融资融券数据 | 2个 | 融资融券汇总和明细 |
| 🐉 龙虎榜数据 | 2个 | 龙虎榜统计和机构交易 |
| 📊 其他数据 | 5个 | SHIBOR利率、期货数据等 |

## 📋 API接口总览

当前系统共包含 **27个路由模块**，提供 **200+个API接口**，覆盖以下功能模块：

| 模块 | 路由前缀 | 接口数量 | 主要功能 |
|------|----------|----------|----------|
| 用户管理 | `/user` | 25+ | 用户注册、登录、权限管理、股票池管理 |
| 市场数据 | `/market` | 15+ | 实时行情、市场概览、指数详情 |
| 股票数据 | `/stock` | 30+ | 股票基本信息、K线数据、技术指标 |
| 指数数据 | `/index` | 20+ | 指数基本信息、成分股、行业分类 |
| 财务数据 | `/financial` | 25+ | 财务报表、财务指标、业绩预告 |
| 期货数据 | `/futures` | 15+ | 期货基本信息、日线数据、持仓分析 |
| ETF数据 | `/etf` | 10+ | ETF基本信息、净值数据、成分股 |
| 期权数据 | `/options` | 8+ | 期权基本信息、日线数据、希腊字母 |
| 交易日历 | `/calendar` | 10+ | 交易日查询、节假日信息、统计分析 |
| 资金流向 | `/money_flow` | 12+ | 个股、行业、大盘资金流向分析 |
| 融资融券 | `/margin` | 8+ | 融资融券余额、明细数据 |
| 龙虎榜 | `/dragon-tiger` | 6+ | 龙虎榜统计、机构席位分析 |
| 涨跌停数据 | `/limit_data` | 5+ | 涨跌停统计、连板分析 |
| 宏观数据 | `/macro` | 5+ | SHIBOR利率、宏观经济指标 |
| 数据分析 | `/analytics` | 15+ | 技术分析、量价关系、趋势分析 |
| 市场情绪 | `/sentiment` | 10+ | 市场情绪指标、恐慌指数 |
| 投资策略 | `/strategy` | 20+ | 量化策略、回测分析、选股筛选 |
| 道氏理论分析 | `/dow-theory` | 5+ | 道氏理论技术分析 |
| 缠论分析 | `/chan-theory` | 5+ | 缠论技术分析 |
| 系统管理 | `/admin` | 15+ | 系统监控、数据库管理、缓存管理 |
| 系统监控 | `/system` | 8+ | 健康检查、性能指标、状态监控 |

## 🔗 API接口架构

### 核心路由模块

```
📁 api/
├── 🔧 core/                    # 核心基础设施
│   ├── cache.py               # Redis缓存管理器
│   ├── database.py            # 高并发数据库管理器
│   └── rate_limiter.py        # 多层限流中间件
├── 🛤️ routers/                 # API路由模块
│   ├── user.py               # 用户认证和管理
│   ├── stock_data.py         # 股票数据接口
│   ├── index_data.py         # 指数数据接口
│   ├── financial_data.py     # 财务数据接口
│   ├── trading_calendar.py   # 交易日历接口
│   ├── market_flow.py        # 资金流向接口
│   ├── margin_data.py        # 融资融券接口
│   ├── dragon_tiger.py       # 龙虎榜接口
│   ├── analytics.py          # 数据分析接口
│   ├── strategy.py           # 投资策略接口
│   ├── content.py            # 智能内容生成
│   ├── admin.py              # 系统管理接口
│   └── system.py             # 系统监控接口
└── 📖 main.py                  # API主入口
```

## 📋 完整接口清单

### 1. 用户管理模块 (`/user`)

#### 1.1 用户认证接口

**POST `/user/register` - 用户注册**

请求参数：
```json
{
  "username": "testuser",
  "password": "password123",
  "email": "test@example.com"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_info": {
      "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
      "username": "testuser",
      "email": "test@example.com",
      "roles": ["user"],
      "created_at": "2024-12-01T10:00:00Z",
      "is_active": true
    }
  },
  "timestamp": "2024-12-01T10:00:00Z"
}
```

**POST `/user/login` - 用户登录**

请求参数：
```json
{
  "username": "testuser",
  "password": "password123"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user_info": {
      "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
      "username": "testuser",
      "email": "test@example.com",
      "roles": ["user"],
      "last_login": "2024-12-01T10:00:00Z",
      "is_active": true,
      "avatar_url": "https://example.com/avatar/default.png"
    }
  },
  "timestamp": "2024-12-01T10:00:00Z"
}
```

**POST `/user/login/wechat` - 微信登录**

请求参数：
```json
{
  "code": "wx_auth_code_123456",
  "state": "random_state_string"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "微信登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_info": {
      "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
      "username": "微信用户_abc123",
      "nickname": "张三",
      "avatar_url": "https://wx.qlogo.cn/mmopen/...",
      "openid": "oABC123DEF456GHI789JKL",
      "unionid": "uXYZ987WVU654TSR321QPN",
      "roles": ["user"],
      "is_active": true,
      "wechat_bound": true
    }
  },
  "timestamp": "2024-12-01T10:00:00Z"
}
```

**GET `/user/user-info` - 获取用户信息**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "email": "test@example.com",
    "nickname": "测试用户",
    "avatar_url": "https://example.com/avatar/user123.png",
    "roles": ["user", "analyst"],
    "permissions": ["read:stock", "read:financial", "write:stock_pool"],
    "created_at": "2024-11-01T10:00:00Z",
    "last_login": "2024-12-01T10:00:00Z",
    "is_active": true,
    "subscription": {
      "plan": "premium",
      "expires_at": "2025-01-01T00:00:00Z",
      "features": ["unlimited_api", "advanced_analysis"]
    }
  },
  "timestamp": "2024-12-01T10:00:00Z"
}
```

**GET `/user/info` - 获取用户详细信息**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "email": "test@example.com",
    "nickname": "测试用户",
    "real_name": "张三",
    "phone": "13800138000",
    "avatar_url": "https://example.com/avatar/user123.png",
    "gender": "male",
    "birthday": "1990-01-01",
    "location": "北京市朝阳区",
    "bio": "量化投资爱好者",
    "roles": ["user", "analyst"],
    "permissions": ["read:stock", "read:financial", "write:stock_pool"],
    "created_at": "2024-11-01T10:00:00Z",
    "updated_at": "2024-12-01T09:00:00Z",
    "last_login": "2024-12-01T10:00:00Z",
    "login_count": 156,
    "is_active": true,
    "is_verified": true,
    "subscription": {
      "plan": "premium",
      "expires_at": "2025-01-01T00:00:00Z",
      "features": ["unlimited_api", "advanced_analysis", "real_time_data"],
      "api_quota": {
        "daily_limit": 10000,
        "used_today": 1250,
        "remaining": 8750
      }
    },
    "preferences": {
      "language": "zh-CN",
      "timezone": "Asia/Shanghai",
      "theme": "dark",
      "notifications": {
        "email": true,
        "sms": false,
        "push": true
      }
    },
    "statistics": {
      "stock_pools_count": 5,
      "favorite_stocks_count": 23,
      "analysis_count": 89,
      "total_api_calls": 15678
    }
  },
  "timestamp": "2024-12-01T10:00:00Z"
}
```

#### 1.2 密码管理接口

**POST `/user/password/reset` - 请求密码重置**

请求参数：
```json
{
  "email": "test@example.com"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "重置邮件已发送",
  "data": {
    "email": "test@example.com",
    "reset_token_expires": "2024-12-01T11:00:00Z",
    "message": "请检查您的邮箱，重置链接将在1小时内有效"
  },
  "timestamp": "2024-12-01T10:00:00Z"
}
```

**POST `/user/password/reset/confirm` - 确认密码重置**

请求参数：
```json
{
  "token": "reset_token_abc123def456",
  "new_password": "newpassword123"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "密码重置成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "reset_time": "2024-12-01T10:30:00Z",
    "message": "密码已成功重置，请使用新密码登录"
  },
  "timestamp": "2024-12-01T10:30:00Z"
}
```

**POST `/user/password/change` - 修改密码**

请求参数：
```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "change_time": "2024-12-01T10:45:00Z",
    "message": "密码已成功修改，下次登录请使用新密码"
  },
  "timestamp": "2024-12-01T10:45:00Z"
}
```

#### 1.3 管理员接口

**POST `/user/admin/add_user` - 管理员添加用户**

请求参数：
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "newuser@example.com",
  "roles": ["user", "analyst"],
  "nickname": "新用户",
  "is_active": true
}
```

返回示例：
```json
{
  "code": 200,
  "message": "用户创建成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j2",
    "username": "newuser",
    "email": "newuser@example.com",
    "nickname": "新用户",
    "roles": ["user", "analyst"],
    "created_at": "2024-12-01T11:00:00Z",
    "created_by": "admin",
    "is_active": true,
    "initial_password_sent": true
  },
  "timestamp": "2024-12-01T11:00:00Z"
}
```

**GET `/user/admin/users` - 获取所有用户**

请求参数：`?page=1&size=20&status=active&role=user`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
        "username": "testuser1",
        "email": "test1@example.com",
        "nickname": "测试用户1",
        "avatar_url": "https://example.com/avatar/user1.png",
        "roles": ["user"],
        "is_active": true,
        "created_at": "2024-11-01T10:00:00Z",
        "last_login": "2024-12-01T09:30:00Z",
        "login_count": 156,
        "subscription": {
          "plan": "premium",
          "expires_at": "2025-01-01T00:00:00Z"
        }
      },
      {
        "user_id": "64f1a2b3c4d5e6f7g8h9i0j2",
        "username": "testuser2",
        "email": "test2@example.com",
        "nickname": "测试用户2",
        "avatar_url": "https://example.com/avatar/user2.png",
        "roles": ["user", "analyst"],
        "is_active": true,
        "created_at": "2024-11-15T14:20:00Z",
        "last_login": "2024-12-01T08:45:00Z",
        "login_count": 89,
        "subscription": {
          "plan": "basic",
          "expires_at": "2024-12-31T23:59:59Z"
        }
      }
    ],
    "pagination": {
      "total": 1250,
      "page": 1,
      "size": 20,
      "pages": 63,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "2024-12-01T11:00:00Z"
}
```

**GET `/user/admin/users/{user_id}` - 获取指定用户信息**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "email": "test@example.com",
    "nickname": "测试用户",
    "real_name": "张三",
    "phone": "13800138000",
    "avatar_url": "https://example.com/avatar/user123.png",
    "roles": ["user", "analyst"],
    "permissions": ["read:stock", "read:financial", "write:stock_pool"],
    "is_active": true,
    "is_verified": true,
    "created_at": "2024-11-01T10:00:00Z",
    "updated_at": "2024-12-01T09:00:00Z",
    "last_login": "2024-12-01T10:00:00Z",
    "login_count": 156,
    "subscription": {
      "plan": "premium",
      "expires_at": "2025-01-01T00:00:00Z",
      "api_quota": {
        "daily_limit": 10000,
        "used_today": 1250,
        "remaining": 8750
      }
    },
    "activity_stats": {
      "total_api_calls": 15678,
      "stock_pools_count": 5,
      "favorite_stocks_count": 23,
      "analysis_count": 89
    }
  },
  "timestamp": "2024-12-01T11:00:00Z"
}
```

**PUT `/user/admin/users/{user_id}/status` - 更新用户状态**

请求参数：
```json
{
  "status": "inactive",
  "reason": "违规操作"
}
```

返回示例：
```json
{
  "code": 200,
  "message": "用户状态更新成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "old_status": "active",
    "new_status": "inactive",
    "reason": "违规操作",
    "updated_by": "admin",
    "updated_at": "2024-12-01T11:15:00Z"
  },
  "timestamp": "2024-12-01T11:15:00Z"
}
```

**PUT `/user/admin/users/{user_id}/roles` - 更新用户角色**

请求参数：
```json
{
  "roles": ["user", "analyst", "premium"]
}
```

返回示例：
```json
{
  "code": 200,
  "message": "用户角色更新成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "old_roles": ["user"],
    "new_roles": ["user", "analyst", "premium"],
    "updated_by": "admin",
    "updated_at": "2024-12-01T11:20:00Z",
    "effective_permissions": [
      "read:stock",
      "read:financial", 
      "write:stock_pool",
      "read:advanced_analysis",
      "write:analysis"
    ]
  },
  "timestamp": "2024-12-01T11:20:00Z"
}
```

**DELETE `/user/admin/users/{user_id}` - 删除用户**

返回示例：
```json
{
  "code": 200,
  "message": "用户删除成功",
  "data": {
    "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "username": "testuser",
    "deleted_by": "admin",
    "deleted_at": "2024-12-01T11:25:00Z",
    "backup_created": true,
    "data_retention_days": 30
  },
  "timestamp": "2024-12-01T11:25:00Z"
}
```

#### 1.4 用户股票池接口

**GET `/user/stock-pools` - 获取用户股票池列表**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "pool_id": "64f1a2b3c4d5e6f7g8h9i0k1",
        "name": "我的自选股",
        "description": "日常关注的优质股票",
        "stock_count": 15,
        "created_at": "2024-11-01T10:00:00Z",
        "updated_at": "2024-12-01T09:30:00Z",
        "is_default": true,
        "is_public": false,
        "tags": ["自选", "长期持有"],
        "performance": {
          "total_return": 12.5,
          "daily_change": 2.3,
          "best_performer": "000001.SZ",
          "worst_performer": "000002.SZ"
        }
      },
      {
        "pool_id": "64f1a2b3c4d5e6f7g8h9i0k2",
        "name": "科技股池",
        "description": "科技行业相关股票",
        "stock_count": 8,
        "created_at": "2024-11-15T14:20:00Z",
        "updated_at": "2024-11-30T16:45:00Z",
        "is_default": false,
        "is_public": true,
        "tags": ["科技", "成长"],
        "performance": {
          "total_return": -3.2,
          "daily_change": -1.1,
          "best_performer": "300750.SZ",
          "worst_performer": "300001.SZ"
        }
      }
    ],
    "total": 5,
    "summary": {
      "total_pools": 5,
      "total_stocks": 45,
      "avg_pool_size": 9,
      "public_pools": 2,
      "private_pools": 3
    }
  },
  "timestamp": "2024-12-01T11:30:00Z"
}
```

**POST `/user/stock-pools` - 创建股票池**

请求参数：
```json
{
  "name": "新股票池",
  "description": "这是一个新的股票池",
  "stocks": ["000001.SZ", "000002.SZ", "300750.SZ"],
  "is_public": false,
  "tags": ["新建", "测试"]
}
```

返回示例：
```json
{
  "code": 200,
  "message": "股票池创建成功",
  "data": {
    "pool_id": "64f1a2b3c4d5e6f7g8h9i0k3",
    "name": "新股票池",
    "description": "这是一个新的股票池",
    "stock_count": 3,
    "stocks": [
      {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "added_at": "2024-12-01T11:35:00Z"
      },
      {
        "ts_code": "000002.SZ", 
        "name": "万科A",
        "added_at": "2024-12-01T11:35:00Z"
      },
      {
        "ts_code": "300750.SZ",
        "name": "宁德时代",
        "added_at": "2024-12-01T11:35:00Z"
      }
    ],
    "created_at": "2024-12-01T11:35:00Z",
    "is_default": false,
    "is_public": false,
    "tags": ["新建", "测试"]
  },
  "timestamp": "2024-12-01T11:35:00Z"
}
```

**GET `/user/stock-pools/{pool_id}` - 获取股票池详情**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "pool_id": "64f1a2b3c4d5e6f7g8h9i0k1",
    "name": "我的自选股",
    "description": "日常关注的优质股票",
    "stock_count": 15,
    "created_at": "2024-11-01T10:00:00Z",
    "updated_at": "2024-12-01T09:30:00Z",
    "is_default": true,
    "is_public": false,
    "tags": ["自选", "长期持有"],
    "stocks": [
      {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "industry": "银行",
        "market": "主板",
        "added_at": "2024-11-01T10:00:00Z",
        "current_price": 10.56,
        "change_pct": 2.3,
        "volume": 1250000,
        "market_cap": 204567890000,
        "pe_ratio": 5.2,
        "pb_ratio": 0.8
      },
      {
        "ts_code": "000002.SZ",
        "name": "万科A",
        "industry": "房地产",
        "market": "主板",
        "added_at": "2024-11-05T14:20:00Z",
        "current_price": 8.95,
        "change_pct": -1.2,
        "volume": 980000,
        "market_cap": 98765432100,
        "pe_ratio": 8.9,
        "pb_ratio": 0.9
      }
    ],
    "performance": {
      "total_return": 12.5,
      "daily_change": 2.3,
      "weekly_change": 5.8,
      "monthly_change": 8.2,
      "best_performer": {
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "return": 15.6
      },
      "worst_performer": {
        "ts_code": "000002.SZ",
        "name": "万科A",
        "return": -2.1
      }
    },
    "statistics": {
      "avg_pe": 7.2,
      "avg_pb": 1.1,
      "total_market_cap": 1567890123456,
      "sector_distribution": {
        "银行": 3,
        "房地产": 2,
        "科技": 5,
        "制造业": 3,
        "其他": 2
      }
    }
  },
  "timestamp": "2024-12-01T11:40:00Z"
}
```

**PUT `/user/stock-pools/{pool_id}` - 更新股票池**

请求参数：
```json
{
  "name": "更新后的股票池名称",
  "description": "更新后的描述",
  "tags": ["更新", "优化"],
  "is_public": true
}
```

返回示例：
```json
{
  "code": 200,
  "message": "股票池更新成功",
  "data": {
    "pool_id": "64f1a2b3c4d5e6f7g8h9i0k1",
    "name": "更新后的股票池名称",
    "description": "更新后的描述",
    "stock_count": 15,
    "updated_at": "2024-12-01T11:45:00Z",
    "is_public": true,
    "tags": ["更新", "优化"],
    "changes": {
      "name": {
        "old": "我的自选股",
        "new": "更新后的股票池名称"
      },
      "description": {
        "old": "日常关注的优质股票",
        "new": "更新后的描述"
      },
      "is_public": {
        "old": false,
        "new": true
      }
    }
  },
  "timestamp": "2024-12-01T11:45:00Z"
}
```

**DELETE `/user/stock-pools/{pool_id}` - 删除股票池**

返回示例：
```json
{
  "code": 200,
  "message": "股票池删除成功",
  "data": {
    "pool_id": "64f1a2b3c4d5e6f7g8h9i0k1",
    "name": "我的自选股",
    "deleted_at": "2024-12-01T11:50:00Z",
    "stock_count": 15,
    "backup_created": true,
    "recovery_deadline": "2024-12-31T23:59:59Z"
  },
  "timestamp": "2024-12-01T11:50:00Z"
}
```

### 2. 市场数据模块 (`/market`)

**GET `/market/quote` - 获取实时行情**

请求参数：`?symbols=000001.SZ,000002.SZ&fields=ts_code,name,close,change,pct_chg,volume`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "quotes": [
      {
        "ts_code": "000001.SZ",
        "symbol": "000001",
        "name": "平安银行",
        "market": "深交所",
        "current_price": 10.56,
        "pre_close": 10.32,
        "open": 10.35,
        "high": 10.68,
        "low": 10.28,
        "close": 10.56,
        "change": 0.24,
        "pct_chg": 2.33,
        "volume": 125000000,
        "amount": 1320000000.0,
        "turnover_rate": 0.61,
        "pe_ratio": 5.23,
        "pb_ratio": 0.82,
        "market_cap": 204567890000,
        "circ_mv": 198765432100,
        "timestamp": "2024-12-01T15:00:00Z",
        "status": "trading"
      },
      {
        "ts_code": "000002.SZ",
        "symbol": "000002", 
        "name": "万科A",
        "market": "深交所",
        "current_price": 8.95,
        "pre_close": 9.06,
        "open": 9.02,
        "high": 9.08,
        "low": 8.89,
        "close": 8.95,
        "change": -0.11,
        "pct_chg": -1.21,
        "volume": 98000000,
        "amount": 876543210.0,
        "turnover_rate": 0.89,
        "pe_ratio": 8.92,
        "pb_ratio": 0.95,
        "market_cap": 98765432100,
        "circ_mv": 95432109876,
        "timestamp": "2024-12-01T15:00:00Z",
        "status": "trading"
      }
    ],
    "update_time": "2024-12-01T15:00:00Z",
    "market_status": "open"
  },
  "timestamp": "2024-12-01T15:00:00Z"
}
```

**GET `/market/overview` - 市场概览**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "market_summary": {
      "trade_date": "20241201",
      "total_stocks": 5234,
      "trading_stocks": 5198,
      "suspended_stocks": 36,
      "up_stocks": 2856,
      "down_stocks": 1987,
      "flat_stocks": 355,
      "limit_up": 89,
      "limit_down": 12,
      "new_high": 156,
      "new_low": 78
    },
    "indices": {
      "sh_composite": {
        "ts_code": "000001.SH",
        "name": "上证指数",
        "close": 3245.67,
        "change": 28.45,
        "pct_chg": 0.88,
        "volume": 2567890123,
        "amount": 345678901234.0
      },
      "sz_component": {
        "ts_code": "399001.SZ",
        "name": "深证成指",
        "close": 10567.89,
        "change": -45.23,
        "pct_chg": -0.43,
        "volume": 1876543210,
        "amount": 234567890123.0
      },
      "cyb_composite": {
        "ts_code": "399006.SZ",
        "name": "创业板指",
        "close": 2134.56,
        "change": 12.34,
        "pct_chg": 0.58,
        "volume": 987654321,
        "amount": 123456789012.0
      }
    },
    "sectors": {
      "top_gainers": [
        {
          "sector": "新能源汽车",
          "pct_chg": 3.45,
          "stocks_count": 156,
          "up_count": 128,
          "down_count": 28
        },
        {
          "sector": "人工智能",
          "pct_chg": 2.89,
          "stocks_count": 89,
          "up_count": 67,
          "down_count": 22
        }
      ],
      "top_losers": [
        {
          "sector": "房地产",
          "pct_chg": -2.34,
          "stocks_count": 234,
          "up_count": 45,
          "down_count": 189
        },
        {
          "sector": "传统能源",
          "pct_chg": -1.78,
          "stocks_count": 123,
          "up_count": 34,
          "down_count": 89
        }
      ]
    },
    "money_flow": {
      "total_amount": 567890123456.0,
      "net_inflow": 12345678901.0,
      "main_inflow": 8765432109.0,
      "retail_inflow": 3580246792.0,
      "north_money": {
        "net_inflow": 2345678901.0,
        "sh_inflow": 1234567890.0,
        "sz_inflow": 1111111011.0
      }
    },
    "market_sentiment": {
      "fear_greed_index": 65,
      "sentiment": "贪婪",
      "vix": 18.45,
      "put_call_ratio": 0.78
    },
    "update_time": "2024-12-01T15:00:00Z"
  },
  "timestamp": "2024-12-01T15:00:00Z"
}
```

**GET `/market/indices` - 主要指数**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "major_indices": [
      {
        "ts_code": "000001.SH",
        "name": "上证指数",
        "close": 3245.67,
        "pre_close": 3217.22,
        "open": 3220.15,
        "high": 3256.89,
        "low": 3215.34,
        "change": 28.45,
        "pct_chg": 0.88,
        "volume": 2567890123,
        "amount": 345678901234.0,
        "pe": 13.45,
        "pb": 1.23,
        "dividend_yield": 2.34
      },
      {
        "ts_code": "399001.SZ",
        "name": "深证成指",
        "close": 10567.89,
        "pre_close": 10613.12,
        "open": 10598.45,
        "high": 10625.67,
        "low": 10542.33,
        "change": -45.23,
        "pct_chg": -0.43,
        "volume": 1876543210,
        "amount": 234567890123.0,
        "pe": 18.67,
        "pb": 1.89,
        "dividend_yield": 1.78
      },
      {
        "ts_code": "399006.SZ",
        "name": "创业板指",
        "close": 2134.56,
        "pre_close": 2122.22,
        "open": 2125.67,
        "high": 2145.89,
        "low": 2118.45,
        "change": 12.34,
        "pct_chg": 0.58,
        "volume": 987654321,
        "amount": 123456789012.0,
        "pe": 35.67,
        "pb": 3.45,
        "dividend_yield": 0.89
      }
    ],
    "sector_indices": [
      {
        "ts_code": "000300.SH",
        "name": "沪深300",
        "close": 3876.54,
        "change": 15.67,
        "pct_chg": 0.41,
        "volume": 1567890123,
        "amount": 198765432109.0
      },
      {
        "ts_code": "000905.SH",
        "name": "中证500",
        "close": 5432.10,
        "change": -8.90,
        "pct_chg": -0.16,
        "volume": 876543210,
        "amount": 98765432101.0
      }
    ],
    "update_time": "2024-12-01T15:00:00Z"
  },
  "timestamp": "2024-12-01T15:00:00Z"
}
```

**GET `/market/sectors` - 行业板块数据**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "sectors": [
      {
        "sector_code": "BK0001",
        "sector_name": "银行",
        "stock_count": 42,
        "avg_price": 6.78,
        "total_market_cap": 1234567890123.0,
        "change": 0.45,
        "pct_chg": 1.23,
        "volume": 567890123,
        "amount": 38765432109.0,
        "up_count": 28,
        "down_count": 14,
        "flat_count": 0,
        "leading_stocks": [
          {
            "ts_code": "000001.SZ",
            "name": "平安银行",
            "pct_chg": 2.33
          },
          {
            "ts_code": "600036.SH",
            "name": "招商银行",
            "pct_chg": 1.89
          }
        ]
      },
      {
        "sector_code": "BK0002",
        "sector_name": "房地产",
        "stock_count": 156,
        "avg_price": 8.95,
        "total_market_cap": 987654321098.0,
        "change": -0.23,
        "pct_chg": -2.34,
        "volume": 234567890,
        "amount": 20987654321.0,
        "up_count": 23,
        "down_count": 133,
        "flat_count": 0,
        "leading_stocks": [
          {
            "ts_code": "000002.SZ",
            "name": "万科A",
            "pct_chg": -1.21
          },
          {
            "ts_code": "000001.SZ",
            "name": "保利发展",
            "pct_chg": -2.45
          }
        ]
      },
      {
        "sector_code": "BK0003",
        "sector_name": "新能源汽车",
        "stock_count": 89,
        "avg_price": 45.67,
        "total_market_cap": 2345678901234.0,
        "change": 1.56,
        "pct_chg": 3.45,
        "volume": 345678901,
        "amount": 15789012345.0,
        "up_count": 67,
        "down_count": 22,
        "flat_count": 0,
        "leading_stocks": [
          {
            "ts_code": "300750.SZ",
            "name": "宁德时代",
            "pct_chg": 4.56
          },
          {
            "ts_code": "002594.SZ",
            "name": "比亚迪",
            "pct_chg": 3.78
          }
        ]
      }
    ],
    "summary": {
      "total_sectors": 28,
      "up_sectors": 16,
      "down_sectors": 12,
      "strongest_sector": {
        "name": "新能源汽车",
        "pct_chg": 3.45
      },
      "weakest_sector": {
        "name": "房地产",
        "pct_chg": -2.34
      }
    },
    "update_time": "2024-12-01T15:00:00Z"
  },
  "timestamp": "2024-12-01T15:00:00Z"
}
```

### 3. 股票数据模块 (`/stock`)

#### 3.1 基础数据接口

**GET `/stock/basic/search` - 股票搜索**

请求参数：`?keyword=平安&limit=10`

返回示例：
```json
{
  "code": 200,
  "message": "搜索成功",
  "data": {
    "results": [
      {
        "ts_code": "000001.SZ",
        "symbol": "000001",
        "name": "平安银行",
        "area": "深圳",
        "industry": "银行",
        "market": "主板",
        "list_date": "19910403",
        "is_hs": "H",
        "current_price": 10.56,
        "market_cap": 204567890000,
        "pe_ratio": 5.23,
        "pb_ratio": 0.82,
        "match_type": "name"
      },
      {
        "ts_code": "601318.SH",
        "symbol": "601318",
        "name": "中国平安",
        "area": "深圳",
        "industry": "保险",
        "market": "主板",
        "list_date": "20070301",
        "is_hs": "H",
        "current_price": 45.67,
        "market_cap": 834567890123,
        "pe_ratio": 8.92,
        "pb_ratio": 1.23,
        "match_type": "name"
      }
    ],
    "total": 2,
    "keyword": "平安",
    "search_time": "2024-12-01T15:30:00Z"
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/basic/info` - 股票基本信息**

请求参数：`?ts_code=000001.SZ`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "basic_info": {
      "ts_code": "000001.SZ",
      "symbol": "000001",
      "name": "平安银行",
      "fullname": "平安银行股份有限公司",
      "enname": "Ping An Bank Co., Ltd.",
      "area": "深圳",
      "industry": "银行",
      "market": "主板",
      "exchange": "SZSE",
      "curr_type": "CNY",
      "list_status": "L",
      "list_date": "19910403",
      "delist_date": null,
      "is_hs": "H"
    },
    "company_info": {
      "chairman": "谢永林",
      "manager": "胡跃飞",
      "secretary": "陈蓉",
      "reg_capital": 19405918198.0,
      "setup_date": "19871212",
      "province": "广东省",
      "city": "深圳市",
      "introduction": "平安银行股份有限公司是一家总部设在深圳的全国性股份制商业银行...",
      "website": "http://bank.pingan.com",
      "email": "ir@pingan.com.cn",
      "office": "深圳市罗湖区深南东路5047号",
      "employees": 58000,
      "main_business": "吸收公众存款；发放短期、中期和长期贷款...",
      "business_scope": "吸收公众存款；发放短期、中期和长期贷款..."
    },
    "current_status": {
      "current_price": 10.56,
      "pre_close": 10.32,
      "change": 0.24,
      "pct_chg": 2.33,
      "volume": 125000000,
      "amount": 1320000000.0,
      "market_cap": 204567890000,
      "circ_mv": 198765432100,
      "pe_ratio": 5.23,
      "pb_ratio": 0.82,
      "ps_ratio": 0.95,
      "pcf_ratio": 3.45,
      "turnover_rate": 0.61,
      "volume_ratio": 1.23,
      "52w_high": 12.89,
      "52w_low": 8.45,
      "avg_price_5d": 10.23,
      "avg_price_20d": 9.87,
      "avg_price_60d": 9.56
    },
    "update_time": "2024-12-01T15:30:00Z"
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/basic/stats` - 股票统计信息**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "market_stats": {
      "total_stocks": 5234,
      "trading_stocks": 5198,
      "suspended_stocks": 36,
      "st_stocks": 89,
      "new_stocks": 12
    },
    "price_distribution": {
      "under_5": 456,
      "5_to_10": 1234,
      "10_to_20": 1567,
      "20_to_50": 1345,
      "50_to_100": 456,
      "over_100": 176
    },
    "market_cap_distribution": {
      "under_50b": 2345,
      "50b_to_100b": 1234,
      "100b_to_500b": 1123,
      "500b_to_1000b": 345,
      "over_1000b": 187
    },
    "pe_distribution": {
      "negative": 234,
      "0_to_20": 1567,
      "20_to_50": 2345,
      "50_to_100": 789,
      "over_100": 299
    },
    "industry_stats": [
      {
        "industry": "银行",
        "count": 42,
        "avg_pe": 5.67,
        "avg_pb": 0.89,
        "avg_market_cap": 234567890123
      },
      {
        "industry": "房地产",
        "count": 156,
        "avg_pe": 12.34,
        "avg_pb": 1.23,
        "avg_market_cap": 98765432109
      }
    ],
    "update_time": "2024-12-01T15:30:00Z"
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/share/float` - 流通股本信息**

请求参数：`?ts_code=000001.SZ&start_date=20240101&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "ts_code": "000001.SZ",
        "ann_date": "20241130",
        "end_date": "20241130",
        "total_share": 19405918198.0,
        "float_share": 19405918198.0,
        "free_share": 19405918198.0,
        "a_share_total": 19405918198.0,
        "b_share_total": 0.0,
        "h_share_total": 0.0,
        "limit_shares": 0.0,
        "share_type": "普通股"
      },
      {
        "ts_code": "000001.SZ",
        "ann_date": "20240630",
        "end_date": "20240630",
        "total_share": 19405918198.0,
        "float_share": 19405918198.0,
        "free_share": 19405918198.0,
        "a_share_total": 19405918198.0,
        "b_share_total": 0.0,
        "h_share_total": 0.0,
        "limit_shares": 0.0,
        "share_type": "普通股"
      }
    ],
    "summary": {
      "current_total_share": 19405918198.0,
      "current_float_share": 19405918198.0,
      "float_ratio": 100.0,
      "share_changes": 0,
      "last_change_date": null
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

#### 3.2 K线数据接口

**GET `/stock/daily/{ts_code}` - 日线数据**

请求参数：`/stock/daily/000001.SZ?start_date=20241101&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "period": "daily",
    "items": [
      {
        "trade_date": "20241201",
        "open": 10.35,
        "high": 10.68,
        "low": 10.28,
        "close": 10.56,
        "pre_close": 10.32,
        "change": 0.24,
        "pct_chg": 2.33,
        "vol": 125000000,
        "amount": 1320000000.0,
        "turnover_rate": 0.61,
        "volume_ratio": 1.23,
        "pe": 5.23,
        "pb": 0.82
      },
      {
        "trade_date": "20241130",
        "open": 10.28,
        "high": 10.45,
        "low": 10.15,
        "close": 10.32,
        "pre_close": 10.25,
        "change": 0.07,
        "pct_chg": 0.68,
        "vol": 98000000,
        "amount": 1010000000.0,
        "turnover_rate": 0.51,
        "volume_ratio": 0.89,
        "pe": 5.11,
        "pb": 0.81
      },
      {
        "trade_date": "20241129",
        "open": 10.20,
        "high": 10.35,
        "low": 10.12,
        "close": 10.25,
        "pre_close": 10.18,
        "change": 0.07,
        "pct_chg": 0.69,
        "vol": 87000000,
        "amount": 890000000.0,
        "turnover_rate": 0.45,
        "volume_ratio": 0.76,
        "pe": 5.08,
        "pb": 0.80
      }
    ],
    "statistics": {
      "total_records": 22,
      "period_return": 3.45,
      "max_price": 10.68,
      "min_price": 9.87,
      "avg_volume": 95000000,
      "avg_amount": 975000000.0,
      "volatility": 2.34
    },
    "technical_indicators": {
      "ma5": 10.23,
      "ma10": 10.12,
      "ma20": 9.98,
      "ma60": 9.76,
      "ema12": 10.34,
      "ema26": 10.15,
      "macd": 0.12,
      "rsi": 65.4,
      "kdj_k": 78.9,
      "kdj_d": 72.3,
      "kdj_j": 92.1
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/weekly/{ts_code}` - 周线数据**

请求参数：`/stock/weekly/000001.SZ?start_date=20241001&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "period": "weekly",
    "items": [
      {
        "trade_date": "20241201",
        "open": 10.15,
        "high": 10.68,
        "low": 10.05,
        "close": 10.56,
        "pre_close": 10.12,
        "change": 0.44,
        "pct_chg": 4.35,
        "vol": 567000000,
        "amount": 5890000000.0,
        "turnover_rate": 2.92
      },
      {
        "trade_date": "20241124",
        "open": 9.98,
        "high": 10.25,
        "low": 9.87,
        "close": 10.12,
        "pre_close": 9.95,
        "change": 0.17,
        "pct_chg": 1.71,
        "vol": 456000000,
        "amount": 4620000000.0,
        "turnover_rate": 2.35
      }
    ],
    "statistics": {
      "total_records": 9,
      "period_return": 8.76,
      "max_price": 10.68,
      "min_price": 9.45,
      "avg_weekly_volume": 478000000,
      "avg_weekly_amount": 4850000000.0
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/monthly/{ts_code}` - 月线数据**

请求参数：`/stock/monthly/000001.SZ?start_date=20240101&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "period": "monthly",
    "items": [
      {
        "trade_date": "20241130",
        "open": 9.87,
        "high": 10.68,
        "low": 9.45,
        "close": 10.56,
        "pre_close": 9.78,
        "change": 0.78,
        "pct_chg": 7.98,
        "vol": 2340000000,
        "amount": 23890000000.0,
        "turnover_rate": 12.06
      },
      {
        "trade_date": "20241031",
        "open": 9.56,
        "high": 10.12,
        "low": 9.23,
        "close": 9.78,
        "pre_close": 9.45,
        "change": 0.33,
        "pct_chg": 3.49,
        "vol": 1890000000,
        "amount": 18450000000.0,
        "turnover_rate": 9.74
      }
    ],
    "statistics": {
      "total_records": 12,
      "ytd_return": 15.67,
      "max_monthly_high": 11.23,
      "min_monthly_low": 8.67,
      "avg_monthly_volume": 1950000000,
      "best_month": {
        "date": "20241130",
        "return": 7.98
      },
      "worst_month": {
        "date": "20240229",
        "return": -5.67
      }
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/intraday/{ts_code}` - 分钟级数据**

请求参数：`/stock/intraday/000001.SZ?freq=5min&start_time=2024-12-01T09:30:00&end_time=2024-12-01T15:00:00`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "freq": "5min",
    "trade_date": "20241201",
    "items": [
      {
        "datetime": "2024-12-01T09:30:00",
        "open": 10.32,
        "high": 10.38,
        "low": 10.30,
        "close": 10.35,
        "volume": 2500000,
        "amount": 25875000.0,
        "vwap": 10.35
      },
      {
        "datetime": "2024-12-01T09:35:00",
        "open": 10.35,
        "high": 10.42,
        "low": 10.33,
        "close": 10.40,
        "volume": 1800000,
        "amount": 18720000.0,
        "vwap": 10.40
      },
      {
        "datetime": "2024-12-01T09:40:00",
        "open": 10.40,
        "high": 10.45,
        "low": 10.38,
        "close": 10.43,
        "volume": 1600000,
        "amount": 16688000.0,
        "vwap": 10.43
      }
    ],
    "summary": {
      "total_bars": 66,
      "session_open": 10.32,
      "session_high": 10.68,
      "session_low": 10.28,
      "session_close": 10.56,
      "total_volume": 125000000,
      "total_amount": 1320000000.0,
      "avg_price": 10.56,
      "price_change": 0.24,
      "pct_change": 2.33
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

#### 3.3 技术指标接口

**GET `/stock/indicators/{ts_code}` - 技术指标**

请求参数：`/stock/indicators/000001.SZ?indicators=ma,macd,rsi,kdj&period=20`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "calculation_date": "20241201",
    "indicators": {
      "moving_averages": {
        "ma5": 10.23,
        "ma10": 10.12,
        "ma20": 9.98,
        "ma60": 9.76,
        "ma120": 9.45,
        "ma250": 9.12,
        "ema12": 10.34,
        "ema26": 10.15,
        "ema50": 10.05
      },
      "macd": {
        "dif": 0.19,
        "dea": 0.07,
        "macd": 0.12,
        "signal": "金叉",
        "trend": "上涨"
      },
      "rsi": {
        "rsi6": 72.4,
        "rsi12": 65.8,
        "rsi24": 58.9,
        "signal": "超买",
        "trend": "强势"
      },
      "kdj": {
        "k": 78.9,
        "d": 72.3,
        "j": 92.1,
        "signal": "金叉",
        "trend": "上涨"
      },
      "bollinger_bands": {
        "upper": 10.89,
        "middle": 10.23,
        "lower": 9.57,
        "width": 1.32,
        "position": 0.75,
        "signal": "接近上轨"
      },
      "volume_indicators": {
        "obv": 1234567890,
        "volume_ma5": 95000000,
        "volume_ma10": 87000000,
        "volume_ratio": 1.23,
        "turnover_rate": 0.61
      },
      "momentum_indicators": {
        "momentum": 0.24,
        "roc": 2.33,
        "williams_r": -22.1,
        "cci": 156.7,
        "atr": 0.45
      }
    },
    "signals": {
      "overall_trend": "上涨",
      "strength": "强势",
      "support_level": 10.05,
      "resistance_level": 10.75,
      "buy_signals": ["MACD金叉", "KDJ金叉"],
      "sell_signals": ["RSI超买"],
      "recommendation": "谨慎买入"
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/money-flow/{ts_code}` - 资金流向**

请求参数：`/stock/money-flow/000001.SZ?start_date=20241101&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "items": [
      {
        "trade_date": "20241201",
        "buy_sm_vol": 15000000,
        "buy_sm_amount": 158700000.0,
        "sell_sm_vol": 12000000,
        "sell_sm_amount": 127200000.0,
        "buy_md_vol": 25000000,
        "buy_md_amount": 264000000.0,
        "sell_md_vol": 22000000,
        "sell_md_amount": 232800000.0,
        "buy_lg_vol": 35000000,
        "buy_lg_amount": 369600000.0,
        "sell_lg_vol": 30000000,
        "sell_lg_amount": 317400000.0,
        "buy_elg_vol": 50000000,
        "buy_elg_amount": 528000000.0,
        "sell_elg_vol": 36000000,
        "sell_elg_amount": 380160000.0,
        "net_mf_vol": 25000000,
        "net_mf_amount": 263940000.0
      }
    ],
    "summary": {
      "period_days": 22,
      "total_net_inflow": 2567890123.0,
      "main_net_inflow": 1876543210.0,
      "retail_net_inflow": 691346913.0,
      "avg_daily_inflow": 116722278.32,
      "max_single_day_inflow": 456789012.0,
      "max_single_day_outflow": -234567890.0,
      "inflow_days": 15,
      "outflow_days": 7
    },
    "analysis": {
      "main_trend": "净流入",
      "retail_trend": "净流入",
      "strength": "强势流入",
      "concentration": "主力集中",
      "recommendation": "资金面支撑较强"
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

**GET `/stock/factor/{ts_code}` - 因子数据**

请求参数：`/stock/factor/000001.SZ?factors=pe,pb,roe,roa&start_date=20241101&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SZ",
    "name": "平安银行",
    "items": [
      {
        "trade_date": "20241201",
        "pe": 5.23,
        "pe_ttm": 5.18,
        "pb": 0.82,
        "ps": 0.95,
        "ps_ttm": 0.93,
        "dv_ratio": 4.56,
        "dv_ttm": 4.48,
        "total_share": 19405918198.0,
        "float_share": 19405918198.0,
        "free_share": 19405918198.0,
        "turnover_rate": 0.61,
        "turnover_rate_f": 0.61,
        "volume_ratio": 1.23,
        "pe_percentile": 15.6,
        "pb_percentile": 25.8,
        "ps_percentile": 35.2
      }
    ],
    "fundamental_factors": {
      "profitability": {
        "roe": 15.67,
        "roa": 0.89,
        "roic": 12.34,
        "gross_margin": 45.67,
        "net_margin": 25.89,
        "operating_margin": 32.45
      },
      "growth": {
        "revenue_growth": 8.9,
        "profit_growth": 12.3,
        "eps_growth": 11.8,
        "book_value_growth": 9.5,
        "operating_cash_flow_growth": 15.2
      },
      "leverage": {
        "debt_to_equity": 0.45,
        "debt_to_assets": 0.31,
        "interest_coverage": 8.9,
        "current_ratio": 1.25,
        "quick_ratio": 0.95
      },
      "efficiency": {
        "asset_turnover": 0.65,
        "inventory_turnover": null,
        "receivables_turnover": 8.5,
        "working_capital_turnover": 2.3
      }
    },
    "technical_factors": {
      "momentum": {
        "return_1m": 7.8,
        "return_3m": 15.6,
        "return_6m": 23.4,
        "return_12m": 45.7,
        "volatility_1m": 2.3,
        "volatility_3m": 2.8,
        "max_drawdown": -8.9
      },
      "liquidity": {
        "avg_turnover_rate": 0.58,
        "avg_volume": 95000000,
        "avg_amount": 975000000.0,
        "bid_ask_spread": 0.01,
        "market_impact": 0.05
      }
    },
    "ranking": {
      "industry_pe_rank": 5,
      "industry_pb_rank": 8,
      "industry_roe_rank": 3,
      "market_cap_rank": 15,
      "total_stocks_in_industry": 42
    }
  },
  "timestamp": "2024-12-01T15:30:00Z"
}
```

### 4. 指数数据模块 (`/index`)

**GET `/index/basic/list` - 指数基本信息列表**

请求参数：`?market=SSE&category=综合指数&limit=20`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "ts_code": "000001.SH",
        "symbol": "000001",
        "name": "上证指数",
        "fullname": "上海证券交易所综合股价指数",
        "market": "SSE",
        "publisher": "上海证券交易所",
        "index_type": "综合指数",
        "category": "规模指数",
        "base_date": "19901219",
        "base_point": 100.0,
        "list_date": "19910715",
        "weight_rule": "流通市值加权",
        "desc": "反映上海证券交易所上市股票价格的变动情况",
        "exp_date": null,
        "current_value": 3245.67,
        "change": 28.45,
        "pct_chg": 0.88,
        "pe": 13.45,
        "pb": 1.23,
        "dividend_yield": 2.34,
        "constituent_count": 1747
      },
      {
        "ts_code": "000300.SH",
        "symbol": "000300",
        "name": "沪深300",
        "fullname": "沪深300指数",
        "market": "MSCI",
        "publisher": "中证指数有限公司",
        "index_type": "规模指数",
        "category": "宽基指数",
        "base_date": "20041231",
        "base_point": 1000.0,
        "list_date": "20050408",
        "weight_rule": "自由流通市值加权",
        "desc": "反映沪深两市A股市场整体表现的宽基指数",
        "exp_date": null,
        "current_value": 3876.54,
        "change": 15.67,
        "pct_chg": 0.41,
        "pe": 12.89,
        "pb": 1.45,
        "dividend_yield": 2.67,
        "constituent_count": 300
      },
      {
        "ts_code": "399001.SZ",
        "symbol": "399001",
        "name": "深证成指",
        "fullname": "深证成份股指数",
        "market": "SZSE",
        "publisher": "深圳证券交易所",
        "index_type": "成份指数",
        "category": "规模指数",
        "base_date": "19940720",
        "base_point": 1000.0,
        "list_date": "19950123",
        "weight_rule": "流通市值加权",
        "desc": "反映深圳证券市场的走势情况",
        "exp_date": null,
        "current_value": 10567.89,
        "change": -45.23,
        "pct_chg": -0.43,
        "pe": 18.67,
        "pb": 1.89,
        "dividend_yield": 1.78,
        "constituent_count": 500
      }
    ],
    "pagination": {
      "total": 156,
      "page": 1,
      "size": 20,
      "pages": 8,
      "has_next": true,
      "has_prev": false
    },
    "summary": {
      "total_indices": 156,
      "by_market": {
        "SSE": 89,
        "SZSE": 67
      },
      "by_category": {
        "综合指数": 12,
        "规模指数": 45,
        "行业指数": 78,
        "主题指数": 21
      }
    }
  },
  "timestamp": "2024-12-01T16:00:00Z"
}
```

**GET `/index/major` - 主要指数数据**

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "major_indices": [
      {
        "ts_code": "000001.SH",
        "name": "上证指数",
        "current_value": 3245.67,
        "pre_close": 3217.22,
        "open": 3220.15,
        "high": 3256.89,
        "low": 3215.34,
        "change": 28.45,
        "pct_chg": 0.88,
        "volume": 2567890123,
        "amount": 345678901234.0,
        "turnover_rate": 0.45,
        "pe": 13.45,
        "pb": 1.23,
        "dividend_yield": 2.34,
        "52w_high": 3456.78,
        "52w_low": 2890.12,
        "ytd_return": 8.76,
        "market_cap": 45678901234567.0
      },
      {
        "ts_code": "399001.SZ",
        "name": "深证成指",
        "current_value": 10567.89,
        "pre_close": 10613.12,
        "open": 10598.45,
        "high": 10625.67,
        "low": 10542.33,
        "change": -45.23,
        "pct_chg": -0.43,
        "volume": 1876543210,
        "amount": 234567890123.0,
        "turnover_rate": 0.67,
        "pe": 18.67,
        "pb": 1.89,
        "dividend_yield": 1.78,
        "52w_high": 11234.56,
        "52w_low": 9876.54,
        "ytd_return": -2.34,
        "market_cap": 23456789012345.0
      },
      {
        "ts_code": "399006.SZ",
        "name": "创业板指",
        "current_value": 2134.56,
        "pre_close": 2122.22,
        "open": 2125.67,
        "high": 2145.89,
        "low": 2118.45,
        "change": 12.34,
        "pct_chg": 0.58,
        "volume": 987654321,
        "amount": 123456789012.0,
        "turnover_rate": 1.23,
        "pe": 35.67,
        "pb": 3.45,
        "dividend_yield": 0.89,
        "52w_high": 2456.78,
        "52w_low": 1876.54,
        "ytd_return": 15.67,
        "market_cap": 12345678901234.0
      },
      {
        "ts_code": "000300.SH",
        "name": "沪深300",
        "current_value": 3876.54,
        "pre_close": 3860.87,
        "open": 3865.23,
        "high": 3889.12,
        "low": 3858.45,
        "change": 15.67,
        "pct_chg": 0.41,
        "volume": 1567890123,
        "amount": 198765432109.0,
        "turnover_rate": 0.56,
        "pe": 12.89,
        "pb": 1.45,
        "dividend_yield": 2.67,
        "52w_high": 4123.45,
        "52w_low": 3456.78,
        "ytd_return": 5.43,
        "market_cap": 34567890123456.0
      },
      {
        "ts_code": "000905.SH",
        "name": "中证500",
        "current_value": 5432.10,
        "pre_close": 5441.00,
        "open": 5438.67,
        "high": 5445.23,
        "low": 5425.89,
        "change": -8.90,
        "pct_chg": -0.16,
        "volume": 876543210,
        "amount": 98765432101.0,
        "turnover_rate": 0.78,
        "pe": 22.34,
        "pb": 2.12,
        "dividend_yield": 1.89,
        "52w_high": 5876.54,
        "52w_low": 4987.65,
        "ytd_return": 3.21,
        "market_cap": 15678901234567.0
      }
    ],
    "market_summary": {
      "total_market_cap": 131728271604938.0,
      "avg_pe": 20.60,
      "avg_pb": 2.01,
      "avg_dividend_yield": 1.91,
      "up_indices": 3,
      "down_indices": 2,
      "strongest_index": {
        "name": "创业板指",
        "pct_chg": 0.58
      },
      "weakest_index": {
        "name": "深证成指",
        "pct_chg": -0.43
      }
    },
    "update_time": "2024-12-01T16:00:00Z"
  },
  "timestamp": "2024-12-01T16:00:00Z"
}
```

**GET `/index/shenwan` - 申万行业指数**

请求参数：`?level=1&date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "trade_date": "20241201",
    "level": 1,
    "industries": [
      {
        "index_code": "801010.SI",
        "index_name": "农林牧渔",
        "close": 2345.67,
        "pre_close": 2334.56,
        "open": 2338.90,
        "high": 2356.78,
        "low": 2332.45,
        "change": 11.11,
        "pct_chg": 0.48,
        "volume": 123456789,
        "amount": 2890123456.0,
        "turnover_rate": 0.67,
        "pe": 25.67,
        "pb": 2.34,
        "constituent_count": 45,
        "market_cap": 567890123456.0
      },
      {
        "index_code": "801020.SI",
        "index_name": "采掘",
        "close": 1876.54,
        "pre_close": 1889.12,
        "open": 1885.67,
        "high": 1892.34,
        "low": 1869.45,
        "change": -12.58,
        "pct_chg": -0.67,
        "volume": 98765432,
        "amount": 1850987654.0,
        "turnover_rate": 0.45,
        "pe": 18.90,
        "pb": 1.67,
        "constituent_count": 32,
        "market_cap": 345678901234.0
      },
      {
        "index_code": "801030.SI",
        "index_name": "化工",
        "close": 3456.78,
        "pre_close": 3445.67,
        "open": 3450.23,
        "high": 3467.89,
        "low": 3442.34,
        "change": 11.11,
        "pct_chg": 0.32,
        "volume": 234567890,
        "amount": 8109876543.0,
        "turnover_rate": 0.78,
        "pe": 22.45,
        "pb": 1.89,
        "constituent_count": 89,
        "market_cap": 1234567890123.0
      },
      {
        "index_code": "801040.SI",
        "index_name": "钢铁",
        "close": 2109.87,
        "pre_close": 2123.45,
        "open": 2118.90,
        "high": 2125.67,
        "low": 2098.76,
        "change": -13.58,
        "pct_chg": -0.64,
        "volume": 156789012,
        "amount": 3309876543.0,
        "turnover_rate": 0.56,
        "pe": 15.67,
        "pb": 1.23,
        "constituent_count": 28,
        "market_cap": 456789012345.0
      },
      {
        "index_code": "801050.SI",
        "index_name": "有色金属",
        "close": 2987.65,
        "pre_close": 2976.54,
        "open": 2980.12,
        "high": 2995.67,
        "low": 2972.34,
        "change": 11.11,
        "pct_chg": 0.37,
        "volume": 187654321,
        "amount": 5609876543.0,
        "turnover_rate": 0.67,
        "pe": 28.90,
        "pb": 2.45,
        "constituent_count": 56,
        "market_cap": 789012345678.0
      }
    ],
    "summary": {
      "total_industries": 28,
      "up_count": 16,
      "down_count": 12,
      "flat_count": 0,
      "strongest_industry": {
        "name": "农林牧渔",
        "pct_chg": 0.48
      },
      "weakest_industry": {
        "name": "采掘",
        "pct_chg": -0.67
      },
      "avg_pct_chg": 0.12,
      "total_volume": 4567890123,
      "total_amount": 56789012345.0
    }
  },
  "timestamp": "2024-12-01T16:00:00Z"
}
```

**GET `/index/daily/{ts_code}` - 指数日线数据**

请求参数：`/index/daily/000001.SH?start_date=20241101&end_date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ts_code": "000001.SH",
    "name": "上证指数",
    "period": "daily",
    "items": [
      {
        "trade_date": "20241201",
        "open": 3220.15,
        "high": 3256.89,
        "low": 3215.34,
        "close": 3245.67,
        "pre_close": 3217.22,
        "change": 28.45,
        "pct_chg": 0.88,
        "vol": 2567890123,
        "amount": 345678901234.0,
        "pe": 13.45,
        "pb": 1.23,
        "dividend_yield": 2.34,
        "turnover_rate": 0.45
      },
      {
        "trade_date": "20241130",
        "open": 3198.76,
        "high": 3225.43,
        "low": 3192.87,
        "close": 3217.22,
        "pre_close": 3205.67,
        "change": 11.55,
        "pct_chg": 0.36,
        "vol": 2234567890,
        "amount": 298765432109.0,
        "pe": 13.32,
        "pb": 1.21,
        "dividend_yield": 2.36,
        "turnover_rate": 0.39
      },
      {
        "trade_date": "20241129",
        "open": 3189.45,
        "high": 3212.34,
        "low": 3185.67,
        "close": 3205.67,
        "pre_close": 3195.43,
        "change": 10.24,
        "pct_chg": 0.32,
        "vol": 1987654321,
        "amount": 267890123456.0,
        "pe": 13.27,
        "pb": 1.20,
        "dividend_yield": 2.37,
        "turnover_rate": 0.35
      }
    ],
    "statistics": {
      "total_records": 22,
      "period_return": 2.45,
      "max_value": 3256.89,
      "min_value": 3145.67,
      "avg_volume": 2198765432,
      "avg_amount": 304567890123.0,
      "volatility": 1.23,
      "max_daily_gain": 1.45,
      "max_daily_loss": -1.67,
      "up_days": 14,
      "down_days": 8
    },
    "technical_indicators": {
      "ma5": 3234.56,
      "ma10": 3223.45,
      "ma20": 3198.76,
      "ma60": 3167.89,
      "ema12": 3241.23,
      "ema26": 3225.67,
      "macd": 5.67,
      "rsi": 58.9,
      "kdj_k": 65.4,
      "kdj_d": 62.1,
      "kdj_j": 72.0
    },
    "valuation_metrics": {
      "current_pe": 13.45,
      "pe_percentile": 45.6,
      "current_pb": 1.23,
      "pb_percentile": 35.8,
      "dividend_yield": 2.34,
      "yield_percentile": 65.2
    }
  },
  "timestamp": "2024-12-01T16:00:00Z"
}
```

**GET `/index/components/{ts_code}` - 指数成分股**

请求参数：`/index/components/000300.SH?date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "index_code": "000300.SH",
    "index_name": "沪深300",
    "trade_date": "20241201",
    "total_constituents": 300,
    "constituents": [
      {
        "con_code": "000001.SZ",
        "con_name": "平安银行",
        "weight": 1.23,
        "in_date": "20050408",
        "out_date": null,
        "is_new": false,
        "industry": "银行",
        "market_cap": 204567890000,
        "free_mv": 198765432100,
        "current_price": 10.56,
        "pct_chg": 2.33,
        "contribution": 0.029
      },
      {
        "con_code": "000002.SZ",
        "con_name": "万科A",
        "weight": 0.89,
        "in_date": "20050408",
        "out_date": null,
        "is_new": false,
        "industry": "房地产",
        "market_cap": 98765432100,
        "free_mv": 95432109876,
        "current_price": 8.95,
        "pct_chg": -1.21,
        "contribution": -0.011
      },
      {
        "con_code": "600036.SH",
        "con_name": "招商银行",
        "weight": 2.45,
        "in_date": "20050408",
        "out_date": null,
        "is_new": false,
        "industry": "银行",
        "market_cap": 567890123456,
        "free_mv": 543210987654,
        "current_price": 34.67,
        "pct_chg": 1.89,
        "contribution": 0.046
      },
      {
        "con_code": "300750.SZ",
        "con_name": "宁德时代",
        "weight": 3.67,
        "in_date": "20180619",
        "out_date": null,
        "is_new": false,
        "industry": "电力设备",
        "market_cap": 1234567890123,
        "free_mv": 1098765432109,
        "current_price": 189.45,
        "pct_chg": 4.56,
        "contribution": 0.167
      },
      {
        "con_code": "600519.SH",
        "con_name": "贵州茅台",
        "weight": 4.89,
        "in_date": "20050408",
        "out_date": null,
        "is_new": false,
        "industry": "食品饮料",
        "market_cap": 2345678901234,
        "free_mv": 2109876543210,
        "current_price": 1876.54,
        "pct_chg": 0.78,
        "contribution": 0.038
      }
    ],
    "industry_distribution": {
      "银行": {
        "count": 12,
        "weight": 8.67,
        "avg_pct_chg": 1.45
      },
      "非银金融": {
        "count": 15,
        "weight": 6.78,
        "avg_pct_chg": 0.89
      },
      "食品饮料": {
        "count": 18,
        "weight": 9.34,
        "avg_pct_chg": 0.56
      },
      "电力设备": {
        "count": 22,
        "weight": 12.45,
        "avg_pct_chg": 2.34
      },
      "医药生物": {
        "count": 28,
        "weight": 8.90,
        "avg_pct_chg": -0.67
      }
    },
    "weight_distribution": {
      "top_10_weight": 35.67,
      "top_50_weight": 68.90,
      "top_100_weight": 85.43,
      "concentration_ratio": 0.3567
    },
    "changes": {
      "new_additions": [],
      "deletions": [],
      "weight_changes": [
        {
          "con_code": "000001.SZ",
          "con_name": "平安银行",
          "old_weight": 1.18,
          "new_weight": 1.23,
          "change": 0.05
        }
      ]
    },
    "performance_attribution": {
      "index_return": 0.41,
      "top_contributors": [
        {
          "con_code": "300750.SZ",
          "con_name": "宁德时代",
          "contribution": 0.167
        },
        {
          "con_code": "600036.SH",
          "con_name": "招商银行",
          "contribution": 0.046
        }
      ],
      "top_detractors": [
        {
          "con_code": "000002.SZ",
          "con_name": "万科A",
          "contribution": -0.011
        }
      ]
    }
  },
  "timestamp": "2024-12-01T16:00:00Z"
}
```

**GET `/index/weight/{ts_code}` - 指数权重**

请求参数：`/index/weight/000300.SH?date=20241201`

返回示例：
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "index_code": "000300.SH",
    "index_name": "沪深300",
    "trade_date": "20241201",
    "weight_method": "自由流通市值加权",
    "total_constituents": 300,
    "weights": [
      {
        "con_code": "600519.SH",
        "con_name": "贵州茅台",
        "weight": 4.89,
        "rank": 1,
        "market_cap": 2345678901234,
        "free_mv": 2109876543210,
        "shares": 1256637768,
        "free_shares": 1125574091,
        "price": 1876.54,
        "industry": "食品饮料"
      },
      {
        "con_code": "300750.SZ",
        "con_name": "宁德时代",
        "weight": 3.67,
        "rank": 2,
        "market_cap": 1234567890123,
        "free_mv": 1098765432109,
        "shares": 4653132950,
        "free_shares": 4141666635,
        "price": 189.45,
        "industry": "电力设备"
      },
      {
        "con_code": "600036.SH",
        "con_name": "招商银行",
        "weight": 2.45,
        "rank": 3,
        "market_cap": 567890123456,
        "free_mv": 543210987654,
        "shares": 25220645819,
        "free_shares": 24109876543,
        "price": 34.67,
        "industry": "银行"
      },
      {
        "con_code": "000858.SZ",
        "con_name": "五粮液",
        "weight": 2.12,
        "rank": 4,
        "market_cap": 456789012345,
        "free_mv": 432109876543,
        "shares": 3868776656,
        "free_shares": 3654321098,
        "price": 156.78,
        "industry": "食品饮料"
      },
      {
        "con_code": "000001.SZ",
        "con_name": "平安银行",
        "weight": 1.23,
        "rank": 5,
        "market_cap": 204567890000,
        "free_mv": 198765432100,
        "shares": 19405918198,
        "free_mv_shares": 19405918198,
        "price": 10.56,
        "industry": "银行"
      }
    ],
    "weight_statistics": {
      "max_weight": 4.89,
      "min_weight": 0.03,
      "avg_weight": 0.33,
      "median_weight": 0.28,
      "std_weight": 0.67,
      "top_10_total_weight": 28.45,
      "top_50_total_weight": 65.78,
      "herfindahl_index": 0.0234
    },
    "industry_weights": {
      "食品饮料": 9.34,
      "电力设备": 12.45,
      "银行": 8.67,
      "非银金融": 6.78,
      "医药生物": 8.90,
      "电子": 7.56,
      "计算机": 5.67,
      "化工": 4.89,
      "机械设备": 4.23,
      "汽车": 6.78
    },
    "market_weights": {
      "上海": 58.67,
      "深圳": 41.33,
      "主板": 78.90,
      "创业板": 12.34,
      "科创板": 8.76
    },
    "weight_changes": {
      "last_adjustment_date": "20241130",
      "next_adjustment_date": "20241215",
      "changes_count": 5,
      "major_changes": [
        {
          "con_code": "000001.SZ",
          "con_name": "平安银行",
          "old_weight": 1.18,
          "new_weight": 1.23,
          "change": 0.05,
          "reason": "市值变化"
        }
      ]
    }
  },
  "timestamp": "2024-12-01T16:00:00Z"
}
```

### 5. 财务数据模块 (`/financial`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/financial/income/{ts_code}` | GET | 利润表数据 | `ts_code`, `period`, `start_date`, `end_date` | 利润表数据数组 |
| `/financial/balance/{ts_code}` | GET | 资产负债表 | `ts_code`, `period`, `start_date`, `end_date` | 资产负债表数据数组 |
| `/financial/cashflow/{ts_code}` | GET | 现金流量表 | `ts_code`, `period`, `start_date`, `end_date` | 现金流量表数据数组 |
| `/financial/indicators/{ts_code}` | GET | 财务指标 | `ts_code`, `period`, `start_date`, `end_date` | 财务指标数据数组 |
| `/financial/forecast/{ts_code}` | GET | 业绩预告 | `ts_code`, `period`, `start_date`, `end_date` | 业绩预告数据数组 |
| `/financial/express/{ts_code}` | GET | 业绩快报 | `ts_code`, `period`, `start_date`, `end_date` | 业绩快报数据数组 |
| `/financial/audit/{ts_code}` | GET | 财务审计意见 | `ts_code`, `period`, `start_date`, `end_date` | 审计意见数据数组 |

### 6. 期货数据模块 (`/futures`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/futures/basic/list` | GET | 期货基本信息 | `exchange`, `fut_type` | 期货基本信息数组 |
| `/futures/daily/{ts_code}` | GET | 期货日线数据 | `ts_code`, `start_date`, `end_date` | 期货K线数据数组 |
| `/futures/holding/{ts_code}` | GET | 期货持仓数据 | `ts_code`, `start_date`, `end_date` | 持仓数据数组 |
| `/futures/settlement/{ts_code}` | GET | 期货结算数据 | `ts_code`, `trade_date` | 结算数据 |

### 7. ETF数据模块 (`/etf`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/etf/basic/list` | GET | ETF基本信息 | `market`, `category` | ETF基本信息数组 |
| `/etf/daily/{ts_code}` | GET | ETF日线数据 | `ts_code`, `start_date`, `end_date` | ETF净值数据数组 |
| `/etf/index-info/list` | GET | ETF指数信息 | `ts_code` | ETF跟踪指数信息 |
| `/etf/components/{ts_code}` | GET | ETF成分股 | `ts_code`, `date` | ETF成分股列表 |
| `/etf/search` | GET | ETF搜索 | `keyword`, `limit` | ETF搜索结果 |

### 8. 期权数据模块 (`/options`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/options/basic/list` | GET | 期权基本信息 | `exchange`, `opt_type` | 期权基本信息数组 |
| `/options/daily/{ts_code}` | GET | 期权日线数据 | `ts_code`, `start_date`, `end_date` | 期权价格数据数组 |
| `/options/greeks/{ts_code}` | GET | 期权希腊字母 | `ts_code`, `trade_date` | 希腊字母数据 |

### 9. 交易日历模块 (`/calendar`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/calendar/basic` | GET | 基础交易日历 | `exchange`, `start_date`, `end_date` | 交易日历数据 |
| `/calendar/exchanges` | GET | 支持的交易所 | 无 | 交易所列表 |
| `/calendar/is-trading-day` | GET | 判断是否交易日 | `date`, `exchange` | `{"is_trading_day": true/false}` |
| `/calendar/trading-days` | GET | 获取交易日列表 | `start_date`, `end_date`, `exchange` | 交易日列表 |
| `/calendar/next-trading-day` | GET | 下一个交易日 | `date`, `exchange` | 下一个交易日 |
| `/calendar/prev-trading-day` | GET | 上一个交易日 | `date`, `exchange` | 上一个交易日 |
| `/calendar/statistics` | GET | 交易日统计 | `year`, `exchange` | 交易日统计数据 |
| `/calendar/monthly-summary` | GET | 月度交易日汇总 | `year`, `month`, `exchange` | 月度汇总数据 |

### 10. 资金流向模块 (`/money_flow`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/money_flow/stock/{ts_code}` | GET | 个股资金流向 | `ts_code`, `start_date`, `end_date` | 个股资金流向数据 |
| `/money_flow/industry` | GET | 行业资金流向 | `date`, `industry` | 行业资金流向数据 |
| `/money_flow/market` | GET | 大盘资金流向 | `start_date`, `end_date` | 大盘资金流向数据 |
| `/money_flow/ranking` | GET | 资金流向排行 | `date`, `type` | 资金流向排行榜 |

### 11. 融资融券模块 (`/margin`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/margin/summary` | GET | 融资融券汇总 | `trade_date`, `exchange` | 融资融券汇总数据 |
| `/margin/detail/{ts_code}` | GET | 个股融资融券明细 | `ts_code`, `start_date`, `end_date` | 融资融券明细数据 |
| `/margin/ranking` | GET | 融资融券排行 | `date`, `type` | 融资融券排行榜 |
| `/margin/trend` | GET | 融资融券趋势 | `start_date`, `end_date` | 融资融券趋势数据 |

### 12. 龙虎榜模块 (`/dragon-tiger`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/dragon-tiger/list` | GET | 龙虎榜列表 | `trade_date`, `ts_code` | 龙虎榜数据列表 |
| `/dragon-tiger/detail/{ts_code}` | GET | 个股龙虎榜详情 | `ts_code`, `trade_date` | 龙虎榜详细数据 |
| `/dragon-tiger/institutions` | GET | 机构席位统计 | `start_date`, `end_date` | 机构席位数据 |
| `/dragon-tiger/ranking` | GET | 龙虎榜排行 | `date`, `type` | 龙虎榜排行榜 |

### 13. 涨跌停数据模块 (`/limit_data`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/limit_data/daily/list` | GET | 涨跌停日报 | `trade_date`, `limit_type` | 涨跌停股票列表 |
| `/limit_data/statistics` | GET | 涨跌停统计 | `start_date`, `end_date` | 涨跌停统计数据 |
| `/limit_data/consecutive` | GET | 连板统计 | `trade_date`, `min_days` | 连板股票数据 |
| `/limit_data/analysis` | GET | 涨跌停分析 | `trade_date` | 涨跌停市场分析 |

### 14. 宏观数据模块 (`/macro`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/macro/shibor` | GET | SHIBOR利率 | `start_date`, `end_date` | SHIBOR利率数据 |
| `/macro/gdp` | GET | GDP数据 | `start_date`, `end_date` | GDP数据 |
| `/macro/cpi` | GET | CPI数据 | `start_date`, `end_date` | CPI数据 |
| `/macro/pmi` | GET | PMI数据 | `start_date`, `end_date` | PMI数据 |

### 15. 数据分析模块 (`/analytics`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/analytics/technical/{ts_code}` | GET | 技术分析 | `ts_code`, `indicators` | 技术分析结果 |
| `/analytics/correlation` | GET | 相关性分析 | `symbols`, `period` | 相关性矩阵 |
| `/analytics/volatility/{ts_code}` | GET | 波动率分析 | `ts_code`, `period` | 波动率数据 |
| `/analytics/momentum/{ts_code}` | GET | 动量分析 | `ts_code`, `period` | 动量指标 |
| `/analytics/volume-price/{ts_code}` | GET | 量价关系分析 | `ts_code`, `period` | 量价关系数据 |

### 16. 市场情绪模块 (`/sentiment`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/sentiment/fear-greed` | GET | 恐慌贪婪指数 | `date` | 恐慌贪婪指数 |
| `/sentiment/market-mood` | GET | 市场情绪 | `date` | 市场情绪指标 |
| `/sentiment/vix` | GET | 波动率指数 | `start_date`, `end_date` | VIX指数数据 |
| `/sentiment/put-call-ratio` | GET | 看跌看涨比率 | `start_date`, `end_date` | 看跌看涨比率 |

### 17. 投资策略模块 (`/strategy`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/strategy/screening` | POST | 策略筛选 | 筛选条件对象 | 筛选结果列表 |
| `/strategy/backtest` | POST | 策略回测 | 策略配置对象 | 回测结果 |
| `/strategy/optimization` | POST | 策略优化 | 优化参数对象 | 优化结果 |
| `/strategy/performance/{strategy_id}` | GET | 策略表现 | `strategy_id`, `period` | 策略表现数据 |
| `/strategy/ranking` | GET | 策略排行 | `category`, `period` | 策略排行榜 |

### 18. 道氏理论分析模块 (`/dow-theory`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/dow-theory/analyze/{ts_code}` | POST | 道氏理论分析 | `ts_code`, 分析参数 | 道氏理论分析结果 |
| `/dow-theory/trend/{ts_code}` | GET | 趋势分析 | `ts_code`, `period` | 趋势分析数据 |
| `/dow-theory/confirmation` | GET | 相互确认分析 | `symbols`, `period` | 确认分析结果 |

### 19. 缠论分析模块 (`/chan-theory`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/chan-theory/analyze` | POST | 缠论分析 | `ts_code`, 分析参数 | 缠论分析结果 |
| `/chan-theory/structure/{ts_code}` | GET | 结构分析 | `ts_code`, `period` | 结构分析数据 |
| `/chan-theory/signals/{ts_code}` | GET | 信号识别 | `ts_code`, `period` | 信号识别结果 |

### 20. 系统管理模块 (`/admin`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/admin/system/info` | GET | 系统信息 | 需要管理员权限 | 系统信息对象 |
| `/admin/cache/clear` | POST | 清除缓存 | `cache_type` | 清除结果 |
| `/admin/database/collections` | GET | 数据库集合信息 | 无 | 集合列表 |
| `/admin/database/stats` | GET | 数据库统计 | 无 | 数据库统计信息 |
| `/admin/users` | GET | 用户管理 | `page`, `size` | 用户列表 |

### 21. 系统监控模块 (`/system`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/system/health` | GET | 健康检查 | 无 | `{"status": "healthy"}` |
| `/system/metrics` | GET | 系统指标 | 无 | 系统性能指标 |
| `/system/status` | GET | 系统状态 | 无 | 系统状态信息 |

### 22. 数据库配置模块 (`/admin`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/admin/database/config` | GET | 获取数据库配置 | 需要管理员权限 | 数据库配置信息 |
| `/admin/database/config` | POST | 更新数据库配置 | 配置对象 | 更新结果 |
| `/admin/database/test` | POST | 测试数据库连接 | 连接参数 | 测试结果 |
| `/admin/database/status` | GET | 数据库状态 | 无 | 数据库状态信息 |
| `/admin/database/reload` | POST | 重新加载配置 | 无 | 重载结果 |

### 23. 概念数据模块

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/limit/list` | GET | 涨停概念统计 | `trade_date` | 涨停概念数据 |
| `/limit/search` | GET | 概念搜索 | `keyword`, `limit` | 概念搜索结果 |
| `/sw/daily` | POST | 申万行业日线数据 | `trade_date`, `industry_codes` | 申万行业数据 |

### 24. HM自定义数据模块 (`/hm`)

| 接口路径 | 方法 | 功能描述 | 参数说明 | 返回格式 |
|---------|------|----------|----------|----------|
| `/hm/detail/list` | GET | HM详情列表 | `start_date`, `end_date` | HM详情数据 |
| `/hm/list/all` | GET | HM列表汇总 | `trade_date` | HM汇总数据 |
| `/hm/batch/query` | POST | 批量查询HM数据 | 查询条件数组 | 批量查询结果 |
| `/hm/export/summary` | GET | HM数据导出汇总 | `format`, `date_range` | 导出汇总信息 |

### 7. 龙虎榜接口 (`/dragon-tiger`)

| 接口路径 | 方法 | 功能描述 | 数据来源 |
|---------|------|----------|----------|
| `/dragon-tiger/list` | GET | 龙虎榜每日统计 | top_list |
| `/dragon-tiger/institution` | GET | 机构交易统计 | top_inst |
| `/dragon-tiger/summary` | GET | 龙虎榜汇总分析 | 聚合计算 |
| `/dragon-tiger/stock/{ts_code}` | GET | 个股龙虎榜历史 | 历史查询 |

### 8. 数据分析接口 (`/analytics`)

| 接口路径 | 方法 | 功能描述 | 计算类型 |
|---------|------|----------|----------|
| `/analytics/correlation` | GET | 相关性分析 | 统计计算 |
| `/analytics/sector-analysis` | GET | 板块分析 | 聚合分析 |
| `/analytics/market-mood` | GET | 市场情绪分析 | 综合指标 |
| `/analytics/volume-price` | GET | 量价关系分析 | 技术分析 |
| `/analytics/technical-indicators` | GET | 技术指标计算 | 技术分析 |

### 9. 投资策略接口 (`/strategy`)

| 接口路径 | 方法 | 功能描述 | 策略类型 |
|---------|------|----------|----------|
| `/strategy/screening` | GET | 股票筛选策略 | 多因子筛选 |
| `/strategy/momentum` | GET | 动量策略分析 | 技术策略 |
| `/strategy/value` | GET | 价值投资策略 | 基本面策略 |
| `/strategy/pairs-trading` | GET | 配对交易策略 | 统计套利 |
| `/strategy/backtesting` | POST | 策略回测 | 历史回测 |

### 10. 交易日历接口 (`/calendar`)

| 接口路径 | 方法 | 功能描述 | 缓存策略 |
|---------|------|----------|----------|
| `/calendar/basic` | GET | 获取交易日历基础信息 | 长期缓存(24h) |
| `/calendar/exchanges` | GET | 获取支持的交易所列表 | 长期缓存(24h) |
| `/calendar/is-trading-day` | GET | 判断指定日期是否为交易日 | 长期缓存(24h) |
| `/calendar/trading-days` | GET | 获取日期范围内的交易日列表 | 长期缓存(24h) |
| `/calendar/next-trading-day` | GET | 获取下一个交易日 | 长期缓存(24h) |
| `/calendar/prev-trading-day` | GET | 获取前一个交易日 | 长期缓存(24h) |
| `/calendar/statistics` | GET | 获取交易日历统计信息 | 长期缓存(24h) |
| `/calendar/monthly-summary` | GET | 获取月度交易日统计 | 长期缓存(24h) |
| `/calendar/batch-check` | POST | 批量检查交易日 | 长期缓存(24h) |

### 11. 系统管理接口 (`/admin` & `/system`)

| 接口路径 | 方法 | 功能描述 | 权限要求 |
|---------|------|----------|----------|
| `/system/health` | GET | 系统健康检查 | 无 |
| `/system/metrics` | GET | 性能指标 | 无 |
| `/admin/cache/clear` | POST | 清理缓存 | 管理员 |
| `/admin/database/stats` | GET | 数据库统计 | 管理员 |
| `/admin/users` | GET | 用户管理 | 管理员 |

## ⚡ 高并发优化策略

### 1. 缓存策略

```python
# 多层缓存配置
CACHE_STRATEGIES = {
    "基础数据": {"ttl": 86400},    # 24小时 - 股票基本信息
    "行情数据": {"ttl": 3600},     # 1小时 - K线数据
    "实时数据": {"ttl": 300},      # 5分钟 - 排行榜、概览
    "用户数据": {"ttl": 3600},     # 1小时 - 自选股等
    "分析结果": {"ttl": 86400},    # 24小时 - 复杂分析结果
}
```

### 2. 限流配置

```python
# 用户分级限流
RATE_LIMITS = {
    "免费用户":   {"rps": 5,   "rpm": 300,   "rph": 1800},
    "基础用户":   {"rps": 20,  "rpm": 1200,  "rph": 7200},
    "高级用户":   {"rps": 50,  "rpm": 3000,  "rph": 18000},
    "企业用户":   {"rps": 200, "rpm": 12000, "rph": 72000},
}
```

### 3. 数据库优化

```python
# 连接池配置
DB_CONFIG = {
    "maxPoolSize": 100,        # 最大连接数
    "minPoolSize": 10,         # 最小连接数
    "maxIdleTimeMS": 60000,    # 连接空闲时间
    "readPreference": "primaryPreferred",  # 读写分离
}
```

### 4. 批量查询优化

```python
# 并行查询示例
async def batch_stock_data(ts_codes: List[str]):
    queries = [
        {"collection": "stock_kline_daily", "filter": {"ts_code": code}}
        for code in ts_codes
    ]
    results = await db_manager.bulk_find_parallel(queries)
    return results
```

## 🔒 安全和认证

### 1. JWT认证
- 用户登录后返回JWT Token
- Token有效期24小时
- 支持角色基访问控制

### 2. API密钥认证
- 企业用户可申请API密钥
- 支持按密钥进行限流和计费

### 3. IP白名单
- 支持IP白名单机制
- 可按IP进行访问控制

## 📊 性能指标

### 1. 目标性能指标

| 指标类型 | 目标值 | 说明 |
|---------|-------|------|
| 响应时间 | < 100ms | 95%的请求 |
| 并发数 | 1000+ | 同时在线用户 |
| 吞吐量 | 10000+ QPS | 峰值处理能力 |
| 缓存命中率 | > 80% | 热点数据缓存 |
| 数据库连接 | < 2s | 连接建立时间 |

### 2. 监控和告警

```python
# 性能监控指标
METRICS = {
    "api_requests_total": "API请求总数",
    "api_request_duration": "API请求耗时",
    "cache_hit_ratio": "缓存命中率", 
    "db_query_duration": "数据库查询耗时",
    "rate_limit_exceeded": "限流触发次数",
}
```

## 🚀 部署和扩展

### 1. 容器化部署
```dockerfile
# 支持Docker容器化部署
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
```

### 2. 负载均衡
- 支持Nginx负载均衡
- 支持多实例水平扩展
- 支持Redis Cluster集群

### 3. 监控集成
- 集成Prometheus监控
- 支持Grafana可视化
- 支持告警通知

## 📖 使用示例

### 1. 获取股票基本信息
```bash
curl -X GET "http://api.domain.com/stock/basic?market=主板&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. 批量获取K线数据
```bash
curl -X GET "http://api.domain.com/stock/batch-kline?ts_codes=000001.SZ,000002.SZ&period=daily" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 获取市场概览
```bash
curl -X GET "http://api.domain.com/stock/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 股票技术分析
```bash
curl -X GET "http://api.domain.com/stock/analysis/000001.SZ?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 交易日历查询
```bash
# 判断是否为交易日
curl -X GET "http://api.domain.com/calendar/is-trading-day?date=20250627&exchange=SSE" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取交易日列表
curl -X GET "http://api.domain.com/calendar/trading-days?start_date=20250601&end_date=20250630&exchange=SSE" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取下一个交易日
curl -X GET "http://api.domain.com/calendar/next-trading-day?date=20250627&exchange=SSE&days=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 更新和维护

### 1. 版本管理
- 采用语义化版本控制
- 支持API版本兼容
- 提供升级迁移指南

### 2. 数据更新
- 支持增量数据更新
- 自动缓存失效机制
- 数据一致性保证

### 3. 性能优化
- 定期性能分析
- 慢查询优化
- 缓存策略调优

---

**🎯 总结**: 本API系统基于当前项目的丰富数据资源，设计了一套完整的高并发接口方案，涵盖了从基础数据查询到复杂分析计算的全方位需求，通过多层缓存、智能限流、异步处理等技术手段，确保系统在高并发场景下的稳定性和高性能表现。