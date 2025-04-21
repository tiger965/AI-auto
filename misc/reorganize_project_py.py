"""
项目结构重组脚本

此脚本用于将已转换的Python文件重组到一个合适的项目结构中。
它会根据文件名模式识别文件类别，创建相应的目录结构，
并将每个文件移动到正确的位置。

使用方法:
python reorganize_project.py <源目录> <目标目录>

例如:
python reorganize_project.py ./python_project ./organized_project
"""

import os
import re
import shutil
import sys

# 文件类别映射规则
CATEGORY_PATTERNS = [
    # 模式, 目标文件夹, 新文件名处理函数
    (r"^1[._]", "core", lambda name: name.split(
        "_", 1)[1] if "_" in name else name),
    (r"^2[._]", "modules", lambda name: name.split(
        "_", 1)[1] if "_" in name else name),
    (r"^3[._]", "api", lambda name: name.split(
        "_", 1)[1] if "_" in name else name),
    (r"ui|界面|交互", "ui", lambda name: name),
    (r"test|verify|测试", "tests", lambda name: name),
    (r"resource|资源|监控", "utils", lambda name: name),
    (r"system|系统集成", "system", lambda name: name),
    (r"主函数|main|入口", "", lambda name: "main.py"),  # 根目录
]


def determine_category(filename):
    """
    根据文件名确定其类别和新名称

    参数:
        filename: 文件名

    返回:
        (category, new_name): 类别和新文件名
    """
    # 移除扩展名
    base_name = os.path.splitext(filename)[0]

    # 检查各个模式
    for pattern, category, name_processor in CATEGORY_PATTERNS:
        if re.search(pattern, base_name, re.IGNORECASE):
            new_name = name_processor(base_name) + ".py"
            return category, new_name

    # 默认类别
    return "misc", filename


def clean_filename(filename):
    """
    清理文件名，移除特殊字符

    参数:
        filename: 原始文件名

    返回:
        清理后的文件名
    """
    # 将中文括号替换为英文括号
    filename = filename.replace("（", "(").replace("）", ")")

    # 提取括号中的英文名称（如果有）
    match = re.search(r"\(([a-zA-Z0-9_]+)\)", filename)
    if match:
        # 使用括号中的名称
        clean_name = match.group(1) + ".py"
    else:
        # 移除括号及其内容
        clean_name = re.sub(r"\([^)]*\)", "", filename)
        # 移除数字前缀
        clean_name = re.sub(r"^\d+[._]", "", clean_name)
        # 替换空格和特殊字符为下划线
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", clean_name)
        # 确保有.py扩展名
        if not clean_name.endswith(".py"):
            clean_name = clean_name + ".py"

    # 移除多余的下划线
    clean_name = re.sub(r"_+", "_", clean_name)
    # 去除首尾下划线
    clean_name = clean_name.strip("_")

    return clean_name


def create_init_files(target_dir):
    """
    在目标目录的每个子目录中创建__init__.py文件

    参数:
        target_dir: 目标目录
    """
    for root, dirs, files in os.walk(target_dir):
        for dir_name in dirs:
            init_path = os.path.join(root, dir_name, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w", encoding="utf-8") as f:
                    f.write("# 自动生成的初始化文件\n")
                print(f"已创建: {init_path}")


def reorganize_project(source_dir, target_dir):
    """
    重组项目结构

    参数:
        source_dir: 源目录
        target_dir: 目标目录
    """
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 获取所有Python文件
    python_files = [f for f in os.listdir(source_dir) if f.endswith(".py")]

    # 处理每个文件
    for filename in python_files:
        source_path = os.path.join(source_dir, filename)

        # 确定类别和新文件名
        category, new_name = determine_category(filename)

        # 清理文件名
        clean_name = clean_filename(new_name)

        # 创建目标目录
        if category:
            category_dir = os.path.join(target_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            target_path = os.path.join(category_dir, clean_name)
        else:
            # 根目录文件
            target_path = os.path.join(target_dir, clean_name)

        # 复制文件
        shutil.copy2(source_path, target_path)
        print(f"已复制: {filename} -> {target_path}")

    # 创建__init__.py文件
    create_init_files(target_dir)

    print("项目重组完成!")
    print(f"请查看新的项目结构: {target_dir}")


def main():
    if len(sys.argv) != 3:
        print("用法: python reorganize_project.py <源目录> <目标目录>")
        print("例如: python reorganize_project.py ./python_project ./organized_project")
        sys.exit(1)

    source_dir = sys.argv[1]
    target_dir = sys.argv[2]

    print(f"正在从 {source_dir} 重组项目到 {target_dir}")
    reorganize_project(source_dir, target_dir)


if __name__ == "__main__":
    main()