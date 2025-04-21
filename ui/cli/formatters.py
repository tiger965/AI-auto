# ui/cli/formatters.py
import sys
import threading
import time
import re
import os
import json
from .themes import get_current_theme, colorize

# 全局设置
_settings = {
    "color_enabled": True,
    "animation_enabled": True,
    "accessibility_mode": False,
    "verbose_mode": False,
    "compact_mode": False,
    "sound_feedback": True,
}

# 主题更改事件处理器
_theme_change_handlers = []


def apply_theme_event(theme):
    """当主题改变时触发事件"""
    for handler in _theme_change_handlers:
        try:
            handler(theme)
        except Exception as e:
            print(f"主题处理器错误: {str(e)}")


def on_theme_change(handler):
    """注册主题更改事件处理器"""
    if handler not in _theme_change_handlers:
        _theme_change_handlers.append(handler)
    return True


def enable_color(enabled=True):
    """启用或禁用颜色"""
    _settings["color_enabled"] = enabled
    if not enabled:
        print("注意: 颜色输出已禁用，界面将使用纯文本模式")
    return _settings["color_enabled"]


def enable_animation(enabled=True):
    """启用或禁用动画效果"""
    _settings["animation_enabled"] = enabled
    return _settings["animation_enabled"]


def enable_accessibility_mode(enabled=True):
    """启用或禁用无障碍模式

    无障碍模式会:
    - 避免使用依赖视觉感知的UI元素
    - 提供更详细的文本描述
    - 使用更容易辨识的颜色方案
    """
    _settings["accessibility_mode"] = enabled
    if enabled:
        # 如果启用了无障碍模式，应用无障碍设置
        print("无障碍模式已启用，界面将优化以提高可访问性")
        # 导入并尝试加载无障碍主题
        from .themes import apply_theme

        apply_theme("light")  # 浅色主题通常对视障用户更友好
    return _settings["accessibility_mode"]


def set_verbose_mode(enabled=True):
    """设置详细输出模式"""
    _settings["verbose_mode"] = enabled
    return _settings["verbose_mode"]


def set_compact_mode(enabled=True):
    """设置紧凑输出模式"""
    _settings["compact_mode"] = enabled
    if enabled and _settings["verbose_mode"]:
        _settings["verbose_mode"] = False
        print("注意: 详细模式已被紧凑模式覆盖")
    return _settings["compact_mode"]


def enable_sound_feedback(enabled=True):
    """启用或禁用声音反馈"""
    _settings["sound_feedback"] = enabled
    try:
        from .sounds import enable_sound

        enable_sound(enabled)
    except ImportError:
        pass
    return _settings["sound_feedback"]


def safe_colorize(text, color_code):
    """安全地应用颜色到文本，如果禁用了颜色则返回原文本"""
    if _settings["color_enabled"]:
        return colorize(text, color_code)
    return text


class ProgressMonitor:
    """用于显示和更新进度的类"""

    def __init__(self, total, description="Processing", bar_length=50):
        self.total = total
        self.description = description
        self.bar_length = bar_length
        self.current = 0
        self.started = False
        self.stopped = False
        self._lock = threading.Lock()
        self._thread = None

        # 无障碍模式的声音反馈
        self.last_percent = 0
        self.sound_feedback = (
            _settings["accessibility_mode"] and _settings["sound_feedback"]
        )

    def start(self, update_interval=0.1):
        """开始进度监控"""
        self.started = True
        self.stopped = False

        def update_progress():
            while not self.stopped:
                self.update(self.current)
                time.sleep(update_interval)

        self._thread = threading.Thread(target=update_progress)
        self._thread.daemon = True
        self._thread.start()

        # 播放开始音效
        if self.sound_feedback:
            try:
                from .sounds import play_effect

                play_effect("notification")
            except ImportError:
                pass

    def update(self, current_value, suffix=""):
        """更新进度显示"""
        with self._lock:
            self.current = current_value
            if self.current > self.total:
                self.current = self.total

            percent = self.current / self.total if self.total > 0 else 0
            filled_length = int(self.bar_length * percent)

            theme = get_current_theme()

            # 处理无障碍模式
            if _settings["accessibility_mode"]:
                # 计算百分比变化
                current_percent_10s = int(percent * 10)  # 转为10%的增量
                if current_percent_10s > self.last_percent:
                    self.last_percent = current_percent_10s
                    # 播放进度提示音
                    if (
                        current_percent_10s > 0 and self.sound_feedback
                    ):  # 避免在开始时就播放
                        try:
                            from .sounds import play_effect

                            play_effect("progress")
                        except ImportError:
                            pass

                # 无障碍模式下使用文本描述
                progress_text = f"进度: {percent:.1%} ({self.current}/{self.total})"
                sys.stdout.write(
                    f"\r{self.description}: {progress_text} {suffix}")
                sys.stdout.flush()
                return

            # 标准图形化进度条
            desc = safe_colorize(self.description, theme["info"])

            if _settings["color_enabled"]:
                # 彩色进度条
                bar = ""
                for i in range(self.bar_length):
                    if i < filled_length:
                        bar += "█"
                    else:
                        bar += "░"
                bar = safe_colorize(bar, theme["progress_bar"])
            else:
                # 普通ASCII进度条
                bar = (
                    "["
                    + "#" * filled_length
                    + "-" * (self.bar_length - filled_length)
                    + "]"
                )

            prog = safe_colorize(f"{percent:.1%}", theme["value"])
            suffix_text = safe_colorize(
                suffix, theme["normal"]) if suffix else ""

            sys.stdout.write(f"\r{desc}: {bar} {prog} {suffix_text}")
            sys.stdout.flush()

    def stop(self):
        """停止进度监控"""
        self.stopped = True
        if self._thread:
            self._thread.join(1.0)
        sys.stdout.write("\n")
        sys.stdout.flush()

        # 播放完成音效
        if self.sound_feedback:
            try:
                from .sounds import play_effect

                play_effect("success")
            except ImportError:
                pass


