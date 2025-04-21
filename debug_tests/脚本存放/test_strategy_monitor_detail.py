# debug_tests/test_strategy_monitor_detail.py
import os
import sys
import traceback

# 将项目根目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)


def test_strategy_monitor_detailed():
    """详细测试策略监控UI模块"""
    print("====== 详细测试策略监控UI模块 ======")

    try:
        # 尝试导入策略监控模块
        print("尝试导入ui.components.strategy_monitor模块...")

        # 获取导入路径
        import_path = os.path.join(
            project_root, "ui", "components", "strategy_monitor.py"
        )
        print(f"导入文件路径: {import_path}")

        # 跟踪导入依赖的文件
        print("\n导入依赖链:")

        # 尝试导入ui包
        try:
            import ui

            print(f"✓ 成功导入ui包 (来自 {ui.__file__})")
        except Exception as e:
            print(f"✗ 导入ui包失败: {e}")
            return

        # 尝试导入ui.components包
        try:
            import ui.components

            print(f"✓ 成功导入ui.components包 (来自 {ui.components.__file__})")
        except Exception as e:
            print(f"✗ 导入ui.components包失败: {e}")
            return

        # 尝试导入StrategyMonitor类
        try:
            from ui.components.strategy_monitor import StrategyMonitor

            print(f"✓ 成功导入StrategyMonitor类")

            # 创建实例
            monitor = StrategyMonitor()
            print(f"✓ 成功创建StrategyMonitor实例")

            # 测试方法
            status = monitor.get_status()
            print(f"✓ 成功调用get_status()方法")
            print(f"  状态数据: {status}")

        except Exception as e:
            print(f"✗ 导入或实例化StrategyMonitor失败:")
            print(f"  错误类型: {type(e).__name__}")
            print(f"  错误信息: {str(e)}")
            print("\n详细错误跟踪:")
            traceback.print_exc()
            return

    except Exception as e:
        print(f"✗ 测试过程中出现未预期的错误:")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {str(e)}")
        print("\n详细错误跟踪:")
        traceback.print_exc()

    print("\n====== 详细测试完成 ======")


if __name__ == "__main__":
    test_strategy_monitor_detailed()