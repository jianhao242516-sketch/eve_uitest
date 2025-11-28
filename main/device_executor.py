#!/usr/bin/env python3
import yaml, time
from utils.driver import get_driver, restart_app
from utils.logger import Logger

def run_case_on_device(device_info, bundle_id, yaml_path, run_number=1, results_file=None, app_path=None, reinstall=False):
    logger = Logger(prefix=device_info.get('name', 'DEV'))
    logger.log(f"设备子进程启动: {device_info} (第{run_number}次执行)")

    # 设置环境变量，传递运行次数信息给截图功能
    import os
    os.environ['CURRENT_RUN_NUMBER'] = str(run_number)

    # 测试结果统计
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'device_name': device_info.get('name', 'DEV'),
        'run_number': run_number
    }

    try:
        driver = get_driver(device_info, appium_server=device_info['appium_server'], app_path=app_path, bundle_id=bundle_id, reinstall=reinstall)
    except Exception as e:
        logger.log(f"无法创建 driver: {e}")
        return

    try:
        restart_app(driver, bundle_id)
        logger.log("✅ APP已启动")
    except Exception as e:
        logger.log(f"重启 App 出错: {e}")
    
    # 只有在重新安装 app 且 bundleId 包含 "MTKing" 时才执行初始化操作
    if reinstall and app_path:
        if bundle_id and 'MTKing' in bundle_id:
            try:
                logger.log("🔧 检测到重新安装且 bundleId 包含 'MTKing'，开始执行 App 初始化操作...")
                from pages.evev.base_page import initialize_app
                initialize_app(driver)
                logger.log("✅ App 初始化操作完成")
            except Exception as e:
                logger.log(f"⚠️ App 初始化操作出错: {e}")
        else:
            logger.log(f"ℹ️ bundleId 不包含 'MTKing'（bundleId: {bundle_id}），跳过初始化操作")
    else:
        logger.log("ℹ️ 未重新安装 app，跳过初始化操作")

    # 如果传入的是 .py 文件，自动尝试 .yaml 文件
    import os
    if yaml_path.endswith('.py'):
        yaml_path_alt = yaml_path.replace('.py', '.yaml')
        if os.path.exists(yaml_path_alt):
            logger.log(f"⚠️ 检测到传入的是 .py 文件，自动使用对应的 .yaml 文件: {yaml_path_alt}")
            yaml_path = yaml_path_alt
        else:
            logger.log(f"⚠️ 传入的是 .py 文件，但对应的 .yaml 文件不存在: {yaml_path_alt}")
    
    # 检查文件是否存在
    if not os.path.exists(yaml_path):
        logger.log(f"❌ 测试用例文件不存在: {yaml_path}")
        return
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        cases = yaml.safe_load(f)

    for case_index, case in enumerate(cases):
        logger.log(f"开始用例 ({case_index + 1}/{len(cases)}): {case.get('name')}")
        test_results['total'] += 1
        case_failed = False  # 用例失败标志
        
        # 设置用例索引环境变量，供截图功能使用
        import os
        os.environ['CURRENT_CASE_INDEX'] = str(case_index + 1)
        
        # 每个用例开始时重启APP，确保环境干净
        try:
            logger.log(f"🔄 重启APP为用例做好准备...")
            restart_app(driver, bundle_id)
            logger.log(f"✅ APP已重启")
            time.sleep(2)  # 给APP一点启动时间
        except Exception as e:
            logger.log(f"⚠️ 重启APP失败: {e}")
        
        for step in case.get('steps', []):
            if case_failed:  # 如果用例已失败，跳过后续步骤
                break
                
            page_name = step.get('page')
            actions = step.get('actions', [])
            
            # 根据页面名称前缀或 bundleId 判断项目类型
            # 优先级：页面名称前缀 > bundleId
            # 如果页面名称以 M_ 开头，使用 evem 项目
            # 如果 bundleId 包含 "eve"，根据页面名判断使用 evem 或 evev 项目
            # 如果 bundleId 不包含 "eve"，使用 other 项目
            if page_name.startswith('M_'):
                # 页面名称以 M_ 开头，使用 evem 项目
                project_dir = 'evem'
            elif bundle_id and 'eve' in bundle_id.lower():
                # bundleId 包含 eve，使用 evev 项目（默认）
                # 注意：如果页面名以 M_ 开头，上面已经处理为 evem
                project_dir = 'evev'
            else:
                # bundleId 不包含 eve，使用 other 项目
                project_dir = 'other'
            
            # 尝试加载页面类，如果不存在则动态创建
            page_class = None
            try:
                import re
                
                # 对于 M_ 前缀的页面，尝试多种模块名格式
                if page_name.startswith('M_'):
                    # 方式1: 尝试 M_login_page 格式（匹配文件名）
                    # M_LoginPage -> 先移除 M_，转换 LoginPage -> login_page，再加回 M_
                    clean_page_name = page_name.replace('M_', '')  # M_LoginPage -> LoginPage
                    module_base = re.sub(r'(?<!^)(?=[A-Z])', '_', clean_page_name).lower()  # LoginPage -> login_page
                    module_name1 = f"M_{module_base}"  # M_login_page
                    # 方式2: 尝试 login_page 格式（移除 M_ 前缀）
                    module_name2 = module_base  # login_page
                    
                    # 先尝试方式1（匹配文件名）
                    try:
                        logger.log(f"🔍 尝试导入模块: pages.{project_dir}.{module_name1}")
                        module = __import__(f"pages.{project_dir}.{module_name1}", fromlist=[page_name])
                        logger.log(f"📦 模块导入成功: {module}")
                        page_class = getattr(module, page_name, None)
                        logger.log(f"🔍 查找类 {page_name}，结果: {page_class}")
                        if page_class:
                            logger.log(f"✅ 从 {project_dir} 项目加载页面类: {page_name} (模块: {module_name1})")
                    except (ImportError, AttributeError) as e1:
                        logger.log(f"⚠️ 方式1导入失败: {e1}")
                        # 再尝试方式2
                        try:
                            logger.log(f"🔍 尝试导入模块: pages.{project_dir}.{module_name2}")
                            module = __import__(f"pages.{project_dir}.{module_name2}", fromlist=[page_name])
                            logger.log(f"📦 模块导入成功: {module}")
                            page_class = getattr(module, page_name, None)
                            logger.log(f"🔍 查找类 {page_name}，结果: {page_class}")
                            if page_class:
                                logger.log(f"✅ 从 {project_dir} 项目加载页面类: {page_name} (模块: {module_name2})")
                        except (ImportError, AttributeError) as e2:
                            logger.log(f"⚠️ 方式2导入也失败: {e2}")
                            pass
                else:
                    # 普通页面名称
                    module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', page_name).lower()  # LoginPage -> login_page
                    
                    # 尝试从项目目录加载
                    try:
                        module = __import__(f"pages.{project_dir}.{module_name}", fromlist=[page_name])
                        page_class = getattr(module, page_name, None)
                        if page_class:
                            logger.log(f"✅ 从 {project_dir} 项目加载页面类: {page_name}")
                    except (ImportError, AttributeError):
                        # 如果项目目录中找不到，尝试从根目录加载（向后兼容）
                        try:
                            module = __import__(f"pages.{module_name}", fromlist=[page_name])
                            page_class = getattr(module, page_name, None)
                            if page_class:
                                logger.log(f"✅ 从根目录加载页面类: {page_name}")
                        except (ImportError, AttributeError):
                            pass
            except Exception as e:
                logger.log(f"⚠️ 页面类 {page_name} 不存在，将动态创建: {e}")
            
            # 如果页面类不存在，动态创建
            if page_class is None:
                # 根据项目目录导入 BasePage
                if project_dir == 'evem':
                    from pages.evem.base_page import BasePage
                elif project_dir == 'evev':
                    from pages.evev.base_page import BasePage
                else:  # other
                    from pages.other.base_page import BasePage
                
                # 动态创建页面类
                def __init__(self, driver):
                    BasePage.__init__(self, driver)
                    self.page_name = page_name
                
                # 创建类字典
                class_dict = {
                    '__init__': __init__,
                    'page_name': page_name
                }
                
                # 动态创建类
                page_class = type(page_name, (BasePage,), class_dict)
                logger.log(f"✅ 已动态创建页面类: {page_name} (项目: {project_dir})")
            
            page = page_class(driver)
            
            for action in actions:
                if case_failed:  # 如果用例已失败，跳出action循环
                    break
                    
                # 检查是否为wait操作
                if action.get('method') == 'wait':
                    wait_time = action.get('params', 1)  # 默认等待1秒
                    logger.log(f"执行强制等待: {wait_time}秒")
                    time.sleep(wait_time)
                    continue
                
                method_name = action.get('method')
                params = action.get('params', None)
                logger.log(f"执行: {page_name}.{method_name}({params})")
                method = getattr(page, method_name, None)
                if not method:
                    logger.log(f"方法未找到: {page_name}.{method_name}")
                    continue
                
                try:
                    # 执行方法
                    if params is not None:
                        # 处理不同参数格式
                        if isinstance(params, str) and '.' in params and method_name.startswith('assert_'):
                            # 元素名称格式，如 'HomePage.searchuser'
                            result = method(params)
                        elif isinstance(params, list) and len(params) >= 2 and method_name.startswith('assert_'):
                            # 传统格式，如 ['xpath', '//XCUIElementTypeTextField'] 或 ['HomePage.searchuser', 'expected_text']
                            if len(params) == 2 and not params[0] in ['xpath', 'id', 'name', 'class', 'tag', 'accessibility_id']:
                                # 元素名称 + 文本参数格式
                                result = method(params[0], params[1])
                            else:
                                # 传统定位器格式
                                result = method(*params)
                        else:
                            # 普通参数
                            if isinstance(params, list):
                                result = method(*params)
                            else:
                                result = method(params)
                    else:
                        result = method()
                    
                    # 检查方法返回值，如果返回 False 也标记为失败
                    if result is False:
                        logger.log(f"❌ 方法返回 False，标记用例失败: {page_name}.{method_name}")
                        case_failed = True
                        break  # 跳出action循环
                    
                    # 如果是断言方法，记录断言结果
                    if method_name.startswith('assert_'):
                        logger.log(f"断言通过: {method_name}")
                        
                except AssertionError as e:
                    logger.log(f"断言失败: {method_name} - {str(e)}")
                    case_failed = True  # 标记用例失败
                    break  # 跳出action循环
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    logger.log(f"执行出错: {page_name}.{method_name} - {error_type}: {error_msg}")
                    
                    # 检查是否是元素找不到或超时的错误（所有元素查找相关的异常）
                    element_not_found_keywords = [
                        "NoSuchElement",
                        "TimeoutException",
                        "Timeout",
                        "element could not be located",
                        "Unable to locate element",
                        "Message: An element could not be located",
                        "selenium.common.exceptions.NoSuchElementException",
                        "selenium.common.exceptions.TimeoutException",
                        "appium.common.exceptions.NoSuchContextException"
                    ]
                    
                    is_element_error = any(keyword in error_msg or keyword in error_type for keyword in element_not_found_keywords)
                    
                    if is_element_error:
                        logger.log(f"❌ 元素找不到或超时，立即停止执行当前用例: {case.get('name')}")
                        logger.log(f"   错误类型: {error_type}")
                        logger.log(f"   错误信息: {error_msg}")
                        case_failed = True  # 标记用例失败
                        break  # 跳出action循环
                    else:
                        # 其他类型的错误也停止执行
                        logger.log(f"❌ 执行出错，停止执行当前用例: {case.get('name')}")
                        logger.log(f"   错误类型: {error_type}")
                        logger.log(f"   错误信息: {error_msg}")
                        case_failed = True  # 标记用例失败
                        break  # 跳出action循环
        
        if case_failed:
            logger.log(f"❌ 用例失败: {case.get('name')}")
            test_results['failed'] += 1
        else:
            logger.log(f"✅ 用例通过: {case.get('name')}")
            test_results['passed'] += 1
        
        # 用例之间等待，确保串行执行
        if case_index < len(cases) - 1:  # 不是最后一个用例
            logger.log(f"⏳ 等待3秒后执行下一个用例...")
            time.sleep(3)

    try:
        driver.quit()
    except Exception:
        pass

    logger.log('设备执行结束。')
    
    # 只在日志中记录结果，不打印到控制台
    logger.log(f"📊 设备 {test_results['device_name']} 第{run_number}次执行结果: 总用例数={test_results['total']}, 通过={test_results['passed']}, 失败={test_results['failed']}")
    
    # 将结果写入文件
    if results_file:
        import json
        try:
            with open(results_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(test_results, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.log(f"写入结果文件失败: {e}")
    
    # 返回测试结果
    return test_results