def create_spinner(description="Processing"):
    """创建一个加载动画"""
    theme = get_current_theme()
    desc = safe_colorize(description, theme["info"])

    # 无障碍模式下使用不同的反馈机制
    if _settings["accessibility_mode"]:
        print(f"{description}... 正在处理")

        def stop():
            print(f"{description}... 完成")
            if _settings["sound_feedback"]:
                try:
                    from .sounds import play_effect

                    play_effect("notification")
                except ImportError:
                    pass

        return stop

    # 动画被禁用时使用静态提示
    if not _settings["animation_enabled"]:
        sys.stdout.write(f"{desc} ... ")
        sys.stdout.flush()

        def stop():
            sys.stdout.write("完成\n")
            sys.stdout.flush()

        return stop

    # 正常动画
    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    stop_spinner = False

    def spin():
        i = 0
        while not stop_spinner:
            with threading.Lock():
                sys.stdout.write(
                    f"\r{desc} {safe_colorize(spinner_chars[i], theme['value'])}"
                )
                sys.stdout.flush()
            i = (i + 1) % len(spinner_chars)
            time.sleep(0.1)

    thread = threading.Thread(target=spin)
    thread.daemon = True
    thread.start()

    def stop():
        nonlocal stop_spinner
        stop_spinner = True
        thread.join(1.0)
        sys.stdout.write("\r" + " " * (len(description) + 10) + "\r")  # 清除整行
        sys.stdout.flush()

    return stop


