# _*_ coding: utf-8 _*_
"""
______________________________________________
project Name : app-ui
File Name : test_setup_methods
Description : 测试用例前置方法集合，组合 handle_switch.py 中的方法
Author : ruby
date : 2025/12/8
______________________________________________

"""
from api_scripts.handle_switch import (
    update_module,
    update_login_qr_code,
    update_login_mode,
    update_dimension,
    update_skin_age,
    update_saas,
    update_app_mode,
    update_app_theme,
    update_store_grant_type,
    update_shoot_support,
    update_common_function,
    update_page_mode
)
import api_scripts.handle_switch as handle_switch_module
import re
import ast
from utils.logger import Logger

logger = Logger(prefix='SETUP')


def setup_method_1():
    """
    示例方法1：配置基础功能开关
    可以根据实际需求组合多个 handle_switch 方法
    """
    logger.log("执行前置方法: setup_method_login_qr_code")
    try:
        # 示例：开启扫码登录
        update_login_qr_code(1)
        # 示例：配置登录模式
        # update_login_mode('user_login_type_eve', [1, 2])
        logger.log("✅ setup_method_login_qr_code 执行完成")
    except Exception as e:
        logger.log(f"❌ setup_method_login_qr_code 执行失败: {e}")
        raise


def setup_method_2():
    """
    示例方法2：配置检测维度和报告页功能
    """
    logger.log("执行前置方法: setup_method_2")
    try:
        # 示例：开启某些检测维度
        update_dimension('eve', {'pore': 1, 'blackhead': 1, 'speckle': 1})
        # 示例：配置报告页功能
        update_saas('eve', {'saas_skin_report': 1, 'saas_section': 1})
        logger.log("✅ setup_method_2 执行完成")
    except Exception as e:
        logger.log(f"❌ setup_method_2 执行失败: {e}")
        raise


def setup_method_3():
    """
    示例方法3：配置APP模式和主题
    """
    logger.log("执行前置方法: setup_method_3")
    try:
        # 示例：设置APP模式
        update_app_mode(app_mode=1)
        # 示例：设置主题
        update_app_theme(0)  # 科技风
        logger.log("✅ setup_method_3 执行完成")
    except Exception as e:
        logger.log(f"❌ setup_method_3 执行失败: {e}")
        raise


# 方法注册表，用于动态调用
SETUP_METHODS = {
    'setup_method_1': setup_method_1,
    'setup_method_2': setup_method_2,
    'setup_method_3': setup_method_3,
    # 可以继续添加更多方法...
}


def parse_method_call(method_string):
    """
    解析方法调用字符串，支持多种格式：
    1. 'update_login_qr_code(1)' - 单个参数
    2. 'update_dimension("eve", {"pore": 1})' - 多个参数
    3. 'update_login_qr_code' - 无参数的方法调用
    4. 'setup_method_1' - 已注册的包装方法
    
    :param method_string: 方法调用字符串
    :return: (method_name, args, kwargs) 或 None（如果解析失败）
    """
    if not method_string:
        return None
    
    # 检查是否是已注册的包装方法（无参数）
    if method_string in SETUP_METHODS:
        return (method_string, (), {})
    
    # 尝试解析为方法调用格式：method_name(args)
    match = re.match(r'^(\w+)\((.*)\)$', method_string, re.DOTALL)
    if match:
        method_name = match.group(1)
        params_str = match.group(2).strip()
        
        # 如果没有参数
        if not params_str:
            return (method_name, (), {})
        
        # 尝试解析参数（支持多个参数）
        try:
            # 使用 ast.literal_eval 安全地解析 Python 字面量
            # 如果参数是单个值，直接解析
            try:
                params = ast.literal_eval(params_str)
                # 如果是单个值
                if not isinstance(params, (list, tuple, dict)):
                    return (method_name, (params,), {})
                # 如果是列表，作为多个位置参数
                elif isinstance(params, list):
                    return (method_name, tuple(params), {})
                # 如果是元组，直接使用
                elif isinstance(params, tuple):
                    return (method_name, params, {})
                # 如果是字典且是单个参数，按位置参数传递给方法
                # 说明：诸如 update_module_ext_common({'saas_change_logo': 0})
                # 的写法应当将整个 dict 作为一个参数而非拆成 kwargs
                elif isinstance(params, dict):
                    return (method_name, (params,), {})
            except (ValueError, SyntaxError):
                # 如果单个 literal_eval 失败，尝试解析多个参数
                # 使用更智能的方式：尝试将参数字符串解析为 Python 表达式
                # 例如: '"eve", {"pore": 1}' -> ('eve', {'pore': 1})
                try:
                    # 包装成元组来解析多个参数
                    wrapped = f"({params_str})"
                    params = ast.literal_eval(wrapped)
                    if isinstance(params, tuple):
                        return (method_name, params, {})
                    else:
                        return (method_name, (params,), {})
                except (ValueError, SyntaxError):
                    # 如果还是失败，尝试作为字符串参数
                    return (method_name, (params_str,), {})
        except Exception:
            # 如果所有解析都失败，尝试作为字符串参数
            return (method_name, (params_str,), {})
    
    # 如果都不匹配，可能是简单的方法名（无参数）
    return (method_string, (), {})


