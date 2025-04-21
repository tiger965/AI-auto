import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 使用python -m命令直接运行测试
# 这样可以确保当前目录被添加到Python路径中
cmd = f'cd "{project_root}" && python -m unittest discover -s tests -p "test_*.py"'
print(f"执行命令: {cmd}")
os.system(cmd)