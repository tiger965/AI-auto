# organized_project/examples/config_usage.py

"""
配置系统使用示例

此文件展示了如何在项目中使用配置系统的各种功能。
"""

from config import config
import os
import sys

# 添加项目根目录到导入路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 导入全局配置


def demonstrate_config_usage():
    """演示配置系统的使用方法"""
    print("配置系统使用示例")
    print("=" * 50)

    # 导入全局配置
    print("# 导入全局配置")
    print("from config import config")
    print()

    # 获取配置项
    print("# 获取配置项")
    debug_mode = config.get("system.debug_mode", False)
    print(
        f'debug_mode = config.get("system.debug_mode", False)  # 结果: {debug_mode}')

    api_port = config.get("api.port", 5000)
    print(f'api_port = config.get("api.port", 5000)  # 结果: {api_port}')

    # 嵌套配置
    print("\n# 获取嵌套配置")
    gui_width = config.get("ui.gui.width", 800)
    print(f'gui_width = config.get("ui.gui.width", 800)  # 结果: {gui_width}')

    # 设置配置项
    print("\n# 设置配置项")
    print('config.set("ui.theme", "dark")')
    config.set("ui.theme", "dark")

    # 验证设置生效
    theme = config.get("ui.theme")
    print(f'config.get("ui.theme")  # 结果: {theme}')

    # 保存配置
    print("\n# 保存配置")
    print("config.save()  # 保存更改")

    # 获取所有配置
    print("\n# 获取完整配置")
    print("all_config = config.get_all()")
    print("print(all_config)  # 打印完整配置字典")

    print("\n配置系统为你的AI自动化项目提供了灵活的配置机制，")
    print("可以轻松调整系统行为而无需修改代码。")


if __name__ == "__main__":
    demonstrate_config_usage()