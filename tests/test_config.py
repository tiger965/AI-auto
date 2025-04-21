"""
配置模块测试脚本

用于测试配置模块的主要功能。
"""

import os
import logging
from config import (
    initialize,
    api_config,
    app_settings,
    credentials,
    paths,
    logging_config,
    validate_all_configs,
    clear_config_cache,
    get_standardized_env_var_name,
    ENV_PREFIX,
)


def test_basic_config():
    """测试基本配置功能"""
    print("=== 测试基本配置功能 ===")

    # 初始化配置模块
    initialize()

    # 获取各种配置
    api_cfg = api_config.get_config()
    app_cfg = app_settings.get_config()
    cred_cfg = credentials.get_config()
    path_cfg = paths.get_config()
    log_cfg = logging_config.get_config()

    # 打印配置信息
    print(f"API URL: {api_cfg.get('server', {}).get('url')}")
    print(f"应用名称: {app_cfg.get('app', {}).get('name')}")
    print(f"数据目录: {path_cfg.get('dirs', {}).get('data')}")
    print(f"日志级别: {log_cfg.get('level')}")

    # 不打印敏感信息
    print(
        f"API密钥存在: {'是' if 'api' in cred_cfg and 'key' in cred_cfg['api'] else '否'}"
    )


def test_environment_override():
    """测试环境变量覆盖功能"""
    print("\n=== 测试环境变量覆盖功能 ===")

    # 设置环境变量
    os.environ[get_standardized_env_var_name("API_SERVER_URL")] = (
        "http://override-api.example.com"
    )
    os.environ[get_standardized_env_var_name("APP_NAME")] = "覆盖应用名称"

    # 清除缓存以使环境变量生效
    clear_config_cache()

    # 获取配置
    api_cfg = api_config.get_config()
    app_cfg = app_settings.get_config()

    # 打印配置信息
    print(f"覆盖后的API URL: {api_cfg.get('server', {}).get('url')}")
    print(f"覆盖后的应用名称: {app_cfg.get('app', {}).get('name')}")

    # 清除环境变量
    del os.environ[get_standardized_env_var_name("API_SERVER_URL")]
    del os.environ[get_standardized_env_var_name("APP_NAME")]


def test_cache_mechanism():
    """测试缓存机制"""
    print("\n=== 测试缓存机制 ===")

    # 首次加载
    import time

    start = time.time()
    api_config.get_config()
    first_load = time.time() - start

    # 缓存加载
    start = time.time()
    api_config.get_config()
    cached_load = time.time() - start

    print(f"首次加载时间: {first_load:.6f}秒")
    print(f"缓存加载时间: {cached_load:.6f}秒")
    print(f"性能提升: {first_load/cached_load:.1f}倍")

    # 清除缓存
    clear_config_cache()
    print("缓存已清除")


def test_validation():
    """测试配置验证功能"""
    print("\n=== 测试配置验证功能 ===")

    # 设置无效的环境变量
    os.environ[get_standardized_env_var_name("API_TIMEOUT")] = "invalid"

    try:
        # 清除缓存以使环境变量生效
        clear_config_cache()

        # 获取配置
        api_cfg = api_config.get_config()
        print("验证成功：无效的超时值被忽略")

    except ValueError as e:
        print(f"验证失败：{str(e)}")

    finally:
        # 清除环境变量
        del os.environ[get_standardized_env_var_name("API_TIMEOUT")]


def main():
    """主测试函数"""
    print(f"配置模块测试 (环境变量前缀: {ENV_PREFIX})")

    # 运行各种测试
    test_basic_config()
    test_environment_override()
    test_cache_mechanism()
    test_validation()

    print("\n所有测试完成!")


if __name__ == "__main__":
    main()