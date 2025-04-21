from flask import render_template, redirect, url_for, flash, request, session, abort, g
from system.security import generate_password_hash
from ..models.user import User
from ..models.chat import Chat, Message
from ..database import db
from . import forms
from ..auth.utils import get_current_user


def render_index():
    """渲染首页"""
    return render_template("web/index.html")


def render_login():
    """渲染登录页面"""
    form = forms.LoginForm()
    return render_template("web/login.html", form=form)


def render_register():
    """渲染注册页面"""
    form = forms.RegistrationForm()
    return render_template("web/register.html", form=form)


def process_registration():
    """处理注册表单数据"""
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        # 创建新用户
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
        )

        # 保存到数据库
        db.session.add(user)
        try:
            db.session.commit()
            flash("注册成功! 现在您可以登录了.", "success")
            return redirect(url_for("web.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"注册失败: {str(e)}", "error")

    # 表单验证失败，返回表单及错误信息
    return render_template("web/register.html", form=form)


def render_dashboard():
    """渲染用户仪表盘"""
    user = get_current_user()
    if not user:
        return redirect(url_for("web.login"))

    # 获取用户最近的聊天记录
    recent_chats = (
        Chat.query.filter_by(user_id=user.id)
        .order_by(Chat.updated_at.desc())
        .limit(5)
        .all()
    )

    return render_template("web/dashboard.html", user=user, recent_chats=recent_chats)


def render_assistant():
    """渲染AI助手界面"""
    user = get_current_user()

    # 创建或获取当前会话
    chat_id = request.args.get("chat_id")

    if chat_id:
        # 加载现有聊天
        chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first_or_404()
    else:
        # 创建新聊天
        chat = Chat(user_id=user.id, title="新对话")
        db.session.add(chat)
        db.session.commit()

    # 获取聊天消息
    messages = (
        Message.query.filter_by(chat_id=chat.id).order_by(
            Message.created_at).all()
    )

    # 准备聊天表单
    chat_form = forms.ChatForm()

    return render_template(
        "web/assistant.html", user=user, chat=chat, messages=messages, form=chat_form
    )


def render_chat_history():
    """渲染聊天历史列表"""
    user = get_current_user()

    # 分页获取聊天记录
    page = request.args.get("page", 1, type=int)
    per_page = 10

    chats = (
        Chat.query.filter_by(user_id=user.id)
        .order_by(Chat.updated_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    return render_template("web/chat_history.html", user=user, chats=chats)


def render_chat_detail(chat_id):
    """渲染单个聊天详情"""
    user = get_current_user()

    # 获取聊天及消息
    chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first_or_404()
    messages = (
        Message.query.filter_by(chat_id=chat.id).order_by(
            Message.created_at).all()
    )

    # 准备聊天表单
    chat_form = forms.ChatForm()

    return render_template(
        "web/chat_detail.html", user=user, chat=chat, messages=messages, form=chat_form
    )


def render_settings():
    """渲染用户设置页面"""
    user = get_current_user()

    # 创建设置表单，预填充用户数据
    form = forms.UserSettingsForm(
        original_username=user.username, original_email=user.email
    )

    form.username.data = user.username
    form.email.data = user.email
    form.theme.data = session.get("theme", "harmony")
    form.enable_sound.data = (
        user.preferences.get("enable_sound", True)
        if hasattr(user, "preferences") and user.preferences
        else True
    )
    form.bio.data = user.bio

    return render_template("web/settings.html", user=user, form=form)


def process_settings():
    """处理用户设置表单提交"""
    user = get_current_user()

    form = forms.UserSettingsForm(
        original_username=user.username, original_email=user.email
    )

    if form.validate_on_submit():
        # 更新用户信息
        user.username = form.username.data
        user.email = form.email.data
        user.bio = form.bio.data

        # 保存主题偏好到会话
        session["theme"] = form.theme.data

        # 处理头像上传
        if form.avatar.data:
            # 处理头像上传逻辑
            pass

        # 保存用户偏好设置
        if not hasattr(user, "preferences") or not user.preferences:
            user.preferences = {}
        user.preferences["theme"] = form.theme.data
        user.preferences["enable_sound"] = form.enable_sound.data

        try:
            db.session.commit()
            flash("设置已更新", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"设置更新失败: {str(e)}", "error")

    return render_template("web/settings.html", user=user, form=form)


def render_api_docs():
    """渲染API文档页面"""
    return render_template("web/api_docs.html")


def render_404():
    """渲染404错误页面"""
    return render_template("web/errors/404.html")


def render_500():
    """渲染500错误页面"""
    return render_template("web/errors/500.html")  # 视图渲染逻辑