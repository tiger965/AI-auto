"""
项目重组快速修复脚本

此脚本专为快速重组Python项目设计，附带详细的错误处理和交互式提示。
只需运行此脚本，它会自动处理路径问题并引导你完成整个过程。

作者: Claude
日期: 2025年4月16日
"""

import os
import shutil
import glob
import re
import sys


def print_colored(text, color_code):
    """打印彩色文本"""
    print(f"\033[{color_code}m{text}\033[0m")


def print_success(text):
    """打印成功信息（绿色）"""
    print_colored(text, "32")


def print_error(text):
    """打印错误信息（红色）"""
    print_colored(text, "31")


def print_info(text):
    """打印一般信息（蓝色）"""
    print_colored(text, "34")


def print_header(text):
    """打印标题（蓝色加粗）"""
    print("\n" + "=" * 80)
    print_colored(text, "1;34")
    print("=" * 80 + "\n")


def find_python_files(directory):
    """在指定目录中查找所有Python文件（包括子目录）"""
    py_files = []

    # 检查目录是否存在
    if not os.path.exists(directory):
        print_error(f"目录不存在: {directory}")
        return py_files

    # 首先尝试查找当前目录中的Python文件
    direct_py_files = glob.glob(os.path.join(directory, "*.py"))
    if direct_py_files:
        py_files.extend(direct_py_files)
        print_info(f"在 {directory} 中找到 {len(direct_py_files)} 个Python文件")

    # 然后搜索子目录
    for root, dirs, files in os.walk(directory):
        if root != directory:  # 避免重复计算当前目录
            python_files = [os.path.join(root, f)
                            for f in files if f.endswith(".py")]
            if python_files:
                py_files.extend(python_files)
                print_info(f"在 {root} 中找到 {len(python_files)} 个Python文件")

    return py_files


def ensure_directory(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print_info(f"创建目录: {directory}")


def clean_filename(filename):
    """生成规范的Python模块文件名"""
    # 只保留文件名部分
    base_name = os.path.basename(filename)
    name_without_ext = os.path.splitext(base_name)[0]

    # 提取括号中的内容作为首选名称
    bracket_match = re.search(r"\(([a-zA-Z0-9_]+)\)", name_without_ext)
    if bracket_match:
        return bracket_match.group(1) + ".py"

    # 移除数字前缀和分隔符
    clean_name = re.sub(r"^\d+[._]", "", name_without_ext)

    # 移除括号和其内容
    clean_name = re.sub(r"\([^)]*\)", "", clean_name)

    # 将中文和特殊字符转换为下划线
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", clean_name)

    # 处理多余的下划线
    clean_name = re.sub(r"_+", "_", clean_name)
    clean_name = clean_name.strip("_")

    # 确保名称是小写的snake_case
    clean_name = clean_name.lower()

    # 添加.py扩展名
    return clean_name + ".py"


def determine_module_type(filename):
    """基于文件名确定模块类型"""
    # 文件名匹配模式
    patterns = {
        "core": [r"错误处理", r"消息总线", r"日志", r"核心", r"基础组件", r"导入模块"],
        "modules": [r"知识库", r"训练", r"修复", r"备份", r"brain", r"gpt", r"claude"],
        "ui": [r"界面", r"控制台", r"图形", r"panel", r"ui"],
        "api": [r"api", r"调用", r"服务"],
        "tests": [r"test", r"测试", r"verify"],
        "utils": [r"工具", r"资源", r"监控"],
        "system": [r"系统集成", r"集成"],
    }

    base_name = os.path.basename(filename).lower()

    for module, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, base_name, re.IGNORECASE):
                return module

    # 默认为misc
    return "misc"


def create_init_file(directory):
    """为目录创建__init__.py文件"""
    init_path = os.path.join(directory, "__init__.py")

    with open(init_path, "w", encoding="utf-8") as f:
        module_name = os.path.basename(directory)
        f.write(f'"""\n{module_name} 模块\n"""\n\n')

        # 添加导入语句
        python_files = [
            f for f in os.listdir(directory) if f.endswith(".py") and f != "__init__.py"
        ]

        for py_file in python_files:
            module_name = os.path.splitext(py_file)[0]
            f.write(f"from .{module_name} import *\n")

    print_info(f"创建: {init_path}")


