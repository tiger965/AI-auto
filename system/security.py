"""
Security Module - Enhanced API Security
---------------------------------------
提供系统API安全功能，包括认证、授权、速率限制和日志记录。
此版本增强了对交易API的安全保障，添加了交易特定的安全措施。

Classes:
  - APISecurityManager: API安全管理器
  - RateLimiter: API请求速率限制器
  - AuthManager: 认证管理器
  - AccessControl: 访问控制管理器
  - TradingAPIGuard: 交易API特定安全防护 (新增)
"""

import hmac
import hashlib
import time
import re
import json
import base64
import uuid
import logging
import threading
import redis
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
import jwt
import secrets
import os

# 导入交易日志模块
from .trading_logger import TradingLogger, LogLevel

# 设置日志
logger = logging.getLogger('security')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 交易日志记录器实例
trading_logger = TradingLogger(log_dir="logs/trading")


class SecurityLevel(Enum):
    """安全级别枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RateLimiter:
    """API请求速率限制器"""
    
    def __init__(self, redis_client=None, default_limit=100, default_window=3600):
        """
        初始化速率限制器
        
        Args:
            redis_client: Redis客户端实例(用于分布式限流)
            default_limit: 默认请求限制数
            default_window: 默认时间窗口(秒)
        """
        self.use_redis = redis_client is not None
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window
        
        # 本地限流计数器(非分布式模式)
        self.counters = {}
        self.lock = threading.Lock()
        
        # 每个端点的限流配置
        self.endpoint_limits = {}
    
    def configure_endpoint(self, endpoint, limit, window=3600):
        """
        配置特定端点的限流规则
        
        Args:
            endpoint: API端点
            limit: 请求限制数
            window: 时间窗口(秒)
        """
        self.endpoint_limits[endpoint] = (limit, window)
    
    def is_allowed(self, client_id, endpoint):
        """
        检查请求是否允许通过限流
        
        Args:
            client_id: 客户端ID
            endpoint: 请求的API端点
            
        Returns:
            tuple: (是否允许, 剩余配额, 重置时间)
        """
        # 获取此端点的限流配置
        limit, window = self.endpoint_limits.get(
            endpoint, (self.default_limit, self.default_window)
        )
        
        # 构建计数器键
        key = f"{client_id}:{endpoint}"
        now = int(time.time())
        window_start = now - (now % window)
        window_key = f"{key}:{window_start}"
        
        if self.use_redis:
            # 分布式模式使用Redis
            count = self.redis.incr(window_key)
            
            # 如果是新计数器，设置过期时间
            if count == 1:
                self.redis.expire(window_key, window)
            
            # 获取过期时间
            ttl = self.redis.ttl(window_key)
            reset_time = now + ttl if ttl > 0 else now + window
            
            return count <= limit, limit - count, reset_time
        else:
            # 本地模式
            with self.lock:
                # 清理过期的计数器
                self._cleanup_expired_counters()
                
                # 获取或创建计数器
                if window_key not in self.counters:
                    self.counters[window_key] = {
                        'count': 0,
                        'expires': now + window
                    }
                
                # 增加计数
                self.counters[window_key]['count'] += 1
                count = self.counters[window_key]['count']
                reset_time = self.counters[window_key]['expires']
                
                return count <= limit, limit - count, reset_time
    
    def _cleanup_expired_counters(self):
        """清理过期的本地计数器"""
        now = int(time.time())
        expired_keys = [
            key for key, data in self.counters.items()
            if data['expires'] <= now
        ]
        
        for key in expired_keys:
            del self.counters[key]


class AuthManager:
    """认证管理器"""
    
    def __init__(self, jwt_secret=None, token_expiry=24*60*60):
        """
        初始化认证管理器
        
        Args:
            jwt_secret: JWT签名密钥
            token_expiry: 令牌过期时间(秒)
        """
        self.jwt_secret = jwt_secret or secrets.token_hex(32)
        self.token_expiry = token_expiry
        
        # API密钥存储 (实际项目中应使用数据库)
        self.api_keys = {}
        
        # 用户凭证存储 (实际项目中应使用数据库)
        self.user_credentials = {}
        
        # 活跃令牌存储
        self.active_tokens = {}
        
        # 吊销的令牌
        self.revoked_tokens = set()
    
    def generate_api_key(self, client_id, permissions=None):
        """
        为客户端生成API密钥
        
        Args:
            client_id: 客户端标识
            permissions: 权限列表
            
        Returns:
            tuple: (api_key, api_secret)
        """
        api_key = f"ak_{uuid.uuid4().hex}"
        api_secret = secrets.token_hex(32)
        
        # 存储API密钥信息
        self.api_keys[api_key] = {
            'client_id': client_id,
            'secret': api_secret,
            'permissions': permissions or [],
            'created_at': datetime.now().isoformat()
        }
        
        return api_key, api_secret
    
    def verify_api_key(self, api_key, api_secret):
        """
        验证API密钥
        
        Args:
            api_key: API密钥
            api_secret: API密钥密文
            
        Returns:
            dict or None: API密钥信息或验证失败返回None
        """
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key]
        if key_info['secret'] != api_secret:
            return None
        
        return key_info
    
    def verify_hmac_signature(self, api_key, signature, payload, timestamp):
        """
        验证HMAC签名
        
        Args:
            api_key: API密钥
            signature: 请求签名
            payload: 请求负载
            timestamp: 请求时间戳
            
        Returns:
            bool: 签名是否有效
        """
        if api_key not in self.api_keys:
            return False
        
        # 检查时间戳是否过期(5分钟内有效)
        try:
            ts = int(timestamp)
            now = int(time.time())
            if abs(now - ts) > 300:
                return False
        except:
            return False
        
        # 重新计算签名
        key_info = self.api_keys[api_key]
        secret = key_info['secret'].encode('utf-8')
        
        # 构建签名字符串
        if isinstance(payload, dict):
            payload = json.dumps(payload, sort_keys=True)
        
        message = f"{api_key}{timestamp}{payload}".encode('utf-8')
        expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        
        # 比较签名
        return hmac.compare_digest(signature, expected_signature)
    
    def create_jwt_token(self, user_id, additional_claims=None):
        """
        创建JWT令牌
        
        Args:
            user_id: 用户ID
            additional_claims: 额外的声明信息
            
        Returns:
            str: JWT令牌
        """
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=self.token_expiry)
        
        # 构建令牌声明
        claims = {
            'sub': str(user_id),
            'iat': now,
            'exp': expiry,
            'jti': str(uuid.uuid4())
        }
        
        # 添加额外声明
        if additional_claims:
            claims.update(additional_claims)
        
        # 签名并生成令牌
        token = jwt.encode(claims, self.jwt_secret, algorithm='HS256')
        
        # 记录活跃令牌
        self.active_tokens[claims['jti']] = {
            'user_id': user_id,
            'expires': expiry,
            'created_at': now
        }
        
        return token
    
    def verify_jwt_token(self, token):
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            dict or None: 令牌声明或验证失败返回None
        """
        try:
            # 解码并验证令牌
            claims = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # 检查令牌是否被吊销
            if claims.get('jti') in self.revoked_tokens:
                return None
            
            return claims
        except jwt.PyJWTError:
            return None
    
    def revoke_token(self, token):
        """
        吊销JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            bool: 是否成功吊销
        """
        try:
            # 解码令牌而不验证，以获取jti
            claims = jwt.decode(token, options={"verify_signature": False})
            jti = claims.get('jti')
            
            if jti:
                self.revoked_tokens.add(jti)
                if jti in self.active_tokens:
                    del self.active_tokens[jti]
                return True
            
            return False
        except:
            return False


