# ui/cli/themes.py
import json
import os
import re
from pathlib import Path

# ANSI color codes
COLORS = {
    # 文本颜色
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    # 明亮文本颜色
    "bright_black": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
    # 背景颜色
    "bg_black": "40",
    "bg_red": "41",
    "bg_green": "42",
    "bg_yellow": "43",
    "bg_blue": "44",
    "bg_magenta": "45",
    "bg_cyan": "46",
    "bg_white": "47",
    # 明亮背景颜色
    "bg_bright_black": "100",
    "bg_bright_red": "101",
    "bg_bright_green": "102",
    "bg_bright_yellow": "103",
    "bg_bright_blue": "104",
    "bg_bright_magenta": "105",
    "bg_bright_cyan": "106",
    "bg_bright_white": "107",
    # 文本样式
    "bold": "1",
    "italic": "3",
    "underline": "4",
    "blink": "5",
    "inverse": "7",
}

# 预定义主题
_builtin_themes = {
    "default": {
        "name": "默认主题",
        "description": "经典的终端风格",
        "normal": COLORS["white"],
        "heading": COLORS["bright_white"] + ";" + COLORS["bold"],
        "key": COLORS["bright_cyan"],
        "value": COLORS["bright_green"],
        "error": COLORS["bright_red"],
        "warning": COLORS["bright_yellow"],
        "success": COLORS["bright_green"],
        "info": COLORS["bright_blue"],
        "string": COLORS["bright_yellow"],
        "number": COLORS["bright_magenta"],
        "prompt": COLORS["bright_green"] + ";" + COLORS["bold"],
        "time": COLORS["bright_blue"],
        "path": COLORS["bright_cyan"],
        "command_suggestion": COLORS["cyan"] + ";" + COLORS["italic"],
        "border": COLORS["blue"],
        "progress_bar": COLORS["bright_green"],
        "progress_background": COLORS["black"],
    },
    "dark": {
        "name": "暗黑主题",
        "description": "低调的暗色系统",
        "normal": COLORS["bright_white"],
        "heading": COLORS["bright_white"] + ";" + COLORS["bold"],
        "key": COLORS["bright_blue"],
        "value": COLORS["bright_green"],
        "error": COLORS["bright_red"],
        "warning": COLORS["yellow"],
        "success": COLORS["green"],
        "info": COLORS["blue"],
        "string": COLORS["yellow"],
        "number": COLORS["magenta"],
        "prompt": COLORS["green"] + ";" + COLORS["bold"],
        "time": COLORS["blue"],
        "path": COLORS["cyan"],
        "command_suggestion": COLORS["cyan"] + ";" + COLORS["italic"],
        "border": COLORS["bright_black"],
        "progress_bar": COLORS["blue"],
        "progress_background": COLORS["black"],
    },
    "light": {
        "name": "明亮主题",
        "description": "清新的浅色系统",
        "normal": COLORS["black"],
        "heading": COLORS["black"] + ";" + COLORS["bold"],
        "key": COLORS["blue"],
        "value": COLORS["green"],
        "error": COLORS["red"],
        "warning": COLORS["yellow"],
        "success": COLORS["green"],
        "info": COLORS["blue"],
        "string": COLORS["yellow"],
        "number": COLORS["magenta"],
        "prompt": COLORS["green"] + ";" + COLORS["bold"],
        "time": COLORS["blue"],
        "path": COLORS["cyan"],
        "command_suggestion": COLORS["cyan"] + ";" + COLORS["italic"],
        "border": COLORS["bright_black"],
        "progress_bar": COLORS["green"],
        "progress_background": COLORS["bright_black"],
    },
    "hacker": {
        "name": "黑客主题",
        "description": "经典的黑客风格",
        "normal": COLORS["bright_green"],
        "heading": COLORS["bright_green"] + ";" + COLORS["bold"],
        "key": COLORS["green"],
        "value": COLORS["bright_white"],
        "error": COLORS["bright_red"],
        "warning": COLORS["bright_yellow"],
        "success": COLORS["bright_green"],
        "info": COLORS["bright_cyan"],
        "string": COLORS["bright_white"],
        "number": COLORS["bright_cyan"],
        "prompt": COLORS["bright_green"] + ";" + COLORS["bold"],
        "time": COLORS["green"],
        "path": COLORS["bright_cyan"],
        "command_suggestion": COLORS["green"] + ";" + COLORS["italic"],
        "border": COLORS["green"],
        "progress_bar": COLORS["bright_green"],
        "progress_background": COLORS["black"],
    },
    "sunset": {
        "name": "日落主题",
        "description": "温暖的橙红色调",
        "normal": COLORS["white"],
        "heading": COLORS["bright_yellow"] + ";" + COLORS["bold"],
        "key": COLORS["bright_red"],
        "value": COLORS["yellow"],
        "error": COLORS["red"],
        "warning": COLORS["bright_yellow"],
        "success": COLORS["yellow"],
        "info": COLORS["bright_magenta"],
        "string": COLORS["bright_yellow"],
        "number": COLORS["yellow"],
        "prompt": COLORS["bright_red"] + ";" + COLORS["bold"],
        "time": COLORS["magenta"],
        "path": COLORS["bright_yellow"],
        "command_suggestion": COLORS["yellow"] + ";" + COLORS["italic"],
        "border": COLORS["red"],
        "progress_bar": COLORS["yellow"],
        "progress_background": COLORS["black"],
    },
    "ocean": {
        "name": "海洋主题",
        "description": "清凉的蓝绿色调",
        "normal": COLORS["white"],
        "heading": COLORS["bright_cyan"] + ";" + COLORS["bold"],
        "key": COLORS["bright_blue"],
        "value": COLORS["cyan"],
        "error": COLORS["red"],
        "warning": COLORS["yellow"],
        "success": COLORS["cyan"],
        "info": COLORS["bright_blue"],
        "string": COLORS["bright_cyan"],
        "number": COLORS["blue"],
        "prompt": COLORS["bright_blue"] + ";" + COLORS["bold"],
        "time": COLORS["cyan"],
        "path": COLORS["bright_cyan"],
        "command_suggestion": COLORS["cyan"] + ";" + COLORS["italic"],
        "border": COLORS["blue"],
        "progress_bar": COLORS["bright_cyan"],
        "progress_background": COLORS["black"],
    },
}