def quickfix_reorganize():
    """交互式快速修复并重组项目"""
    print_header("项目重组快速修复工具")

    # 用户交互获取路径
    current_dir = os.getcwd()
    print_info(f"当前工作目录: {current_dir}")

    # 源目录
    source_dir = input("请输入Python文件所在目录 [默认: 当前目录]: ").strip()
    if not source_dir:
        source_dir = current_dir
    source_dir = os.path.abspath(source_dir)

    if not os.path.exists(source_dir):
        print_error(f"源目录不存在: {source_dir}")
        create_dir = input("是否创建此目录? (y/n): ").strip().lower()
        if create_dir == "y":
            os.makedirs(source_dir)
            print_success(f"已创建目录: {source_dir}")
        else:
            print_error("无法继续，退出程序")
            return

    # 目标目录
    target_dir = input("请输入重组后的项目目录 [默认: organized_project]: ").strip()
    if not target_dir:
        target_dir = os.path.join(current_dir, "organized_project")
    target_dir = os.path.abspath(target_dir)

    # 查找Python文件
    print_info(f"正在搜索Python文件...")
    python_files = find_python_files(source_dir)

    if not python_files:
        print_error(f"在 {source_dir} 中未找到Python文件")
        return

    print_success(f"找到 {len(python_files)} 个Python文件")

    # 创建目标目录结构
    ensure_directory(target_dir)

    # 创建模块目录
    module_dirs = {
        "core": os.path.join(target_dir, "core"),
        "modules": os.path.join(target_dir, "modules"),
        "ui": os.path.join(target_dir, "ui"),
        "api": os.path.join(target_dir, "api"),
        "tests": os.path.join(target_dir, "tests"),
        "utils": os.path.join(target_dir, "utils"),
        "system": os.path.join(target_dir, "system"),
        "misc": os.path.join(target_dir, "misc"),
    }

    for directory in module_dirs.values():
        ensure_directory(directory)

    # 复制并分类文件
    print_header("正在重组文件...")

    # 记录每个模块中的文件
    module_files = {module: [] for module in module_dirs.keys()}

    for py_file in python_files:
        # 确定模块类型
        module_type = determine_module_type(py_file)

        # 清理文件名
        clean_name = clean_filename(py_file)

        # 目标路径
        target_path = os.path.join(module_dirs[module_type], clean_name)

        # 复制文件
        try:
            shutil.copy2(py_file, target_path)
            print_success(f"已复制: {os.path.basename(py_file)} -> {target_path}")
            module_files[module_type].append(clean_name)
        except Exception as e:
            print_error(f"复制失败: {e}")

    # 创建__init__.py文件
    print_header("创建初始化文件...")

    for module, directory in module_dirs.items():
        if module_files[module]:  # 只为非空模块创建初始化文件
            create_init_file(directory)

    # 创建项目级__init__.py
    with open(os.path.join(target_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write('"""\nAI自动化系统\n"""\n\n')

        # 导入所有非空模块
        for module in module_dirs.keys():
            if module_files[module]:
                f.write(f"from . import {module}\n")

    print_success(f"已创建项目级初始化文件")

    # 创建main.py
    main_path = os.path.join(target_dir, "main.py")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(
            '''"""
AI自动化系统入口
"""

import os
import sys

# 添加当前目录到导入路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    """主函数"""
    print("AI自动化系统启动...")
    
    try:
        # 尝试导入各个模块
        modules_imported = []
        
        # 导入核心模块
        try:
            import core
            modules_imported.append("core")
        except ImportError:
            print("警告: 核心模块导入失败")
        
        # 导入其他模块
        for module in ["modules", "ui", "api", "system", "utils"]:
            try:
                exec(f"import {module}")
                modules_imported.append(module)
            except ImportError:
                pass
        
        print(f"成功导入的模块: {', '.join(modules_imported)}")
        
        # 这里添加实际的应用逻辑
        print("系统就绪")
        
        # 简单的交互循环
        print("输入'exit'退出")
        while True:
            cmd = input("> ")
            if cmd.lower() == 'exit':
                break
            print(f"执行命令: {cmd}")
    
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"错误: {e}")
    
    print("系统关闭")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        )

    print_success(f"已创建主程序入口: {main_path}")

    # 创建README.md
    readme_path = os.path.join(target_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(
            """# AI自动化系统

## 项目概述
这是一个基于Python的AI自动化系统，提供了模块化的架构来支持各种AI自动化任务。

## 项目结构
```
organized_project/
├── core/           # 核心系统组件
├── modules/        # 功能模块
├── ui/             # 用户界面
├── api/            # API接口
├── system/         # 系统集成
├── utils/          # 工具函数
├── tests/          # 测试模块
├── misc/           # 杂项文件
└── main.py         # 主程序入口
```

## 使用方法
```
python main.py
```
"""
        )

    print_success(f"已创建README文件: {readme_path}")

    print_header("项目重组完成")
    print_info(f"新的项目结构已创建在: {target_dir}")
    print_info(f"你可以通过运行以下命令启动项目:")
    print_info(f"    cd {target_dir}")
    print_info(f"    python main.py")


if __name__ == "__main__":
    try:
        quickfix_reorganize()
    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
    except Exception as e:
        print_error(f"发生错误: {e}")
        print_error("如果问题持续存在，请尝试手动创建目录结构")