def interactive_menu(options, title="请选择一个选项", multi_select=False):
    """显示交互式菜单并返回用户选择"""
    theme = get_current_theme()

    # 无障碍模式下简化菜单
    if _settings["accessibility_mode"]:
        print(safe_colorize(title, theme["heading"]))
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")

        print(
            "\n请输入选项编号" + ("(多个选项用逗号分隔)" if multi_select else "") + ":"
        )

        # 播放提示音
        if _settings["sound_feedback"]:
            try:
                from .sounds import play_effect

                play_effect("notification")
            except ImportError:
                pass

        while True:
            try:
                choice = input("> ")

                if multi_select:
                    # 多选模式
                    try:
                        indices = [int(x.strip()) -
                                   1 for x in choice.split(",")]
                        valid = all(0 <= idx < len(options) for idx in indices)
                        if valid:
                            # 播放确认音
                            if _settings["sound_feedback"]:
                                try:
                                    from .sounds import play_effect

                                    play_effect("success")
                                except ImportError:
                                    pass
                            return indices
                        else:
                            print("某些选项无效，请重试。")
                            if _settings["sound_feedback"]:
                                try:
                                    from .sounds import play_effect

                                    play_effect("error")
                                except ImportError:
                                    pass
                    except ValueError:
                        print("格式错误，请使用逗号分隔的数字。")
                        if _settings["sound_feedback"]:
                            try:
                                from .sounds import play_effect

                                play_effect("error")
                            except ImportError:
                                pass
                else:
                    # 单选模式
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(options):
                            # 播放确认音
                            if _settings["sound_feedback"]:
                                try:
                                    from .sounds import play_effect

                                    play_effect("success")
                                except ImportError:
                                    pass
                            return idx
                        else:
                            print("无效的选择，请重试。")
                            if _settings["sound_feedback"]:
                                try:
                                    from .sounds import play_effect

                                    play_effect("error")
                                except ImportError:
                                    pass
                    except ValueError:
                        print("请输入有效的数字。")
                        if _settings["sound_feedback"]:
                            try:
                                from .sounds import play_effect

                                play_effect("error")
                            except ImportError:
                                pass
            except Exception as e:
                print(f"输入错误: {str(e)}")

        return -1

    # 标准交互式菜单
    print(safe_colorize(title, theme["heading"]))

    # 确定最长的选项文本长度
    max_len = max(len(str(option)) for option in options)

    # 计算适合屏幕的列数
    term_width = (
        os.get_terminal_size().columns if hasattr(os, "get_terminal_size") else 80
    )
    item_width = max_len + 10  # 为编号和边距添加额外空间
    cols = max(1, term_width // item_width)

    # 显示选项列表
    rows = (len(options) + cols - 1) // cols
    for row in range(rows):
        line = ""
        for col in range(cols):
            idx = row + col * rows
            if idx < len(options):
                option = options[idx]
                num = safe_colorize(f"{idx + 1:2d}", theme["key"])
                opt = safe_colorize(str(option), theme["normal"])
                item = f"{num}. {opt:<{max_len}} "
                line += item + " " * \
                    (item_width - len(item) - opt.count("\033"))
        print(line)

    # 添加多选提示
    if multi_select:
        print(
            safe_colorize("\n提示: 输入多个编号并用逗号分隔，如 1,3,5", theme["info"])
        )

    # 播放UI音效
    if _settings["sound_feedback"]:
        try:
            from .sounds import play_effect

            play_effect("notification")
        except ImportError:
            pass

    # 获取用户输入
    while True:
        try:
            prompt = safe_colorize("请输入选项编号: ", theme["prompt"])
            choice = input(prompt)

            if multi_select:
                # 多选模式
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(",")]
                    valid = all(0 <= idx < len(options) for idx in indices)
                    if valid:
                        # 播放确认音
                        if _settings["sound_feedback"]:
                            try:
                                from .sounds import play_effect

                                play_effect("success")
                            except ImportError:
                                pass
                        return indices
                    else:
                        error_msg = safe_colorize(
                            "某些选项无效，请重试。", theme["error"]
                        )
                        print(error_msg)
                        if _settings["sound_feedback"]:
                            try:
                                from .sounds import play_effect

                                play_effect("error")
                            except ImportError:
                                pass
                except ValueError:
                    error_msg = safe_colorize(
                        "格式错误，请使用逗号分隔的数字。", theme["error"]
                    )
                    print(error_msg)
                    if _settings["sound_feedback"]:
                        try:
                            from .sounds import play_effect

                            play_effect("error")
                        except ImportError:
                            pass
            else:
                # 单选模式
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        # 播放确认音
                        if _settings["sound_feedback"]:
                            try:
                                from .sounds import play_effect

                                play_effect("success")
                            except ImportError:
                                pass
                        return idx
                    else:
                        error_msg = safe_colorize(
                            "无效的选择，请重试。", theme["error"]
                        )
                        print(error_msg)
                        if _settings["sound_feedback"]:
                            try:
                                from .sounds import play_effect

                                play_effect("error")
                            except ImportError:
                                pass
                except ValueError:
                    error_msg = safe_colorize("请输入有效的数字。", theme["error"])
                    print(error_msg)
                    if _settings["sound_feedback"]:
                        try:
                            from .sounds import play_effect

                            play_effect("error")
                        except ImportError:
                            pass
        except Exception as e:
            print(f"输入错误: {str(e)}")

    return -1


