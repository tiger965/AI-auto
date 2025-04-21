# debug.py
"""AI自动化系统调试工具"""

import sys
import os
import importlib

# 确保项目根目录在Python路径中
project_root = os.path.abspath(".")
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# 尝试创建必要的目录和初始化文件
def ensure_project_structure():
    """确保项目目录结构完整"""
    # 主要目录
    dirs = ["api", "config", "core", "utils",
            "system", "modules", "ui", "tests"]

    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"创建目录: {d}")

        # 确保__init__.py存在
        init_file = os.path.join(d, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# 自动生成的初始化文件\n")
            print(f"创建文件: {init_file}")


def test_config():
    """测试配置模块"""
    try:
        # 尝试导入config模块
        import config

        importlib.reload(config)  # 强制重新加载

        # 检查config模块是否有get_config函数
        if hasattr(config, "get_config"):
            config_data = config.get_config()
            print("✓ 配置文件加载成功")
            return True

        # 检查config模块是否直接暴露了config变量
        elif hasattr(config, "config"):
            config_data = config.config
            print("✓ 配置文件加载成功")
            return True

        else:
            print("✗ 配置模块结构不正确")
            return False

    except Exception as e:
        print(f"✗ 配置文件加载失败: {str(e)}")
        return False


def test_api():
    """测试API模块"""
    try:
        # 尝试导入api_manager模块
        from api.api_manager import APIManager

        # 创建API管理器实例
        api_manager = APIManager()
        print("✓ API模块导入成功")
        return True
    except Exception as e:
        print(f"✗ API模块导入失败: {str(e)}")
        return False


def test_core():
    """测试核心模块"""
    try:
        # 尝试导入引擎模块
        from core.engine import Engine

        # 创建引擎实例
        engine = Engine()
        print("✓ 核心模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 核心模块导入失败: {str(e)}")
        return False


def test_ui():
    """测试UI模块"""
    try:
        # 尝试导入UI CLI模块
        from ui.cli import initialize_cli

        print("✓ UI模块导入成功")
        return True
    except Exception as e:
        print(f"✗ UI模块导入失败: {str(e)}")
        return False


def test_modules():
    """测试功能模块"""
    try:
        # 检查模块目录是否存在
        if not os.path.exists("modules"):
            print("✗ 模块目录不存在")
            return False

        # 尝试导入trading_api模块（如果存在）
        if os.path.exists("api/modules/trading_api.py"):
            try:
                from api.modules.trading_api import TradingAPI

                trading_api = TradingAPI()
                print("✓ 交易模块导入成功")
            except Exception as e:
                print(f"✗ 交易模块导入失败: {str(e)}")
                return False

        print("✓ 功能模块检查成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("===== AI自动化系统调试工具 =====")

    # 确保项目结构完整
    ensure_project_structure()

    # 设置测试项
    tests = [
        ("配置模块", test_config),
        ("API模块", test_api),
        ("核心模块", test_core),
        ("UI模块", test_ui),
        ("功能模块", test_modules),
    ]

    # 运行测试
    results = []
    for name, test_func in tests:
        print(f"\n正在测试 {name}...")
        result = test_func()
        results.append((name, result))

    # 显示测试结果
    print("\n===== 测试结果汇总 =====")
    all_passed = True
    for name, result in results:
        status = "通过" if result else "失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False

    # 给出后续建议
    if all_passed:
        print("\n所有模块测试通过！系统应该可以正常运行。")
        print("尝试运行: python start.py")
    else:
        print("\n一些模块测试失败。需要修复这些问题才能运行系统。")
        print("可以运行: python fix_imports.py 修复导入问题")


if __name__ == "__main__":
    main()