class AccessControl:
    """访问控制管理器"""
    
    def __init__(self):
        """初始化访问控制管理器"""
        # 角色-权限映射
        self.role_permissions = {
            'admin': set(['read', 'write', 'delete', 'admin']),
            'trader': set(['read', 'trade']),
            'analyst': set(['read', 'analyze']),
            'viewer': set(['read'])
        }
        
        # 用户-角色映射
        self.user_roles = {}
        
        # 资源-权限映射
        self.resource_permissions = {}
    
    def assign_role(self, user_id, role):
        """
        给用户分配角色
        
        Args:
            user_id: 用户ID
            role: 角色名称
            
        Returns:
            bool: 是否成功分配
        """
        if role not in self.role_permissions:
            return False
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
            
        self.user_roles[user_id].add(role)
        return True
    
    def remove_role(self, user_id, role):
        """
        移除用户角色
        
        Args:
            user_id: 用户ID
            role: 角色名称
            
        Returns:
            bool: 是否成功移除
        """
        if user_id not in self.user_roles:
            return False
            
        if role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            return True
            
        return False
    
    def define_resource_permissions(self, resource, required_permissions):
        """
        定义资源所需的权限
        
        Args:
            resource: 资源标识
            required_permissions: 所需权限集合
        """
        self.resource_permissions[resource] = set(required_permissions)
    
    def check_permission(self, user_id, resource):
        """
        检查用户是否有权限访问资源
        
        Args:
            user_id: 用户ID
            resource: 资源标识
            
        Returns:
            bool: 是否有权限
        """
        # 如果资源没有权限定义，默认拒绝
        if resource not in self.resource_permissions:
            return False
            
        # 如果用户没有角色，拒绝访问
        if user_id not in self.user_roles:
            return False
            
        # 获取资源所需权限
        required_permissions = self.resource_permissions[resource]
        
        # 获取用户所有角色的所有权限
        user_permissions = set()
        for role in self.user_roles[user_id]:
            if role in self.role_permissions:
                user_permissions.update(self.role_permissions[role])
        
        # 检查是否拥有所有所需权限
        return required_permissions.issubset(user_permissions)
    
    def get_accessible_resources(self, user_id):
        """
        获取用户可访问的所有资源
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 可访问资源列表
        """
        # 如果用户没有角色，返回空列表
        if user_id not in self.user_roles:
            return []
            
        # 获取用户所有权限
        user_permissions = set()
        for role in self.user_roles[user_id]:
            if role in self.role_permissions:
                user_permissions.update(self.role_permissions[role])
        
        # 查找可访问的资源
        accessible = []
        for resource, required_permissions in self.resource_permissions.items():
            if required_permissions.issubset(user_permissions):
                accessible.append(resource)
                
        return accessible