def format_table(headers, rows, border=True):
    """格式化数据为表格"""
    theme = get_current_theme()

    # 无障碍模式使用简化表格
    if _settings["accessibility_mode"]:
        output = []
        for row in rows:
            row_data = []
            for i, cell in enumerate(row):
                row_data.append(f"{headers[i]}: {cell}")
            output.append(", ".join(row_data))

        return "\n".join(output)

    # 紧凑模式使用CSV风格
    if _settings["compact_mode"]:
        result = [",".join(headers)]
        for row in rows:
            result.append(",".join(str(cell) for cell in row))
        return "\n".join(result)

    # 计算列宽
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # 创建格式化行的函数
    def format_row(row, is_header=False):
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell).ljust(col_widths[i])
            if is_header:
                cells.append(safe_colorize(cell_str, theme["heading"]))
            else:
                cells.append(safe_colorize(cell_str, theme["normal"]))
        return "  ".join(cells)

    # 创建表格
    result = []

    # 添加上边框
    if border:
        top_border = "┌"
        for i, width in enumerate(col_widths):
            top_border += "─" * (width + 2)
            top_border += "┬" if i < len(col_widths) - 1 else "┐"
        result.append(safe_colorize(top_border, theme["border"]))

    # 添加表头
    if border:
        header_row = "│ "
        header_row += " │ ".join(
            safe_colorize(str(headers[i]).ljust(
                col_widths[i]), theme["heading"])
            for i in range(len(headers))
        )
        header_row += " │"
        result.append(header_row)

        # 添加分隔线
        separator = "├"
        for i, width in enumerate(col_widths):
            separator += "─" * (width + 2)
            separator += "┼" if i < len(col_widths) - 1 else "┤"
        result.append(safe_colorize(separator, theme["border"]))
    else:
        # 无边框表头
        result.append(format_row(headers, True))
        separator = "─" * \
            sum([w + 2 for w in col_widths] + [len(col_widths) - 1])
        result.append(safe_colorize(separator, theme["border"]))

    # 添加数据行
    for row in rows:
        if border:
            data_row = "│ "
            data_row += " │ ".join(
                str(row[i]).ljust(col_widths[i]) for i in range(len(row))
            )
            data_row += " │"
            result.append(data_row)
        else:
            result.append(format_row(row))

    # 添加下边框
    if border:
        bottom_border = "└"
        for i, width in enumerate(col_widths):
            bottom_border += "─" * (width + 2)
            bottom_border += "┴" if i < len(col_widths) - 1 else "┘"
        result.append(safe_colorize(bottom_border, theme["border"]))

    return "\n".join(result)


def format_json(data, indent=2):
    """格式化数据为彩色JSON"""
    theme = get_current_theme()

    # 无障碍模式或紧凑模式使用简化输出
    if _settings["accessibility_mode"] or _settings["compact_mode"]:
        indent = None if _settings["compact_mode"] else 2
        return json.dumps(data, ensure_ascii=False, indent=indent)

    # 彩色JSON输出
    if _settings["color_enabled"]:
        formatted = json.dumps(data, indent=indent, ensure_ascii=False)

        # 着色不同部分
        formatted = formatted.replace('"', safe_colorize('"', theme["string"]))
        formatted = re.sub(
            r"(true|false|null)",
            lambda m: safe_colorize(m.group(0), theme["value"]),
            formatted,
        )
        formatted = re.sub(
            r"(\d+)", lambda m: safe_colorize(m.group(0),
                                              theme["number"]), formatted
        )
        formatted = re.sub(
            r'("[^"]+"):',
            lambda m: safe_colorize(m.group(1), theme["key"]) + ":",
            formatted,
        )

        return formatted
    else:
        # 无颜色时使用基本格式化
        return json.dumps(data, indent=indent, ensure_ascii=False)


def format_box(text, title=None, style="single"):
    """在边框内显示文本"""
    theme = get_current_theme()

    # 无障碍模式使用简化输出
    if _settings["accessibility_mode"]:
        if title:
            return f"--- {title} ---\n{text}\n-----------"
        return f"---\n{text}\n---"

    # 紧凑模式省略边框
    if _settings["compact_mode"]:
        if title:
            return f"{title}:\n{text}"
        return text

    # 确定边框字符
    if style == "double":
        h_char, v_char = "═", "║"
        tl_char, tr_char = "╔", "╗"
        bl_char, br_char = "╚", "╝"
        tm_char, bm_char = "╤", "╧"
    elif style == "bold":
        h_char, v_char = "━", "┃"
        tl_char, tr_char = "┏", "┓"
        bl_char, br_char = "┗", "┛"
        tm_char, bm_char = "┯", "┷"
    else:  # single, default
        h_char, v_char = "─", "│"
        tl_char, tr_char = "┌", "┐"
        bl_char, br_char = "└", "┘"
        tm_char, bm_char = "┬", "┴"

    # 计算边框宽度
    lines = text.split("\n")
    width = max(len(line) for line in lines)
    if title and len(title) + 4 > width:
        width = len(title) + 4

    # 创建边框
    result = []

    # 添加顶部边框
    if title:
        # 带标题的顶部边框
        title_pos = (width - len(title)) // 2
        top_border = tl_char + h_char * (title_pos - 1) + tm_char
        top_border += h_char * (len(title) + 2) + tm_char
        top_border += h_char * (width - title_pos - len(title) - 1) + tr_char
        result.append(safe_colorize(top_border, theme["border"]))

        # 添加标题行
        title_line = v_char + " " * (title_pos - 1) + v_char
        title_line += " " + \
            safe_colorize(title, theme["heading"]) + " " + v_char
        title_line += " " * (width - title_pos - len(title) - 1) + v_char
        result.append(title_line)

        # 添加标题下的分隔线
        mid_border = v_char + h_char * (title_pos - 1) + bm_char
        mid_border += h_char * (len(title) + 2) + bm_char
        mid_border += h_char * (width - title_pos - len(title) - 1) + v_char
        result.append(safe_colorize(mid_border, theme["border"]))
    else:
        # 无标题的顶部边框
        top_border = tl_char + h_char * width + tr_char
        result.append(safe_colorize(top_border, theme["border"]))

    # 添加内容行
    for line in lines:
        padding = width - len(line)
        content_line = v_char + line + " " * padding + v_char
        result.append(content_line)

    # 添加底部边框
    bottom_border = bl_char + h_char * width + br_char
    result.append(safe_colorize(bottom_border, theme["border"]))

    return "\n".join(result)


