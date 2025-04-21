# start.py
"""AI自动化系统启动脚本"""

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.abspath(".")
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def check_dependencies():
    """检查依赖项"""
    required_packages = ["numpy", "pandas", "requests", "pyyaml"]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("警告: 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请使用以下命令安装缺少的依赖:")
        print("pip install -r requirements.txt")

        return False

    return True


def ensure_config():
    """确保配置文件存在"""
    config_dir = os.path.join(project_root, "config")
    config_file = os.path.join(config_dir, "config.json")

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"创建目录: {config_dir}")

    if not os.path.exists(config_file):
        # 创建默认配置文件
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(
                """{
    "app_name": "AI自动化系统",
    "version": "1.0.0",
    "debug": true,
    "log_level": "debug",
    "api": {
        "enabled": true,
        "port": 8000,
        "host": "127.0.0.1"
    },
    "modules": {
        "nlp": true,
        "vision": true,
        "audio": true,
        "data": true,
        "trading": false
    },
    "paths": {
        "data": "data",
        "logs": "logs",
        "temp": "temp"
    },
    "security": {
        "encryption_enabled": false,
        "auth_required": false
    }
}"""
            )
        print(f"创建默认配置文件: {config_file}")

    return True


def initialize_system():
    """初始化系统"""
    try:
        # 尝试导入main模块
        import main

        # 如果main模块有initialize_cli函数，调用它
        if hasattr(main, "initialize_cli"):
            return main.initialize_cli()

        # 否则尝试直接从UI模块导入
        from ui.cli import initialize_cli

        return initialize_cli()

    except ImportError:
        # 如果导入失败，直接尝试从UI模块导入
        try:
            from ui.cli import initialize_cli

            return initialize_cli()
        except ImportError:
            print("错误: 无法导入初始化函数")
            return False

    except Exception as e:
        print(f"初始化系统失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("===== 正在启动AI自动化系统 =====")

    # 检查依赖项
    if not check_dependencies():
        print("警告: 一些依赖项缺失，但将继续尝试启动系统")

    # 确保配置文件存在
    ensure_config()

    # 初始化并启动系统
    success = initialize_system()

    if not success:
        print("系统启动失败。请尝试运行: python debug.py")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        print("请尝试运行: python debug.py")
        sys.exit(1)