# 用户主题目录
USER_THEMES_DIR = os.path.expanduser("~/.window73/themes")

# 当前主题
_current_theme = "default"
_themes = _builtin_themes.copy()

# 主题改变事件处理器列表
_theme_change_handlers = []


def ensure_user_themes_dir():
    """确保用户主题目录存在"""
    Path(USER_THEMES_DIR).mkdir(parents=True, exist_ok=True)
    # 创建一个示例自定义主题文件，如果它不存在
    example_path = os.path.join(USER_THEMES_DIR, "example_custom.json")
    if not os.path.exists(example_path):
        with open(example_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "name": "示例自定义主题",
                    "description": "这是一个自定义主题示例",
                    "normal": COLORS["white"],
                    "heading": COLORS["bright_magenta"] + ";" + COLORS["bold"],
                    "key": COLORS["bright_blue"],
                    "value": COLORS["bright_green"],
                    "prompt": COLORS["bright_magenta"] + ";" + COLORS["bold"],
                },
                f,
                indent=4,
                ensure_ascii=False,
            )


def load_user_themes():
    """加载用户自定义主题"""
    ensure_user_themes_dir()

    for filename in os.listdir(USER_THEMES_DIR):
        if filename.endswith(".json"):
            theme_path = os.path.join(USER_THEMES_DIR, filename)
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    theme_data = json.load(f)

                # 创建主题ID
                theme_id = os.path.splitext(filename)[0]

                # 确保至少包含基本颜色
                if "name" in theme_data and "normal" in theme_data:
                    # 从默认主题获取缺失的颜色
                    complete_theme = _builtin_themes["default"].copy()
                    complete_theme.update(theme_data)

                    _themes[theme_id] = complete_theme
                    print(f"已加载自定义主题: {theme_data.get('name', theme_id)}")
            except Exception as e:
                print(f"加载主题 {filename} 时出错: {str(e)}")


