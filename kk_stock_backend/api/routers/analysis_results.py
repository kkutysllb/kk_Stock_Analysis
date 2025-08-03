#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户分析结果管理API
提供趋势分析结果的存储、查询、管理等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from bson import ObjectId
import uuid

from api.routers.user import get_current_user, require_roles
from api.cache_middleware import cache_endpoint
from api.global_db import db_handler


# 创建路由器
router = APIRouter(prefix="/analysis-results", tags=["分析结果"])

# ==================== 数据模型 ====================

class AnalysisResultCreate(BaseModel):
    """创建分析结果请求"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    analysis_type: str = Field(..., description="分析类型", pattern="^(dow_theory|chan_theory|relative_valuation)$")
    overall_trend: str = Field(..., description="整体趋势")
    overall_phase: Optional[str] = Field(None, description="趋势阶段")
    confidence: float = Field(..., description="信心指数", ge=0, le=100)
    recommendation: str = Field(..., description="操作建议")
    detailed_analysis: Dict[str, Any] = Field(..., description="详细分析数据")
    tags: List[str] = Field(default_factory=list, description="标签")
    notes: Optional[str] = Field(None, description="备注")

class AnalysisResultUpdate(BaseModel):
    """更新分析结果请求"""
    tags: Optional[List[str]] = Field(None, description="标签")
    notes: Optional[str] = Field(None, description="备注")
    is_archived: Optional[bool] = Field(None, description="是否归档")

class AnalysisResultResponse(BaseModel):
    """分析结果响应"""
    result_id: str = Field(..., description="分析结果ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    analysis_type: str = Field(..., description="分析类型")
    overall_trend: str = Field(..., description="整体趋势")
    overall_phase: Optional[str] = Field(None, description="趋势阶段")
    confidence: float = Field(..., description="信心指数")
    recommendation: str = Field(..., description="操作建议")
    detailed_analysis: Dict[str, Any] = Field(..., description="详细分析数据")
    tags: List[str] = Field(..., description="标签")
    notes: Optional[str] = Field(None, description="备注")
    is_archived: bool = Field(..., description="是否归档")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")

class AnalysisResultSummary(BaseModel):
    """分析结果汇总"""
    result_id: str = Field(..., description="分析结果ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    analysis_type: str = Field(..., description="分析类型")
    overall_trend: str = Field(..., description="整体趋势")
    confidence: float = Field(..., description="信心指数")
    recommendation: str = Field(..., description="操作建议")
    create_time: datetime = Field(..., description="创建时间")

class BatchCreateAnalysisResultsRequest(BaseModel):
    """批量创建分析结果请求"""
    results: List[AnalysisResultCreate] = Field(..., description="分析结果列表")
    replace_existing: bool = Field(default=False, description="是否替换已存在的分析结果")

# ==================== API接口 ====================

@router.get("/", response_model=List[AnalysisResultSummary])
@cache_endpoint(data_type="user_analysis_results", ttl=60)  # 短期缓存，1分钟
async def get_user_analysis_results(
    current_user: dict = Depends(get_current_user),
    analysis_type: Optional[str] = Query(None, description="分析类型筛选"),
    stock_code: Optional[str] = Query(None, description="股票代码筛选"),
    recommendation: Optional[str] = Query(None, description="操作建议筛选"),
    start_date: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD)"),
    include_archived: bool = Query(False, description="是否包含归档数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取用户分析结果列表"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        # 构建查询条件
        query = {"user_id": current_user["user_id"]}
        
        if analysis_type:
            query["analysis_type"] = analysis_type
        
        if stock_code:
            query["stock_code"] = stock_code.upper()
        
        if recommendation:
            query["recommendation"] = recommendation
        
        if not include_archived:
            query["is_archived"] = {"$ne": True}
        
        # 日期范围筛选
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                date_filter["$lte"] = datetime.strptime(end_date, "%Y-%m-%d")
            query["create_time"] = date_filter
        
        # 分页查询
        skip = (page - 1) * page_size
        cursor = collection.find(
            query,
            {
                "result_id": 1,
                "stock_code": 1,
                "stock_name": 1,
                "analysis_type": 1,
                "overall_trend": 1,
                "confidence": 1,
                "recommendation": 1,
                "create_time": 1
            }
        ).sort("create_time", -1).skip(skip).limit(page_size)
        
        results = []
        for doc in cursor:
            result_summary = {
                "result_id": str(doc["_id"]),
                "stock_code": doc["stock_code"],
                "stock_name": doc["stock_name"],
                "analysis_type": doc["analysis_type"],
                "overall_trend": doc["overall_trend"],
                "confidence": doc["confidence"],
                "recommendation": doc["recommendation"],
                "create_time": doc["create_time"]
            }
            results.append(result_summary)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析结果列表失败: {str(e)}")

@router.get("/{result_id}", response_model=AnalysisResultResponse)
@cache_endpoint(data_type="user_analysis_result_detail", ttl=300)
async def get_analysis_result_detail(
    result_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取指定分析结果详情"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        # 查询分析结果
        result_doc = collection.find_one({
            "_id": ObjectId(result_id),
            "user_id": current_user["user_id"]
        })
        
        if not result_doc:
            raise HTTPException(status_code=404, detail="分析结果不存在或无权限访问")
        
        # 创建符合响应模型的数据
        result_response = {
            "result_id": str(result_doc["_id"]),
            "stock_code": result_doc["stock_code"],
            "stock_name": result_doc["stock_name"],
            "analysis_type": result_doc["analysis_type"],
            "overall_trend": result_doc["overall_trend"],
            "overall_phase": result_doc.get("overall_phase"),
            "confidence": result_doc["confidence"],
            "recommendation": result_doc["recommendation"],
            "detailed_analysis": result_doc["detailed_analysis"],
            "tags": result_doc.get("tags", []),
            "notes": result_doc.get("notes"),
            "is_archived": result_doc.get("is_archived", False),
            "create_time": result_doc["create_time"],
            "update_time": result_doc["update_time"]
        }
        
        return AnalysisResultResponse(**result_response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析结果详情失败: {str(e)}")

@router.post("/", response_model=AnalysisResultResponse)
async def create_analysis_result(
    result_data: AnalysisResultCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建新分析结果"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        # 检查是否已有相同股票在短时间内的分析结果（可选择替换）
        recent_threshold = datetime.utcnow().replace(minute=0, second=0, microsecond=0)  # 1小时内
        existing_result = collection.find_one({
            "user_id": current_user["user_id"],
            "stock_code": result_data.stock_code.upper(),
            "analysis_type": result_data.analysis_type,
            "create_time": {"$gte": recent_threshold}
        })
        
        if existing_result:
            # 更新现有结果而不是创建新的
            update_data = {
                "stock_name": result_data.stock_name,
                "overall_trend": result_data.overall_trend,
                "overall_phase": result_data.overall_phase,
                "confidence": result_data.confidence,
                "recommendation": result_data.recommendation,
                "detailed_analysis": result_data.detailed_analysis,
                "tags": result_data.tags,
                "notes": result_data.notes,
                "update_time": datetime.utcnow()
            }
            
            collection.update_one(
                {"_id": existing_result["_id"]},
                {"$set": update_data}
            )
            
            result_id = str(existing_result["_id"])
        else:
            # 创建新的分析结果文档
            result_doc = {
                "user_id": current_user["user_id"],
                "stock_code": result_data.stock_code.upper(),
                "stock_name": result_data.stock_name,
                "analysis_type": result_data.analysis_type,
                "overall_trend": result_data.overall_trend,
                "overall_phase": result_data.overall_phase,
                "confidence": result_data.confidence,
                "recommendation": result_data.recommendation,
                "detailed_analysis": result_data.detailed_analysis,
                "tags": result_data.tags,
                "notes": result_data.notes,
                "is_archived": False,
                "create_time": datetime.utcnow(),
                "update_time": datetime.utcnow()
            }
            
            # 插入数据库
            result = collection.insert_one(result_doc)
            result_id = str(result.inserted_id)
        
        # 记录操作日志
        await _log_analysis_operation(
            current_user["user_id"],
            result_id,
            "create" if not existing_result else "update",
            f"{'创建' if not existing_result else '更新'}分析结果: {result_data.stock_code} ({result_data.analysis_type})"
        )
        
        # 返回创建的分析结果
        return await get_analysis_result_detail(result_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分析结果失败: {str(e)}")

@router.put("/{result_id}", response_model=AnalysisResultResponse)
async def update_analysis_result(
    result_id: str,
    result_data: AnalysisResultUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新分析结果信息"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        # 检查分析结果是否存在且属于当前用户
        result_doc = collection.find_one({
            "_id": ObjectId(result_id),
            "user_id": current_user["user_id"]
        })
        
        if not result_doc:
            raise HTTPException(status_code=404, detail="分析结果不存在或无权限修改")
        
        # 构建更新数据
        update_data = {"update_time": datetime.utcnow()}
        
        if result_data.tags is not None:
            update_data["tags"] = result_data.tags
        
        if result_data.notes is not None:
            update_data["notes"] = result_data.notes
        
        if result_data.is_archived is not None:
            update_data["is_archived"] = result_data.is_archived
        
        # 更新数据库
        collection.update_one(
            {"_id": ObjectId(result_id)},
            {"$set": update_data}
        )
        
        # 记录操作日志
        await _log_analysis_operation(
            current_user["user_id"],
            result_id,
            "update",
            f"更新分析结果: {result_doc['stock_code']}"
        )
        
        # 返回更新后的分析结果
        return await get_analysis_result_detail(result_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新分析结果失败: {str(e)}")

@router.delete("/{result_id}")
async def delete_analysis_result(
    result_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除分析结果"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        # 检查分析结果是否存在且属于当前用户
        result_doc = collection.find_one({
            "_id": ObjectId(result_id),
            "user_id": current_user["user_id"]
        })
        
        if not result_doc:
            raise HTTPException(status_code=404, detail="分析结果不存在或无权限删除")
        
        # 删除分析结果
        collection.delete_one({"_id": ObjectId(result_id)})
        
        # 记录操作日志
        await _log_analysis_operation(
            current_user["user_id"],
            result_id,
            "delete",
            f"删除分析结果: {result_doc['stock_code']}"
        )
        
        return {"message": "分析结果删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除分析结果失败: {str(e)}")

@router.post("/batch", response_model=Dict[str, Any])
async def batch_create_analysis_results(
    request: BatchCreateAnalysisResultsRequest,
    current_user: dict = Depends(get_current_user)
):
    """批量创建分析结果"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        created_results = []
        updated_results = []
        failed_results = []
        
        for result_data in request.results:
            try:
                # 检查是否已有相同分析结果
                existing_result = None
                if not request.replace_existing:
                    recent_threshold = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                    existing_result = collection.find_one({
                        "user_id": current_user["user_id"],
                        "stock_code": result_data.stock_code.upper(),
                        "analysis_type": result_data.analysis_type,
                        "create_time": {"$gte": recent_threshold}
                    })
                
                if existing_result:
                    # 更新现有结果
                    update_data = {
                        "stock_name": result_data.stock_name,
                        "overall_trend": result_data.overall_trend,
                        "overall_phase": result_data.overall_phase,
                        "confidence": result_data.confidence,
                        "recommendation": result_data.recommendation,
                        "detailed_analysis": result_data.detailed_analysis,
                        "tags": result_data.tags,
                        "notes": result_data.notes,
                        "update_time": datetime.utcnow()
                    }
                    
                    collection.update_one(
                        {"_id": existing_result["_id"]},
                        {"$set": update_data}
                    )
                    updated_results.append(str(existing_result["_id"]))
                else:
                    # 创建新结果
                    result_doc = {
                        "user_id": current_user["user_id"],
                        "stock_code": result_data.stock_code.upper(),
                        "stock_name": result_data.stock_name,
                        "analysis_type": result_data.analysis_type,
                        "overall_trend": result_data.overall_trend,
                        "overall_phase": result_data.overall_phase,
                        "confidence": result_data.confidence,
                        "recommendation": result_data.recommendation,
                        "detailed_analysis": result_data.detailed_analysis,
                        "tags": result_data.tags,
                        "notes": result_data.notes,
                        "is_archived": False,
                        "create_time": datetime.utcnow(),
                        "update_time": datetime.utcnow()
                    }
                    
                    result = collection.insert_one(result_doc)
                    created_results.append(str(result.inserted_id))
                    
            except Exception as e:
                failed_results.append({
                    "stock_code": result_data.stock_code,
                    "error": str(e)
                })
        
        return {
            "message": "批量操作完成",
            "created_count": len(created_results),
            "updated_count": len(updated_results),
            "failed_count": len(failed_results),
            "created_results": created_results,
            "updated_results": updated_results,
            "failed_results": failed_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建分析结果失败: {str(e)}")

@router.get("/stats/summary")
async def get_analysis_stats(
    current_user: dict = Depends(get_current_user),
    analysis_type: Optional[str] = Query(None, description="分析类型筛选"),
    days: int = Query(30, description="统计天数", ge=1, le=365)
):
    """获取分析结果统计信息"""
    try:
        collection = db_handler.db["user_analysis_results"]
        
        # 构建查询条件
        query = {
            "user_id": current_user["user_id"],
            "create_time": {
                "$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - 
                        timedelta(days=days)
            }
        }
        
        if analysis_type:
            query["analysis_type"] = analysis_type
        
        # 聚合统计
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": {
                    "recommendation": "$recommendation",
                    "analysis_type": "$analysis_type"
                },
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"}
            }}
        ]
        
        stats_result = list(collection.aggregate(pipeline))
        
        # 整理统计数据
        stats = {
            "total_analysis": collection.count_documents(query),
            "by_recommendation": {},
            "by_analysis_type": {},
            "avg_confidence": 0
        }
        
        total_confidence = 0
        total_count = 0
        
        for item in stats_result:
            rec = item["_id"]["recommendation"]
            analysis_type = item["_id"]["analysis_type"]
            count = item["count"]
            avg_conf = item["avg_confidence"]
            
            if rec not in stats["by_recommendation"]:
                stats["by_recommendation"][rec] = 0
            stats["by_recommendation"][rec] += count
            
            if analysis_type not in stats["by_analysis_type"]:
                stats["by_analysis_type"][analysis_type] = 0
            stats["by_analysis_type"][analysis_type] += count
            
            total_confidence += avg_conf * count
            total_count += count
        
        if total_count > 0:
            stats["avg_confidence"] = round(total_confidence / total_count, 2)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析统计失败: {str(e)}")

# ==================== 辅助函数 ====================

async def _log_analysis_operation(
    user_id: str,
    result_id: str,
    operation_type: str,
    description: str
):
    """记录分析结果操作日志"""
    try:
        collection = db_handler.db["user_analysis_operations"]
        
        operation_doc = {
            "user_id": user_id,
            "result_id": result_id,
            "operation_type": operation_type,
            "description": description,
            "operation_time": datetime.utcnow()
        }
        
        collection.insert_one(operation_doc)
        
    except Exception as e:
        # 日志记录失败不应影响主要操作
        print(f"记录分析操作日志失败: {str(e)}")