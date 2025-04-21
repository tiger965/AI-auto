# ui/cli/commands.py
"""命令行命令处理器"""

import sys
import os
import time

# 尝试导入formatters模块，如果不存在则使用简单版本
try:
    from ui.cli.formatters import format_output
except ImportError:
    # 简单版本的format_output
    def format_output(result):
        """简单版本的输出格式化"""
        if not result:
            return

        if isinstance(result, dict) and "type" in result:
            result_type = result["type"]
            if result_type == "exit":
                print("再见！CLI正在关闭。")
                sys.exit(0)
            elif result_type == "error":
                print(f"错误: {result.get('content', '未知错误')}")
            else:
                print(str(result))
        else:
            print(str(result))


class CommandProcessor:
    """命令行命令处理器"""

    def __init__(self, engine):
        """初始化命令处理器"""
        self.engine = engine
        self.running = False
        self.commands = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "start": self.cmd_start,
            "stop": self.cmd_stop,
            "status": self.cmd_status,
            "version": self.cmd_version,
            "modules": self.cmd_modules,
            "config": self.cmd_config,
        }

        print("命令处理器初始化完成")

    def start_cli(self):
        """启动命令行循环"""
        self.running = True

        while self.running:
            try:
                # 显示提示符
                command = input("\n> ").strip()

                if not command:
                    continue

                # 处理命令
                parts = command.split(maxsplit=1)
                cmd_name = parts[0].lower()
                cmd_args = parts[1] if len(parts) > 1 else ""

                if cmd_name in self.commands:
                    result = self.commands[cmd_name](cmd_args)
                    format_output(result)
                else:
                    print(f"未知命令: '{cmd_name}'，输入 'help' 查看可用命令")

            except KeyboardInterrupt:
                print("\n操作已取消")
            except EOFError:
                print("\n再见！")
                self.running = False
            except Exception as e:
                print(f"错误: {str(e)}")

        # 确保引擎停止
        if self.engine.running:
            self.engine.stop()

        return True

    def cmd_help(self, args):
        """显示帮助信息"""
        help_text = """
可用命令:
  help                显示此帮助信息
  exit, quit          退出系统
  start               启动核心引擎
  stop                停止核心引擎
  status              显示系统状态
  version             显示系统版本
  modules             列出已加载的模块
  config [key]        显示配置信息
"""
        print(help_text)
        return {"type": "info", "content": "帮助信息已显示"}

    def cmd_exit(self, args):
        """退出系统"""
        print("正在关闭系统...")
        self.running = False

        # 确保引擎停止
        if self.engine.running:
            self.engine.stop()

        return {"type": "exit"}

    def cmd_start(self, args):
        """启动核心引擎"""
        if self.engine.running:
            return {"type": "info", "content": "引擎已经在运行中"}

        success = self.engine.start()
        if success:
            return {"type": "info", "content": "引擎启动成功"}
        else:
            return {"type": "error", "content": "引擎启动失败"}

    def cmd_stop(self, args):
        """停止核心引擎"""
        if not self.engine.running:
            return {"type": "info", "content": "引擎未在运行"}

        success = self.engine.stop()
        if success:
            return {"type": "info", "content": "引擎已停止"}
        else:
            return {"type": "error", "content": "引擎停止失败"}

    def cmd_status(self, args):
        """显示系统状态"""
        status_info = self.engine.status()

        status_text = f"""
系统状态:
  运行状态: {'运行中' if status_info['running'] else '已停止'}
  运行时间: {status_info['uptime']:.2f}秒
  模块数量: {status_info['modules']}
  模块列表: {', '.join(status_info['module_list']) if status_info['module_list'] else '无'}
"""
        print(status_text)
        return {
            "type": "status",
            "components": {
                "engine": "running" if status_info["running"] else "stopped"
            },
        }

    def cmd_version(self, args):
        """显示系统版本"""
        from config import get_config

        config = get_config()

        version_text = f"""
系统版本信息:
  应用名称: {config.get('app_name', 'AI自动化系统')}
  版本号: {config.get('version', '1.0.0')}
  调试模式: {'启用' if config.get('debug', False) else '禁用'}
"""
        print(version_text)
        return {
            "type": "info",
            "content": f"当前版本: {config.get('version', '1.0.0')}",
        }

    def cmd_modules(self, args):
        """列出已加载的模块"""
        modules = self.engine.modules

        if not modules:
            print("当前没有已加载的模块")
            return {"type": "info", "content": "无已加载模块"}

        modules_text = "\n已加载的模块:\n"
        for name in modules:
            modules_text += f"  - {name}\n"

        print(modules_text)
        return {"type": "info", "content": f"已加载 {len(modules)} 个模块"}

    def cmd_config(self, args):
        """显示配置信息"""
        from config import get_config

        config = get_config()

        if not args:
            # 显示顶级配置项
            config_text = "\n配置信息:\n"
            for key, value in config.items():
                if isinstance(value, dict):
                    config_text += f"  {key}: {len(value)} 个配置项\n"
                else:
                    config_text += f"  {key}: {value}\n"

            print(config_text)
            return {"type": "info", "content": "配置信息已显示"}

        # 显示特定配置项
        keys = args.split(".")
        current = config

        try:
            for key in keys:
                current = current[key]

            if isinstance(current, dict):
                config_text = f"\n配置项 '{args}':\n"
                for k, v in current.items():
                    config_text += f"  {k}: {v}\n"
                print(config_text)
            else:
                print(f"\n配置项 '{args}': {current}")

            return {"type": "info", "content": f"配置项 '{args}' 已显示"}
        except KeyError:
            return {"type": "error", "content": f"配置项 '{args}' 不存在"}


# 为了便于测试
if __name__ == "__main__":
    from core.engine import Engine

    # 创建引擎和命令处理器
    engine = Engine()
    cmd_processor = CommandProcessor(engine)

    # 测试帮助命令
    cmd_processor.cmd_help("")