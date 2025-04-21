from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, session
from ..models.user import User
from ..models.chat import Chat, Message
from ..database import db
from ..auth.utils import get_current_user
from ..ai.assistant import generate_response
import json
import time
from datetime import datetime

socketio = SocketIO()


@socketio.on("connect")
def handle_connect():
    """处理客户端连接"""
    user = get_current_user()
    if user:
        # 将用户加入自己的私人房间
        join_room(f"user_{user.id}")
        emit("connect_response", {"status": "connected", "user_id": user.id})
    else:
        # 未登录用户
        emit("connect_response", {"status": "unauthorized"})
        return False  # 拒绝连接


@socketio.on("disconnect")
def handle_disconnect():
    """处理客户端断开连接"""
    user = get_current_user()
    if user:
        leave_room(f"user_{user.id}")
        # 更新用户在线状态
        user.last_seen = datetime.utcnow()
        db.session.commit()


@socketio.on("join_chat")
def handle_join_chat(data):
    """用户加入特定聊天室"""
    user = get_current_user()
    chat_id = data.get("chat_id")

    if not user or not chat_id:
        emit("error", {"message": "未授权或缺少聊天ID"})
        return

    # 验证聊天室所有权
    chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        emit("error", {"message": "聊天不存在或无权访问"})
        return

    # 加入聊天室
    join_room(f"chat_{chat_id}")
    emit("chat_joined", {"chat_id": chat_id, "title": chat.title})


@socketio.on("leave_chat")
def handle_leave_chat(data):
    """用户离开特定聊天室"""
    chat_id = data.get("chat_id")
    if chat_id:
        leave_room(f"chat_{chat_id}")
        emit("chat_left", {"chat_id": chat_id})