def on_theme_change(handler):
    """注册主题更改事件处理器"""
    if handler not in _theme_change_handlers:
        _theme_change_handlers.append(handler)
    return True


def remove_theme_change_handler(handler):
    """移除主题更改事件处理器"""
    if handler in _theme_change_handlers:
        _theme_change_handlers.remove(handler)
    return True


def apply_theme(theme_name):
    """应用一个主题"""
    global _current_theme
    if theme_name in _themes:
        _current_theme = theme_name
        theme = _themes[theme_name]

        # 通知所有事件处理器
        for handler in _theme_change_handlers:
            try:
                handler(theme)
            except Exception as e:
                print(f"主题更改处理器错误: {str(e)}")

        return True
    return False


def get_current_theme():
    """获取当前主题颜色"""
    return _themes.get(_current_theme, _themes["default"])


def get_available_themes():
    """获取可用主题列表"""
    themes_list = []
    for theme_id, theme_data in _themes.items():
        themes_list.append(
            {
                "id": theme_id,
                "name": theme_data.get("name", theme_id),
                "description": theme_data.get("description", ""),
            }
        )
    return themes_list


def create_custom_theme(name, color_map):
    """创建新的自定义主题"""
    ensure_user_themes_dir()

    # 创建一个有效的文件名
    filename = re.sub(r"[^\w\-]", "_", name.lower()) + ".json"
    theme_path = os.path.join(USER_THEMES_DIR, filename)

    # 添加元数据
    theme_data = color_map.copy()
    theme_data["name"] = name
    theme_data.setdefault("description", f"自定义主题: {name}")

    # 保存主题文件
    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme_data, f, indent=4, ensure_ascii=False)

    # 重新加载主题
    theme_id = os.path.splitext(filename)[0]

    # 从默认主题获取缺失的颜色
    complete_theme = _builtin_themes["default"].copy()
    complete_theme.update(theme_data)

    _themes[theme_id] = complete_theme

    return theme_id


def delete_custom_theme(theme_id):
    """删除自定义主题"""
    # 内置主题不能被删除
    if theme_id in _builtin_themes:
        return False

    # 检查主题是否存在
    if theme_id not in _themes:
        return False

    # 检查主题文件是否存在
    theme_path = os.path.join(USER_THEMES_DIR, f"{theme_id}.json")
    if not os.path.exists(theme_path):
        return False

    # 如果当前正在使用该主题，先切换到默认主题
    if _current_theme == theme_id:
        apply_theme("default")

    # 删除主题文件
    os.remove(theme_path)

    # 从主题字典中移除
    if theme_id in _themes:
        del _themes[theme_id]

    return True


def export_theme(theme_id, export_path=None):
    """导出主题为JSON文件"""
    if theme_id not in _themes:
        return False

    theme_data = _themes[theme_id]

    # 如果没有指定导出路径，使用当前目录
    if export_path is None:
        export_path = os.path.join(os.getcwd(), f"{theme_id}_export.json")

    try:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(theme_data, f, indent=4, ensure_ascii=False)
        return export_path
    except Exception as e:
        print(f"导出主题时出错: {str(e)}")
        return False


