"""
TXT到Python文件转换器（针对使用分隔符的代码文件）

这个脚本专门用于处理使用特定分隔符标记不同模块的大型TXT文件，
将它们分割为单独的Python文件，并保持适当的目录结构。
"""

import os
import re
import sys

def extract_modules(txt_file, pattern=r'# ={10,}\n# ([^\n]+)\n# ={10,}'):
    """
    从大型TXT文件中提取不同的模块
    
    参数:
    - txt_file: 输入的TXT文件路径
    - pattern: 用于识别模块开始的正则表达式模式
    
    返回:
    - 模块列表，每个元素为 (模块名称, 模块内容)
    """
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式找到所有匹配的模块标记
    regex = re.compile(pattern)
    matches = list(regex.finditer(content))
    
    print(f"在 {txt_file} 中找到 {len(matches)} 个模块标记")
    
    # 如果没有找到任何匹配项，可能需要调整模式
    if not matches:
        print("警告: 没有找到任何模块标记。请检查模式是否正确。")
        return []
    
    # 提取每个模块的内容
    modules = []
    for i, match in enumerate(matches):
        module_name = match.group(1).strip()
        content_start = match.end()
        
        # 确定内容结束位置
        if i < len(matches) - 1:
            content_end = matches[i + 1].start()
        else:
            content_end = len(content)
        
        # 提取模块内容
        module_content = content[content_start:content_end].strip()
        
        # 将模块名转换为合法的文件名
        file_name = module_name.lower().replace(' ', '_').replace('-', '_')
        if not file_name.endswith('.py'):
            file_name += '.py'
        
        modules.append((file_name, module_content))
    
    return modules

def save_modules(modules, output_dir):
    """
    将提取的模块保存到指定目录
    
    参数:
    - modules: 模块列表，每个元素为 (模块名称, 模块内容)
    - output_dir: 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    for file_name, module_content in modules:
        # 创建完整路径
        full_path = os.path.join(output_dir, file_name)
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(module_content)
        
        print(f"已创建文件: {full_path}")

def main():
    if len(sys.argv) < 3:
        print("用法: python module_extractor.py <输入文件> <输出目录> [模式]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    pattern = sys.argv[3] if len(sys.argv) > 3 else r'# ={10,}\n# ([^\n]+)\n# ={10,}'
    
    print(f"处理文件: {input_file}")
    print(f"输出目录: {output_dir}")
    print(f"使用模式: {pattern}")
    
    # 提取模块
    modules = extract_modules(input_file, pattern)
    print(f"找到 {len(modules)} 个模块")
    
    # 保存模块
    save_modules(modules, output_dir)
    print("转换完成!")

if __name__ == "__main__":
    main()