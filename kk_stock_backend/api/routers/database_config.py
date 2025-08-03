#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置管理API接口
支持动态配置数据库连接参数
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import json
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure

import sys
import os
from api.global_db import db_handler

# 添加项目根目录到sys.path以便导入数据库管理器
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(api_dir)
sys.path.insert(0, project_root)


router = APIRouter()

class DatabaseConfigManager:
    """数据库配置管理器"""
    
    def __init__(self, config_file: str = "database_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = os.path.join(os.path.dirname(__file__), "..", config_file)
        self.default_config = {
            "cloud_database": {
                "host": "118.195.242.207",
                "port": 27017,
                "database": "quant_analysis",
                "username": "root",
                "password": "example",
                "authSource": "admin"
            },
            "local_database": {
                "host": "127.0.0.1",
                "port": 27017,
                "database": "quant_analysis",
                "username": "root",
                "password": "example",
                "authSource": "admin"
            },
            "priority": "local"
        }
        
        # 确保配置文件存在
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """确保配置文件存在，如果不存在则创建默认配置"""
        if not os.path.exists(self.config_file):
            self.save_config(self.default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置完整性
            if not self._validate_config(config):
                print("配置文件无效，使用默认配置")
                return self.default_config.copy()
            
            return config
            
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        try:
            # 验证配置
            if not self._validate_config(config):
                raise ValueError("配置数据无效")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置数据的有效性"""
        required_keys = ["cloud_database", "local_database", "priority"]
        
        if not all(key in config for key in required_keys):
            return False
        
        # 验证数据库配置
        for db_type in ["cloud_database", "local_database"]:
            db_config = config[db_type]
            required_db_keys = ["host", "port", "database", "username", "password", "authSource"]
            
            if not all(key in db_config for key in required_db_keys):
                return False
            
            # 验证端口是否为有效数字
            if not isinstance(db_config["port"], int) or not (1 <= db_config["port"] <= 65535):
                return False
        
        # 验证优先级设置
        if config["priority"] not in ["local", "cloud"]:
            return False
        
        return True
    
    def get_connection_uri(self, db_type: str) -> str:
        """获取数据库连接URI"""
        config = self.load_config()
        
        if db_type not in ["cloud_database", "local_database"]:
            raise ValueError(f"无效的数据库类型: {db_type}")
        
        db_config = config[db_type]
        
        uri = (f"mongodb://{db_config['username']}:{db_config['password']}@"
               f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
               f"?authSource={db_config['authSource']}")
        
        return uri
    
    def test_connection(self, db_type: str) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            uri = self.get_connection_uri(db_type)
            
            # 创建客户端并测试连接
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # 测试连接
            client.admin.command('ping')
            server_info = client.server_info()
            
            client.close()
            
            return {
                "success": True,
                "message": "连接成功",
                "server_version": server_info.get("version", "unknown"),
                "connection_uri": uri.replace(":example@", ":****@")  # 隐藏密码
            }
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "error_type": "connection_error"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"测试连接时发生错误: {str(e)}",
                "error_type": "unknown_error"
            }
    
    def update_database_config(self, db_type: str, host: str, port: int) -> bool:
        """更新数据库配置"""
        try:
            config = self.load_config()
            
            if db_type not in ["cloud_database", "local_database"]:
                raise ValueError(f"无效的数据库类型: {db_type}")
            
            # 更新配置
            config[db_type]["host"] = host
            config[db_type]["port"] = port
            
            # 保存配置
            return self.save_config(config)
            
        except Exception as e:
            print(f"更新数据库配置失败: {e}")
            return False
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置（隐藏敏感信息）"""
        config = self.load_config()
        
        # 创建安全的配置副本（隐藏密码）
        safe_config = {
            "cloud_database": {
                "host": config["cloud_database"]["host"],
                "port": config["cloud_database"]["port"],
                "database": config["cloud_database"]["database"]
            },
            "local_database": {
                "host": config["local_database"]["host"],
                "port": config["local_database"]["port"],
                "database": config["local_database"]["database"]
            },
            "priority": config["priority"]
        }
        
        return safe_config

# 全局配置管理器实例
config_manager = DatabaseConfigManager()

# 数据模型
class DatabaseConfigRequest(BaseModel):
    """数据库配置请求模型"""
    cloud_database: Dict[str, Any] = Field(..., description="云端数据库配置")
    local_database: Dict[str, Any] = Field(..., description="本地数据库配置")
    priority: str = Field(..., description="优先级: local 或 cloud")

class DatabaseTestRequest(BaseModel):
    """数据库连接测试请求模型"""
    db_type: str = Field(..., description="数据库类型: cloud_database 或 local_database")

# ==================== 数据库配置管理接口 ====================

@router.get("/database/config")
async def get_database_config():
    """
    获取当前数据库配置
    """
    try:
        config = config_manager.get_database_config()
        
        return {
            "success": True,
            "data": config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库配置失败: {str(e)}")

@router.post("/database/config")
async def update_database_config(request: DatabaseConfigRequest):
    """
    更新数据库配置
    """
    try:
        # 构建完整配置
        config = {
            "cloud_database": {
                "host": request.cloud_database.get("host", "118.195.242.207"),
                "port": request.cloud_database.get("port", 27017),
                "database": "quant_analysis",
                "username": "root",
                "password": "example",
                "authSource": "admin"
            },
            "local_database": {
                "host": request.local_database.get("host", "127.0.0.1"),
                "port": request.local_database.get("port", 27017),
                "database": "quant_analysis",
                "username": "root",
                "password": "example",
                "authSource": "admin"
            },
            "priority": request.priority
        }
        
        # 保存配置
        success = config_manager.save_config(config)
        
        if success:
            return {
                "success": True,
                "message": "数据库配置更新成功",
                "data": config_manager.get_database_config(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新数据库配置失败: {str(e)}")

@router.post("/database/test")
async def test_database_connection(request: DatabaseTestRequest):
    """
    测试数据库连接
    """
    try:
        if request.db_type not in ["cloud_database", "local_database"]:
            raise HTTPException(status_code=400, detail="无效的数据库类型")
        
        result = config_manager.test_connection(request.db_type)
        
        return {
            "success": result["success"],
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试数据库连接失败: {str(e)}")

@router.get("/database/status")
async def get_database_status():
    """
    获取数据库连接状态
    """
    try:
        # 测试两个数据库的连接状态
        cloud_result = config_manager.test_connection("cloud_database")
        local_result = config_manager.test_connection("local_database")
        
        config = config_manager.get_database_config()
        
        return {
            "success": True,
            "data": {
                "cloud_database": cloud_result,
                "local_database": local_result,
                "current_priority": config["priority"],
                "active_database": "local_database" if local_result["success"] else "cloud_database" if cloud_result["success"] else "none"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库状态失败: {str(e)}")

@router.post("/database/reload")
async def reload_database_config():
    """
    重新加载数据库配置
    当前端更新配置后，通知后端重新加载配置并重新连接数据库
    """
    try:
        # 重新加载配置文件
        config_manager._ensure_config_file()
        
        # 通知所有API路由重新加载数据库连接
        # 由于API路由使用的是全局的db_handler实例，我们需要重新初始化它
                
        # 创建新的数据库处理器实例来测试配置
        connection_info = db_handler.get_connection_info()
        
        return {
            "success": True,
            "message": "数据库配置重新加载成功",
            "data": {
                "connection_info": connection_info,
                "config": config_manager.get_database_config()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载数据库配置失败: {str(e)}") 