def format_list(items, numbered=False, bullet="•"):
    """格式化列表"""
    theme = get_current_theme()

    if not items:
        return ""

    result = []
    for i, item in enumerate(items, 1):
        if numbered:
            prefix = f"{i}. "
            prefix = safe_colorize(prefix, theme["key"])
        else:
            prefix = f"{bullet} "
            prefix = safe_colorize(prefix, theme["key"])

        item_text = safe_colorize(str(item), theme["normal"])
        result.append(f"{prefix}{item_text}")

    return "\n".join(result)


def format_tree(data, indent=0, is_last=False, prefix=""):
    """格式化树状结构"""
    theme = get_current_theme()

    # 无障碍模式使用缩进表示层级
    if _settings["accessibility_mode"]:
        lines = []
        if isinstance(data, dict):
            for i, (key, value) in enumerate(data.items()):
                is_last_item = i == len(data) - 1
                # 添加当前节点
                lines.append(
                    "  " * indent +
                    ("└── " if is_last_item else "├── ") + str(key)
                )
                # 添加子节点
                if isinstance(value, (dict, list)):
                    sub_lines = format_tree(
                        value, indent + 1, is_last_item, "")
                    lines.append(sub_lines)
                else:
                    lines.append("  " * (indent + 1) + "└── " + str(value))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                is_last_item = i == len(data) - 1
                if isinstance(item, (dict, list)):
                    sub_lines = format_tree(item, indent, is_last_item, "")
                    lines.append(sub_lines)
                else:
                    lines.append(
                        "  " * indent +
                        ("└── " if is_last_item else "├── ") + str(item)
                    )
        else:
            lines.append("  " * indent + "└── " + str(data))
        return "\n".join(lines)

    # 定义连接符号
    if indent == 0:
        connector = ""
    else:
        if is_last:
            connector = "└── "
        else:
            connector = "├── "

    line = prefix + connector

    # 处理不同类型的数据
    if isinstance(data, dict):
        lines = []
        items = list(data.items())

        for i, (key, value) in enumerate(items):
            is_last_item = i == len(items) - 1
            key_str = safe_colorize(str(key), theme["key"])

            if isinstance(value, (dict, list)) and value:
                # 复杂值，需要递归
                lines.append(line + key_str + ":")

                # 确定下一级的前缀
                if indent > 0:
                    child_prefix = prefix + ("    " if is_last else "│   ")
                else:
                    child_prefix = prefix

                # 递归处理子节点
                sub_tree = format_tree(
                    value, indent + 1, is_last_item, child_prefix)
                lines.append(sub_tree)
            else:
                # 简单值
                if isinstance(value, str):
                    value_str = safe_colorize(f'"{value}"', theme["string"])
                elif isinstance(value, (int, float)):
                    value_str = safe_colorize(str(value), theme["number"])
                elif value is None:
                    value_str = safe_colorize("null", theme["value"])
                elif isinstance(value, bool):
                    value_str = safe_colorize(
                        str(value).lower(), theme["value"])
                else:
                    value_str = safe_colorize(str(value), theme["normal"])

                lines.append(line + key_str + ": " + value_str)

        return "\n".join(lines)

    elif isinstance(data, list):
        lines = []
        for i, item in enumerate(data):
            is_last_item = i == len(data) - 1

            if isinstance(item, (dict, list)) and item:
                # 递归处理子列表或字典
                sub_tree = format_tree(
                    item,
                    indent + 1,
                    is_last_item,
                    prefix + ("    " if is_last else "│   "),
                )
                lines.append(line + f"[{i}]:")
                lines.append(sub_tree)
            else:
                # 简单值
                if isinstance(item, str):
                    item_str = safe_colorize(f'"{item}"', theme["string"])
                elif isinstance(item, (int, float)):
                    item_str = safe_colorize(str(item), theme["number"])
                elif item is None:
                    item_str = safe_colorize("null", theme["value"])
                elif isinstance(item, bool):
                    item_str = safe_colorize(str(item).lower(), theme["value"])
                else:
                    item_str = safe_colorize(str(item), theme["normal"])

                lines.append(line + f"[{i}]: " + item_str)

        return "\n".join(lines)

    else:
        # 简单值
        if isinstance(data, str):
            data_str = safe_colorize(f'"{data}"', theme["string"])
        elif isinstance(data, (int, float)):
            data_str = safe_colorize(str(data), theme["number"])
        elif data is None:
            data_str = safe_colorize("null", theme["value"])
        elif isinstance(data, bool):
            data_str = safe_colorize(str(data).lower(), theme["value"])
        else:
            data_str = safe_colorize(str(data), theme["normal"])

        return line + data_str


