#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI交易系统主修复工具
按顺序执行所有修复步骤，解决项目中的各种问题
"""

import os
import sys
import time
import trading.utils
import subprocess


def print_header(message):
    """打印带格式的标题"""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)


def load_script(script_path):
    """动态加载Python脚本"""
    try:
        spec = importlib.util.spec_from_file_location("module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"加载脚本失败: {script_path}")
        print(f"错误: {str(e)}")
        return None


def run_advanced_python_fixer(directory):
    """运行高级Python语法错误修复工具"""
    print_header("高级Python语法错误修复")

    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "advanced_python_fixer.py"
    )

    if os.path.exists(script_path):
        try:
            module = load_script(script_path)
            if module:
                fixer = module.AdvancedPythonFixer(
                    directory, verbose=True, create_backup=True
                )
                fixer.scan_and_fix_directory()
                return True
        except Exception as e:
            print(f"运行高级Python修复工具时出错: {str(e)}")
    else:
        print(f"高级Python修复工具脚本不存在: {script_path}")
        print("尝试使用内置Python修复功能...")
        try:
            import advanced_python_fixer

            fixer = advanced_python_fixer.AdvancedPythonFixer(
                directory, verbose=True, create_backup=True
            )
            fixer.scan_and_fix_directory()
            return True
        except Exception as e:
            print(f"使用内置修复工具时出错: {str(e)}")

    return False


def run_import_path_fixer(directory):
    """运行导入路径修复工具"""
    print_header("导入路径修复")

    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "import_path_fixer.py"
    )

    if os.path.exists(script_path):
        try:
            module = load_script(script_path)
            if module:
                fixer = module.ImportPathFixer(
                    directory, verbose=True, create_backup=True
                )
                fixer.scan_and_fix_imports()
                return True
        except Exception as e:
            print(f"运行导入路径修复工具时出错: {str(e)}")
    else:
        print(f"导入路径修复工具脚本不存在: {script_path}")
        print("尝试使用内置导入路径修复功能...")
        try:
            import import_path_fixer

            fixer = import_path_fixer.ImportPathFixer(
                directory, verbose=True, create_backup=True
            )
            fixer.scan_and_fix_imports()
            return True
        except Exception as e:
            print(f"使用内置修复工具时出错: {str(e)}")

    return False


def run_bom_encoding_fixer(directory):
    """运行BOM编码修复工具"""
    print_header("BOM编码修复")

    # 内联实现BOM修复功能
    import codecs
    from collections import defaultdict

    stats = {"total_files": 0, "fixed_files": 0}

    print(f"开始扫描目录: {directory}")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                stats["total_files"] += 1

                if stats["total_files"] % 20 == 0:
                    print(f"已检查文件数: {stats['total_files']}...")

                try:
                    # 读取文件内容（二进制模式）
                    with open(file_path, "rb") as f:
                        content = f.read()

                    # 检查是否有BOM标记
                    if content.startswith(codecs.BOM_UTF8):
                        print(f"发现BOM标记: {file_path}")

                        # 创建备份
                        backup_path = file_path + ".bom.bak"
                        with open(backup_path, "wb") as f:
                            f.write(content)

                        # 移除BOM标记并保存
                        with open(file_path, "wb") as f:
                            f.write(content[len(codecs.BOM_UTF8):])

                        print(f"已修复: {file_path}")
                        stats["fixed_files"] += 1
                except Exception as e:
                    print(f"处理文件时出错 {file_path}: {str(e)}")

    print("\n== BOM编码修复完成 ==")
    print(f"检查的文件总数: {stats['total_files']}")
    print(f"修复的文件总数: {stats['fixed_files']}")

    return True


def run_test_script(directory):
    """运行测试脚本"""
    print_header("运行测试脚本")

    test_script = os.path.join(directory, "tests", "master_test.py")
    if os.path.exists(test_script):
        print(f"发现测试脚本: {test_script}")
        print("开始运行测试...")

        try:
            result = subprocess.run(
                [sys.executable, test_script],
                check=False,
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)

            if result.returncode == 0:
                print("测试成功！所有测试通过")
                return True
            else:
                print("测试失败。请查看输出了解详细信息")
                return False
        except Exception as e:
            print(f"运行测试脚本时出错: {str(e)}")
            return False
    else:
        print(f"测试脚本不存在: {test_script}")

        # 尝试在tests目录下寻找其他测试脚本
        tests_dir = os.path.join(directory, "tests")
        if os.path.exists(tests_dir) and os.path.isdir(tests_dir):
            print("在tests目录下寻找其他测试脚本...")

            test_files = [
                f
                for f in os.listdir(tests_dir)
                if f.endswith(".py") and "test" in f.lower()
            ]
            if test_files:
                print(f"找到 {len(test_files)} 个测试文件:")
                for i, test_file in enumerate(test_files):
                    print(f"{i+1}. {test_file}")

                print("\n您可以手动运行这些测试脚本来验证修复效果")

        return None


def main():
    # 默认目录路径
    default_dir = r"C:\Users\tiger\Desktop\key\code\organized_project"

    # 使用命令行参数或默认路径
    directory = sys.argv[1] if len(sys.argv) > 1 else default_dir

    if not os.path.exists(directory):
        print(f"错误: 目录不存在 - {directory}")
        return

    print(f"开始修复项目: {directory}")
    start_time = time.time()

    # 步骤1: 修复BOM编码问题
    print_header("步骤1: 修复BOM编码问题")
    run_bom_encoding_fixer(directory)

    # 步骤2: 修复语法错误
    print_header("步骤2: 修复语法错误")
    run_advanced_python_fixer(directory)

    # 步骤3: 修复导入路径问题
    print_header("步骤3: 修复导入路径问题")
    run_import_path_fixer(directory)

    # 步骤4: 运行测试脚本
    print_header("步骤4: 运行测试脚本")
    test_result = run_test_script(directory)

    # 计算总执行时间
    elapsed = time.time() - start_time

    print_header("修复完成")
    print(f"总耗时: {elapsed:.2f} 秒")

    if test_result is True:
        print("恭喜！系统已成功修复，所有测试通过")
    elif test_result is False:
        print("系统已经修复，但测试未通过，可能需要进一步修复")
    else:
        print("系统已经修复，但无法验证结果（未找到测试脚本）")


if __name__ == "__main__":
    main()