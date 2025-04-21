"""
项目自动修复工具

全面检测并修复Python项目中的常见问题:
- 缩进问题(制表符/空格混用)
- 语法错误
- 导入问题
- 编码问题
- 空行处理

使用方法: python project_fixer.py [项目根目录路径]
"""
import os
import sys
import re
import shutil
import tokenize
import io
from pathlib import Path  # noqa
import traceback
import time

class ProjectFixer:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        self.report = {
            "scanned_files": 0,
            "fixed_files": 0,
            "error_files": 0,
            "skipped_files": 0,
            "issues": {
                "indentation": 0,
                "syntax": 0,
                "imports": 0,
                "encoding": 0,
                "empty_lines": 0
            },
            "errors": []
        }
        
        # 创建备份目录
        self.backup_dir = os.path.join(self.project_root, "_fix_backups", time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 跳过的目录和文件
        self.skip_dirs = [
            "__pycache__", 
            "venv", 
            "env",
            "dist",
            "build",
            ".git",
            ".idea",
            ".vscode",
            "_fix_backups"
        ]
        
        self.skip_files = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".bak"
        ]
    
    def scan_project(self):
        """扫描整个项目"""
        print(f"开始扫描项目: {self.project_root}")
        
        for root, dirs, files in os.walk(self.project_root):
            # 跳过指定目录
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            # 处理Python文件
            for file in files:
                if file.endswith(".py") and not any(skip in file for skip in self.skip_files):
                    file_path = os.path.join(root, file)
                    self.process_file(file_path)
        
        # 生成报告
        self.generate_report()
    
    def process_file(self, file_path):
        """处理单个文件"""
        rel_path = os.path.relpath(file_path, self.project_root)
        self.report["scanned_files"] += 1
        
        try:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 创建备份
            backup_path = os.path.join(self.backup_dir, rel_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(file_path, backup_path)
            
            # 处理文件内容
            fixed, issues = self.fix_content(content, file_path)
            
            if fixed != content:
                # 写入修复后的内容
                with open(file_path, 'wb') as f:
                    f.write(fixed)
                
                # 更新报告
                self.report["fixed_files"] += 1
                for issue_type in issues:
                    self.report["issues"][issue_type] += 1
                
                print(f"已修复文件: {rel_path} (问题: {', '.join(issues)})")
            else:
                print(f"检查文件: {rel_path} (无问题)")
                
        except Exception as e:
            self.report["error_files"] += 1
            error_info = {
                "file": rel_path,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            self.report["errors"].append(error_info)
            print(f"处理文件失败: {rel_path} - {str(e)}")
    
    def fix_content(self, content, file_path):
        """修复文件内容"""
        issues = set()
        
        # 尝试解码内容
        try:
            # 检测编码
            encoding = self.detect_encoding(content)
            text_content = content.decode(encoding)
        except UnicodeDecodeError:
            # 编码问题，尝试不同编码
            try:
                text_content = content.decode('utf-8-sig')
                issues.add("encoding")
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('latin1')
                    issues.add("encoding")
                except UnicodeDecodeError:
                    # 如果所有尝试都失败，使用错误处理器
                    text_content = content.decode('utf-8', errors='replace')
                    issues.add("encoding")
        
        # 修复缩进问题
        fixed_content, indent_fixed = self.fix_indentation(text_content)
        if indent_fixed:
            issues.add("indentation")
        
        # 修复空行问题
        fixed_content, empty_line_fixed = self.fix_empty_lines(fixed_content)
        if empty_line_fixed:
            issues.add("empty_lines")
        
        # 修复导入问题
        fixed_content, import_fixed = self.fix_imports(fixed_content, file_path)
        if import_fixed:
            issues.add("imports")
        
        # 检查语法错误
        syntax_valid, syntax_error = self.check_syntax(fixed_content)
        if not syntax_valid:
            # 记录语法错误但不尝试修复
            issues.add("syntax")
            print(f"警告: {os.path.basename(file_path)} 可能存在语法错误: {syntax_error}")
        
        # 返回修复后的内容和问题列表
        return fixed_content.encode(encoding), issues
    
    def detect_encoding(self, content):
        """检测文件编码"""
        try:
            encoding = tokenize.detect_encoding(io.BytesIO(content).readline)[0]
            return encoding
        except:
            return 'utf-8'
    
    def fix_indentation(self, content):
        """修复缩进问题"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False
        
        # 检查是否混合使用制表符和空格
        has_tabs = '\t' in content
        has_spaces = re.search(r'^ +', content, re.MULTILINE) is not None
        mixed_indent = has_tabs and has_spaces
        
        # 确定主要缩进类型
        if mixed_indent:
            # 如果存在混合缩进，统一使用4个空格
            spaces_count = 0
            tabs_count = 0
            
            for line in lines:
                if line.startswith(' '):
                    spaces_count += 1
                elif line.startswith('\t'):
                    tabs_count += 1
            
            # 确定主要使用的缩进类型
            use_spaces = spaces_count >= tabs_count
            
            # 修复每一行的缩进
            for line in lines:
                if use_spaces:
                    # 将制表符转换为空格
                    if '\t' in line:
                        indent = re.match(r'^\t+', line)
                        if indent:
                            tabs = indent.group(0)
                            spaces = ' ' * (4 * len(tabs))
                            new_line = spaces + line[len(tabs):]
                            fixed_lines.append(new_line)
                            fixed = True
                        else:
                            fixed_lines.append(line.replace('\t', '    '))
                            if '\t' in line:
                                fixed = True
                    else:
                        fixed_lines.append(line)
                else:
                    # 将空格转换为制表符
                    if line.startswith(' '):
                        indent = re.match(r'^ +', line)
                        if indent:
                            spaces = indent.group(0)
                            tabs = '\t' * (len(spaces) // 4)
                            new_line = tabs + line[len(spaces):]
                            fixed_lines.append(new_line)
                            fixed = True
                        else:
                            fixed_lines.append(line)
                    else:
                        fixed_lines.append(line)
        else:
            # 如果没有混合缩进，保持原样
            fixed_lines = lines
        
        # 检查try/except块的缩进
        for i in range(1, len(fixed_lines)):
            prev_line = fixed_lines[i-1].rstrip()
            current_line = fixed_lines[i]
            
            if prev_line.endswith(':') and not current_line.strip():
                # 空行在代码块定义后面，确保适当缩进
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                if len(current_line) < prev_indent + 4:
                    if has_tabs:
                        fixed_lines[i] = '\t' * ((prev_indent // 4) + 1)
                    else:
                        fixed_lines[i] = ' ' * (prev_indent + 4)
                    fixed = True
        
        return '\n'.join(fixed_lines), fixed
    
    def fix_empty_lines(self, content):
        """修复空行问题"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False
        
        # 确保文件末尾有一个空行
        if lines and lines[-1].strip():
            lines.append('')
            fixed = True
        
        # 移除多余的连续空行
        consecutive_empty = 0
        for line in lines:
            if not line.strip():
                consecutive_empty += 1
                if consecutive_empty <= 2:  # 允许最多2个连续空行
                    fixed_lines.append(line)
            else:
                consecutive_empty = 0
                fixed_lines.append(line)
        
        if len(fixed_lines) != len(lines):
            fixed = True
        
        return '\n'.join(fixed_lines), fixed
    
    def fix_imports(self, content, file_path):
        """修复导入问题"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False
        
        # 获取项目目录结构信息
        module_path = os.path.relpath(file_path, self.project_root)
        module_parts = os.path.dirname(module_path).split(os.sep)
        
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                # 尝试修复相对导入
                if 'ModuleNotFoundError' in content:
                    if line.strip().startswith('from .'):
                        # 相对导入可能有问题，尝试转为绝对导入
                        modified_line = self.convert_relative_to_absolute(line, module_parts)
                        if modified_line != line:
                            fixed_lines.append(modified_line)
                            fixed = True
                            continue
                
                # 处理循环导入
                if 'ImportError: cannot import name' in content:
                    # 可能有循环导入问题，添加延迟导入
                    if not any(marker in line for marker in ['# noqa', '# type: ignore']):
                        indentation = len(line) - len(line.lstrip())
                        if 'import' in line and 'from' in line:
                            # 对于循环导入，添加注释
                            fixed_lines.append(line + '  # noqa')
                            fixed = True
                            continue
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixed
    
    def convert_relative_to_absolute(self, line, module_parts):
        """将相对导入转换为绝对导入"""
        # 简单处理，只转换明显的情况
        if line.startswith('from .'):
            dot_count = 0
            for c in line:
                if c == '.':
                    dot_count += 1
                else:
                    break
            
            if dot_count <= len(module_parts):
                # 构建绝对导入路径
                absolute_path = '.'.join(module_parts[:-dot_count] if dot_count > 0 else module_parts)
                rest_of_line = line[dot_count:].lstrip()
                
                if absolute_path:
                    return f'from {absolute_path}.{rest_of_line}'
                else:
                    return f'from {rest_of_line}'
        
        return line
    
    def check_syntax(self, content):
        """检查Python语法错误"""
        try:
            compile(content, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, str(e)
    
    def generate_report(self):
        """生成修复报告"""
        print("\n" + "="*50)
        print("项目修复报告")
        print("="*50)
        print(f"项目根目录: {self.project_root}")
        print(f"备份目录: {self.backup_dir}")
        print(f"扫描文件总数: {self.report['scanned_files']}")
        print(f"修复的文件数: {self.report['fixed_files']}")
        print(f"错误的文件数: {self.report['error_files']}")
        print(f"跳过的文件数: {self.report['skipped_files']}")
        print("\n问题统计:")
        for issue_type, count in self.report["issues"].items():
            if count > 0:
                print(f"  - {issue_type}: {count}个文件")
        
        if self.report["errors"]:
            print("\n错误文件列表:")
            for error in self.report["errors"][:10]:  # 只显示前10个错误
                print(f"  - {error['file']}: {error['error']}")
            
            if len(self.report["errors"]) > 10:
                print(f"    ... 还有 {len(self.report['errors']) - 10} 个错误未显示")
        
        print("\n修复完成！")
        print("备份文件已保存，如需还原，请复制备份目录中的文件")
        print("="*50)

# 主函数
if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # 默认使用当前目录
        project_root = os.getcwd()
    
    fixer = ProjectFixer(project_root)
    fixer.scan_project()