def execute_setup_method(method_name):
    """
    执行指定的前置方法
    
    支持三种方式：
    1. 已注册的包装方法：'setup_method_1'
    2. 直接调用 handle_switch 中的方法（无参数）：'update_login_qr_code'
    3. 直接调用 handle_switch 中的方法（带参数）：'update_login_qr_code(1)'
    
    :param method_name: 方法名称（字符串），可以是 'method_name' 或 'method_name(args)'
    :return: 执行结果
    """
    if not method_name:
        logger.log("⚠️ 未指定前置方法，跳过")
        return True
    
    # 解析方法调用
    parsed = parse_method_call(method_name)
    if not parsed:
        logger.log(f"❌ 无法解析前置方法: {method_name}")
        return False
    
    method_name_parsed, args, kwargs = parsed
    
    try:
        # 首先检查是否是已注册的包装方法
        if method_name_parsed in SETUP_METHODS:
            logger.log(f"🔧 开始执行前置方法: {method_name}")
            method = SETUP_METHODS[method_name_parsed]
            method()
            logger.log(f"✅ 前置方法 '{method_name}' 执行成功")
            return True
        
        # 尝试从 handle_switch 模块中获取方法
        if hasattr(handle_switch_module, method_name_parsed):
            logger.log(f"🔧 开始执行前置方法: {method_name}")
            method = getattr(handle_switch_module, method_name_parsed)
            
            # 调用方法
            if args or kwargs:
                method(*args, **kwargs)
            else:
                method()
            
            logger.log(f"✅ 前置方法 '{method_name}' 执行成功")
            return True
        else:
            logger.log(f"❌ 前置方法 '{method_name_parsed}' 不存在")
            logger.log(f"可用包装方法: {', '.join(SETUP_METHODS.keys())}")
            logger.log(f"可用直接方法: update_login_qr_code, update_login_mode, update_dimension, update_skin_age, update_saas, update_app_mode, update_app_theme, update_store_grant_type, update_shoot_support, update_common_function, update_page_mode, update_module")
            return False
            
    except Exception as e:
        logger.log(f"❌ 前置方法 '{method_name}' 执行失败: {e}")
        import traceback
        logger.log(f"错误详情: {traceback.format_exc()}")
        return False


# ==================== Teardown 方法 ====================

def teardown_method_1():
    """
    示例清理方法1：恢复默认配置
    """
    logger.log("执行清理方法: teardown_method_1")
    try:
        # 示例：恢复扫码登录为默认状态
        update_login_qr_code(2)
        logger.log("✅ teardown_method_1 执行完成")
    except Exception as e:
        logger.log(f"❌ teardown_method_1 执行失败: {e}")
        raise


def teardown_method_2():
    """
    示例清理方法2：关闭某些功能
    """
    logger.log("执行清理方法: teardown_method_2")
    try:
        # 示例：关闭某些检测维度
        update_dimension('eve', {'pore': 0})
        logger.log("✅ teardown_method_2 执行完成")
    except Exception as e:
        logger.log(f"❌ teardown_method_2 执行失败: {e}")
        raise


# Teardown 方法注册表，用于动态调用
TEARDOWN_METHODS = {
    'teardown_method_1': teardown_method_1,
    'teardown_method_2': teardown_method_2,
    # 可以继续添加更多方法...
    # 也可以复用 setup 方法
    'setup_method_1': setup_method_1,  # 示例：复用 setup 方法
}


def execute_teardown_method(method_name):
    """
    执行指定的清理方法
    
    支持三种方式：
    1. 已注册的清理方法：'teardown_method_1'
    2. 直接调用 handle_switch 中的方法（无参数）：'update_login_qr_code'
    3. 直接调用 handle_switch 中的方法（带参数）：'update_login_qr_code(2)'
    
    :param method_name: 方法名称（字符串），可以是 'method_name' 或 'method_name(args)'
    :return: 执行结果
    """
    if not method_name:
        logger.log("⚠️ 未指定清理方法，跳过")
        return True
    
    # 解析方法调用
    parsed = parse_method_call(method_name)
    if not parsed:
        logger.log(f"❌ 无法解析清理方法: {method_name}")
        return False
    
    method_name_parsed, args, kwargs = parsed
    
    try:
        # 首先检查是否是已注册的清理方法
        if method_name_parsed in TEARDOWN_METHODS:
            logger.log(f"🧹 开始执行清理方法: {method_name}")
            method = TEARDOWN_METHODS[method_name_parsed]
            method()
            logger.log(f"✅ 清理方法 '{method_name}' 执行成功")
            return True
        
        # 尝试从 handle_switch 模块中获取方法
        if hasattr(handle_switch_module, method_name_parsed):
            logger.log(f"🧹 开始执行清理方法: {method_name}")
            method = getattr(handle_switch_module, method_name_parsed)
            
            # 调用方法
            if args or kwargs:
                method(*args, **kwargs)
            else:
                method()
            
            logger.log(f"✅ 清理方法 '{method_name}' 执行成功")
            return True
        else:
            logger.log(f"❌ 清理方法 '{method_name_parsed}' 不存在")
            logger.log(f"可用清理方法: {', '.join(TEARDOWN_METHODS.keys())}")
            logger.log(f"可用直接方法: update_login_qr_code, update_login_mode, update_dimension, update_skin_age, update_saas, update_app_mode, update_app_theme, update_store_grant_type, update_shoot_support, update_common_function, update_page_mode, update_module")
            return False
            
    except Exception as e:
        logger.log(f"❌ 清理方法 '{method_name}' 执行失败: {e}")
        import traceback
        logger.log(f"错误详情: {traceback.format_exc()}")
        return False

