"""
认证相关中间件
处理用户认证、会话管理和权限控制
"""

import time  # 添加time模块导入，用于记录开始时间
from flask import request, session, g, redirect, url_for, flash
from functools import wraps
from datetime import datetime
from ...models.user import User


def init_app(app):
    """
    初始化认证中间件

    Args:
        app: Flask应用实例
    """

    @app.before_request
    def load_user():
        """在请求处理前加载当前用户"""
        # 设置请求开始时间，用于性能监控
        g.start_time = time.time()

        # 从会话中获取用户ID
        user_id = session.get("user_id")

        # 将当前用户对象存储在g对象中，方便视图函数访问
        if user_id:
            user = User.query.get(user_id)
            if user:
                g.user = user
                # 更新用户最后活动时间
                user.last_seen = datetime.utcnow()
            else:
                # 用户ID无效，清除会话
                g.user = None
                session.pop("user_id", None)
        else:
            g.user = None

        # 设置当前请求的主题
        g.theme = session.get("theme", "harmony")

        # 记录请求信息到日志
        app.logger.info(
            f"Request: {request.method} {request.path} - User: {user_id or 'Anonymous'}"
        )


def login_required(f):
    """
    登录验证装饰器
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            # 保存请求的URL，以便登录后重定向回来
            next_url = request.url
            return redirect(url_for("web.login", next=next_url))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    管理员权限检查装饰器
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.is_admin:
            flash("该操作需要管理员权限", "error")
            return redirect(url_for("web.login"))
        return f(*args, **kwargs)

    return decorated_function


def permission_required(permission):
    """
    特定权限检查装饰器

    Args:
        permission: 需要的权限名称
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user or not g.user.has_permission(permission):
                flash(f"该操作需要{permission}权限", "error")
                return redirect(url_for("web.dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator