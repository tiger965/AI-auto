# debug_tests/fix_all_init_files.py
import os
import glob
import sys


def fix_all_init_files(project_root):
    """查找并修复所有__init__.py文件中的BOM标记问题"""
    print("====== 开始修复所有__init__.py文件 ======")

    # 查找所有的__init__.py文件
    init_files = glob.glob(
        os.path.join(project_root, "**", "__init__.py"), recursive=True
    )

    if not init_files:
        print("未找到任何__init__.py文件")
        return

    print(f"找到 {len(init_files)} 个__init__.py文件")

    # 修复每个文件
    fixed_count = 0
    for file_path in init_files:
        try:
            # 读取文件内容
            with open(file_path, "rb") as f:
                content = f.read()

            # 检查是否包含BOM标记
            has_bom = False
            if content.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
                content = content[3:]
                has_bom = True
            elif content.startswith(b"\xff\xfe") or content.startswith(
                b"\xfe\xff"
            ):  # UTF-16 BOM
                has_bom = True
                # 解码并重新编码为UTF-8
                if content.startswith(b"\xff\xfe"):
                    text = content.decode("utf-16-le")
                else:
                    text = content.decode("utf-16-be")
                content = text.encode("utf-8")

            # 如果有BOM标记或强制修复，重写文件
            if has_bom or "--force" in sys.argv:
                with open(file_path, "wb") as f:
                    f.write(content)

                status = "修复了BOM" if has_bom else "强制重写"
                print(f"✅ {status}: {file_path}")
                fixed_count += 1

        except Exception as e:
            print(f"❌ 处理失败: {file_path} - {str(e)}")

    print(f"\n总计修复了 {fixed_count} 个文件")
    print("\n====== 修复完成 ======")

    if fixed_count > 0:
        print("\n建议重新运行测试脚本检查问题是否解决")


if __name__ == "__main__":
    # 获取项目根目录
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        project_root = sys.argv[1]
    else:
        # 使用当前脚本所在目录的上一级目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

    print(f"使用项目根目录: {project_root}")
    fix_all_init_files(project_root)