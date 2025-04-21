from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    TextAreaField,
    SelectField,
    FileField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from ..models.user import User


class LoginForm(FlaskForm):
    """用户登录表单"""

    username = StringField(
        "用户名",
        validators=[
            DataRequired(message="用户名不能为空"),
            Length(min=3, max=20, message="用户名长度必须在3-20个字符之间"),
        ],
    )
    password = PasswordField(
        "密码",
        validators=[
            DataRequired(message="密码不能为空"),
            Length(min=8, message="密码长度不能少于8个字符"),
        ],
    )
    remember = BooleanField("记住我")
    submit = SubmitField("登录")


class RegistrationForm(FlaskForm):
    """用户注册表单"""

    username = StringField(
        "用户名",
        validators=[
            DataRequired(message="用户名不能为空"),
            Length(min=3, max=20, message="用户名长度必须在3-20个字符之间"),
        ],
    )
    email = StringField(
        "电子邮箱",
        validators=[
            DataRequired(message="电子邮箱不能为空"),
            Email(message="请输入有效的电子邮箱地址"),
        ],
    )
    password = PasswordField(
        "密码",
        validators=[
            DataRequired(message="密码不能为空"),
            Length(min=8, message="密码长度不能少于8个字符"),
        ],
    )
    confirm_password = PasswordField(
        "确认密码",
        validators=[
            DataRequired(message="请确认密码"),
            EqualTo("password", message="两次输入的密码不一致"),
        ],
    )
    submit = SubmitField("注册")

    def validate_username(self, username):
        """验证用户名是否已存在"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("该用户名已被注册，请选择其他用户名")

    def validate_email(self, email):
        """验证邮箱是否已存在"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("该邮箱已被注册，请使用其他邮箱")


class UserSettingsForm(FlaskForm):
    """用户设置表单"""

    username = StringField(
        "用户名",
        validators=[
            DataRequired(message="用户名不能为空"),
            Length(min=3, max=20, message="用户名长度必须在3-20个字符之间"),
        ],
    )
    email = StringField(
        "电子邮箱",
        validators=[
            DataRequired(message="电子邮箱不能为空"),
            Email(message="请输入有效的电子邮箱地址"),
        ],
    )
    theme = SelectField(
        "界面主题", choices=[("harmony", "明亮主题"), ("night", "暗黑主题")]
    )
    enable_sound = BooleanField("启用音效")
    avatar = FileField("更新头像")
    bio = TextAreaField(
        "个人简介", validators=[Length(max=200, message="个人简介不能超过200个字符")]
    )
    submit = SubmitField("保存设置")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        """验证用户名是否被其他用户使用"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("该用户名已被注册，请选择其他用户名")

    def validate_email(self, email):
        """验证邮箱是否被其他用户使用"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("该邮箱已被注册，请使用其他邮箱")


class ChatForm(FlaskForm):
    """聊天输入表单"""

    message = TextAreaField(
        "消息",
        validators=[
            DataRequired(message="消息不能为空"),
            Length(max=2000, message="消息长度不能超过2000个字符"),
        ],
    )
    submit = SubmitField("发送")


class FeedbackForm(FlaskForm):
    """用户反馈表单"""

    subject = StringField(
        "主题",
        validators=[
            DataRequired(message="主题不能为空"),
            Length(max=100, message="主题不能超过100个字符"),
        ],
    )
    content = TextAreaField(
        "内容",
        validators=[
            DataRequired(message="内容不能为空"),
            Length(max=1000, message="内容不能超过1000个字符"),
        ],
    )
    category = SelectField(
        "分类",
        choices=[("bug", "错误报告"), ("feature", "功能建议"), ("general", "一般反馈")],
    )
    submit = SubmitField("提交反馈")


class SearchForm(FlaskForm):
    """搜索表单"""

    query = StringField(
        "搜索",
        validators=[
            DataRequired(message="搜索内容不能为空"),
            Length(min=2, message="搜索内容不能少于2个字符"),
        ],
    )
    submit = SubmitField("搜索")  # 表单处理和验证