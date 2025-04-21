from flask import Blueprint, request, redirect, url_for, flash, session, jsonify
from system.security import check_password_hash
from ..auth.decorators import login_required
from . import views
from ..models.user import User
from ..auth.utils import get_current_user
from ..database import db

# 创建Web蓝图
web_bp = Blueprint("web", __name__)


# 首页路由
@web_bp.route("/")
def index():
    return views.render_index()


# 登录页面
@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = "remember" in request.form

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("web.dashboard"))

        flash("用户名或密码不正确", "error")

    return views.render_login()


# 注册页面
@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 表单处理逻辑
        return views.process_registration()

    return views.render_register()


# 用户仪表盘
@web_bp.route("/dashboard")
@login_required
def dashboard():
    return views.render_dashboard()


# AI助手界面
@web_bp.route("/assistant")
@login_required
def assistant():
    return views.render_assistant()


# 聊天历史
@web_bp.route("/chat/history")
@login_required
def chat_history():
    return views.render_chat_history()


# 单个聊天会话
@web_bp.route("/chat/<int:chat_id>")
@login_required
def chat_detail(chat_id):
    return views.render_chat_detail(chat_id)


# 用户设置
@web_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        return views.process_settings()

    return views.render_settings()


# 主题切换
@web_bp.route("/theme/<theme_name>")
def set_theme(theme_name):
    if theme_name in ["harmony", "night"]:
        session["theme"] = theme_name
        # 如果用户已登录，保存到用户偏好
        user = get_current_user()
        if user and hasattr(user, "preferences"):
            if not user.preferences:
                user.preferences = {}
            user.preferences["theme"] = theme_name
            db.session.commit()
    return redirect(request.referrer or url_for("web.index"))


# 音效设置
@web_bp.route("/settings/sound/<int:enabled>")
@login_required
def set_sound(enabled):
    user = get_current_user()
    if user and hasattr(user, "preferences"):
        if not user.preferences:
            user.preferences = {}
        user.preferences["enable_sound"] = bool(enabled)
        db.session.commit()
    return jsonify({"success": True})