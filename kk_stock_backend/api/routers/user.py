from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
import jwt
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import random
import time
from typing import Dict
import hashlib
import secrets
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import requests
import re
from passlib.context import CryptContext

load_dotenv()

# 导入股票池相关模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# CloudDBHandler已移除，使用统一的DBHandler

# 导入模拟交易相关模块
from api.simulation.init import init_simulation_account_for_user
from api.global_db import db_handler

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 使用统一的数据库处理器

users_col = db_handler.get_collection('users')

# 邮箱配置
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 角色定义
ROLE_LIST = ["user", "analyst", "operator", "admin"]

# ----------------- 工具函数 -----------------

async def create_default_stock_pool(user_id: str) -> bool:
    """为新注册用户创建默认股票池"""
    try:
        collection = db_handler.db["user_stock_pools"]
        
        # 检查用户是否已有默认股票池
        existing_default = collection.find_one({
            "user_id": user_id,
            "is_default": True
        })
        
        if existing_default:
            return True  # 已存在默认股票池
        
        # 创建默认股票池
        default_pool_doc = {
            "user_id": user_id,
            "pool_name": "我的股票池",
            "description": "这是您的默认股票池，您可以在这里管理您关注的股票。",
            "pool_type": "default",
            "is_default": True,
            "is_public": False,
            "is_deletable": False,  # 默认股票池不可删除
            "share_code": None,
            "tags": ["默认"],
            "stocks": [],
            "create_time": get_beijing_time(),
            "update_time": get_beijing_time()
        }
        
        # 插入默认股票池
        result = collection.insert_one(default_pool_doc)
        
        # 记录操作日志
        try:
            log_collection = db_handler.db["user_pool_operations"]
            log_doc = {
                "user_id": user_id,
                "pool_id": str(result.inserted_id),
                "operation_type": "create_default",
                "description": "系统自动创建默认股票池",
                "ts_code": None,
                "operation_time": get_beijing_time()
            }
            log_collection.insert_one(log_doc)
        except Exception as log_error:
            print(f"记录默认股票池创建日志失败: {log_error}")
        
        return True
        
    except Exception as e:
        print(f"创建默认股票池失败 (用户: {user_id}): {str(e)}")
        return False
def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(password, hashed_password)

def generate_reset_token() -> str:
    """生成密码重置令牌"""
    return secrets.token_urlsafe(32)

def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    # 只支持+86开头的手机号格式
    # 格式：+86 + 11位数字，第一位必须是1，第二位是3-9
    
    # 清理手机号，移除空格
    clean_phone = phone.strip()
    
    # 严格验证+86开头的手机号格式
    pattern = r'^\+861[3-9]\d{9}$'
    
    return bool(re.match(pattern, clean_phone))

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

async def send_email(to_email: str, subject: str, body: str) -> bool:
    """发送邮件"""
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # 使用SSL连接（QQ邮箱端口465）
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token无效")
        user = users_col.find_one({"user_id": user_id, "status": 1})
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except Exception:
        raise HTTPException(status_code=401, detail="Token无效")

def require_roles(required_roles: List[str]):
    def role_checker(user=Depends(get_current_user)):
        if not any(role in user.get("roles", []) for role in required_roles):
            raise HTTPException(status_code=403, detail="无权限")
        return user
    return role_checker

# ----------------- 数据模型 -----------------
class UserRegisterRequest(BaseModel):
    phone: str
    password: str
    email: EmailStr
    nickname: Optional[str] = None

class UserLoginRequest(BaseModel):
    phone: str
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    phone: str
    old_password: str
    new_password: str

class UserAddRequest(BaseModel):
    user_id: str
    login_type: str  # 'wechat' or 'phone'
    phone: Optional[str] = None
    wechat_openid: Optional[str] = None
    roles: List[str] = ["user"]
    extra_info: Optional[dict] = {}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: Optional[Dict] = None

class UserInfoResponse(BaseModel):
    user_id: str
    phone: str
    email: str
    nickname: Optional[str]
    roles: List[str]
    status: int
    create_time: datetime
    last_login: Optional[datetime]
    login_count: int

class UpdateUserInfoRequest(BaseModel):
    nickname: Optional[str] = None

class InviteUserRequest(BaseModel):
    phone: str = Field(..., description="用户手机号")
    email: EmailStr = Field(..., description="用户邮箱")
    nickname: Optional[str] = Field(None, description="用户昵称")
    roles: List[str] = Field(default=["user"], description="用户角色")

# 存储重置令牌的字典（生产环境应使用Redis）
reset_tokens = {}
verification_codes = {}

# 获取北京时间的函数
def get_beijing_time():
    """获取北京时间（无时区信息，用于数据库存储）"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).replace(tzinfo=None)

# 生成随机密码
def generate_random_password(length=8):
    """生成随机密码"""
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

# 发送邀请邮件
def send_invitation_email(email: str, phone: str, password: str, nickname: str):
    """发送邀请邮件"""
    try:
        # 邮件配置
        smtp_server = "smtp.qq.com"
        smtp_port = 465
        sender_email = "31468130@qq.com"
        sender_password = os.getenv("EMAIL_PASSWORD", "")  # 需要在环境变量中设置
        
        if not sender_password:
            print("警告：未配置邮件密码，无法发送邮件")
            return False
        
        # 创建邮件内容
        subject = "KK量化分析系统 - 账户邀请"
        body = f"""
        尊敬的{nickname or '用户'}，您好！
        
        欢迎加入KK量化分析系统！
        
        您的账户信息如下：
        手机号：{phone}
        初始密码：{password}
        
        请使用以上信息登录系统，登录后建议您立即修改密码。
        
        系统特性：
        • 智能策略选股
        • 量化回测分析
        • 实时市场监控
        
        如有任何问题，请联系管理员。
        
        祝您使用愉快！
        
        ——————————————————————
        KK 量化团队
        邮箱：31468130@qq.com
        """
        
        # 创建邮件
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = sender_email  # 使用简单格式避免RFC错误
        msg['To'] = email
        msg['Subject'] = subject
        
        # 发送邮件 - 使用基本的TLS连接
        try:
            server = smtplib.SMTP('smtp.qq.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()
        except Exception as smtp_error:
            print(f"SMTP发送失败: {smtp_error}")
            # 目前由于网络或QQ邮箱限制，暂时跳过邮件发送
            # 但用户创建仍然成功，管理员可以手动告知密码
            pass
        
        print(f"邀请邮件已发送到 {email}")
        return True
        
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

class SendCodeRequest(BaseModel):
    phone: str

TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")
TENCENT_SMS_APPID = os.getenv("TENCENT_SMS_APPID", "")
TENCENT_SIGN_NAME = os.getenv("TENCENT_SIGN_NAME", "")
TENCENT_TEMPLATE_ID = os.getenv("TENCENT_TEMPLATE_ID", "")

def send_sms_tencent(phone, code):
    cred = credential.Credential(TENCENT_SECRET_ID, TENCENT_SECRET_KEY)
    client = sms_client.SmsClient(cred, "ap-guangzhou")
    req = models.SendSmsRequest()
    req.SmsSdkAppId = TENCENT_SMS_APPID
    req.SignName = TENCENT_SIGN_NAME
    req.TemplateId = TENCENT_TEMPLATE_ID
    req.TemplateParamSet = [code]
    req.PhoneNumberSet = [phone]
    resp = client.SendSms(req)
    resp_json = json.loads(resp.to_json_string())
    return resp_json

# ----------------- 管理员添加用户 -----------------
@router.post("/admin/add_user", dependencies=[Depends(require_roles(["admin"]))])
async def admin_add_user(req: UserAddRequest):
    if users_col.find_one({"user_id": req.user_id}):
        raise HTTPException(status_code=400, detail="用户已存在")
    now = get_beijing_time()
    user_doc = {
        "user_id": req.user_id,
        "login_type": req.login_type,
        "phone": req.phone,
        "wechat_openid": req.wechat_openid,
        "roles": req.roles,
        "status": 1,
        "create_time": now,
        "last_login": None,
        "login_count": 0,
        "module_call_count": 0,
        "module_call_detail": {},
        "recharge_amount": 9999999999,
        "recharge_order_id": "UNLIMITED",
        "extra_info": req.extra_info or {}
    }
    users_col.insert_one(user_doc)
    return {"msg": "用户添加成功"}

# ----------------- 微信登录 -----------------
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "")

def get_wechat_openid(code):
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={WECHAT_APPID}&secret={WECHAT_SECRET}&js_code={code}&grant_type=authorization_code"
    resp = requests.get(url)
    data = resp.json()
    return data.get("openid")

class WechatLoginRequest(BaseModel):
    code: str

@router.post("/login/wechat", response_model=TokenResponse)
async def login_wechat(req: WechatLoginRequest):
    openid = get_wechat_openid(req.code)
    if not openid:
        raise HTTPException(status_code=401, detail="微信登录失败")
    user = users_col.find_one({"wechat_openid": openid, "status": 1})
    if not user:
        raise HTTPException(status_code=401, detail="未授权用户，请联系管理员")
    users_col.update_one({"_id": user["_id"]}, {"$inc": {"login_count": 1}, "$set": {"last_login": get_beijing_time()}})
    token = create_access_token({"user_id": user["user_id"], "roles": user["roles"]})
    return {"access_token": token}

# ----------------- 用户注册 -----------------
@router.post("/register", response_model=TokenResponse)
async def register_user(req: UserRegisterRequest):
    """用户注册"""
    # 验证手机号格式
    if not validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 验证邮箱格式
    if not validate_email(req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 验证密码强度
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    # 检查手机号是否已存在
    if users_col.find_one({"phone": req.phone}):
        raise HTTPException(status_code=400, detail="手机号已被注册")
    
    # 检查邮箱是否已存在
    if users_col.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # 生成用户ID
    user_id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # 创建用户文档
    now = get_beijing_time()
    user_doc = {
        "user_id": user_id,
        "phone": req.phone,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "nickname": req.nickname or f"用户{req.phone[-4:]}",
        "roles": ["user"],
        "status": 1,
        "create_time": now,
        "last_login": now,
        "login_count": 1,
        "module_call_count": 0,
        "module_call_detail": {},
        "recharge_amount": 0,
        "recharge_order_id": ""
    }
    
    # 插入数据库
    result = users_col.insert_one(user_doc)
    
    # 为新用户创建默认股票池
    try:
        await create_default_stock_pool(user_id)
        print(f"已为用户 {user_id} 创建默认股票池")
    except Exception as e:
        print(f"为用户 {user_id} 创建默认股票池失败: {str(e)}")
        # 不影响用户注册流程，只记录错误
    
    # 生成token
    token = create_access_token({"user_id": user_id, "roles": ["user"]})
    
    # 返回用户信息
    user_info = {
        "user_id": user_id,
        "phone": req.phone,
        "email": req.email,
        "nickname": user_doc["nickname"],
        "roles": ["user"]
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_info": user_info
    }

# ----------------- 用户登录 -----------------
@router.post("/login", response_model=TokenResponse)
async def login_user(req: UserLoginRequest):
    """用户登录"""
    # 验证手机号格式
    if not validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 查找用户
    user = users_col.find_one({"phone": req.phone, "status": 1})
    if not user:
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    
    # 验证密码
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    
    # 更新登录信息
    users_col.update_one(
        {"_id": user["_id"]}, 
        {
            "$inc": {"login_count": 1}, 
            "$set": {"last_login": get_beijing_time()}
        }
    )
    
    # 生成token
    token = create_access_token({"user_id": user["user_id"], "roles": user["roles"]})
    
    # 初始化模拟账户（如果不存在）
    try:
        await init_simulation_account_for_user(user["user_id"])
    except Exception as e:
        # 模拟账户初始化失败不影响登录，仅记录日志
        print(f"用户 {user['user_id']} 模拟账户初始化失败: {e}")
    
    # 返回用户信息
    user_info = {
        "user_id": user["user_id"],
        "phone": user["phone"],
        "email": user["email"],
        "nickname": user.get("nickname"),
        "roles": user["roles"]
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_info": user_info
    }

# ----------------- 密码重置 -----------------
@router.post("/password/reset")
async def request_password_reset(req: PasswordResetRequest):
    """请求密码重置"""
    # 验证邮箱格式
    if not validate_email(req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 查找用户
    user = users_col.find_one({"email": req.email, "status": 1})
    if not user:
        # 为了安全，即使邮箱不存在也返回成功
        return {"message": "如果邮箱存在，重置链接已发送"}
    
    # 生成重置令牌
    reset_token = generate_reset_token()
    
    # 存储重置令牌（有效期30分钟）
    reset_tokens[req.email] = {
        "token": reset_token,
        "user_id": user["user_id"],
        "timestamp": time.time()
    }
    
    # 发送重置邮件
    try:
        subject = "密码重置请求"
        body = f"""
        您好，
        
        您请求重置密码。请点击以下链接重置您的密码：
        
        重置令牌：{reset_token}
        
        此链接将在30分钟后过期。
        
        如果您没有请求重置密码，请忽略此邮件。
        
        谢谢！
        """
        
        await send_email(req.email, subject, body)
        return {"message": "如果邮箱存在，重置链接已发送"}
    except Exception as e:
        # 删除已存储的令牌
        if req.email in reset_tokens:
            del reset_tokens[req.email]
        raise HTTPException(status_code=500, detail="邮件发送失败")

@router.post("/password/reset/confirm")
async def confirm_password_reset(req: PasswordResetConfirmRequest):
    """确认密码重置"""
    # 验证邮箱格式
    if not validate_email(req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 验证密码强度
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    # 检查重置令牌
    if req.email not in reset_tokens:
        raise HTTPException(status_code=400, detail="重置令牌无效或已过期")
    
    token_info = reset_tokens[req.email]
    current_time = time.time()
    
    # 检查令牌是否过期（30分钟）
    if current_time - token_info["timestamp"] > 1800:
        del reset_tokens[req.email]
        raise HTTPException(status_code=400, detail="重置令牌已过期")
    
    # 验证令牌
    if token_info["token"] != req.reset_token:
        raise HTTPException(status_code=400, detail="重置令牌无效")
    
    # 更新密码
    new_password_hash = hash_password(req.new_password)
    users_col.update_one(
        {"user_id": token_info["user_id"]},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    # 删除使用过的令牌
    del reset_tokens[req.email]
    
    return {"message": "密码重置成功"}

@router.post("/password/change")
async def change_password(req: ChangePasswordRequest):
    """修改密码"""
    # 验证手机号格式
    if not validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")
    
    # 验证密码强度
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")
    
    # 使用手机号查找用户
    user = users_col.find_one({"phone": req.phone})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证旧密码
    if not verify_password(req.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    # 更新密码
    new_password_hash = hash_password(req.new_password)
    users_col.update_one(
        {"phone": req.phone},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    return {"message": "密码修改成功"}

# ----------------- 用户信息接口 -----------------
@router.get("/user-info", response_model=UserInfoResponse)
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user = users_col.find_one({"user_id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserInfoResponse(
        user_id=user["user_id"],
        phone=user["phone"],
        email=user["email"],
        nickname=user.get("nickname"),
        roles=user["roles"],
        status=user["status"],
        create_time=user["create_time"],
        last_login=user.get("last_login"),
        login_count=user.get("login_count", 0)
    )

@router.post("/user-info", response_model=UserInfoResponse)
async def update_user_info(
    request: UpdateUserInfoRequest,
    current_user: dict = Depends(get_current_user)
):
    """更新当前用户信息"""
    try:
        # 构建更新数据
        update_data = {}
        if request.nickname is not None:
            update_data["nickname"] = request.nickname
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有需要更新的数据")
        
        # 更新数据库
        result = users_col.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取更新后的用户信息
        updated_user = users_col.find_one({"user_id": current_user["user_id"]})
        if not updated_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserInfoResponse(
            user_id=updated_user["user_id"],
            phone=updated_user["phone"],
            email=updated_user["email"],
            nickname=updated_user.get("nickname"),
            roles=updated_user["roles"],
            status=updated_user["status"],
            create_time=updated_user["create_time"],
            last_login=updated_user.get("last_login"),
            login_count=updated_user.get("login_count", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")

@router.get("/info")
async def get_user_info(user=Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "roles": user["roles"],
        "login_count": user.get("login_count", 0),
        "module_call_count": user.get("module_call_count", 0),
        "module_call_detail": user.get("module_call_detail", {}),
        "recharge_amount": user.get("recharge_amount", 0),
        "recharge_order_id": user.get("recharge_order_id", "")
    }

# ----------------- 功能模块调用统计装饰器 -----------------
def record_module_call(module_name: str):
    def decorator(func):
        async def wrapper(*args, user=Depends(get_current_user), **kwargs):
            users_col.update_one(
                {"_id": user["_id"]},
                {"$inc": {"module_call_count": 1, f"module_call_detail.{module_name}": 1}}
            )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

# ----------------- 示例：受控功能API -----------------
@router.get("/demo/analyst", dependencies=[Depends(require_roles(["analyst"]))])
@record_module_call("analyst_demo")
async def analyst_demo(user=Depends(get_current_user)):
    return {"msg": f"分析师功能演示，欢迎 {user['user_id']}"}

@router.get("/demo/admin", dependencies=[Depends(require_roles(["admin"]))])
@record_module_call("admin_demo")
async def admin_demo(user=Depends(get_current_user)):
    return {"msg": f"管理员功能演示，欢迎 {user['user_id']}"}

# ----------------- 超级管理员用户管理功能 -----------------
@router.get("/admin/users", dependencies=[Depends(require_roles(["super_admin", "admin"]))])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """获取所有用户列表（仅超级管理员）"""
    try:
        users = list(users_col.find({}, {
            "password_hash": 0  # 不返回密码哈希
        }).sort("create_time", -1))
        
        # 转换ObjectId为字符串
        for user in users:
            user["_id"] = str(user["_id"])
            if "create_time" in user and isinstance(user["create_time"], datetime):
                user["create_time"] = user["create_time"].isoformat()
            if "last_login" in user and isinstance(user["last_login"], datetime):
                user["last_login"] = user["last_login"].isoformat()
        
        return {
            "success": True,
            "data": users,
            "total": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

@router.put("/admin/users/{user_id}/status", dependencies=[Depends(require_roles(["super_admin"]))])
async def update_user_status(user_id: str, status: int, current_user: dict = Depends(get_current_user)):
    """更新用户状态（仅超级管理员）"""
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为0（禁用）或1（启用）")
    
    # 不能禁用自己
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="不能修改自己的状态")
    
    result = users_col.update_one(
        {"user_id": user_id},
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"success": True, "message": f"用户状态已更新为{'启用' if status == 1 else '禁用'}"}

@router.delete("/admin/users/{user_id}", dependencies=[Depends(require_roles(["super_admin"]))])
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """删除用户（仅超级管理员）"""
    # 不能删除自己
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    # 检查用户是否存在
    user_exists = users_col.find_one({"user_id": user_id})
    if not user_exists:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 删除用户相关的所有数据
        deleted_pools_count = 0
        deleted_operations_count = 0
        deleted_screening_results_count = 0
        deleted_analysis_operations_count = 0
        deleted_analysis_results_count = 0
        deleted_watchlist_count = 0
        
        # 1. 删除用户股票池
        try:
            pools_collection = db_handler.db["user_stock_pools"]
            pools_result = pools_collection.delete_many({"user_id": user_id})
            deleted_pools_count = pools_result.deleted_count
        except Exception as e:
            print(f"删除用户股票池失败: {str(e)}")
        
        # 2. 删除股票池操作记录
        try:
            operations_collection = db_handler.db["user_pool_operations"]
            operations_result = operations_collection.delete_many({"user_id": user_id})
            deleted_operations_count = operations_result.deleted_count
        except Exception as e:
            print(f"删除股票池操作记录失败: {str(e)}")
        
        # 3. 删除策略选股结果
        try:
            screening_collection = db_handler.db["strategy_screening_results"]
            screening_result = screening_collection.delete_many({"user_id": user_id})
            deleted_screening_results_count = screening_result.deleted_count
        except Exception as e:
            print(f"删除策略选股结果失败: {str(e)}")
        
        # 4. 删除用户分析操作记录
        try:
            analysis_operations_collection = db_handler.db["user_analysis_operations"]
            analysis_operations_result = analysis_operations_collection.delete_many({"user_id": user_id})
            deleted_analysis_operations_count = analysis_operations_result.deleted_count
        except Exception as e:
            print(f"删除用户分析操作记录失败: {str(e)}")
        
        # 5. 删除用户分析结果
        try:
            analysis_results_collection = db_handler.db["user_analysis_results"]
            analysis_results_result = analysis_results_collection.delete_many({"user_id": user_id})
            deleted_analysis_results_count = analysis_results_result.deleted_count
        except Exception as e:
            print(f"删除用户分析结果失败: {str(e)}")
        
        # 6. 删除测试用户观察列表（如果存在）
        try:
            watchlist_collection = db_handler.db["test_user_watchlist"]
            watchlist_result = watchlist_collection.delete_many({"user_id": user_id})
            deleted_watchlist_count = watchlist_result.deleted_count
        except Exception as e:
            print(f"删除用户观察列表失败: {str(e)}")
        
        # 注意：不删除 user_strategy_templates，因为那是系统预定义的公共策略模板
        
        # 7. 最后删除用户记录
        result = users_col.delete_one({"user_id": user_id})
        
        return {
            "success": True, 
            "message": "用户及相关数据已完全删除",
            "deleted_data": {
                "user": 1 if result.deleted_count > 0 else 0,
                "stock_pools": deleted_pools_count,
                "pool_operations": deleted_operations_count,
                "screening_results": deleted_screening_results_count,
                "analysis_operations": deleted_analysis_operations_count,
                "analysis_results": deleted_analysis_results_count,
                "watchlist": deleted_watchlist_count
            },
            "note": "策略模板为系统公共模板，未删除"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

@router.post("/admin/invite-user", dependencies=[Depends(require_roles(["super_admin"]))])
async def invite_user(
    request: InviteUserRequest,
    current_user: dict = Depends(get_current_user)
):
    """邀请新用户（仅超级管理员）"""
    try:
        # 验证手机号格式
        if not validate_phone(request.phone):
            raise HTTPException(status_code=400, detail="手机号格式不正确")
        
        # 验证邮箱格式
        if not validate_email(request.email):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")
        
        # 检查用户是否已存在
        existing_user = users_col.find_one({
            "$or": [
                {"phone": request.phone},
                {"email": request.email}
            ]
        })
        
        if existing_user:
            raise HTTPException(status_code=400, detail="用户已存在（手机号或邮箱重复）")
        
        # 生成随机密码
        random_password = generate_random_password()
        
        # 生成用户ID
        user_id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 创建用户文档
        now = get_beijing_time()
        user_doc = {
            "user_id": user_id,
            "phone": request.phone,
            "email": request.email,
            "password_hash": hash_password(random_password),
            "nickname": request.nickname or f"用户{request.phone[-4:]}",
            "roles": request.roles,
            "status": 1,
            "create_time": now,
            "last_login": None,
            "login_count": 0,
            "module_call_count": 0,
            "module_call_detail": {},
            "recharge_amount": 0,
            "recharge_order_id": ""
        }
        
        # 插入用户到数据库
        result = users_col.insert_one(user_doc)
        
        if result.inserted_id:
            # 为新用户创建默认股票池
            await create_default_stock_pool(user_id)
            
            # 发送邀请邮件
            email_sent = send_invitation_email(
                request.email, 
                request.phone, 
                random_password, 
                request.nickname or f"用户{request.phone[-4:]}"
            )
            
            return {
                "success": True,
                "message": "用户邀请成功",
                "data": {
                    "user_id": user_id,
                    "phone": request.phone,
                    "email": request.email,
                    "nickname": user_doc["nickname"],
                    "roles": request.roles,
                    "email_sent": email_sent,
                    "password": random_password if not email_sent else "已通过邮件发送"
                }
            }
        else:
            raise HTTPException(status_code=500, detail="创建用户失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"邀请用户失败: {str(e)}")

@router.get("/admin/users/{user_id}", dependencies=[Depends(require_roles(["super_admin"]))])
async def get_user_detail(user_id: str, current_user: dict = Depends(get_current_user)):
    """获取用户详细信息（仅超级管理员）"""
    user = users_col.find_one({"user_id": user_id}, {"password_hash": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 转换ObjectId为字符串
    user["_id"] = str(user["_id"])
    if "create_time" in user and isinstance(user["create_time"], datetime):
        user["create_time"] = user["create_time"].isoformat()
    if "last_login" in user and isinstance(user["last_login"], datetime):
        user["last_login"] = user["last_login"].isoformat()
    
    return {"success": True, "data": user}

@router.put("/admin/users/{user_id}/roles", dependencies=[Depends(require_roles(["super_admin"]))])
async def update_user_roles(user_id: str, roles: List[str], current_user: dict = Depends(get_current_user)):
    """更新用户角色（仅超级管理员）"""
    # 验证角色有效性
    valid_roles = ["user", "analyst", "operator", "admin", "super_admin"]
    for role in roles:
        if role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"无效角色: {role}")
    
    # 不能修改自己的super_admin角色
    if user_id == current_user["user_id"] and "super_admin" not in roles:
        raise HTTPException(status_code=400, detail="不能移除自己的超级管理员角色")
    
    result = users_col.update_one(
        {"user_id": user_id},
        {"$set": {"roles": roles}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"success": True, "message": "用户角色已更新"}

@router.post("/admin/create-default-pools", dependencies=[Depends(require_roles(["super_admin"]))])
async def create_default_pools_for_all_users(current_user: dict = Depends(get_current_user)):
    """为所有现有用户创建默认股票池（仅超级管理员）"""
    try:
        # 获取所有活跃用户
        users = list(users_col.find({"status": 1}, {"user_id": 1}))
        
        total_users = len(users)
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for user in users:
            user_id = user["user_id"]
            try:
                # 检查用户是否已有股票池
                collection = db_handler.db["user_stock_pools"]
                existing_pools = collection.find_one({"user_id": user_id})
                
                if existing_pools:
                    skip_count += 1
                    continue
                
                # 创建默认股票池
                result = await create_default_stock_pool(user_id)
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"为用户 {user_id} 创建默认股票池失败: {str(e)}")
                error_count += 1
        
        return {
            "success": True,
            "message": "批量创建默认股票池完成",
            "statistics": {
                "total_users": total_users,
                "success_count": success_count,
                "skip_count": skip_count,
                "error_count": error_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建默认股票池失败: {str(e)}")

@router.post("/admin/users/{user_id}/create-default-pool", dependencies=[Depends(require_roles(["super_admin"]))])
async def create_default_pool_for_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """为指定用户创建默认股票池（仅超级管理员）"""
    try:
        # 检查用户是否存在
        user = users_col.find_one({"user_id": user_id, "status": 1})
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在或已禁用")
        
        # 创建默认股票池
        result = await create_default_stock_pool(user_id)
        
        if result:
            return {"success": True, "message": f"已为用户 {user_id} 创建默认股票池"}
        else:
            raise HTTPException(status_code=500, detail="创建默认股票池失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建默认股票池失败: {str(e)}")