def import_theme(import_path, new_name=None):
    """从JSON文件导入主题"""
    try:
        with open(import_path, "r", encoding="utf-8") as f:
            theme_data = json.load(f)

        # 验证主题数据
        if "normal" not in theme_data:
            print("无效的主题文件：缺少基本颜色定义")
            return False

        # 使用文件名或指定名称
        if new_name:
            theme_data["name"] = new_name
        elif "name" not in theme_data:
            file_base = os.path.basename(import_path)
            theme_data["name"] = os.path.splitext(file_base)[0]

        # 创建主题
        return create_custom_theme(theme_data["name"], theme_data)
    except Exception as e:
        print(f"导入主题时出错: {str(e)}")
        return False


def colorize(text, color_code):
    """应用ANSI颜色代码到文本"""
    if not color_code:
        return text
    return f"\033[{color_code}m{text}\033[0m"


def style_demo():
    """显示当前主题的样式演示"""
    theme = get_current_theme()
    demo = []

    demo.append(colorize("==== 主题样式演示 ====", theme["heading"]))
    demo.append("")

    demo.append(colorize("文本样式:", theme["heading"]))
    demo.append(f"  {colorize('普通文本', theme['normal'])}")
    demo.append(f"  {colorize('标题文本', theme['heading'])}")
    demo.append(
        f"  {colorize('键名文本', theme['key'])}: {colorize('值文本', theme['value'])}"
    )
    demo.append(f"  {colorize('错误文本', theme['error'])}")
    demo.append(f"  {colorize('警告文本', theme['warning'])}")
    demo.append(f"  {colorize('成功文本', theme['success'])}")
    demo.append(f"  {colorize('信息文本', theme['info'])}")
    demo.append("")

    demo.append(colorize("UI元素:", theme["heading"]))
    demo.append(f"  时间: {colorize('[12:34:56]', theme['time'])}")
    demo.append(f"  路径: {colorize('/home/user/projects', theme['path'])}")
    demo.append(f"  提示符: {colorize('$ ', theme['prompt'])}")
    demo.append(
        f"  命令建议: {colorize('try help command', theme['command_suggestion'])}"
    )
    demo.append(f"  字符串: {colorize('\"示例字符串\"', theme['string'])}")
    demo.append(f"  数值: {colorize('42', theme['number'])}")
    demo.append(f"  边框: {colorize('┌───────────┐', theme['border'])}")
    demo.append(
        f"  {colorize('│', theme['border'])} 进度条: {colorize('█████░░░░░', theme['progress_bar'])} {colorize('│', theme['border'])}"
    )
    demo.append(f"  {colorize('└───────────┘', theme['border'])}")

    return "\n".join(demo)


def generate_theme_preview(theme_id):
    """生成主题预览图"""
    if theme_id not in _themes:
        return None

    # 保存当前主题
    original_theme = _current_theme

    # 临时应用要预览的主题
    apply_theme(theme_id)

    # 生成预览
    preview = style_demo()

    # 恢复原来的主题
    apply_theme(original_theme)

    return preview


def modify_theme(theme_id, color_changes):
    """修改现有主题的颜色配置"""
    if theme_id not in _themes:
        return False

    # 不允许直接修改内置主题
    if theme_id in _builtin_themes:
        # 创建一个副本作为自定义主题
        theme_data = _themes[theme_id].copy()
        theme_data["name"] = f"{theme_data['name']} (自定义)"
        theme_data["description"] = f"基于 {theme_id} 主题的自定义版本"

        # 应用颜色更改
        theme_data.update(color_changes)

        # 创建新主题
        new_id = create_custom_theme(theme_data["name"], theme_data)
        return new_id
    else:
        # 更新自定义主题
        theme_data = _themes[theme_id]
        theme_data.update(color_changes)

        # 保存更改
        theme_path = os.path.join(USER_THEMES_DIR, f"{theme_id}.json")
        with open(theme_path, "w", encoding="utf-8") as f:
            json.dump(theme_data, f, indent=4, ensure_ascii=False)

        # 如果正在使用该主题，重新应用
        if _current_theme == theme_id:
            apply_theme(theme_id)

        return True


# 初始化时加载用户主题
load_user_themes()