@socketio.on("send_message")
def handle_send_message(data):
    """处理用户发送的消息"""
    user = get_current_user()
    chat_id = data.get("chat_id")
    content = data.get("content")

    if not user or not chat_id or not content:
        emit("error", {"message": "消息发送失败，缺少必要信息"})
        return

    # 验证聊天室所有权
    chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        emit("error", {"message": "聊天不存在或无权访问"})
        return

    # 创建用户消息
    user_message = Message(
        chat_id=chat_id, sender_id=user.id, content=content, is_from_ai=False
    )
    db.session.add(user_message)

    # 更新聊天最后活动时间
    chat.updated_at = datetime.utcnow()

    # 提交用户消息到数据库
    db.session.commit()

    # 广播用户消息到聊天室
    emit(
        "new_message",
        {
            "id": user_message.id,
            "chat_id": chat_id,
            "content": content,
            "sender_id": user.id,
            "sender_name": user.username,
            "is_from_ai": False,
            "timestamp": int(time.time()),
            "play_sound": "message",  # 添加这行
        },
        room=f"chat_{chat_id}",
    )

    # 异步生成AI响应
    emit("ai_typing", {"chat_id": chat_id}, room=f"chat_{chat_id}")

    # 获取历史消息以提供上下文
    recent_messages = (
        Message.query.filter_by(chat_id=chat_id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    context = [
        {"role": "user" if not msg.is_from_ai else "assistant", "content": msg.content}
        for msg in reversed(recent_messages)
    ]

    # 生成AI响应
    ai_response = generate_response(content, context)

    # 创建AI消息
    ai_message = Message(
        chat_id=chat_id,
        sender_id=None,  # AI没有用户ID
        content=ai_response,
        is_from_ai=True,
    )
    db.session.add(ai_message)

    # 更新聊天最后活动时间
    chat.updated_at = datetime.utcnow()

    # 如果是第一条消息，更新聊天标题
    if chat.title == "新对话" and len(content) < 30:
        chat.title = content
    elif chat.title == "新对话":
        chat.title = content[:30] + "..."

    db.session.commit()

    # 广播AI响应到聊天室
    emit(
        "new_message",
        {
            "id": ai_message.id,
            "chat_id": chat_id,
            "content": ai_response,
            "is_from_ai": True,
            "timestamp": int(time.time()),
            "play_sound": "ai_response",  # 添加这行
        },
        room=f"chat_{chat_id}",
    )

    # 异步生成AI响应
    emit("ai_typing", {"chat_id": chat_id}, room=f"chat_{chat_id}")

    # 获取历史消息以提供上下文
    recent_messages = (
        Message.query.filter_by(chat_id=chat_id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    context = [
        {"role": "user" if not msg.is_from_ai else "assistant", "content": msg.content}
        for msg in reversed(recent_messages)
    ]

    # 生成AI响应
    ai_response = generate_response(content, context)

    # 创建AI消息
    ai_message = Message(
        chat_id=chat_id,
        sender_id=None,  # AI没有用户ID
        content=ai_response,
        is_from_ai=True,
    )
    db.session.add(ai_message)

    # 更新聊天最后活动时间
    chat.updated_at = datetime.utcnow()

    # 如果是第一条消息，更新聊天标题
    if chat.title == "新对话" and len(content) < 30:
        chat.title = content
    elif chat.title == "新对话":
        chat.title = content[:30] + "..."

    db.session.commit()

    # 广播AI响应到聊天室
    emit(
        "new_message",
        {
            "id": ai_message.id,
            "chat_id": chat_id,
            "content": ai_response,
            "is_from_ai": True,
            "timestamp": int(time.time()),
        },
        room=f"chat_{chat_id}",
    )


@socketio.on("rename_chat")
def handle_rename_chat(data):
    """重命名聊天"""
    user = get_current_user()
    chat_id = data.get("chat_id")
    new_title = data.get("title")

    if not user or not chat_id or not new_title:
        emit("error", {"message": "重命名失败，缺少必要信息"})
        return

    # 验证聊天室所有权
    chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        emit("error", {"message": "聊天不存在或无权访问"})
        return

    # 更新聊天标题
    chat.title = new_title
    db.session.commit()

    # 广播聊天重命名事件
    emit(
        "chat_renamed", {"chat_id": chat_id, "title": new_title}, room=f"chat_{chat_id}"
    )

    # 也广播到用户的私人房间，更新其他页面上的聊天列表
    emit(
        "chat_updated", {"chat_id": chat_id, "title": new_title}, room=f"user_{user.id}"
    )


@socketio.on("delete_chat")
def handle_delete_chat(data):
    """删除聊天"""
    user = get_current_user()
    chat_id = data.get("chat_id")

    if not user or not chat_id:
        emit("error", {"message": "删除失败，缺少必要信息"})
        return

    # 验证聊天室所有权
    chat = Chat.query.filter_by(id=chat_id, user_id=user.id).first()
    if not chat:
        emit("error", {"message": "聊天不存在或无权访问"})
        return

    # 删除聊天及关联消息
    try:
        Message.query.filter_by(chat_id=chat_id).delete()
        db.session.delete(chat)
        db.session.commit()

        # 广播聊天删除事件到用户的私人房间
        emit("chat_deleted", {"chat_id": chat_id}, room=f"user_{user.id}")

        return {"status": "success"}
    except Exception as e:
        db.session.rollback()
        emit("error", {"message": f"删除失败: {str(e)}"})


@socketio.on("notification")
def handle_notification(data):
    """处理系统通知"""
    user_id = data.get("user_id")
    message = data.get("message")
    level = data.get("level", "info")  # info, warning, error

    if user_id and message:
        # 发送通知到特定用户
        emit(
            "notification",
            {"message": message, "level": level,
                "timestamp": int(time.time())},
            room=f"user_{user_id}",
        )


def send_system_notification(user_id, message, level="info"):
    """发送系统通知到特定用户"""
    socketio.emit(
        "notification",
        {"message": message, "level": level, "timestamp": int(time.time())},
        room=f"user_{user_id}",
    )


def broadcast_announcement(message, level="info"):
    """广播系统公告到所有连接的用户"""
    socketio.emit(
        "announcement",
        {"message": message, "level": level, "timestamp": int(time.time())},
    )


def init_app(app):
    """初始化SocketIO到Flask应用"""
    socketio.init_app(app, cors_allowed_origins="*")