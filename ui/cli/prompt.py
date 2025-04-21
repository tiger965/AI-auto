# ui/cli/prompt.py
import os
import time
import readline
from .themes import get_current_theme
from .helpers import context_manager

# Global prompt configuration
_prompt_config = {
    "style": "default",
    "show_time": True,
    "show_status": True,
    "current_status": "ready",
    "show_path": True,
}


def setup_prompt(style="default", show_time=True, show_status=True, show_path=True):
    """Configure the command prompt appearance"""
    _prompt_config["style"] = style
    _prompt_config["show_time"] = show_time
    _prompt_config["show_status"] = show_status
    _prompt_config["show_path"] = show_path

    # 设置自动补全
    setup_autocomplete()


def get_prompt():
    """Generate the current command prompt string"""
    theme = get_current_theme()

    prompt_parts = []

    # Add time if enabled
    if _prompt_config["show_time"]:
        current_time = time.strftime("%H:%M:%S")
        prompt_parts.append(colorize(f"[{current_time}]", theme["time"]))

    # Add status if enabled
    if _prompt_config["show_status"]:
        # 使用上下文作为状态
        context = (
            context_manager.current_context
            if hasattr(context_manager, "current_context")
            else "ready"
        )
        status = context if context != "global" else _prompt_config["current_status"]
        status_color = theme["success"] if status == "ready" else theme["info"]
        prompt_parts.append(colorize(f"({status})", status_color))

    # Add current path if enabled
    if _prompt_config["show_path"]:
        current_path = os.path.basename(os.getcwd())
        prompt_parts.append(colorize(current_path, theme["path"]))

    # Add the prompt character based on style and context
    context = (
        context_manager.current_context
        if hasattr(context_manager, "current_context")
        else "global"
    )
    if context == "global":
        if _prompt_config["style"] == "default":
            prompt_char = colorize("$ ", theme["prompt"])
        elif _prompt_config["style"] == "power":
            prompt_char = colorize("» ", theme["prompt"])
        elif _prompt_config["style"] == "minimal":
            prompt_char = colorize("> ", theme["prompt"])
        else:
            prompt_char = colorize("$ ", theme["prompt"])
    else:
        # 非全局上下文使用不同的提示符
        prompt_char = colorize("» ", theme["prompt"])

    # Combine all parts
    return " ".join(prompt_parts) + " " + prompt_char


def set_status(status):
    """Update the current status displayed in the prompt"""
    _prompt_config["current_status"] = status


def colorize(text, color_code):
    """Apply ANSI color code to text"""
    return f"\033[{color_code}m{text}\033[0m"


def setup_autocomplete():
    """设置命令自动补全"""
    # 设置自动补全功能
    try:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(command_completer)
    except:
        print("警告: readline 模块不可用，自动补全功能被禁用")


def command_completer(text, state):
    """命令自动补全函数"""
    # 获取当前上下文中可用的命令建议
    suggestions = context_manager.suggest_commands(text)

    if state < len(suggestions):
        return suggestions[state]
    else:
        return None