class TradingAPIGuard:
    """交易API特定安全防护（新增）"""
    
    def __init__(self, auth_manager, rate_limiter, access_control):
        """
        初始化交易API防护
        
        Args:
            auth_manager: 认证管理器实例
            rate_limiter: 速率限制器实例
            access_control: 访问控制管理器实例
        """
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
        self.access_control = access_control
        
        # 交易操作风险级别定义
        self.operation_risk_levels = {
            'get_market_data': SecurityLevel.LOW,
            'analyze_strategy': SecurityLevel.LOW,
            'create_strategy': SecurityLevel.MEDIUM,
            'modify_strategy': SecurityLevel.MEDIUM,
            'place_order': SecurityLevel.HIGH,
            'cancel_order': SecurityLevel.MEDIUM,
            'withdraw_funds': SecurityLevel.CRITICAL
        }
        
        # 可疑模式检测计数器
        self.suspicious_activity = {}
        self.lock = threading.Lock()
        
        # 风险级别对应的额外验证方法
        self.security_level_checks = {
            SecurityLevel.LOW: self._basic_check,
            SecurityLevel.MEDIUM: self._medium_check,
            SecurityLevel.HIGH: self._high_security_check,
            SecurityLevel.CRITICAL: self._critical_security_check
        }
        
        # 交易最大金额限制
        self.transaction_limits = {
            'default': 10000.0,  # 默认最大交易金额
            'user_specific': {}  # 用户特定限制
        }
    
    def set_user_transaction_limit(self, user_id, limit):
        """
        设置用户特定的交易金额限制
        
        Args:
            user_id: 用户ID
            limit: 交易金额限制
        """
        self.transaction_limits['user_specific'][user_id] = float(limit)
    
    def get_transaction_limit(self, user_id):
        """
        获取用户的交易金额限制
        
        Args:
            user_id: 用户ID
            
        Returns:
            float: 交易金额限制
        """
        return self.transaction_limits['user_specific'].get(
            user_id, self.transaction_limits['default']
        )
    
    def secure_trading_operation(self, operation, user_id, client_ip, payload=None, security_context=None):
        """
        交易操作安全检查
        
        Args:
            operation: 操作类型
            user_id: 用户ID
            client_ip: 客户端IP
            payload: 操作参数
            security_context: 安全上下文(如会话ID、二次验证状态等)
            
        Returns:
            tuple: (是否允许操作, 拒绝原因)
        """
        # 获取操作风险级别
        risk_level = self.operation_risk_levels.get(operation, SecurityLevel.MEDIUM)
        
        # 基本权限检查
        operation_resource = f"trading:{operation}"
        if not self.access_control.check_permission(user_id, operation_resource):
            # 记录未授权尝试
            trading_logger.log_error(
                f"security_{user_id}",
                "Unauthorized trading operation attempt",
                {
                    "operation": operation,
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "timestamp": datetime.now().isoformat()
                }
            )
            return False, "Unauthorized operation"
        
        # 速率限制检查
        endpoint = f"trading/{operation}"
        allowed, remaining, reset_time = self.rate_limiter.is_allowed(user_id, endpoint)
        if not allowed:
            # 记录速率限制
            trading_logger.log_error(
                f"security_{user_id}",
                "Rate limit exceeded for trading operation",
                {
                    "operation": operation,
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "reset_time": reset_time
                }
            )
            return False, f"Rate limit exceeded. Try again after {datetime.fromtimestamp(reset_time)}"
        
        # 根据风险级别执行额外检查
        check_func = self.security_level_checks[risk_level]
        is_allowed, reason = check_func(operation, user_id, client_ip, payload, security_context)
        
        # 记录高风险操作
        if risk_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            trading_logger.log_strategy(
                f"security_{user_id}",
                f"HIGH_RISK_OPERATION_{operation.upper()}",
                {
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "risk_level": risk_level.name,
                    "allowed": is_allowed,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat()
                },
                LogLevel.WARNING if is_allowed else LogLevel.ERROR
            )
        
        return is_allowed, reason
    
    def _basic_check(self, operation, user_id, client_ip, payload, security_context):
        """
        基本安全检查(低风险操作)
        
        Returns:
            tuple: (是否允许, 原因)
        """
        # 对于低风险操作，基本权限检查已经足够
        return True, ""
    
    def _medium_check(self, operation, user_id, client_ip, payload, security_context):
        """
        中等级别安全检查
        
        Returns:
            tuple: (是否允许, 原因)
        """
        # 检查是否存在可疑活动模式
        suspicious = self._check_suspicious_activity(user_id, client_ip, operation)
        if suspicious:
            return False, "Suspicious activity pattern detected"
        
        # 检查会话有效性
        if not security_context or 'session_id' not in security_context:
            return False, "Valid session required"
        
        # 通过所有检查
        return True, ""
    
    def _high_security_check(self, operation, user_id, client_ip, payload, security_context):
        """
        高级别安全检查
        
        Returns:
            tuple: (是否允许, 原因)
        """
        # 首先执行中级检查
        allowed, reason = self._medium_check(operation, user_id, client_ip, payload, security_context)
        if not allowed:
            return allowed, reason
        
        # 检查交易金额限制
        if payload and 'amount' in payload:
            try:
                amount = float(payload['amount'])
                limit = self.get_transaction_limit(user_id)
                if amount > limit:
                    return False, f"Transaction amount exceeds limit of {limit}"
            except (ValueError, TypeError):
                return False, "Invalid transaction amount"
        
        # 检查是否需要二次验证
        if not security_context or not security_context.get('two_factor_verified'):
            return False, "Two-factor authentication required"
        
        # 通过所有检查
        return True, ""
    
    def _critical_security_check(self, operation, user_id, client_ip, payload, security_context):
        """
        关键级别安全检查
        
        Returns:
            tuple: (是否允许, 原因)
        """
        # 首先执行高级检查
        allowed, reason = self._high_security_check(operation, user_id, client_ip, payload, security_context)
        if not allowed:
            return allowed, reason
        
        # 检查最近的认证时间(要求15分钟内重新认证)
        if not security_context or 'last_auth_time' not in security_context:
            return False, "Recent authentication required"
        
        try:
            last_auth = datetime.fromisoformat(security_context['last_auth_time'])
            now = datetime.now()
            if (now - last_auth).total_seconds() > 900:  # 15分钟
                return False, "Recent authentication required (within 15 minutes)"
        except:
            return False, "Invalid authentication timestamp"
        
        # 检查是否来自已知设备
        if not security_context or not security_context.get('known_device'):
            return False, "Operation must be performed from a known device"
        
        # 通过所有检查
        return True, ""
    
    def _check_suspicious_activity(self, user_id, client_ip, operation):
        """
        检查可疑活动模式
        
        Returns:
            bool: 是否检测到可疑活动
        """
        with self.lock:
            key = f"{user_id}:{client_ip}"
            now = int(time.time())
            
            # 初始化计数器
            if key not in self.suspicious_activity:
                self.suspicious_activity[key] = {
                    'operations': [],
                    'last_check': now
                }
            
            # 添加操作记录
            self.suspicious_activity[key]['operations'].append({
                'op': operation,
                'time': now
            })
            
            # 仅保留最近30分钟的操作记录
            cutoff = now - 1800
            self.suspicious_activity[key]['operations'] = [
                op for op in self.suspicious_activity[key]['operations']
                if op['time'] >= cutoff
            ]
            
            # 可疑模式检测
            operations = self.suspicious_activity[key]['operations']
            
            # 1. 短时间内多次高风险操作
            high_risk_ops = [
                op for op in operations 
                if self.operation_risk_levels.get(op['op'], SecurityLevel.LOW) in 
                [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            ]
            
            if len(high_risk_ops) >= 5:  # 30分钟内5次或更多高风险操作
                return True
            
            # 2. 短时间内大量操作
            if len(operations) >= 50:  # 30分钟内50次或更多操作
                return True
            
            # 3. 多次快速重复相同操作
            op_counts = {}
            for op in operations:
                op_type = op['op']
                if op_type not in op_counts:
                    op_counts[op_type] = 0
                op_counts[op_type] += 1
            
            # 检查是否有任何操作超过阈值
            for op_type, count in op_counts.items():
                if count >= 20:  # 30分钟内20次或更多相同操作
                    return True
            
            # 未检测到可疑模式
            return False


class APISecurityManager:
    """API安全管理器"""
    
    def __init__(self, redis_client=None, jwt_secret=None):
        """
        初始化API安全管理器
        
        Args:
            redis_client: Redis客户端(用于分布式限流)
            jwt_secret: JWT签名密钥
        """
        # 初始化组件
        self.auth_manager = AuthManager(jwt_secret=jwt_secret)
        self.rate_limiter = RateLimiter(redis_client=redis_client)
        self.access_control = AccessControl()
        
        # 初始化交易API防护
        self.trading_guard = TradingAPIGuard(
            self.auth_manager, 
            self.rate_limiter, 
            self.access_control
        )
        
        # 配置基本速率限制
        self._configure_default_rate_limits()
        
        # 配置资源权限
        self._configure_resource_permissions()
    
    def _configure_default_rate_limits(self):
        """配置默认的API速率限制"""
        # 常规API端点
        self.rate_limiter.configure_endpoint('api/v1/market/data', 300, 60)  # 每分钟300次
        self.rate_limiter.configure_endpoint('api/v1/user/profile', 60, 60)  # 每分钟60次
        
        # 交易相关端点
        self.rate_limiter.configure_endpoint('trading/place_order', 30, 60)  # 每分钟30次
        self.rate_limiter.configure_endpoint('trading/cancel_order', 50, 60)  # 每分钟50次
        self.rate_limiter.configure_endpoint('trading/get_market_data', 500, 60)  # 每分钟500次
        self.rate_limiter.configure_endpoint('trading/create_strategy', 10, 60)  # 每分钟10次
    
    def _configure_resource_permissions(self):
        """配置资源权限"""
        # 交易相关资源
        self.access_control.define_resource_permissions('trading:get_market_data', {'read'})
        self.access_control.define_resource_permissions('trading:analyze_strategy', {'read', 'analyze'})
        self.access_control.define_resource_permissions('trading:create_strategy', {'read', 'trade'})
        self.access_control.define_resource_permissions('trading:modify_strategy', {'read', 'trade'})
        self.access_control.define_resource_permissions('trading:place_order', {'read', 'trade'})
        self.access_control.define_resource_permissions('trading:cancel_order', {'read', 'trade'})
        self.access_control.define_resource_permissions('trading:withdraw_funds', {'read', 'trade', 'withdraw'})
    
    def secure_api_request(self, endpoint, client_id, auth_data, request_data=None):
        """
        通用API请求安全验证
        
        Args:
            endpoint: API端点
            client_id: 客户端ID
            auth_data: 认证数据
            request_data: 请求数据
            
        Returns:
            tuple: (是否允许, 响应数据)
        """
        # 速率限制检查
        allowed, remaining, reset_time = self.rate_limiter.is_allowed(client_id, endpoint)
        if not allowed:
            logger.warning(f"Rate limit exceeded: {client_id} for {endpoint}")
            return False, {
                'error': 'rate_limit_exceeded',
                'message': 'API rate limit exceeded',
                'remaining': remaining,
                'reset': reset_time
            }
        
        # 认证检查
        auth_type = auth_data.get('type', 'none')
        
        if auth_type == 'api_key':
            api_key = auth_data.get('api_key')
            api_secret = auth_data.get('api_secret')
            
            if not api_key or not api_secret:
                return False, {'error': 'unauthorized', 'message': 'Missing API credentials'}
            
            key_info = self.auth_manager.verify_api_key(api_key, api_secret)
            if not key_info:
                logger.warning(f"Invalid API key: {api_key} for {endpoint}")
                return False, {'error': 'unauthorized', 'message': 'Invalid API credentials'}
            
            # 检查权限
            resource = endpoint.replace('/', ':')
            if not self.access_control.check_permission(key_info['client_id'], resource):
                logger.warning(f"Permission denied: {client_id} for {resource}")
                return False, {'error': 'forbidden', 'message': 'Permission denied'}
            
        elif auth_type == 'jwt':
            token = auth_data.get('token')
            
            if not token:
                return False, {'error': 'unauthorized', 'message': 'Missing authentication token'}
            
            claims = self.auth_manager.verify_jwt_token(token)
            if not claims:
                logger.warning(f"Invalid JWT token for {endpoint}")
                return False, {'error': 'unauthorized', 'message': 'Invalid or expired token'}
            
            # 检查权限
            user_id = claims['sub']
            resource = endpoint.replace('/', ':')
            if not self.access_control.check_permission(user_id, resource):
                logger.warning(f"Permission denied: {user_id} for {resource}")
                return False, {'error': 'forbidden', 'message': 'Permission denied'}
            
        elif auth_type == 'hmac':
            api_key = auth_data.get('api_key')
            signature = auth_data.get('signature')
            timestamp = auth_data.get('timestamp')
            
            if not api_key or not signature or not timestamp:
                return False, {'error': 'unauthorized', 'message': 'Missing HMAC authentication data'}
            
            # 验证HMAC签名
            payload_str = json.dumps(request_data) if request_data else ''
            if not self.auth_manager.verify_hmac_signature(api_key, signature, payload_str, timestamp):
                logger.warning(f"Invalid HMAC signature: {api_key} for {endpoint}")
                return False, {'error': 'unauthorized', 'message': 'Invalid signature'}
            
            # 获取API密钥信息
            key_info = self.api_keys.get(api_key)
            if not key_info:
                return False, {'error': 'unauthorized', 'message': 'Unknown API key'}
            
            # 检查权限
            resource = endpoint.replace('/', ':')
            if not self.access_control.check_permission(key_info['client_id'], resource):
                logger.warning(f"Permission denied: {key_info['client_id']} for {resource}")
                return False, {'error': 'forbidden', 'message': 'Permission denied'}
            
        else:
            # 未认证请求，检查是否为公开端点
            if not endpoint.startswith('public/'):
                return False, {'error': 'unauthorized', 'message': 'Authentication required'}
        
        # 通过所有检查
        return True, {'success': True, 'message': 'Request authorized'}
    
    def secure_trading_request(self, operation, user_id, client_ip, payload=None, security_context=None):
        """
        安全验证交易请求
        
        Args:
            operation: 交易操作
            user_id: 用户ID
            client_ip: 客户端IP
            payload: 请求负载
            security_context: 安全上下文
            
        Returns:
            tuple: (是否允许, 响应数据)
        """
        allowed, reason = self.trading_guard.secure_trading_operation(
            operation, user_id, client_ip, payload, security_context
        )
        
        if not allowed:
            logger.warning(f"Trading operation denied: {user_id}, {operation}, reason: {reason}")
            return False, {
                'error': 'operation_denied',
                'message': reason
            }
        
        return True, {'success': True, 'message': 'Operation authorized'}


# 示例用法
if __name__ == "__main__":
    # 创建安全管理器
    security_manager = APISecurityManager()
    
    # 创建用户角色
    security_manager.access_control.assign_role('user1', 'trader')
    security_manager.access_control.assign_role('user2', 'analyst')
    security_manager.access_control.assign_role('admin1', 'admin')
    
    # 设置交易限额
    security_manager.trading_guard.set_user_transaction_limit('user1', 50000)
    
    # 测试交易API请求
    security_context = {
        'session_id': 'sess_123456',
        'two_factor_verified': True,
        'last_auth_time': datetime.now().isoformat(),
        'known_device': True
    }
    
    # 下单请求
    allowed, response = security_manager.secure_trading_request(
        'place_order', 
        'user1', 
        '192.168.1.1', 
        {'symbol': 'AAPL', 'type': 'buy', 'amount': 25000}, 
        security_context
    )
    
    print(f"Place order request allowed: {allowed}")
    print(f"Response: {response}")
    
    # 资金提取请求(超限额)
    allowed, response = security_manager.secure_trading_request(
        'withdraw_funds', 
        'user1', 
        '192.168.1.1', 
        {'amount': 60000, 'destination': 'bank_account_1'}, 
        security_context
    )
    
    print(f"Withdraw funds request allowed: {allowed}")
    print(f"Response: {response}")