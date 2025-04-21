# debug_tests/check_init_files.py
import os
import glob
import sys


def check_init_files(project_root):
    """检查所有__init__.py文件是否包含BOM标记(U+FEFF)"""
    print("====== 开始检查 __init__.py 文件 ======")

    # 查找所有的__init__.py文件
    init_files = glob.glob(
        os.path.join(project_root, "**", "__init__.py"), recursive=True
    )

    if not init_files:
        print("未找到任何__init__.py文件")
        return

    print(f"找到 {len(init_files)} 个__init__.py文件")

    # 检查每个文件
    problem_files = []
    for file_path in init_files:
        with open(file_path, "rb") as f:
            content = f.read()
            # 检查UTF-8 BOM标记 (EF BB BF)
            if content.startswith(b"\xef\xbb\xbf"):
                problem_files.append((file_path, "UTF-8 BOM"))
            # 检查UTF-16 BOM标记
            elif content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff"):
                problem_files.append((file_path, "UTF-16 BOM"))
            # 检查UTF-32 BOM标记
            elif content.startswith(b"\xff\xfe\x00\x00") or content.startswith(
                b"\x00\x00\xfe\xff"
            ):
                problem_files.append((file_path, "UTF-32 BOM"))

    # 输出结果
    if problem_files:
        print("\n发现问题文件:")
        for file_path, problem in problem_files:
            print(f"❌ {file_path}: 包含 {problem} 标记")

        # 自动修复问题文件
        if input("\n是否自动修复这些文件? (y/n): ").lower() == "y":
            fix_files(problem_files)
    else:
        print("\n✅ 所有__init__.py文件格式正确，未发现BOM标记")

    print("\n====== 检查完成 ======")


def fix_files(problem_files):
    """修复包含BOM标记的文件"""
    for file_path, _ in problem_files:
        try:
            # 读取文件内容，忽略BOM
            with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

            # 重新写入文件，不带BOM
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ 已修复: {file_path}")
        except Exception as e:
            print(f"❌ 修复失败: {file_path} - {str(e)}")


if __name__ == "__main__":
    # 获取项目根目录
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # 如果未提供参数，使用当前脚本所在目录的上一级目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

    print(f"使用项目根目录: {project_root}")
    check_init_files(project_root)