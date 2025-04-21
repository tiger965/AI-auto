import os
import sys
import stat
import time


def force_remove(path):
    """强制删除文件，处理只读或其他权限问题"""
    try:
        # 移除只读属性
        os.chmod(path, stat.S_IWRITE)
        # 删除文件
        os.remove(path)
        return True
    except Exception as e:
        print(f"无法删除文件 {path}: {e}")
        return False


def delete_all_bak_files(directory):
    """强制删除所有.bak文件"""
    total = 0
    success = 0

    print(f"开始在 {directory} 中查找并删除所有备份文件...")

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".bak") or ".try_except_fix.bak" in file:
                total += 1
                file_path = os.path.join(root, file)
                print(f"正在删除: {file_path}")

                # 尝试多次删除
                for attempt in range(3):
                    if force_remove(file_path):
                        success += 1
                        break
                    # 等待一段时间再重试
                    print(f"  重试 {attempt+1}/3...")
                    time.sleep(0.5)

    print(f"\n操作完成: 成功删除 {success}/{total} 个备份文件")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        # 默认为当前目录
        target_dir = os.path.dirname(os.path.abspath(__file__))

    confirm = input(f"即将在 {target_dir} 中删除所有备份文件，确认? (y/n): ")
    if confirm.lower() == "y":
        delete_all_bak_files(target_dir)
    else:
        print("操作已取消")