def format_output(result):
    """格式化并显示命令输出"""
    if not result:
        return

    theme = get_current_theme()
    result_type = result.get("type", "text")

    # 声音反馈
    sound_feedback = _settings.get("sound_feedback", False)
    if sound_feedback:
        try:
            from .sounds import play_effect
        except ImportError:
            sound_feedback = False

    # 处理不同类型的结果
    if result_type == "exit":
        message = "Goodbye! CLI is shutting down."
        if _settings["accessibility_mode"]:
            message = "正在关闭命令行界面。再见！"

        print(safe_colorize(message, theme["success"]))
        if sound_feedback:
            play_effect("shutdown")
        exit(0)

    elif result_type == "error":
        content = result.get("content", "未知错误")
        if _settings["accessibility_mode"]:
            print(f"错误: {content}")
        else:
            print(safe_colorize(f"ERROR: {content}", theme["error"]))

        if sound_feedback:
            play_effect("error")

    elif result_type == "info":
        content = result.get("content", "")
        print(safe_colorize(content, theme["info"]))

        if sound_feedback:
            play_effect("notification")

    elif result_type == "help":
        # 帮助命令已在 commands.py 中处理输出
        if sound_feedback:
            play_effect("notification")

    elif result_type == "status":
        if _settings["accessibility_mode"]:
            print("系统状态:")
            for component, status in result.get("components", {}).items():
                print(f"- {component}: {status}")
        else:
            print(safe_colorize("系统状态", theme["heading"]))
            components = result.get("components", {})

            # 为状态选择合适的颜色
            for component, status in components.items():
                status_color = (
                    theme["success"]
                    if status in ["ready", "active", "online", "good"]
                    else theme["warning"]
                )
                print(
                    f"  {safe_colorize(component, theme['key'])}: {safe_colorize(status, status_color)}"
                )

        if sound_feedback:
            play_effect("notification")

    # 训练相关输出
    elif result_type == "training":
        if _settings["accessibility_mode"]:
            print("AI 模型训练")
            print(f"状态: {result.get('status', 'unknown')}")
            print("参数:")
            for param, value in result.get("params", {}).items():
                print(f"- {param}: {value}")

            if "message" in result:
                print(f"\n{result['message']}")
        else:
            print(safe_colorize("AI 模型训练", theme["heading"]))
            print(
                f"  {safe_colorize('状态', theme['key'])}: {safe_colorize(result.get('status', 'unknown'), theme['info'])}"
            )
            print(f"  {safe_colorize('参数', theme['key'])}:")
            for param, value in result.get("params", {}).items():
                print(
                    f"    {safe_colorize(param, theme['normal'])}: {safe_colorize(str(value), theme['value'])}"
                )

            if "message" in result:
                print(f"\n{safe_colorize(result['message'], theme['info'])}")

        if sound_feedback:
            play_effect("startup")

    elif result_type == "training_progress":
        if _settings["accessibility_mode"]:
            print("训练进度")
            status = result.get("status", "unknown")
            print(f"状态: {status}")

            progress = result.get("progress", {})
            current = progress.get("current_epoch", "?")
            total = progress.get("total_epochs", "?")
            percent = progress.get("percent", 0)
            elapsed = progress.get("elapsed_time", "00:00:00")

            print(f"当前周期: {current}/{total}")
            print(f"完成百分比: {percent:.1f}%")
            print(f"已用时间: {elapsed}")

            if "params" in result:
                print("\n训练参数:")
                for param, value in result.get("params", {}).items():
                    print(f"- {param}: {value}")
        else:
            print(safe_colorize("训练进度", theme["heading"]))

            status = result.get("status", "unknown")
            status_color = theme["success"] if status == "completed" else theme["info"]
            print(
                f"  {safe_colorize('状态', theme['key'])}: {safe_colorize(status, status_color)}"
            )

            progress = result.get("progress", {})
            print(
                f"  {safe_colorize('当前周期', theme['key'])}: {safe_colorize(str(progress.get('current_epoch', '?')), theme['value'])}/{safe_colorize(str(progress.get('total_epochs', '?')), theme['normal'])}"
            )
            print(
                f"  {safe_colorize('完成百分比', theme['key'])}: {safe_colorize(f'{progress.get('percent', 0):.1f}%', theme['value'])}"
            )
            print(
                f"  {safe_colorize('已用时间', theme['key'])}: {safe_colorize(progress.get('elapsed_time', '00:00:00'), theme['value'])}"
            )

            if "params" in result:
                print(f"\n  {safe_colorize('训练参数', theme['key'])}:")
                for param, value in result.get("params", {}).items():
                    print(
                        f"    {safe_colorize(param, theme['normal'])}: {safe_colorize(str(value), theme['value'])}"
                    )

        if sound_feedback and status == "completed":
            play_effect("success")

    # 模型信息输出
    elif result_type == "model_info":
        info = result.get("info", {})

        if _settings["accessibility_mode"]:
            print("模型信息")
            print(f"名称: {info.get('name', 'Unknown')}")
            print(f"版本: {info.get('version', 'Unknown')}")
            print(f"参数量: {info.get('parameters', 'Unknown')}")

            print("\n架构:")
            for k, v in info.get("architecture", {}).items():
                print(f"- {k}: {v}")

            print("\n训练:")
            for k, v in info.get("training", {}).items():
                print(f"- {k}: {v}")

            print("\n性能:")
            for k, v in info.get("performance", {}).items():
                print(f"- {k}: {v}")
        else:
            print(safe_colorize("模型信息", theme["heading"]))

            print(
                f"  {safe_colorize('名称', theme['key'])}: {safe_colorize(info.get('name', 'Unknown'), theme['value'])}"
            )
            print(
                f"  {safe_colorize('版本', theme['key'])}: {safe_colorize(info.get('version', 'Unknown'), theme['value'])}"
            )
            print(
                f"  {safe_colorize('参数量', theme['key'])}: {safe_colorize(info.get('parameters', 'Unknown'), theme['value'])}"
            )

            print(f"\n  {safe_colorize('架构', theme['heading'])}")
            for k, v in info.get("architecture", {}).items():
                print(
                    f"    {safe_colorize(k, theme['key'])}: {safe_colorize(str(v), theme['value'])}"
                )

            print(f"\n  {safe_colorize('训练', theme['heading'])}")
            for k, v in info.get("training", {}).items():
                print(
                    f"    {safe_colorize(k, theme['key'])}: {safe_colorize(str(v), theme['value'])}"
                )

            print(f"\n  {safe_colorize('性能', theme['heading'])}")
            for k, v in info.get("performance", {}).items():
                print(
                    f"    {safe_colorize(k, theme['key'])}: {safe_colorize(str(v), theme['value'])}"
                )

        if sound_feedback:
            play_effect("notification")

    # 可视化输出
    elif result_type == "visualization":
        viz_type = result.get("viz_type", "")
        data = result.get("data", [])

        if viz_type == "performance":
            if _settings["accessibility_mode"]:
                print("性能可视化")
                print("周期\t训练损失\t验证损失\t准确率")
                for entry in data:
                    print(
                        f"{entry.get('epoch', '?')}\t{entry.get('train_loss', 0):.4f}\t{entry.get('val_loss', 0):.4f}\t{entry.get('accuracy', 0):.4f}"
                    )
            else:
                print(safe_colorize("性能可视化", theme["heading"]))

                # 打印表格
                headers = ["周期", "训练损失", "验证损失", "准确率"]
                rows = []
                for entry in data:
                    rows.append(
                        [
                            entry.get("epoch", "?"),
                            f"{entry.get('train_loss', 0):.4f}",
                            f"{entry.get('val_loss', 0):.4f}",
                            f"{entry.get('accuracy', 0):.4f}",
                        ]
                    )

                table = format_table(headers, rows, border=True)
                print(table)

                print(
                    f"\n{safe_colorize('提示: 使用 \"visualize --type=attention\" 查看注意力可视化', theme['command_suggestion'])}"
                )

        elif viz_type == "attention":
            print(safe_colorize("注意力权重可视化", theme["heading"]))

            if _settings["accessibility_mode"]:
                print("注意力矩阵 (每行的值表示该位置对其他位置的注意力权重):")
                for i, row in enumerate(data):
                    print(f"位置 {i+1}: {', '.join(f'{w:.2f}' for w in row)}")
            else:
                # 创建一个简单的热力图
                print("  " + safe_colorize("注意力热力图:", theme["normal"]))

                for row in data:
                    # 为每个权重创建不同强度的块
                    blocks = []
                    for weight in row:
                        # 将权重映射到不同的块字符
                        if weight < 0.1:
                            block = "░"
                        elif weight < 0.3:
                            block = "▒"
                        elif weight < 0.5:
                            block = "▓"
                        else:
                            block = "█"

                        # 根据权重选择颜色
                        if weight < 0.2:
                            color = "blue"
                        elif weight < 0.4:
                            color = "cyan"
                        elif weight < 0.6:
                            color = "green"
                        elif weight < 0.8:
                            color = "yellow"
                        else:
                            color = "red"

                        blocks.append(safe_colorize(block * 2, color))

                    print("  " + "".join(blocks))

                print(
                    f"\n{safe_colorize('提示: 使用 \"visualize --type=performance\" 查看性能指标', theme['command_suggestion'])}"
                )

        if sound_feedback:
            play_effect("notification")

    # 评估输出
    elif result_type == "evaluation":
        if _settings["accessibility_mode"]:
            print("模型评估")
            print(f"状态: {result.get('status', 'unknown')}")

            if "metrics" in result:
                print("\n评估指标:")
                for metric, value in result.get("metrics", {}).items():
                    print(f"- {metric}: {value}")
        else:
            print(safe_colorize("模型评估", theme["heading"]))
            print(
                f"  {safe_colorize('状态', theme['key'])}: {safe_colorize(result.get('status', 'unknown'), theme['info'])}"
            )

            if "metrics" in result:
                print(f"\n  {safe_colorize('评估指标', theme['heading'])}")
                for metric, value in result.get("metrics", {}).items():
                    print(
                        f"    {safe_colorize(metric, theme['key'])}: {safe_colorize(str(value), theme['value'])}"
                    )

        if sound_feedback and result.get("status") == "completed":
            play_effect("success")

    # 部署输出
    elif result_type == "deployment":
        if _settings["accessibility_mode"]:
            print("模型部署")
            print(f"状态: {result.get('status', 'unknown')}")

            if "details" in result:
                print("\n部署详情:")
                for key, value in result.get("details", {}).items():
                    if key == "monitoring":
                        print("- 监控数据:")
                        for m_key, m_value in value.items():
                            print(f"  - {m_key}: {m_value}")
                    else:
                        print(f"- {key}: {value}")
        else:
            print(safe_colorize("模型部署", theme["heading"]))
            print(
                f"  {safe_colorize('状态', theme['key'])}: {safe_colorize(result.get('status', 'unknown'), theme['info'])}"
            )

            if "details" in result:
                details = result["details"]

                # 特殊处理监控数据
                if "monitoring" in details:
                    monitoring = details["monitoring"]
                    print(f"\n  {safe_colorize('监控数据', theme['heading'])}")
                    for key, value in monitoring.items():
                        print(
                            f"    {safe_colorize(key, theme['key'])}: {safe_colorize(str(value), theme['value'])}"
                        )

                    if "timestamp" in details:
                        print(
                            f"    {safe_colorize('时间戳', theme['key'])}: {safe_colorize(details['timestamp'], theme['time'])}"
                        )
                else:
                    print(f"\n  {safe_colorize('部署详情', theme['heading'])}")
                    for key, value in details.items():
                        print(
                            f"    {safe_colorize(key, theme['key'])}: {safe_colorize(str(value), theme['value'])}"
                        )

        if sound_feedback:
            if result.get("status") in ["active", "completed"]:
                play_effect("success")
            elif result.get("status") in ["deploying", "rolling_back"]:
                play_effect("notification")
            elif result.get("status") in ["failed", "error"]:
                play_effect("error")

    # 默认文本输出
    else:
        print(safe_colorize(str(result), theme["normal"]))