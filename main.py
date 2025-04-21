# main.py
"""AI自动化系统主入口文件"""

import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath("."))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI自动化系统")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--no-cli", action="store_true", help="不启动命令行界面")

    return parser.parse_args()


def initialize_cli():
    """初始化命令行界面"""
    try:
        from ui.cli import initialize_cli as start_cli

        return start_cli()
    except ImportError as e:
        print(f"初始化命令行界面失败: {str(e)}")
        return False


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 加载配置
    from config import load_config, update_config

    if args.config:
        config = load_config(args.config)
    else:
        config = load_config()

    # 应用命令行参数
    if args.debug:
        update_config("debug", True)

    # 启动系统
    if not args.no_cli:
        return initialize_cli()

    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"系统启动失败: {str(e)}")

        # 详细错误信息（仅在调试模式下显示）
        try:
            from config import get_config

            if get_config().get("debug", False):
                import traceback

                traceback.print_exc()
        except:
            pass