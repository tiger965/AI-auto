#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python导入路径修复工具
专门用于解决模块导入和路径问题
"""

import os
import sys
import re
import ast
import importlib
import pkgutil
import traceback
import time
from collections import defaultdict


class ImportFixResult:
    """存储导入修复结果的类"""

    def __init__(self):
        self.fixed = False
        self.error_message = None
        self.fix_method = None
        self.module_name = None
        self.original_import = None
        self.fixed_import = None


class ImportPathFixer:
    """专门用于修复Python导入问题的工具"""

    def __init__(self, root_dir, verbose=True, create_backup=True):
        self.root_dir = os.path.abspath(root_dir)
        self.verbose = verbose
        self.create_backup = create_backup
        self.stats = {
            "total_files": 0,
            "error_files": 0,
            "fixed_files": 0,
            "error_types": defaultdict(int),
            "fixed_types": defaultdict(int),
        }

        # 记录项目中的所有Python模块
        self.project_modules = set()
        self.package_structure = {}
        self.init_files = set()

        # 标准库模块列表
        self.stdlib_modules = self._get_stdlib_modules()

        # 初始化项目结构
        self._analyze_project_structure()

    def log(self, message):
        """打印日志（如果启用了详细模式）"""
        if self.verbose:
            print(message)

    def _get_stdlib_modules(self):
        """获取Python标准库模块列表"""
        stdlib_modules = set()

        # 尝试获取所有标准库模块
        for module in pkgutil.iter_modules():
            if not module.ispkg:
                stdlib_modules.add(module.name)

        # 添加一些常见的标准库模块
        common_stdlib = [
            "os",
            "sys",
            "re",
            "math",
            "time",
            "datetime",
            "json",
            "csv",
            "random",
            "collections",
            "itertools",
            "functools",
            "types",
            "threading",
            "multiprocessing",
            "subprocess",
            "socket",
            "urllib",
            "http",
            "email",
            "xml",
            "html",
            "logging",
            "argparse",
            "pathlib",
            "io",
            "shutil",
            "tempfile",
            "zipfile",
            "tarfile",
            "hashlib",
            "pickle",
            "sqlite3",
            "tkinter",
            "unittest",
            "asyncio",
            "typing",
        ]

        stdlib_modules.update(common_stdlib)
        return stdlib_modules

    def _analyze_project_structure(self):
        """分析项目结构，找出所有Python模块和包"""
        self.log("分析项目结构...")

        for root, dirs, files in os.walk(self.root_dir):
            # 计算相对于项目根目录的路径
            rel_path = os.path.relpath(root, self.root_dir)
            if rel_path == ".":
                rel_path = ""

            # 检查__init__.py文件
            if "__init__.py" in files:
                # 这是一个包
                package_path = rel_path.replace(os.path.sep, ".")
                if package_path:
                    self.project_modules.add(package_path)
                    self.init_files.add(os.path.join(root, "__init__.py"))

            # 添加所有Python模块
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    module_name = os.path.splitext(file)[0]
                    module_path = os.path.join(rel_path, module_name).replace(
                        os.path.sep, "."
                    )
                    if module_path.startswith("."):
                        module_path = module_path[1:]
                    self.project_modules.add(module_path)

                    # 添加到包结构中
                    package = rel_path.replace(os.path.sep, ".")
                    if package not in self.package_structure:
                        self.package_structure[package] = []
                    self.package_structure[package].append(module_name)

        self.log(
            f"找到 {len(self.project_modules)} 个模块和 {len(self.init_files)} 个包"
        )

    def backup_file(self, file_path):
        """创建文件备份"""
        if not self.create_backup:
            return True

        backup_path = file_path + ".import.bak"
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as src:
                content = src.read()
            with open(backup_path, "w", encoding="utf-8") as dst:
                dst.write(content)
            return True
        except Exception as e:
            self.log(f"创建备份失败: {file_path} - {str(e)}")
            return False

    def _extract_imports(self, file_path):
        """提取文件中的所有导入语句"""
        imports = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(
                            {
                                "type": "import",
                                "module": name.name,
                                "alias": name.asname,
                                "lineno": node.lineno,
                            }
                        )
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        imports.append(
                            {
                                "type": "from",
                                "module": module,
                                "name": name.name,
                                "alias": name.asname,
                                "level": node.level,
                                "lineno": node.lineno,
                            }
                        )

            return imports
        except SyntaxError:
            # 如果文件有语法错误，使用正则表达式提取导入
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # 使用正则表达式匹配导入语句
                import_pattern = re.compile(
                    r"^import\s+([\w\.]+)(?:\s+as\s+([\w]+))?", re.MULTILINE
                )
                from_pattern = re.compile(
                    r"^from\s+(\.*)?([\w\.]*)\s+import\s+([\w\.\*]+)(?:\s+as\s+([\w]+))?",
                    re.MULTILINE,
                )

                for match in import_pattern.finditer(content):
                    module, alias = match.groups()
                    imports.append(
                        {
                            "type": "import",
                            "module": module,
                            "alias": alias,
                            "lineno": content[: match.start()].count("\n") + 1,
                        }
                    )

                for match in from_pattern.finditer(content):
                    dots, module, name, alias = match.groups()
                    level = len(dots) if dots else 0
                    imports.append(
                        {
                            "type": "from",
                            "module": module or "",
                            "name": name,
                            "alias": alias,
                            "level": level,
                            "lineno": content[: match.start()].count("\n") + 1,
                        }
                    )

                return imports
            except Exception as e:
                self.log(f"无法提取导入语句: {file_path} - {str(e)}")
                return []
        except Exception as e:
            self.log(f"无法提取导入语句: {file_path} - {str(e)}")
            return []

    def _check_import_errors(self, file_path):
        """检查文件中的导入错误"""
        errors = []
        original_sys_path = sys.path.copy()

        try:
            # 添加文件所在目录到sys.path
            file_dir = os.path.dirname(file_path)
            if file_dir not in sys.path:
                sys.path.insert(0, file_dir)

            # 添加项目根目录到sys.path
            if self.root_dir not in sys.path:
                sys.path.insert(0, self.root_dir)

            # 提取导入语句
            imports = self._extract_imports(file_path)

            # 相对于项目根目录的路径
            rel_path = os.path.relpath(
                os.path.dirname(file_path), self.root_dir)
            if rel_path == ".":
                rel_path = ""
            current_package = rel_path.replace(os.path.sep, ".")

            for imp in imports:
                result = ImportFixResult()
                result.original_import = self._format_import(imp)

                if imp["type"] == "import":
                    module = imp["module"]

                    # 检查是否是标准库模块
                    if module.split(".")[0] in self.stdlib_modules:
                        continue

                    # 检查模块是否存在于项目中
                    if module not in self.project_modules:
                        # 可能是相对导入或模块名称错误
                        if (
                            current_package
                            and f"{current_package}.{module}" in self.project_modules
                        ):
                            # 可以通过添加当前包前缀修复
                            result.error_message = f"模块 '{module}' 不存在，但 '{current_package}.{module}' 存在"
                            result.fix_method = "添加包前缀"
                            result.module_name = module
                            result.fixed_import = (
                                f"from {current_package} import {module}"
                            )
                            errors.append(result)
                        else:
                            # 尝试寻找相似的模块名
                            similar_modules = self._find_similar_modules(
                                module)
                            if similar_modules:
                                result.error_message = f"模块 '{module}' 不存在，可能是 '{similar_modules[0]}'"
                                result.fix_method = "修正模块名称"
                                result.module_name = module
                                result.fixed_import = f"import {similar_modules[0]}"
                                if imp["alias"]:
                                    result.fixed_import += f" as {imp['alias']}"
                                errors.append(result)

                elif imp["type"] == "from":
                    module = imp["module"]
                    level = imp["level"]

                    if level > 0:
                        # 相对导入
                        parts = current_package.split(".")
                        if len(parts) < level:
                            result.error_message = (
                                f"相对导入层级 ({level}) 超出了当前包的层级"
                            )
                            result.fix_method = "减少相对导入层级"
                            result.module_name = module
                            result.fixed_import = f"from {'.' * (len(parts))} {module} import {imp['name']}"
                            if imp["alias"]:
                                result.fixed_import += f" as {imp['alias']}"
                            errors.append(result)
                    else:
                        # 非相对导入
                        if (
                            module
                            and module.split(".")[0] not in self.stdlib_modules
                            and module not in self.project_modules
                        ):
                            # 可能是模块名称错误
                            similar_modules = self._find_similar_modules(
                                module)
                            if similar_modules:
                                result.error_message = f"模块 '{module}' 不存在，可能是 '{similar_modules[0]}'"
                                result.fix_method = "修正模块名称"
                                result.module_name = module
                                result.fixed_import = (
                                    f"from {similar_modules[0]} import {imp['name']}"
                                )
                                if imp["alias"]:
                                    result.fixed_import += f" as {imp['alias']}"
                                errors.append(result)

            return errors

        except Exception as e:
            self.log(f"检查导入错误时出错: {file_path} - {str(e)}")
            return []

        finally:
            # 恢复原始sys.path
            sys.path = original_sys_path

    def _format_import(self, imp):
        """格式化导入语句"""
        if imp["type"] == "import":
            result = f"import {imp['module']}"
            if imp["alias"]:
                result += f" as {imp['alias']}"
            return result

        elif imp["type"] == "from":
            result = f"from {'.' * imp['level']}{imp['module']} import {imp['name']}"
            if imp["alias"]:
                result += f" as {imp['alias']}"
            return result

    def _find_similar_modules(self, module_name):
        """寻找相似的模块名"""
        similar_modules = []

        # 简单的编辑距离函数
        def levenshtein(s1, s2):
            if len(s1) < len(s2):
                return levenshtein(s2, s1)
            if len(s2) == 0:
                return len(s1)

            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(
                        min(insertions, deletions, substitutions))
                previous_row = current_row

            return previous_row[-1]

        # 计算编辑距离
        for proj_module in self.project_modules:
            # 只比较模块名最后一部分
            proj_parts = proj_module.split(".")
            mod_parts = module_name.split(".")

            # 如果模块名的一部分匹配，增加相似度
            if mod_parts[-1] == proj_parts[-1]:
                similar_modules.append((0, proj_module))
            else:
                # 计算编辑距离
                distance = levenshtein(mod_parts[-1], proj_parts[-1])
                if distance <= 3:  # 最多允许3个字符的差异
                    similar_modules.append((distance, proj_module))

        # 按编辑距离排序
        similar_modules.sort()
        return [module for _, module in similar_modules]

    def _fix_import_errors(self, file_path, errors):
        """修复文件中的导入错误"""
        if not errors:
            return False

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # 按行号从大到小排序，避免修改后行号变化
            errors.sort(
                key=lambda e: self._extract_line_number(
                    e.original_import, content),
                reverse=True,
            )

            lines = content.split("\n")
            fixed = False

            for error in errors:
                # 查找导入语句的行号
                lineno = self._extract_line_number(
                    error.original_import, content)
                if lineno is None or lineno <= 0 or lineno > len(lines):
                    continue

                # 替换导入语句
                lines[lineno - 1] = error.fixed_import
                fixed = True

                self.log(
                    f"行 {lineno}: {error.original_import} -> {error.fixed_import}"
                )

            if fixed:
                # 保存修复后的内容
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

                return True

            return False

        except Exception as e:
            self.log(f"修复导入错误时出错: {file_path} - {str(e)}")
            return False

    def _extract_line_number(self, import_stmt, content):
        """从内容中提取导入语句的行号"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if import_stmt in line:
                return i + 1
        return None

    def _check_missing_init(self):
        """检查缺失的__init__.py文件并创建"""
        created_count = 0

        for root, dirs, files in os.walk(self.root_dir):
            # 检查是否有Python文件但没有__init__.py
            has_py_files = any(f.endswith(".py") and f !=
                               "__init__.py" for f in files)
            has_init = "__init__.py" in files

            if has_py_files and not has_init:
                init_path = os.path.join(root, "__init__.py")

                # 确保这个目录应该是一个包
                rel_path = os.path.relpath(root, self.root_dir)
                if rel_path == ".":
                    continue  # 跳过项目根目录

                parent_dir = os.path.dirname(root)
                parent_has_init = os.path.exists(
                    os.path.join(parent_dir, "__init__.py")
                )

                if parent_has_init or rel_path.count(os.path.sep) == 0:
                    # 创建空的__init__.py文件
                    with open(init_path, "w", encoding="utf-8") as f:
                        f.write("# -*- coding: utf-8 -*-\n")

                    self.log(f"创建 __init__.py: {init_path}")
                    created_count += 1

                    # 更新项目模块列表
                    package_path = rel_path.replace(os.path.sep, ".")
                    self.project_modules.add(package_path)
                    self.init_files.add(init_path)

        return created_count

    def fix_imports_in_file(self, file_path):
        """修复文件中的导入问题"""
        # 检查导入错误
        errors = self._check_import_errors(file_path)

        if not errors:
            return False

        self.log(f"\n检查文件: {file_path}")
        self.log(f"发现 {len(errors)} 个导入问题")

        # 创建备份
        if not self.backup_file(file_path):
            self.log(f"跳过修复 (无法创建备份): {file_path}")
            return False

        # 修复导入错误
        if self._fix_import_errors(file_path, errors):
            self.log(f"成功修复导入问题: {file_path}")
            return True
        else:
            self.log(f"无法修复导入问题: {file_path}")
            return False

    def scan_and_fix_imports(self):
        """扫描项目并修复所有导入问题"""
        self.log(f"开始扫描目录: {self.root_dir}")

        # 首先检查缺失的__init__.py文件
        created_inits = self._check_missing_init()
        self.log(f"创建了 {created_inits} 个缺失的 __init__.py 文件")

        # 如果创建了新的__init__.py文件，重新分析项目结构
        if created_inits > 0:
            self._analyze_project_structure()

        # 修复导入问题
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.stats["total_files"] += 1

                    if self.stats["total_files"] % 10 == 0:
                        self.log(f"已检查文件数: {self.stats['total_files']}...")

                    # 检查和修复导入问题
                    try:
                        errors = self._check_import_errors(file_path)
                        if errors:
                            self.stats["error_files"] += 1
                            if self.fix_imports_in_file(file_path):
                                self.stats["fixed_files"] += 1
                    except Exception as e:
                        self.log(f"处理文件出错: {file_path} - {str(e)}")

        self.log("\n== 修复完成 ==")
        self.log(f"检查的文件总数: {self.stats['total_files']}")
        self.log(f"有导入问题的文件数: {self.stats['error_files']}")
        self.log(f"成功修复的文件数: {self.stats['fixed_files']}")

        return self.stats


def main():
    # 默认目录路径
    default_dir = r"C:\Users\tiger\Desktop\key\code\organized_project"

    # 使用命令行参数或默认路径
    directory = sys.argv[1] if len(sys.argv) > 1 else default_dir

    if not os.path.exists(directory):
        print(f"错误: 目录不存在 - {directory}")
        return

    # 创建修复器实例
    fixer = ImportPathFixer(directory, verbose=True, create_backup=True)

    # 记录开始时间
    start_time = time.time()

    # 执行修复
    fixer.scan_and_fix_imports()

    # 计算总执行时间
    elapsed = time.time() - start_time
    print(f"总耗时: {elapsed:.2f} 秒")

    # 尝试运行测试脚本
    test_script = os.path.join(directory, "tests", "master_test.py")
    if os.path.exists(test_script):
        print("\n尝试运行测试脚本...")
        try:
            import subprocess

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
                print("所有测试通过！系统已成功修复")
            else:
                print("测试未通过。请查看错误信息以进行进一步修复")
        except Exception as e:
            print(f"运行测试时出错: {str(e)}")
    else:
        print(f"测试脚本不存在: {test_script}")


if __name__ == "__main__":
    main()