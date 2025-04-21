
# 添加项目根目录到Python路径
import os
import sys
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../" * __file__.count("/")))
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
﻿  # UI工具初始化